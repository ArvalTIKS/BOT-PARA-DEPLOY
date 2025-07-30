const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.CLIENT_PORT || 3002;
const FASTAPI_URL = 'http://localhost:8001';
const CLIENT_ID = process.env.CLIENT_ID || 'b7ed840b-fa6e-443e-8726-1b124afaa165';

// Deploy-aware environment detection
const isDeployEnv = process.env.EMERGENT_ENV === 'deploy';
console.log(`Individual service for Estudio Jurídico Villegas running in ${isDeployEnv ? 'DEPLOY' : 'PREVIEW'} environment`);

let client = null;
let qrCodeData = null;
let isConnected = false;
let connectedUser = null;
let sessionDir = './whatsapp_session';
let isInitializing = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Enhanced Puppeteer configuration for individual services
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
            `--user-data-dir=${uniqueProfileDir}`
        ]
    };
    
    // FORCE system Chromium for individual services (ARM64 compatibility)
    const systemChromiumPath = '/usr/bin/chromium';
    if (fs.existsSync(systemChromiumPath)) {
        baseConfig.executablePath = systemChromiumPath;
        console.log(`Individual service using system Chromium: ${systemChromiumPath}`);
    } else {
        console.log('WARNING: System Chromium not found, using Puppeteer bundled (may fail on ARM64)');
    }
    
    return baseConfig;
};

// Initialize WhatsApp with whatsapp-web.js
async function initializeWhatsApp() {
    try {
        if (isInitializing) {
            console.log('WhatsApp is already initializing, skipping...');
            return;
        }
        
        isInitializing = true;
        console.log(`Initializing WhatsApp for client Estudio Jurídico Villegas...`);
        
        if (client) {
            console.log('Destroying existing client...');
            try {
                await client.destroy();
            } catch (destroyError) {
                console.log('Error destroying client (safe to ignore):', destroyError.message);
            }
            client = null;
        }
        
        // Ensure session directory exists
        if (!fs.existsSync(sessionDir)) {
            fs.mkdirSync(sessionDir, { recursive: true });
        }

        // Create client with system Chromium configuration
        const puppeteerConfig = getPuppeteerConfig();
        
        client = new Client({
            authStrategy: new LocalAuth({
                clientId: `whatsapp-client-${CLIENT_ID}`,
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
            console.log(`QR Code received for Estudio Jurídico Villegas`);
            qrCodeData = qr;
            reconnectAttempts = 0;
            try {
                const qrDataUrl = await qrcode.toDataURL(qr);
                console.log(`QR Code generated successfully for Estudio Jurídico Villegas`);
            } catch (err) {
                console.error('Error generating QR code:', err);
            }
        });

        // Authentication success
        client.on('authenticated', () => {
            console.log(`WhatsApp authenticated successfully for Estudio Jurídico Villegas`);
        });

        // Ready event
        client.on('ready', async () => {
            console.log(`WhatsApp client is ready for Estudio Jurídico Villegas!`);
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
                
                console.log(`Connected user for Estudio Jurídico Villegas:`, connectedUser);
            } catch (err) {
                console.error('Error getting user info:', err);
            }
        });

        // Disconnection handling
        client.on('disconnected', async (reason) => {
            console.log(`WhatsApp disconnected for Estudio Jurídico Villegas:`, reason);
            isConnected = false;
            connectedUser = null;
            qrCodeData = null;
            
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                console.log(`Reconnection attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} for Estudio Jurídico Villegas`);
                
                const delay = Math.min(5000 * reconnectAttempts, 30000);
                setTimeout(() => {
                    initializeWhatsApp();
                }, delay);
            }
        });

        // Authentication failure
        client.on('auth_failure', async (msg) => {
            console.error(`Authentication failure for Estudio Jurídico Villegas:`, msg);
            
            if (fs.existsSync(sessionDir)) {
                console.log(`Removing corrupted auth data for Estudio Jurídico Villegas`);
                try {
                    fs.rmSync(sessionDir, { recursive: true, force: true });
                } catch (rmError) {
                    console.log('Error removing session dir (safe to ignore):', rmError.message);
                }
            }
            
            setTimeout(() => {
                console.log(`Reinitializing after auth failure for Estudio Jurídico Villegas`);
                initializeWhatsApp();
            }, 10000);
        });

        // Message received event
        client.on('message', async (message) => {
            if (!message.fromMe && message.body) {
                // Only respond to private messages
                if (message.from.includes('-') || message.from.includes('@g.us')) {
                    console.log(`Ignored group message for Estudio Jurídico Villegas from ${message.from}: ${message.body}`);
                    return;
                }
                
                if (!message.from.includes('@c.us')) {
                    console.log(`Ignored non-private message for Estudio Jurídico Villegas from ${message.from}`);
                    return;
                }
                
                console.log(`Message for Estudio Jurídico Villegas from ${message.from}: ${message.body}`);
                
                try {
                    // Send message to FastAPI for processing
                    const response = await axios.post(`${FASTAPI_URL}/api/client/${CLIENT_ID}/process-message`, {
                        phone_number: message.from.split('@')[0],
                        message: message.body,
                        message_id: message.id.id,
                        timestamp: message.timestamp
                    });

                    // Send AI response back to WhatsApp if there's a reply
                    if (response.data.reply) {
                        await message.reply(response.data.reply);
                        console.log(`Reply sent for Estudio Jurídico Villegas:`, response.data.reply);
                    } else if (response.data.paused) {
                        console.log(`Conversation is paused for Estudio Jurídico Villegas, no automatic reply sent`);
                    }
                } catch (error) {
                    console.error(`Error processing message for Estudio Jurídico Villegas:`, error);
                    try {
                        await message.reply('Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.');
                    } catch (replyError) {
                        console.error(`Error sending fallback message for Estudio Jurídico Villegas:`, replyError);
                    }
                }
            }
        });

        // Initialize the client
        console.log(`Starting WhatsApp client initialization for Estudio Jurídico Villegas...`);
        await client.initialize();

    } catch (error) {
        console.error(`Error initializing WhatsApp for Estudio Jurídico Villegas:`, error);
        isInitializing = false;
        
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            console.log(`Initialization retry ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} for Estudio Jurídico Villegas`);
            
            setTimeout(() => {
                initializeWhatsApp();
            }, 10000);
        }
    }
}

