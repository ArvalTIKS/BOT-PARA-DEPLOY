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

const PORT = process.env.CLIENT_PORT || 3010;
const FASTAPI_URL = 'http://localhost:8001';
const CLIENT_ID = process.env.CLIENT_ID || '6e5e007a-25fa-485d-b61d-ef5fc6d04701';

// Deploy-aware environment detection
const isDeployEnv = process.env.EMERGENT_ENV === 'deploy';
console.log(`Individual service for Roberto Deploy Test running in ${isDeployEnv ? 'DEPLOY' : 'PREVIEW'} environment`);

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
        console.log(`🚀 FAST INIT: Starting WhatsApp for client Roberto Deploy Test...`);
        
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

        // Clear any existing QR to show loading state
        qrCodeData = null;
        console.log('🔄 QR cleared - initializing...');

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
            console.log(`QR Code received for Roberto Deploy Test`);
            qrCodeData = qr;
            reconnectAttempts = 0;
            try {
                const qrDataUrl = await qrcode.toDataURL(qr);
                console.log(`QR Code generated successfully for Roberto Deploy Test`);
            } catch (err) {
                console.error('Error generating QR code:', err);
            }
        });

        // Authentication success
        client.on('authenticated', () => {
            console.log(`WhatsApp authenticated successfully for Roberto Deploy Test`);
        });

        // Ready event
        client.on('ready', async () => {
            console.log(`WhatsApp client is ready for Roberto Deploy Test!`);
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
                
                console.log(`Connected user for Roberto Deploy Test:`, connectedUser);
            } catch (err) {
                console.error('Error getting user info:', err);
            }
        });

        // Disconnection handling - ROBUST RECOVERY
        client.on('disconnected', async (reason) => {
            console.log(`🔄 WhatsApp disconnected for Roberto Deploy Test:`, reason);
            isConnected = false;
            connectedUser = null;
            qrCodeData = null;
            isInitializing = false;
            
            // Immediate reconnection with exponential backoff
            const reconnectDelay = Math.min(5000 * Math.pow(2, reconnectAttempts), 60000);
            console.log(`🔄 Auto-reconnecting Roberto Deploy Test in ${reconnectDelay/1000}s (attempt ${reconnectAttempts + 1})`);
            
            setTimeout(async () => {
                try {
                    await initializeWhatsApp();
                } catch (error) {
                    console.error(`❌ Reconnection failed for Roberto Deploy Test:`, error);
                    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                        setTimeout(() => initializeWhatsApp(), 15000);
                    }
                }
            }, reconnectDelay);
        });

        // Authentication failure - IMMEDIATE RECOVERY
        client.on('auth_failure', async (msg) => {
            console.log(`❌ Auth failed for Roberto Deploy Test:`, msg);
            qrCodeData = null;
            isConnected = false;
            connectedUser = null;
            isInitializing = false;
            
            // Clear corrupted session immediately
            try {
                if (fs.existsSync(sessionDir)) {
                    const sessionFiles = fs.readdirSync(sessionDir);
                    sessionFiles.forEach(file => {
                        const filePath = path.join(sessionDir, file);
                        if (fs.statSync(filePath).isDirectory()) {
                            fs.rmSync(filePath, { recursive: true, force: true });
                        } else {
                            fs.unlinkSync(filePath);
                        }
                    });
                    console.log(`🧹 Cleared session for Roberto Deploy Test`);
                }
            } catch (cleanError) {
                console.log('Error clearing session (safe to ignore):', cleanError.message);
            }
            
            // Force restart with clean session
            console.log(`🔄 Force restarting Roberto Deploy Test with clean session`);
            setTimeout(() => {
                initializeWhatsApp();
            }, 5000);
        });

        // Message received event
        client.on('message', async (message) => {
            if (!message.fromMe && message.body) {
                // Only respond to private messages
                if (message.from.includes('-') || message.from.includes('@g.us')) {
                    console.log(`Ignored group message for Roberto Deploy Test from ${message.from}: ${message.body}`);
                    return;
                }
                
                if (!message.from.includes('@c.us')) {
                    console.log(`Ignored non-private message for Roberto Deploy Test from ${message.from}`);
                    return;
                }
                
                console.log(`Message for Roberto Deploy Test from ${message.from}: ${message.body}`);
                
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
                        console.log(`Reply sent for Roberto Deploy Test:`, response.data.reply);
                    } else if (response.data.paused) {
                        console.log(`Conversation is paused for Roberto Deploy Test, no automatic reply sent`);
                    }
                } catch (error) {
                    console.error(`Error processing message for Roberto Deploy Test:`, error);
                    try {
                        await message.reply('Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.');
                    } catch (replyError) {
                        console.error(`Error sending fallback message for Roberto Deploy Test:`, replyError);
                    }
                }
            }
        });

        // Initialize the client
        console.log(`Starting WhatsApp client initialization for Roberto Deploy Test...`);
        await client.initialize();

    } catch (error) {
        console.error(`Error initializing WhatsApp for Roberto Deploy Test:`, error);
        isInitializing = false;
        
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            console.log(`Initialization retry ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} for Roberto Deploy Test`);
            
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
        client: 'Roberto Deploy Test',
        port: PORT,
        timestamp: new Date().toISOString()
    });
});

