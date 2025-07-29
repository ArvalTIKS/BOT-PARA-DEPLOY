const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');
const deployConfig = require('./deploy-config');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = deployConfig.server.port;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';

// Deploy-aware environment detection
const isDeployEnv = deployConfig.isProduction || process.env.EMERGENT_ENV === 'deploy';
console.log(`Running in ${isDeployEnv ? 'DEPLOY' : 'PREVIEW'} environment`);

let client = null;
let qrCodeData = null;
let isConnected = false;
let connectedUser = null;
let sessionDir = deployConfig.session.authDirectory;
let isInitializing = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = deployConfig.reconnection.maxAttempts;

// Enhanced Puppeteer configuration for deployment
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
            '--disable-renderer-backgrounding'
        ]
    };
    
    if (isDeployEnv) {
        // Deploy-specific Puppeteer optimizations
        baseConfig.args.push(
            '--single-process',
            '--no-zygote',
            '--disable-dev-shm-usage',
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection'
        );
        
        // Longer timeouts for deploy environment
        baseConfig.timeout = deployConfig.puppeteer.navigationTimeout;
        baseConfig.defaultViewport = null;
    } else {
        // Preview environment optimizations
        baseConfig.timeout = 60000;
    }
    
    // Use system Chromium if available
    const chromiumPath = '/usr/bin/chromium';
    if (fs.existsSync(chromiumPath)) {
        baseConfig.executablePath = chromiumPath;
        console.log('Using system Chromium:', chromiumPath);
    }
    
    return baseConfig;
};

