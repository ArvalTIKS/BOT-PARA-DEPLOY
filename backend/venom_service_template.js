const express = require('express');
const { create, Whatsapp } = require('venom-bot');
const qrcode = require('qrcode');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Configuración del cliente
const CLIENT_CONFIG = {CLIENT_CONFIG_PLACEHOLDER};
const PORT = CLIENT_CONFIG.port;
const CLIENT_ID = CLIENT_CONFIG.id;
const CLIENT_NAME = CLIENT_CONFIG.name;

// Variables de estado
let client = null;
let qrCodeData = null;
let isConnected = false;
let connectedUser = null;
let isInitializing = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;

// Directorio de sesión
const sessionDir = path.join(__dirname, 'venom_session');

const app = express();
app.use(express.json());

// Configuración de Venom con mejor estabilidad
const venomOptions = {
    session: 'whatsapp-session',
    folderNameToken: sessionDir,
    headless: true,
    devtools: false,
    useChrome: false,
    debug: false,
    logQR: false,
    browserArgs: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding'
    ],
    puppeteerOptions: {
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
};

// Inicializar Venom WhatsApp
async function initializeVenomWhatsApp() {
    try {
        if (isInitializing) {
            console.log('🔄 Venom ya está inicializándose, esperando...');
            return;
        }
        
        isInitializing = true;
        console.log(`🚀 VENOM: Iniciando WhatsApp para ${CLIENT_NAME}...`);
        
        // Limpiar cliente existente
        if (client) {
            try {
                await client.close();
            } catch (e) {
                console.log('Error cerrando cliente (safe):', e.message);
            }
            client = null;
        }
        
        // Reset estados
        qrCodeData = null;
        isConnected = false;
        connectedUser = null;
        
        // Crear sesión con Venom
        client = await create({
            session: `client-${CLIENT_ID}`,
            ...venomOptions
        })
        .then((client) => {
            console.log(`✅ VENOM: Cliente inicializado para ${CLIENT_NAME}`);
            isInitializing = false;
            reconnectAttempts = 0;
            return client;
        })
        .catch(async (erro) => {
            console.error(`❌ VENOM: Error inicializando ${CLIENT_NAME}:`, erro);
            isInitializing = false;
            
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                const delay = Math.min(10000 * reconnectAttempts, 60000);
                console.log(`🔄 VENOM: Reintentando en ${delay/1000}s (intento ${reconnectAttempts})`);
                
                setTimeout(() => {
                    initializeVenomWhatsApp();
                }, delay);
            }
            throw erro;
        });

        // Eventos de Venom
        if (client) {
            // QR Code event
            client.onStateChange((state) => {
                console.log(`🔄 VENOM: Estado cambiado a ${state} para ${CLIENT_NAME}`);
                
                if (state === 'CONNECTED') {
                    isConnected = true;
                    console.log(`✅ VENOM: ${CLIENT_NAME} conectado exitosamente`);
                    
                    // Obtener info del usuario
                    client.getHostDevice().then(hostDevice => {
                        connectedUser = hostDevice;
                        console.log(`📱 VENOM: Conectado como ${hostDevice.pushname || hostDevice.phone}`);
                    }).catch(e => console.log('Error obteniendo info del usuario:', e));
                }
                else if (state === 'DISCONNECTED') {
                    isConnected = false;
                    connectedUser = null;
                    console.log(`❌ VENOM: ${CLIENT_NAME} desconectado`);
                    
                    // Auto-reconexión
                    setTimeout(() => {
                        console.log(`🔄 VENOM: Intentando reconectar ${CLIENT_NAME}...`);
                        initializeVenomWhatsApp();
                    }, 5000);
                }
            });

            // Mensaje recibido
            client.onMessage(async (message) => {
                try {
                    if (message.body && !message.isGroupMsg && message.from !== 'status@broadcast') {
                        console.log(`📨 VENOM: Mensaje recibido en ${CLIENT_NAME} de ${message.from}`);
                        
                        // Enviar a backend para procesamiento
                        const response = await axios.post(`http://localhost:8001/api/client/${CLIENT_ID}/process-message`, {
                            phone_number: message.from.replace('@c.us', ''),
                            message: message.body,
                            message_id: message.id,
                            timestamp: message.timestamp
                        }, {
                            headers: { 'Content-Type': 'application/json' }
                        });
                        
                        if (response.data.success && response.data.reply) {
                            // Enviar respuesta
                            await client.sendText(message.from, response.data.reply);
                            console.log(`📤 VENOM: Respuesta enviada a ${message.from}`);
                        }
                    }
                } catch (error) {
                    console.error(`❌ VENOM: Error procesando mensaje:`, error);
                }
            });

            // QR Code
            client.onQRCode(async (qrCode) => {
                try {
                    console.log(`📱 VENOM: QR generado para ${CLIENT_NAME}`);
                    qrCodeData = await qrcode.toDataURL(qrCode);
                    console.log(`✅ VENOM: QR disponible para ${CLIENT_NAME}`);
                } catch (error) {
                    console.error(`❌ VENOM: Error generando QR:`, error);
                    qrCodeData = null;
                }
            });
        }
        
    } catch (error) {
        console.error(`💥 VENOM: Error crítico inicializando ${CLIENT_NAME}:`, error);
        isInitializing = false;
        
        // Retry con backoff exponencial
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            const delay = Math.min(15000 * Math.pow(2, reconnectAttempts), 300000); // Max 5 minutos
            console.log(`🔄 VENOM: Retry en ${delay/1000}s (intento ${reconnectAttempts})`);
            
            setTimeout(() => {
                initializeVenomWhatsApp();
            }, delay);
        }
    }
}