app.get('/logout', (req, res) => {
    res.json({
        success: true,
        message: 'Logout initiated for Roberto Deploy Test',
        instructions: 'Please wait while we disconnect your device from WhatsApp.'
    });
    
    setTimeout(async () => {
        try {
            console.log(`Initiating complete WhatsApp logout for Roberto Deploy Test...`);
            
            if (client) {
                await client.logout();
                console.log(`WhatsApp logout completed for Roberto Deploy Test`);
                
                isConnected = false;
                connectedUser = null;
                qrCodeData = null;
                
                if (fs.existsSync(sessionDir)) {
                    console.log(`Removing all session data for Roberto Deploy Test...`);
                    fs.rmSync(sessionDir, { recursive: true, force: true });
                }
                
                console.log(`Complete logout and cleanup finished for Roberto Deploy Test`);
                client = null;
            }
        } catch (error) {
            console.error(`Error during logout for Roberto Deploy Test:`, error);
        }
    }, 1000);
});

// Force restart endpoint - EMERGENCY RECOVERY
        app.get('/force-restart', async (req, res) => {
            console.log(`🚨 FORCE RESTART requested for Roberto Deploy Test`);
            
            try {
                // Destroy existing client
                if (client) {
                    await client.destroy().catch(e => console.log('Destroy error (safe):', e.message));
                    client = null;
                }
                
                // Reset all states
                isConnected = false;
                connectedUser = null;
                qrCodeData = null;
                isInitializing = false;
                reconnectAttempts = 0;
                
                // Clear session
                if (fs.existsSync(sessionDir)) {
                    fs.rmSync(sessionDir, { recursive: true, force: true });
                }
                
                // Immediate restart
                console.log(`🔄 IMMEDIATE restart Roberto Deploy Test...`);
                setTimeout(() => {
                    initializeWhatsApp();
                }, 2000);
                
                res.json({ success: true, message: `Force restart initiated for Roberto Deploy Test` });
            } catch (error) {
                console.error('Force restart error:', error);
                res.json({ success: false, error: error.message });
            }
        });

// Start server
const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`Individual WhatsApp service for Roberto Deploy Test running on port ${PORT}`);
    
    // Initialize WhatsApp after server starts
    setTimeout(() => {
        initializeWhatsApp();
    }, 2000);
});

// Graceful shutdown
const gracefulShutdown = async () => {
    console.log(`Shutting down individual service for Roberto Deploy Test...`);
    
    if (client) {
        console.log(`Destroying WhatsApp client for Roberto Deploy Test...`);
        try {
            await client.destroy();
        } catch (error) {
            console.error(`Error destroying client for Roberto Deploy Test:`, error);
        }
    }
    
    if (server) {
        console.log(`Closing HTTP server for Roberto Deploy Test...`);
        server.close(() => {
            console.log(`HTTP server closed for Roberto Deploy Test`);
            process.exit(0);
        });
        
        setTimeout(() => {
            console.log(`Forcing shutdown for Roberto Deploy Test...`);
            process.exit(1);
        }, 30000);
    } else {
        process.exit(0);
    }
};

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);