// API Routes
app.get('/qr', async (req, res) => {
    try {
        if (qrCodeData) {
            const qrDataUrl = await qrcode.toDataURL(qrCodeData);
            res.json({ 
                qr: qrDataUrl,
                raw: qrCodeData
            });
        } else {
            res.json({ qr: null });
        }
    } catch (error) {
        console.error('Error generating QR:', error);
        res.status(500).json({ error: error.message });
    }
});

app.get('/status', (req, res) => {
    res.json({
        connected: isConnected,
        user: connectedUser,
        hasQR: !!qrCodeData
    });
});

app.get('/health', (req, res) => {
    res.json({
        status: 'running',
        connected: isConnected,
        client: 'Estudio Jurídico Villegas',
        port: PORT,
        timestamp: new Date().toISOString()
    });
});

app.get('/logout', (req, res) => {
    res.json({
        success: true,
        message: 'Logout initiated for Estudio Jurídico Villegas',
        instructions: 'Please wait while we disconnect your device from WhatsApp.'
    });
    
    setTimeout(async () => {
        try {
            console.log(`Initiating complete WhatsApp logout for Estudio Jurídico Villegas...`);
            
            if (client) {
                await client.logout();
                console.log(`WhatsApp logout completed for Estudio Jurídico Villegas`);
                
                isConnected = false;
                connectedUser = null;
                qrCodeData = null;
                
                if (fs.existsSync(sessionDir)) {
                    console.log(`Removing all session data for Estudio Jurídico Villegas...`);
                    fs.rmSync(sessionDir, { recursive: true, force: true });
                }
                
                console.log(`Complete logout and cleanup finished for Estudio Jurídico Villegas`);
                client = null;
            }
        } catch (error) {
            console.error(`Error during logout for Estudio Jurídico Villegas:`, error);
        }
    }, 1000);
});

// Start server
const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`Individual WhatsApp service for Estudio Jurídico Villegas running on port ${PORT}`);
    
    // Initialize WhatsApp after server starts
    setTimeout(() => {
        initializeWhatsApp();
    }, 2000);
});

// Graceful shutdown
const gracefulShutdown = async () => {
    console.log(`Shutting down individual service for Estudio Jurídico Villegas...`);
    
    if (client) {
        console.log(`Destroying WhatsApp client for Estudio Jurídico Villegas...`);
        try {
            await client.destroy();
        } catch (error) {
            console.error(`Error destroying client for Estudio Jurídico Villegas:`, error);
        }
    }
    
    if (server) {
        console.log(`Closing HTTP server for Estudio Jurídico Villegas...`);
        server.close(() => {
            console.log(`HTTP server closed for Estudio Jurídico Villegas`);
            process.exit(0);
        });
        
        setTimeout(() => {
            console.log(`Forcing shutdown for Estudio Jurídico Villegas...`);
            process.exit(1);
        }, 30000);
    } else {
        process.exit(0);
    }
};

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);