// API Endpoints
app.get('/status', (req, res) => {
    res.json({
        connected: isConnected,
        user: connectedUser,
        hasQR: !!qrCodeData,
        library: 'venom-bot',
        reconnectAttempts: reconnectAttempts
    });
});

app.get('/qr', (req, res) => {
    if (qrCodeData) {
        res.json({ qr: qrCodeData });
    } else {
        res.json({ qr: null });
    }
});

app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        client: CLIENT_NAME,
        library: 'venom-bot',
        connected: isConnected 
    });
});

app.post('/logout', async (req, res) => {
    try {
        if (client && isConnected) {
            await client.logout();
            console.log(`👋 VENOM: ${CLIENT_NAME} desconectado por solicitud`);
            
            // Reset estados
            isConnected = false;
            connectedUser = null;
            qrCodeData = null;
            
            res.json({ success: true, message: 'Logged out successfully' });
            
            // Reinicializar después de logout
            setTimeout(() => {
                initializeVenomWhatsApp();
            }, 3000);
        } else {
            res.json({ success: false, error: 'Not connected' });
        }
    } catch (error) {
        console.error('❌ VENOM: Error en logout:', error);
        res.json({ success: false, error: error.message });
    }
});

app.get('/force-restart', async (req, res) => {
    console.log(`🚨 VENOM: FORCE RESTART solicitado para ${CLIENT_NAME}`);
    
    try {
        // Limpiar cliente
        if (client) {
            await client.close().catch(e => console.log('Error cerrando (safe):', e.message));
            client = null;
        }
        
        // Reset estados
        isConnected = false;
        connectedUser = null;
        qrCodeData = null;
        isInitializing = false;
        reconnectAttempts = 0;
        
        // Limpiar sesión
        if (fs.existsSync(sessionDir)) {
            fs.rmSync(sessionDir, { recursive: true, force: true });
        }
        
        // Restart inmediato
        console.log(`🔄 VENOM: REINICIO INMEDIATO ${CLIENT_NAME}...`);
        setTimeout(() => {
            initializeVenomWhatsApp();
        }, 2000);
        
        res.json({ success: true, message: `Venom force restart iniciado para ${CLIENT_NAME}` });
    } catch (error) {
        console.error('💥 VENOM: Error en force restart:', error);
        res.json({ success: false, error: error.message });
    }
});

// Iniciar servidor
const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 VENOM: Servicio individual para ${CLIENT_NAME} corriendo en puerto ${PORT}`);
    console.log(`📡 VENOM: Iniciando WhatsApp en 5 segundos...`);
    
    // Inicializar WhatsApp después de que el servidor esté listo
    setTimeout(() => {
        initializeVenomWhatsApp();
    }, 5000);
});

// Manejo de señales para cierre limpio
process.on('SIGTERM', async () => {
    console.log(`🛑 VENOM: Cerrando servicio para ${CLIENT_NAME}...`);
    if (client) {
        await client.close().catch(e => console.log('Error cerrando cliente:', e));
    }
    server.close();
});

process.on('SIGINT', async () => {
    console.log(`🛑 VENOM: Cerrando servicio para ${CLIENT_NAME}...`);
    if (client) {
        await client.close().catch(e => console.log('Error cerrando cliente:', e));
    }
    server.close();
});