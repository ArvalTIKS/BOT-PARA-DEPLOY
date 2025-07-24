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

// Initialize WhatsApp client
function initializeWhatsApp() {
    client = new Client({
        authStrategy: new LocalAuth({
            clientId: "whatsapp-assistant"
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu'
            ],
            executablePath: '/usr/bin/chromium'
        }
    });

    // QR Code event
    client.on('qr', async (qr) => {
        console.log('QR RECEIVED');
        qrCodeData = qr;
        
        try {
            // Generate QR code as data URL for frontend
            const qrDataUrl = await qrcode.toDataURL(qr);
            console.log('QR Code generated successfully');
        } catch (err) {
            console.error('Error generating QR code:', err);
        }
    });

    // Ready event
    client.on('ready', () => {
        console.log('WhatsApp client is ready!');
        isConnected = true;
        qrCodeData = null;
        
        // Get client info
        const clientInfo = client.info;
        connectedUser = {
            name: clientInfo.pushname || 'WhatsApp User',
            phone: clientInfo.wid._serialized.replace('@c.us', ''),
            profileImage: null,
            connectedAt: new Date().toISOString()
        };
        
        console.log('Connected user:', connectedUser);
    });

    // Disconnected event
    client.on('disconnected', (reason) => {
        console.log('WhatsApp client was disconnected:', reason);
        isConnected = false;
        connectedUser = null;
        qrCodeData = null;
        
        // Restart after 5 seconds
        setTimeout(() => {
            console.log('Attempting to reconnect...');
            initializeWhatsApp();
        }, 5000);
    });

    // Message received event
    client.on('message', async (message) => {
        // Only process messages that are not from the client himself
        if (!message.fromMe && message.from.endsWith('@c.us')) {
            console.log('Received message:', message.body);
            console.log('From:', message.from);
            
            try {
                // Send message to FastAPI for OpenAI processing
                const response = await axios.post(`${FASTAPI_URL}/api/whatsapp/process-message`, {
                    phone_number: message.from.replace('@c.us', ''),
                    message: message.body,
                    message_id: message.id.id,
                    timestamp: message.timestamp
                });

                // Send AI response back to WhatsApp
                if (response.data.reply) {
                    await message.reply(response.data.reply);
                    console.log('Reply sent:', response.data.reply);
                }
            } catch (error) {
                console.error('Error processing message:', error);
                // Send fallback message
                await message.reply('Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.');
            }
        }
    });

    // Auth failure event
    client.on('auth_failure', msg => {
        console.error('Authentication failure:', msg);
        qrCodeData = null;
    });

    // Initialize the client
    console.log('Initializing WhatsApp client...');
    client.initialize();
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
        console.error('Error sending message:', error);
        res.status(500).json({ 
            success: false, 
            error: error.message 
        });
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'running',
        connected: isConnected,
        timestamp: new Date().toISOString()
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`WhatsApp service running on port ${PORT}`);
    initializeWhatsApp();
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('Shutting down gracefully...');
    if (client) {
        await client.destroy();
    }
    process.exit();
});

process.on('SIGTERM', async () => {
    console.log('Shutting down gracefully...');
    if (client) {
        await client.destroy();
    }
    process.exit();
});