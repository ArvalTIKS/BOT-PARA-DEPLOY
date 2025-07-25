const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3001;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';

let sock = null;
let qrCodeData = null;
let isConnected = false;
let connectedUser = null;
let authDir = './baileys_auth_info';

// Initialize WhatsApp with Baileys
async function initializeWhatsApp() {
    try {
        console.log('Initializing WhatsApp with Baileys...');
        
        // Ensure auth directory exists
        if (!fs.existsSync(authDir)) {
            fs.mkdirSync(authDir, { recursive: true });
        }

        const { state, saveCreds } = await useMultiFileAuthState(authDir);
        const { version, isLatest } = await fetchLatestBaileysVersion();
        
        console.log(`Using WA version ${version.join('.')}, isLatest: ${isLatest}`);

        sock = makeWASocket({
            version,
            auth: state,
            printQRInTerminal: false,
            logger: { level: 'silent' },
            browser: ['WhatsApp Assistant', 'Chrome', '4.0.0'],
            connectTimeoutMs: 60000,
            defaultQueryTimeoutMs: 0,
            keepAliveIntervalMs: 10000,
            emitOwnEvents: true,
            getMessage: async (key) => {
                return { conversation: '' };
            }
        });

        // QR Code event
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            if (qr) {
                console.log('QR Code received');
                qrCodeData = qr;
                try {
                    const qrDataUrl = await qrcode.toDataURL(qr);
                    console.log('QR Code generated successfully');
                } catch (err) {
                    console.error('Error generating QR code:', err);
                }
            }

            if (connection === 'close') {
                const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
                console.log('Connection closed due to ', lastDisconnect?.error, ', reconnecting ', shouldReconnect);
                
                isConnected = false;
                connectedUser = null;
                qrCodeData = null;
                
                if (shouldReconnect) {
                    setTimeout(() => {
                        initializeWhatsApp();
                    }, 5000);
                }
            } else if (connection === 'open') {
                console.log('WhatsApp connection opened successfully');
                isConnected = true;
                qrCodeData = null;
                
                try {
                    const userInfo = sock.user;
                    connectedUser = {
                        name: userInfo?.name || 'WhatsApp User',
                        phone: userInfo?.id?.split(':')[0] || 'Unknown',
                        profileImage: null,
                        connectedAt: new Date().toISOString()
                    };
                    console.log('Connected user:', connectedUser);
                } catch (err) {
                    console.error('Error getting user info:', err);
                }
            }
        });

        // Save credentials when updated
        sock.ev.on('creds.update', saveCreds);

        // Message received event
        sock.ev.on('messages.upsert', async (m) => {
            const message = m.messages[0];
            if (!message.key.fromMe && message.message) {
                const messageText = message.message.conversation || 
                                 message.message.extendedTextMessage?.text || '';
                
                if (messageText) {
                    console.log('Received message:', messageText);
                    console.log('From:', message.key.remoteJid);
                    
                    try {
                        // Send message to FastAPI for OpenAI processing
                        const response = await axios.post(`${FASTAPI_URL}/api/whatsapp/process-message`, {
                            phone_number: message.key.remoteJid.split('@')[0],
                            message: messageText,
                            message_id: message.key.id,
                            timestamp: message.messageTimestamp
                        });

                        // Send AI response back to WhatsApp
                        if (response.data.reply) {
                            await sock.sendMessage(message.key.remoteJid, { 
                                text: response.data.reply 
                            });
                            console.log('Reply sent:', response.data.reply);
                        }
                    } catch (error) {
                        console.error('Error processing message:', error);
                        try {
                            await sock.sendMessage(message.key.remoteJid, { 
                                text: 'Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.' 
                            });
                        } catch (replyError) {
                            console.error('Error sending fallback message:', replyError);
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error initializing WhatsApp:', error);
        setTimeout(() => {
            initializeWhatsApp();
        }, 10000);
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

app.post('/send-message', async (req, res) => {
    const { phoneNumber, message } = req.body;
    
    if (!isConnected || !sock) {
        return res.status(400).json({ 
            success: false, 
            error: 'WhatsApp not connected' 
        });
    }

    try {
        const formattedNumber = phoneNumber.includes('@') ? phoneNumber : `${phoneNumber}@s.whatsapp.net`;
        await sock.sendMessage(formattedNumber, { text: message });
        
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

// Restart endpoint
app.post('/restart', async (req, res) => {
    console.log('Manual restart requested');
    try {
        if (sock) {
            sock.end();
        }
        setTimeout(() => {
            initializeWhatsApp();
        }, 2000);
        res.json({ success: true, message: 'Restarting WhatsApp client...' });
    } catch (error) {
        console.error('Error restarting:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`WhatsApp service (Baileys) running on port ${PORT}`);
    initializeWhatsApp();
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('Shutting down gracefully...');
    if (sock) {
        sock.end();
    }
    process.exit();
});

process.on('SIGTERM', async () => {
    console.log('Shutting down gracefully...');
    if (sock) {
        sock.end();
    }
    process.exit();
});