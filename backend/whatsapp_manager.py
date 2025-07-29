import asyncio
import subprocess
import psutil
import signal
import os
from typing import Dict, List
from models import Client, ClientStatus

class WhatsAppServiceManager:
    def __init__(self):
        self.services: Dict[str, dict] = {}  # client_id -> service info
        self.base_port = 3001
        
    def get_next_available_port(self) -> int:
        """Get next available port starting from base_port"""
        port = self.base_port
        while port in [service['port'] for service in self.services.values()]:
            port += 1
        return port
    
    async def create_service_for_client(self, client: Client) -> bool:
        """Create and start WhatsApp service for a specific client"""
        try:
            port = self.get_next_available_port()
            service_dir = f"/app/whatsapp-services/client-{client.id}"
            
            # Create service directory
            os.makedirs(service_dir, exist_ok=True)
            
            # Create client-specific config
            config_content = self._generate_client_config(client, port)
            with open(f"{service_dir}/client-config.js", "w") as f:
                f.write(config_content)
            
            # Create client-specific service file
            service_content = self._generate_client_service(client, port)
            with open(f"{service_dir}/service.js", "w") as f:
                f.write(service_content)
            
            # Copy dependencies
            await self._copy_dependencies(service_dir)
            
            # Start the service
            cmd = [
                "node",
                f"{service_dir}/service.js"
            ]
            
            env = os.environ.copy()
            env.update({
                'CLIENT_ID': client.id,
                'CLIENT_PORT': str(port),
                'CLIENT_NAME': client.name,
                'OPENAI_API_KEY': client.openai_api_key,
                'OPENAI_ASSISTANT_ID': client.openai_assistant_id,
                'FASTAPI_URL': 'http://localhost:8001'
            })
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=service_dir
            )
            
            # Store service info
            self.services[client.id] = {
                'port': port,
                'process': process,
                'service_dir': service_dir,
                'status': 'starting'
            }
            
            print(f"✅ Started WhatsApp service for client {client.name} on port {port}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating service for client {client.name}: {str(e)}")
            return False
    
    async def stop_service_for_client(self, client_id: str) -> bool:
        """Stop WhatsApp service for a specific client"""
        try:
            if client_id not in self.services:
                print(f"⚠️ No service found for client {client_id}")
                return True
            
            service = self.services[client_id]
            process = service['process']
            
            # Terminate process
            if process and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            
            # Clean up service directory
            service_dir = service['service_dir']
            if os.path.exists(service_dir):
                import shutil
                shutil.rmtree(service_dir)
            
            # Remove from services
            del self.services[client_id]
            
            print(f"✅ Stopped service for client {client_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping service for client {client_id}: {str(e)}")
            return False
    
    def get_service_status(self, client_id: str) -> dict:
        """Get status of client's WhatsApp service"""
        if client_id not in self.services:
            return {"status": "stopped", "port": None}
        
        service = self.services[client_id]
        process = service['process']
        
        if process and process.returncode is None:
            return {
                "status": "running",
                "port": service['port'],
                "pid": process.pid
            }
        else:
            return {"status": "stopped", "port": service['port']}
    
    def _generate_client_config(self, client: Client, port: int) -> str:
        """Generate client-specific configuration"""
        return f"""
// Client-specific configuration for {client.name}
module.exports = {{
    client: {{
        id: '{client.id}',
        name: '{client.name}',
        email: '{client.email}',
        openai_api_key: '{client.openai_api_key}',
        openai_assistant_id: '{client.openai_assistant_id}'
    }},
    server: {{
        host: '0.0.0.0',
        port: {port},
        gracefulShutdownTimeoutMs: 30000
    }},
    session: {{
        authDirectory: './whatsapp_session',
        persistData: true,
        backupAuthData: true
    }},
    puppeteer: {{
        navigationTimeout: 120000,
        pageLoadTimeout: 90000,
        defaultTimeout: 60000
    }},
    reconnection: {{
        maxAttempts: 5,
        baseDelayMs: 15000,
        maxDelayMs: 120000,
        sessionRecoveryDelayMs: 30000
    }}
}};
"""
    
    def _generate_client_service(self, client: Client, port: int) -> str:
        """Generate client-specific WhatsApp service"""
        return """
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
"""
    
    async def _copy_dependencies(self, service_dir: str):
        """Copy necessary dependencies to service directory"""
        try:
            # Copy package.json
            original_package = "/app/whatsapp-service/package.json"
            target_package = f"{service_dir}/package.json"
            
            if os.path.exists(original_package):
                import shutil
                shutil.copy2(original_package, target_package)
                
                # Install dependencies
                process = await asyncio.create_subprocess_exec(
                    'yarn', 'install',
                    cwd=service_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
                
        except Exception as e:
            print(f"Error copying dependencies: {str(e)}")

# Global service manager instance
service_manager = WhatsAppServiceManager()