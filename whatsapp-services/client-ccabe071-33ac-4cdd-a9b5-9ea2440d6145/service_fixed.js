const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const puppeteer = require('puppeteer');

const app = express();
app.use(cors());
app.use(express.json());

// Client-specific configuration
const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_PORT = process.env.CLIENT_PORT || 3003;
const CLIENT_NAME = process.env.CLIENT_NAME || 'Cliente Final Test';
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_ASSISTANT_ID = process.env.OPENAI_ASSISTANT_ID;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';

let client = null;
let qrCodeData = null;
let isConnected = false;
let connectedUser = null;
let isInitializing = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;

console.log(`Starting WhatsApp service for ${CLIENT_NAME} on port ${CLIENT_PORT}`);

// Enhanced Puppeteer configuration for deployment
const getPuppeteerConfig = () => {
    const uniqueProfileDir = `/tmp/whatsapp-chrome-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const baseConfig = {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-sync',
            '--disable-translate',
            '--disable-plugins',
            '--disable-component-extensions-with-background-pages',
            `--user-data-dir=${uniqueProfileDir}`
        ]
    };
    
    const systemChromiumPath = '/usr/bin/chromium';
    
    if (fs.existsSync(systemChromiumPath)) {
        baseConfig.executablePath = systemChromiumPath;
        console.log('Using system Chromium:', systemChromiumPath);
    } else {
        console.log('Using Puppeteer bundled Chromium (automatic)');
    }
    
    return baseConfig;
};

// Initialize WhatsApp client
async function initializeWhatsApp() {
    if (isInitializing) return;
    
    try {
        isInitializing = true;
        console.log(`Initializing WhatsApp for client ${CLIENT_NAME}`);
        
        if (client) {
            console.log('Destroying existing client...');
            try {
                await client.destroy();
            } catch (destroyError) {
                console.log('Error destroying client (safe to ignore):', destroyError.message);
            }
            client = null;
        }
        
        const sessionDir = './.wwebjs_auth';
        if (!fs.existsSync(sessionDir)) {
            fs.mkdirSync(sessionDir, { recursive: true });
        }

        const puppeteerConfig = getPuppeteerConfig();
        
        client = new Client({
            authStrategy: new LocalAuth({
                clientId: CLIENT_ID,
                dataPath: sessionDir
            }),
            puppeteer: puppeteerConfig,
            webVersionCache: {
                type: 'remote',
                remotePath: 'https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html',
            }
        });

        isInitializing = false;

        // QR Code event
        client.on('qr', async (qr) => {
            console.log(`QR Code received for client ${CLIENT_NAME}`);
            qrCodeData = qr;
            reconnectAttempts = 0;
        });

        // Authentication event
        client.on('authenticated', () => {
            console.log(`WhatsApp authenticated for client ${CLIENT_NAME}`);
        });

        // Ready event
        client.on('ready', async () => {
            console.log(`WhatsApp client ready for ${CLIENT_NAME}!`);
            isConnected = true;
            qrCodeData = null;
            
            try {
                const info = client.info;
                connectedUser = {
                    name: info.pushname || 'WhatsApp User',
                    phone: info.wid.user || 'Unknown',
                    profileImage: null,
                    connectedAt: new Date().toISOString()
                };
                console.log('Connected user:', connectedUser);
            } catch (err) {
                console.error('Error getting user info:', err);
            }
        });

        // Message received event
        client.on('message', async (message) => {
            const isOwnerCommand = message.fromMe && message.body && 
                ['pausar', 'reactivar', 'pausar todo', 'activar todo', 'estado'].includes(message.body.toLowerCase().trim());
            
            if ((!message.fromMe && message.body) || isOwnerCommand) {
                // Ignore group messages
                if (message.from.includes('-') || message.from.includes('@g.us')) {
                    console.log(`🚫 IGNORED GROUP MESSAGE from ${message.from}: ${message.body}`);
                    return;
                }
                
                if (!message.from.includes('@c.us')) {
                    console.log(`🚫 IGNORED NON-PRIVATE MESSAGE from ${message.from}`);
                    return;
                }
                
                const messageText = message.body;
                const normalizedMessage = messageText.toLowerCase().trim();
                const messageSource = message.fromMe ? "OWNER" : "CLIENT";
                
                console.log(`📱 ${messageSource} MESSAGE from ${message.from}: ${messageText}`);
                
                // Legacy bot commands for clients only
                if (!message.fromMe) {
                    if (normalizedMessage === 'activar bot') {
                        try {
                            await message.reply('✅ Bot activado. Responderé automáticamente a todos los mensajes con tu asistente personalizado.');
                            console.log('Bot activated for:', message.from);
                            return;
                        } catch (error) {
                            console.error('Error activating bot:', error);
                        }
                    }
                    
                    if (normalizedMessage === 'suspender bot') {
                        try {
                            await message.reply('⏸️ Bot suspendido. Ahora puedes usar tu celular normalmente.');
                            console.log('Bot suspended for:', message.from);
                            return;
                        } catch (error) {
                            console.error('Error suspending bot:', error);
                        }
                    }
                }
                
                // Pause control commands for everyone
                const pauseCommands = ['pausar', 'reactivar', 'pausar todo', 'activar todo', 'estado'];
                if (pauseCommands.includes(normalizedMessage)) {
                    console.log(`✅ COMMAND DETECTED: ${normalizedMessage} from ${messageSource}`);
                    
                    try {
                        const response = await axios.post(`${FASTAPI_URL}/api/client/${CLIENT_ID}/process-message`, {
                            phone_number: message.from.split('@')[0],
                            message: messageText,
                            message_id: message.id.id,
                            timestamp: message.timestamp
                        });

                        if (response.data.reply) {
                            await message.reply(response.data.reply);
                            console.log(`✅ Command reply sent to ${messageSource}:`, response.data.reply);
                        }
                        
                        return;
                        
                    } catch (error) {
                        console.error('❌ Error processing command:', error);
                        try {
                            await message.reply('❌ Error procesando comando. Intenta nuevamente.');
                        } catch (replyError) {
                            console.error('Error sending error message:', replyError);
                        }
                        return;
                    }
                }
                
                // For owner messages that are NOT commands, don't process with AI
                if (message.fromMe) {
                    console.log(`🤐 OWNER MESSAGE (not command) - ignoring: ${messageText}`);
                    return;
                }
                
                console.log('Received message:', messageText);
                console.log('From:', message.from);
                
                try {
                    const response = await axios.post(`${FASTAPI_URL}/api/client/${CLIENT_ID}/process-message`, {
                        phone_number: message.from.split('@')[0],
                        message: messageText,
                        message_id: message.id.id,
                        timestamp: message.timestamp
                    });

                    if (response.data.reply) {
                        await message.reply(response.data.reply);
                        console.log('Reply sent:', response.data.reply);
                    } else if (response.data.paused) {
                        console.log('Conversation is paused, no automatic reply sent');
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                    try {
                        await message.reply('Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.');
                    } catch (replyError) {
                        console.error('Error sending fallback message:', replyError);
                    }
                }
            }
        });

        // Disconnection handling
        client.on('disconnected', async (reason) => {
            console.log('WhatsApp disconnected:', reason);
            isConnected = false;
            connectedUser = null;
            qrCodeData = null;
            
            const needsCleanup = reason === 'LOGOUT' || reason === 'NAVIGATION' || 
                               reason === 'UNPAIRED' || reason === 'UNPAIRED_PHONE';
            
            if (needsCleanup) {
                console.log('🧹 Removing corrupted session data automatically');
                if (fs.existsSync(sessionDir)) {
                    try {
                        fs.rmSync(sessionDir, { recursive: true, force: true });
                    } catch (rmError) {
                        console.log('Error removing session (safe to ignore):', rmError.message);
                    }
                }
                
                reconnectAttempts = 0;
                setTimeout(() => {
                    console.log('🔄 Auto-reinitializing WhatsApp with clean session');
                    initializeWhatsApp();
                }, 5000);
                
                return;
            }
            
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                console.log(`Reconnection attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
                
                const delay = Math.min(15000 * reconnectAttempts, 120000);
                setTimeout(() => {
                    initializeWhatsApp();
                }, delay);
            }
        });

        // Authentication failure
        client.on('auth_failure', async (msg) => {
            console.error('Authentication failure:', msg);
            
            if (fs.existsSync(sessionDir)) {
                console.log('🧹 Removing corrupted auth data due to auth failure');
                try {
                    fs.rmSync(sessionDir, { recursive: true, force: true });
                } catch (rmError) {
                    console.log('Error removing session dir (safe to ignore):', rmError.message);
                }
            }
            
            setTimeout(() => {
                console.log('🔄 Reinitializing after auth failure');
                initializeWhatsApp();
            }, 10000);
        });

        await client.initialize();

    } catch (error) {
        console.error(`Error initializing WhatsApp for ${CLIENT_NAME}:`, error);
        isInitializing = false;
        
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            console.log(`Initialization retry ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
            
            if (fs.existsSync('./.wwebjs_auth')) {
                try {
                    fs.rmSync('./.wwebjs_auth', { recursive: true, force: true });
                } catch (rmError) {
                    console.log('Error removing session (safe to ignore):', rmError.message);
                }
            }
            
            const retryDelay = 20000;
            setTimeout(() => {
                initializeWhatsApp();
            }, retryDelay);
        } else {
            console.log('❌ Max initialization attempts reached. Resetting attempts and trying again...');
            reconnectAttempts = 0;
            setTimeout(() => {
                console.log('🔄 Final attempt after full reset...');
                initializeWhatsApp();
            }, 30000);
        }
    }
}

// API Routes
app.get('/qr', async (req, res) => {
    try {
        if (qrCodeData) {
            const qrDataUrl = await qrcode.toDataURL(qrCodeData);
            res.json({ qr: qrDataUrl, raw: qrCodeData });
        } else {
            res.json({ qr: null });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/status', (req, res) => {
    res.json({
        connected: isConnected,
        user: connectedUser,
        hasQR: !!qrCodeData,
        client_id: CLIENT_ID,
        client_name: CLIENT_NAME
    });
});

app.get('/logout', (req, res) => {
    res.json({
        success: true,
        message: 'Logout initiated. WhatsApp device will be disconnected.',
        instructions: 'Please wait while we disconnect your device from WhatsApp.'
    });
    
    setTimeout(async () => {
        try {
            console.log('🔐 Initiating complete WhatsApp logout...');
            
            if (client) {
                await client.logout();
                console.log('✅ WhatsApp logout completed');
                
                isConnected = false;
                connectedUser = null;
                qrCodeData = null;
                
                const sessionDir = './.wwebjs_auth';
                if (fs.existsSync(sessionDir)) {
                    console.log('🧹 Removing all session data...');
                    fs.rmSync(sessionDir, { recursive: true, force: true });
                }
                
                console.log('✅ Complete logout and cleanup finished');
                client = null;
                
            } else {
                console.log('ℹ️  No active client to logout');
            }
        } catch (error) {
            console.error('❌ Error during logout:', error);
        }
    }, 1000);
});

app.get('/health', (req, res) => {
    res.json({
        status: 'running',
        connected: isConnected,
        client_id: CLIENT_ID,
        client_name: CLIENT_NAME,
        timestamp: new Date().toISOString()
    });
});

// Start server
const server = app.listen(CLIENT_PORT, '0.0.0.0', () => {
    console.log(`✅ WhatsApp service for ${CLIENT_NAME} running on port ${CLIENT_PORT}`);
    setTimeout(() => initializeWhatsApp(), 5000);
});

// Graceful shutdown
const gracefulShutdown = async () => {
    console.log(`Shutting down service for ${CLIENT_NAME}...`);
    
    if (client) {
        try {
            await client.destroy();
        } catch (error) {
            console.error('Error destroying client:', error);
        }
    }
    
    if (server) {
        server.close(() => {
            process.exit(0);
        });
        
        setTimeout(() => process.exit(1), 30000);
    }
};

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);