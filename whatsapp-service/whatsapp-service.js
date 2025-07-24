const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3001;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';

let client = null;
let qrCodeData = null;
let isConnected = false;
let connectedUser = null;
let isInitializing = false;

// Initialize WhatsApp client with improved stability
function initializeWhatsApp() {
    if (isInitializing) {
        console.log('Already initializing, skipping...');
        return;
    }
    
    isInitializing = true;
    console.log('Initializing WhatsApp client with stable configuration...');

    client = new Client({
        authStrategy: new LocalAuth({
            clientId: "stable-whatsapp-client",
            dataPath: './whatsapp_sessions'
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-zygote',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ],
            executablePath: '/usr/bin/chromium',
            timeout: 60000
        }
    });

    // QR Code event - only generate once and keep stable
    client.on('qr', async (qr) => {
        console.log('🔄 QR Code received - generating stable version...');
        qrCodeData = qr;
        
        try {
            const qrDataUrl = await qrcode.toDataURL(qr, {
                errorCorrectionLevel: 'H',
                type: 'image/png',
                quality: 1.0,
                margin: 2,
                width: 512,
                color: {
                    dark: '#000000',
                    light: '#FFFFFF'
                }
            });
            console.log('✅ QR Code generated successfully and ready for scanning');
        } catch (err) {
            console.error('❌ Error generating QR code:', err);
        }
    });

    // Ready event - client connected successfully
    client.on('ready', () => {
        console.log('🟢 WhatsApp client is ready and connected!');
        isConnected = true;
        qrCodeData = null;
        isInitializing = false;
        
        const clientInfo = client.info;
        connectedUser = {
            name: clientInfo.pushname || 'WhatsApp Business',
            phone: clientInfo.wid._serialized.replace('@c.us', ''),
            profileImage: null,
            connectedAt: new Date().toISOString()
        };
        
        console.log('📱 Connected user:', connectedUser);
    });

    // Authentication success
    client.on('authenticated', () => {
        console.log('🔐 WhatsApp client authenticated successfully');
    });

    // Disconnected event - handle reconnection carefully  
    client.on('disconnected', (reason) => {
        console.log('🔴 WhatsApp client disconnected:', reason);
        isConnected = false;
        connectedUser = null;
        qrCodeData = null;
        isInitializing = false;
        
        // Only reconnect if not a deliberate logout
        if (reason !== 'LOGOUT') {
            console.log('🔄 Attempting to reconnect in 10 seconds...');
            setTimeout(() => {
                initializeWhatsApp();
            }, 10000);
        }
    });

    // Message received event
    client.on('message', async (message) => {
        if (!message.fromMe && message.from.endsWith('@c.us')) {
            console.log('📨 Message received from:', message.from);
            console.log('💬 Content:', message.body);
            
            try {
                const response = await axios.post(`${FASTAPI_URL}/api/whatsapp/process-message`, {
                    phone_number: message.from.replace('@c.us', ''),
                    message: message.body,
                    message_id: message.id.id,
                    timestamp: message.timestamp
                }, { timeout: 30000 });

                if (response.data.reply) {
                    await message.reply(response.data.reply);
                    console.log('✅ Reply sent successfully');
                }
            } catch (error) {
                console.error('❌ Error processing message:', error.message);
                try {
                    await message.reply('Lo siento, hubo un problema procesando tu mensaje. Por favor intenta nuevamente en un momento.');
                } catch (replyError) {
                    console.error('❌ Could not send error reply:', replyError.message);
                }
            }
        }
    });

    // Auth failure event
    client.on('auth_failure', msg => {
        console.error('🔴 Authentication failure:', msg);
        qrCodeData = null;
        isConnected = false;
        isInitializing = false;
    });

    // Loading screen event
    client.on('loading_screen', (percent, message) => {
        console.log(`⏳ Loading: ${percent}% - ${message}`);
    });

    // Initialize the client
    client.initialize().catch(err => {
        console.error('❌ Failed to initialize WhatsApp client:', err);
        isInitializing = false;
    });
}

// REST API Routes
app.get('/qr', async (req, res) => {
    try {
        if (qrCodeData && !isConnected) {
            const qrDataUrl = await qrcode.toDataURL(qrCodeData, {
                errorCorrectionLevel: 'H',
                type: 'image/png',
                quality: 1.0,
                margin: 2,
                width: 512,
                color: {
                    dark: '#000000',
                    light: '#FFFFFF'
                }
            });
            res.json({ 
                qr: qrDataUrl,
                raw: qrCodeData,
                connected: isConnected
            });
        } else {
            res.json({ 
                qr: null,
                connected: isConnected,
                message: isConnected ? 'Already connected' : 'No QR available'
            });
        }
    } catch (error) {
        console.error('❌ Error in QR endpoint:', error);
        res.status(500).json({ error: error.message });
    }
});

app.get('/status', (req, res) => {
    res.json({
        connected: isConnected,
        user: connectedUser,
        hasQR: !!qrCodeData && !isConnected,
        initializing: isInitializing,
        timestamp: new Date().toISOString()
    });
});

app.post('/send-message', async (req, res) => {
    const { phoneNumber, message } = req.body;
    
    if (!isConnected) {
        return res.status(400).json({ 
            success: false, 
            error: 'WhatsApp not connected' 
        });
    }

    try {
        const formattedNumber = phoneNumber.includes('@') ? phoneNumber : `${phoneNumber}@c.us`;
        await client.sendMessage(formattedNumber, message);
        
        res.json({ 
            success: true,
            message: 'Message sent successfully'
        });
    } catch (error) {
        console.error('❌ Error sending message:', error);
        res.status(500).json({ 
            success: false, 
            error: error.message 
        });
    }
});

app.get('/health', (req, res) => {
    res.json({
        status: 'running',
        connected: isConnected,
        hasQR: !!qrCodeData,
        initializing: isInitializing,
        timestamp: new Date().toISOString()
    });
});

// Restart endpoint for troubleshooting
app.post('/restart', (req, res) => {
    console.log('🔄 Manual restart requested');
    if (client) {
        client.destroy().then(() => {
            setTimeout(initializeWhatsApp, 2000);
            res.json({ success: true, message: 'Restarting WhatsApp client...' });
        }).catch(err => {
            console.error('❌ Error destroying client:', err);
            res.status(500).json({ success: false, error: err.message });
        });
    } else {
        initializeWhatsApp();
        res.json({ success: true, message: 'Starting WhatsApp client...' });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 WhatsApp service running on port ${PORT}`);
    console.log(`🔗 Health check: http://localhost:${PORT}/health`);
    initializeWhatsApp();
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('🛑 Shutting down gracefully...');
    if (client) {
        await client.destroy();
    }
    process.exit();
});

process.on('SIGTERM', async () => {
    console.log('🛑 Shutting down gracefully...');
    if (client) {
        await client.destroy();
    }
    process.exit();
});