// Initialize WhatsApp with whatsapp-web.js
async function initializeWhatsApp() {
    try {
        // Prevent multiple initializations
        if (isInitializing) {
            console.log('WhatsApp is already initializing, skipping...');
            return;
        }
        
        isInitializing = true;
        console.log('Initializing WhatsApp with whatsapp-web.js...');
        
        // Close existing client if present
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

        // Create client with optimized configuration
        const puppeteerConfig = getPuppeteerConfig();
        
        client = new Client({
            authStrategy: new LocalAuth({
                clientId: 'whatsapp-client',
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
            console.log('QR Code received');
            qrCodeData = qr;
            reconnectAttempts = 0; // Reset reconnect attempts when QR is generated
            try {
                const qrDataUrl = await qrcode.toDataURL(qr);
                console.log('QR Code generated successfully');
            } catch (err) {
                console.error('Error generating QR code:', err);
            }
        });

        // Authentication success
        client.on('authenticated', () => {
            console.log('WhatsApp authenticated successfully');
        });

        // Ready event
        client.on('ready', async () => {
            console.log('WhatsApp client is ready!');
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
                
                // Notify the consolidated manager about the phone connection
                try {
                    await axios.post(`${FASTAPI_URL}/api/consolidated/phone-connected`, {
                        phone_number: connectedUser.phone,
                        user_info: connectedUser
                    });
                    console.log('✅ Notified consolidated manager about phone connection');
                } catch (notifyError) {
                    console.error('❌ Error notifying consolidated manager:', notifyError);
                }
                
            } catch (err) {
                console.error('Error getting user info:', err);
            }
        });

        // Enhanced disconnection handling with automatic cleanup
        client.on('disconnected', async (reason) => {
            console.log('WhatsApp disconnected:', reason);
            isConnected = false;
            connectedUser = null;
            qrCodeData = null;
            
            // Check for specific reasons that need cleanup
            const needsCleanup = reason === 'LOGOUT' || reason === 'NAVIGATION' || 
                               reason === 'UNPAIRED' || reason === 'UNPAIRED_PHONE';
            
            if (needsCleanup) {
                console.log('🚨 Detected session corruption - cleaning and reinitializing');
                console.log('Disconnect reason:', reason);
                
                // Clean up session data for fresh start
                if (fs.existsSync(sessionDir)) {
                    console.log('🧹 Removing corrupted session data automatically');
                    fs.rmSync(sessionDir, { recursive: true, force: true });
                }
                
                // Reset reconnection attempts
                reconnectAttempts = 0;
                
                // Reinitialize after short delay
                setTimeout(() => {
                    console.log('🔄 Auto-reinitializing WhatsApp with clean session');
                    initializeWhatsApp();
                }, 5000);
                
                return;
            }
            
            // Normal reconnection logic
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                console.log(`Reconnection attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
                
                // Deploy-optimized reconnection strategy
                const reconnectConfig = isDeployEnv ? deployConfig.reconnection : {
                    baseDelayMs: 5000,
                    maxDelayMs: 30000
                };
                
                const delay = Math.min(reconnectConfig.baseDelayMs * reconnectAttempts, reconnectConfig.maxDelayMs);
                
                setTimeout(() => {
                    initializeWhatsApp();
                }, delay);
            } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                console.log('Max reconnection attempts reached, implementing deploy-specific recovery');
                
                // Deploy-specific recovery: Don't immediately clear session data
                if (isDeployEnv && deployConfig.session.persistData) {
                    console.log('Attempting session recovery in deploy environment');
                    setTimeout(() => {
                        reconnectAttempts = 0;
                        initializeWhatsApp();
                    }, deployConfig.reconnection.sessionRecoveryDelayMs);
                } else {
                    // Clear session data if not in deploy
                    if (fs.existsSync(sessionDir)) {
                        fs.rmSync(sessionDir, { recursive: true, force: true });
                    }
                    setTimeout(() => {
                        reconnectAttempts = 0;
                        initializeWhatsApp();
                    }, 60000);
                }
            }
        });

        // Authentication failure
        client.on('auth_failure', async (msg) => {
            console.error('Authentication failure:', msg);
            
            // Clean up corrupted auth data
            if (fs.existsSync(sessionDir)) {
                console.log('🧹 Removing corrupted auth data due to auth failure');
                try {
                    fs.rmSync(sessionDir, { recursive: true, force: true });
                } catch (rmError) {
                    console.log('Error removing session dir (safe to ignore):', rmError.message);
                }
            }
            
            // Reinitialize after delay
            setTimeout(() => {
                console.log('🔄 Reinitializing after auth failure');
                initializeWhatsApp();
            }, 10000);
        });

        // Message received event
        client.on('message', async (message) => {
            if (!message.fromMe && message.body) {
                const messageText = message.body;
                const normalizedMessage = messageText.toLowerCase().trim();
                
                // Check for legacy bot control commands (compatibility)
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
                
                // Check for new pause control commands
                const pauseCommands = ['pausar', 'reactivar', 'pausar todo', 'activar todo', 'estado'];
                if (pauseCommands.includes(normalizedMessage)) {
                    console.log(`Pause command detected: ${normalizedMessage} from ${message.from}`);
                    // Let the consolidated manager handle pause commands - they will be processed there
                }
                
                console.log('Received message:', messageText);
                console.log('From:', message.from);
                
                try {
                    // Use consolidated message processing endpoint
                    const response = await axios.post(`${FASTAPI_URL}/api/consolidated/process-message`, {
                        phone_number: message.from.split('@')[0],
                        message: messageText,
                        message_id: message.id.id,
                        timestamp: message.timestamp
                    });

                    // Send AI response back to WhatsApp if there's a reply
                    if (response.data.reply) {
                        await message.reply(response.data.reply);
                        console.log('Reply sent:', response.data.reply);
                    } else if (response.data.paused) {
                        console.log('Conversation is paused, no automatic reply sent');
                    } else if (response.data.error) {
                        console.log('Processing error:', response.data.error);
                        // Only send error message if it's not a "no client found" error
                        if (!response.data.error.includes('No client found')) {
                            await message.reply('Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.');
                        }
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

        // Initialize the client
        console.log('Starting WhatsApp client initialization...');
        await client.initialize();

    } catch (error) {
        console.error('Error initializing WhatsApp:', error);
        isInitializing = false;
        
        // If there's a persistent initialization error, try with deploy-specific recovery
        if (fs.existsSync(sessionDir) && (!isDeployEnv || !deployConfig.session.persistData)) {
            console.log('Removing session directory due to initialization error (preview mode)');
            fs.rmSync(sessionDir, { recursive: true, force: true });
        } else if (isDeployEnv && deployConfig.session.persistData) {
            console.log('Keeping session directory for persistence (deploy mode)');
        }
        
        // Retry initialization with deploy-optimized delay
        const retryDelay = isDeployEnv ? 15000 : 10000;
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
    
    if (!isConnected || !client) {
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

// Restart endpoint
app.post('/restart', async (req, res) => {
    console.log('Manual restart requested');
    try {
        if (client) {
            await client.destroy();
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

// Start server with deploy-optimized configuration
const server = app.listen(PORT, deployConfig.server.host, () => {
    console.log(`WhatsApp service (Baileys) running on port ${PORT} in ${isDeployEnv ? 'DEPLOY' : 'PREVIEW'} mode`);
    // Wait a moment before initializing to ensure server is ready
    const initDelay = isDeployEnv ? 5000 : 2000; // Longer delay for deploy
    setTimeout(() => {
        initializeWhatsApp();
    }, initDelay);
});

// Enhanced server error handling for deploy
server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.log(`Port ${PORT} is already in use. Attempting deploy-specific recovery...`);
        if (isDeployEnv) {
            // In deploy, try graceful recovery
            setTimeout(() => {
                process.exit(1); // Let supervisor restart
            }, 5000);
        } else {
            // In preview, try alternative port
            const alternativePort = PORT + 1;
            server.listen(alternativePort, deployConfig.server.host, () => {
                console.log(`WhatsApp service (Baileys) running on alternative port ${alternativePort}`);
                setTimeout(() => {
                    initializeWhatsApp();
                }, 2000);
            });
        }
    } else {
        console.error('Server error:', err);
        if (isDeployEnv) {
            // In deploy, exit gracefully to trigger supervisor restart
            setTimeout(() => {
                process.exit(1);
            }, 1000);
        }
    }
});

// Enhanced graceful shutdown for deploy environment
const gracefulShutdown = async () => {
    console.log('Shutting down gracefully...');
    
    // Close WhatsApp client
    if (client) {
        console.log('Destroying WhatsApp client...');
        try {
            await client.destroy();
        } catch (error) {
            console.error('Error destroying client:', error);
        }
    }
    
    // Close HTTP server
    if (server) {
        console.log('Closing HTTP server...');
        server.close(() => {
            console.log('HTTP server closed');
            process.exit(0);
        });
        
        // Force close after timeout
        setTimeout(() => {
            console.log('Forcing shutdown...');
            process.exit(1);
        }, deployConfig.server.gracefulShutdownTimeoutMs);
    } else {
        process.exit(0);
    }
};

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);

// Enhanced error handling for deploy
process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
    
    if (isDeployEnv) {
        // In deploy, attempt graceful recovery
        console.log('Attempting graceful recovery in deploy environment...');
        setTimeout(() => {
            process.exit(1); // Let supervisor restart
        }, 5000);
    } else {
        // In preview, try to continue
        console.log('Continuing in preview mode...');
    }
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled rejection at:', promise, 'reason:', reason);
    
    if (isDeployEnv) {
        // In deploy, be more conservative
        console.log('Unhandled rejection in deploy environment, restarting...');
        setTimeout(() => {
            process.exit(1); // Let supervisor restart
        }, 3000);
    } else {
        // In preview, try to continue
        console.log('Continuing in preview mode...');
    }
});