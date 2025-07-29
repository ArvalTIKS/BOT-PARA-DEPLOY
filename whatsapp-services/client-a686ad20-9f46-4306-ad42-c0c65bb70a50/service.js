
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const puppeteer = require('puppeteer');
const config = require('./client-config');

const app = express();
app.use(cors());
app.use(express.json());

const CLIENT_ID = process.env.CLIENT_ID;
const PORT = process.env.CLIENT_PORT;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';

let client = null;
let qrCodeData = null;
let isConnected = false;
let connectedUser = null;
let isInitializing = false;
let reconnectAttempts = 0;

// Enhanced Puppeteer configuration
const getPuppeteerConfig = () => {
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
            '--single-process'
        ]
    };
    
    const chromiumPath = '/usr/bin/chromium';
    if (fs.existsSync(chromiumPath)) {
        baseConfig.executablePath = chromiumPath;
    }
    
    return baseConfig;
};

// Initialize WhatsApp client
async function initializeWhatsApp() {
    if (isInitializing) return;
    
    try {
        isInitializing = true;
        console.log(`Initializing WhatsApp for client ${config.client.name} (${CLIENT_ID})`);
        
        if (client) {
            await client.destroy();
            client = null;
        }
        
        const sessionDir = config.session.authDirectory;
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

        // Event handlers
        client.on('qr', async (qr) => {
            console.log(`QR Code received for client ${config.client.name}`);
            qrCodeData = qr;
            reconnectAttempts = 0;
        });

        client.on('authenticated', () => {
            console.log(`WhatsApp authenticated for client ${config.client.name}`);
        });

        client.on('ready', async () => {
            console.log(`WhatsApp client ready for ${config.client.name}!`);
            isConnected = true;
            qrCodeData = null;
            
            try {
                const info = client.info;
                connectedUser = {
                    name: info.pushname || 'WhatsApp User',
                    phone: info.wid.user || 'Unknown',
                    connectedAt: new Date().toISOString()
                };
                
                // Notify backend about connection
                await axios.post(`${FASTAPI_URL}/api/admin/clients/${CLIENT_ID}/connected`, {
                    phone: connectedUser.phone
                });
                
            } catch (err) {
                console.error('Error getting user info:', err);
            }
        });

        client.on('disconnected', async (reason) => {
            console.log(`WhatsApp disconnected for ${config.client.name}:`, reason);
            isConnected = false;
            connectedUser = null;
            qrCodeData = null;
            
            // Notify backend about disconnection
            try {
                await axios.post(`${FASTAPI_URL}/api/admin/clients/${CLIENT_ID}/disconnected`);
            } catch (err) {
                console.error('Error notifying backend:', err);
            }
            
            // Handle reconnection
            const needsCleanup = reason === 'LOGOUT' || reason === 'NAVIGATION' || 
                               reason === 'UNPAIRED' || reason === 'UNPAIRED_PHONE';
            
            if (needsCleanup) {
                if (fs.existsSync(sessionDir)) {
                    fs.rmSync(sessionDir, { recursive: true, force: true });
                }
                setTimeout(() => initializeWhatsApp(), 5000);
            }
        });

        client.on('auth_failure', async (msg) => {
            console.error(`Authentication failure for ${config.client.name}:`, msg);
            if (fs.existsSync(sessionDir)) {
                fs.rmSync(sessionDir, { recursive: true, force: true });
            }
            setTimeout(() => initializeWhatsApp(), 10000);
        });

        client.on('message', async (message) => {
            if (!message.fromMe && message.body) {
                const messageText = message.body;
                console.log(`Message from ${message.from} for client ${config.client.name}: ${messageText}`);
                
                try {
                    // Send to client-specific message processor
                    const response = await axios.post(`${FASTAPI_URL}/api/clients/${CLIENT_ID}/process-message`, {
                        phone_number: message.from.split('@')[0],
                        message: messageText,
                        message_id: message.id.id,
                        timestamp: message.timestamp
                    });

                    if (response.data.reply) {
                        await message.reply(response.data.reply);
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                    await message.reply('Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.');
                }
            }
        });

        await client.initialize();

    } catch (error) {
        console.error(`Error initializing WhatsApp for ${config.client.name}:`, error);
        isInitializing = false;
        setTimeout(() => initializeWhatsApp(), 15000);
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
        client_name: config.client.name
    });
});

app.get('/health', (req, res) => {
    res.json({
        status: 'running',
        connected: isConnected,
        client_id: CLIENT_ID,
        timestamp: new Date().toISOString()
    });
});

// Start server
const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`WhatsApp service for ${config.client.name} running on port ${PORT}`);
    setTimeout(() => initializeWhatsApp(), 5000);
});

// Graceful shutdown
const gracefulShutdown = async () => {
    console.log(`Shutting down service for ${config.client.name}...`);
    
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
