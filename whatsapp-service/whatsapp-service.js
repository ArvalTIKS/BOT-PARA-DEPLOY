const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const deployConfig = require('./deploy-config');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = deployConfig.server.port;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';

// Deploy-aware environment detection
const isDeployEnv = deployConfig.isProduction || process.env.EMERGENT_ENV === 'deploy';
console.log(`Running in ${isDeployEnv ? 'DEPLOY' : 'PREVIEW'} environment`);

let sock = null;
let qrCodeData = null;
let isConnected = false;
let connectedUser = null;
let authDir = deployConfig.session.authDirectory;
let isInitializing = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = deployConfig.reconnection.maxAttempts;

// Initialize WhatsApp with Baileys
async function initializeWhatsApp() {
    try {
        // Prevent multiple initializations
        if (isInitializing) {
            console.log('WhatsApp is already initializing, skipping...');
            return;
        }
        
        isInitializing = true;
        console.log('Initializing WhatsApp with Baileys...');
        
        // Close existing socket if present
        if (sock) {
            console.log('Closing existing socket...');
            sock.end();
            sock = null;
        }
        
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
            logger: require('pino')({ level: 'silent' }),
            browser: ['WhatsApp Assistant', 'Chrome', '4.0.0'],
            connectTimeoutMs: ENV_CONFIG.connectTimeoutMs,
            defaultQueryTimeoutMs: 0,
            keepAliveIntervalMs: ENV_CONFIG.keepAliveIntervalMs,
            emitOwnEvents: true,
            markOnlineOnConnect: false,
            syncFullHistory: false,
            // Deploy-specific optimizations
            retryRequestDelayMs: 1000,
            maxMsgRetryCount: 3,
            requestTimeoutMs: 30000,
            getMessage: async (key) => {
                return { conversation: '' };
            }
        });

        isInitializing = false;

        // QR Code event
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            if (qr) {
                console.log('QR Code received');
                qrCodeData = qr;
                reconnectAttempts = 0; // Reset reconnect attempts when QR is generated
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
                
                if (shouldReconnect && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    reconnectAttempts++;
                    console.log(`Reconnection attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
                    
                    // Deploy-optimized reconnection strategy
                    const baseDelay = ENV_CONFIG.reconnectDelayMs;
                    const delay = Math.min(baseDelay * reconnectAttempts, ENV_CONFIG.maxReconnectDelay);
                    
                    setTimeout(() => {
                        initializeWhatsApp();
                    }, delay);
                } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                    console.log('Max reconnection attempts reached, implementing deploy-specific recovery');
                    
                    // Deploy-specific recovery: Don't immediately clear auth data
                    if (ENV_CONFIG.sessionPersistence) {
                        console.log('Attempting session recovery in deploy environment');
                        setTimeout(() => {
                            reconnectAttempts = 0;
                            initializeWhatsApp();
                        }, ENV_CONFIG.maxReconnectDelay);
                    } else {
                        // Clear auth data if not in deploy
                        if (fs.existsSync(authDir)) {
                            fs.rmSync(authDir, { recursive: true, force: true });
                        }
                        setTimeout(() => {
                            reconnectAttempts = 0;
                            initializeWhatsApp();
                        }, 60000);
                    }
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
                    const normalizedMessage = messageText.toLowerCase().trim();
                    
                    // Check for bot control commands
                    if (normalizedMessage === 'activar bot') {
                        try {
                            await sock.sendMessage(message.key.remoteJid, { 
                                text: '✅ Bot activado. Responderé automáticamente a todos los mensajes del Estudio Jurídico Villegas Otárola.' 
                            });
                            console.log('Bot activated for:', message.key.remoteJid);
                            return;
                        } catch (error) {
                            console.error('Error activating bot:', error);
                        }
                    }
                    
                    if (normalizedMessage === 'suspender bot') {
                        try {
                            await sock.sendMessage(message.key.remoteJid, { 
                                text: '⏸️ Bot suspendido. Ahora puedes usar tu celular normalmente.' 
                            });
                            console.log('Bot suspended for:', message.key.remoteJid);
                            return;
                        } catch (error) {
                            console.error('Error suspending bot:', error);
                        }
                    }
                    
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
        isInitializing = false;
        
        // If there's a persistent initialization error, try with deploy-specific recovery
        if (fs.existsSync(authDir) && !ENV_CONFIG.sessionPersistence) {
            console.log('Removing auth directory due to initialization error (preview mode)');
            fs.rmSync(authDir, { recursive: true, force: true });
        } else if (ENV_CONFIG.sessionPersistence) {
            console.log('Keeping auth directory for session persistence (deploy mode)');
        }
        
        // Retry initialization with deploy-optimized delay
        const retryDelay = ENV_CONFIG.sessionPersistence ? 15000 : 10000;
        setTimeout(() => {
            initializeWhatsApp();
        }, retryDelay);
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
const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`WhatsApp service (Baileys) running on port ${PORT}`);
    // Wait a moment before initializing to ensure server is ready
    setTimeout(() => {
        initializeWhatsApp();
    }, 2000);
});

// Handle server errors
server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.log(`Port ${PORT} is already in use. Trying to find available port...`);
        // Try a different port
        const alternativePort = PORT + 1;
        server.listen(alternativePort, '0.0.0.0', () => {
            console.log(`WhatsApp service (Baileys) running on alternative port ${alternativePort}`);
            setTimeout(() => {
                initializeWhatsApp();
            }, 2000);
        });
    } else {
        console.error('Server error:', err);
    }
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('Shutting down gracefully...');
    if (sock) {
        sock.end();
    }
    if (server) {
        server.close();
    }
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    if (sock) {
        sock.end();
    }
    if (server) {
        server.close();
    }
    process.exit(0);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
    // Don't exit, try to recover
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled rejection at:', promise, 'reason:', reason);
    // Don't exit, try to recover
});