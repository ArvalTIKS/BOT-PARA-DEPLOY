import asyncio
import subprocess
import psutil
import signal
import os
import shutil
from typing import Dict, List
from models import Client, ClientStatus

class WhatsAppServiceManager:
    """
    Multi-tenant WhatsApp service manager - cada cliente tiene su propio servicio independiente
    """
    
    def __init__(self):
        self.services: Dict[str, dict] = {}  # client_id -> service info
        self.base_port = 3002  # Start from 3002 (3001 is reserved for legacy)
        
    async def get_next_available_port(self, db) -> int:
        """Get next available port starting from base_port, checking database"""
        port = self.base_port
        
        # Get all ports currently assigned in database
        clients_collection = db.clients
        existing_clients = await clients_collection.find().to_list(length=None)
        used_ports = [client.get('whatsapp_port') for client in existing_clients if client.get('whatsapp_port')]
        
        # Also check ports from running services
        service_ports = [service['port'] for service in self.services.values()]
        all_used_ports = set(used_ports + service_ports)
        
        while port in all_used_ports:
            port += 1
        return port
    
    async def create_service_for_client(self, client: Client) -> bool:
        """Create and start independent WhatsApp service for a specific client"""
        try:
            port = client.whatsapp_port  # Use the port assigned to the client
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
                'FASTAPI_URL': os.environ.get('FASTAPI_URL'),
                'EMERGENT_ENV': os.environ.get('EMERGENT_ENV', 'preview')
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
                'status': 'starting',
                'client_name': client.name
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
                shutil.rmtree(service_dir)
            
            # Remove from services
            client_name = service.get('client_name', client_id)
            del self.services[client_id]
            
            print(f"✅ Stopped service for client {client_name}")
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
    
    async def get_whatsapp_status_for_client(self, client_id: str) -> dict:
        """Get WhatsApp connection status for specific client"""
        try:
            if client_id not in self.services:
                return {"connected": False, "error": "Service not running"}
            
            service = self.services[client_id]
            port = service['port']
            
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as http_client:
                response = await http_client.get(f"http://localhost:{port}/status")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"connected": False, "error": "Service unavailable"}
                    
        except Exception as e:
            print(f"❌ Error getting WhatsApp status for client {client_id}: {str(e)}")
            return {"connected": False, "error": str(e)}
    
    async def get_qr_code_for_client(self, client_id: str) -> dict:
        """Get QR code for client's WhatsApp service"""
        try:
            if client_id not in self.services:
                return {"qr": None, "error": "Service not running"}
            
            service = self.services[client_id]
            port = service['port']
            
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.get(f"http://localhost:{port}/qr")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"qr": None, "error": "QR not available"}
                    
        except Exception as e:
            print(f"❌ Error getting QR for client {client_id}: {str(e)}")
            return {"qr": None, "error": str(e)}
    
    async def disconnect_client_whatsapp(self, client_id: str) -> dict:
        """Disconnect WhatsApp for specific client"""
        try:
            if client_id not in self.services:
                return {"success": False, "error": "Service not running"}
            
            service = self.services[client_id]
            port = service['port']
            
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                response = await http_client.get(f"http://localhost:{port}/logout")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"success": False, "error": "Logout failed"}
                    
        except Exception as e:
            print(f"❌ Error disconnecting client {client_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
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
        maxAttempts: 10,
        baseDelayMs: 20000,
        maxDelayMs: 120000,
        sessionRecoveryDelayMs: 30000
    }}
}};
"""
    
    def _generate_client_service(self, client: Client, port: int) -> str:
        """Generate client-specific WhatsApp service with correct Chromium configuration"""
        try:
            # Generate optimized individual service with system Chromium
            client_service = f"""const {{ Client, LocalAuth, MessageMedia }} = require('whatsapp-web.js');
const qrcode = require('qrcode');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.CLIENT_PORT || {port};
const FASTAPI_URL = 'http://localhost:8001';
const CLIENT_ID = process.env.CLIENT_ID || '{client.id}';

// Deploy-aware environment detection
const isDeployEnv = process.env.EMERGENT_ENV === 'deploy';
console.log(`Individual service for {client.name} running in ${{isDeployEnv ? 'DEPLOY' : 'PREVIEW'}} environment`);

let client = null;
let qrCodeData = null;
let isConnected = false;
let connectedUser = null;
let sessionDir = './whatsapp_session';
let isInitializing = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Enhanced Puppeteer configuration for individual services
const getPuppeteerConfig = () => {{
    const uniqueProfileDir = `/tmp/whatsapp-chrome-${{Date.now()}}-${{Math.random().toString(36).substr(2, 9)}}`;
    
    const baseConfig = {{
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
            `--user-data-dir=${{uniqueProfileDir}}`
        ]
    }};
    
    // FORCE system Chromium for individual services (ARM64 compatibility)
    const systemChromiumPath = '/usr/bin/chromium';
    if (fs.existsSync(systemChromiumPath)) {{
        baseConfig.executablePath = systemChromiumPath;
        console.log(`Individual service using system Chromium: ${{systemChromiumPath}}`);
    }} else {{
        console.log('WARNING: System Chromium not found, using Puppeteer bundled (may fail on ARM64)');
    }}
    
    return baseConfig;
}};

// Initialize WhatsApp with whatsapp-web.js
async function initializeWhatsApp() {{
    try {{
        if (isInitializing) {{
            console.log('WhatsApp is already initializing, skipping...');
            return;
        }}
        
        isInitializing = true;
        console.log(`🚀 FAST INIT: Starting WhatsApp for client {client.name}...`);
        
        if (client) {{
            console.log('Destroying existing client...');
            try {{
                await client.destroy();
            }} catch (destroyError) {{
                console.log('Error destroying client (safe to ignore):', destroyError.message);
            }}
            client = null;
        }}
        
        // Ensure session directory exists
        if (!fs.existsSync(sessionDir)) {{
            fs.mkdirSync(sessionDir, {{ recursive: true }});
        }}

        // Clear any existing QR to show loading state
        qrCodeData = null;
        console.log('🔄 QR cleared - initializing...');

        // Create client with system Chromium configuration
        const puppeteerConfig = getPuppeteerConfig();
        
        client = new Client({{
            authStrategy: new LocalAuth({{
                clientId: `whatsapp-client-${{CLIENT_ID}}`,
                dataPath: sessionDir
            }}),
            puppeteer: puppeteerConfig,
            webVersionCache: {{
                type: 'remote',
                remotePath: 'https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html',
            }}
        }});

        isInitializing = false;

        // QR Code event
        client.on('qr', async (qr) => {{
            console.log(`QR Code received for {client.name}`);
            qrCodeData = qr;
            reconnectAttempts = 0;
            try {{
                const qrDataUrl = await qrcode.toDataURL(qr);
                console.log(`QR Code generated successfully for {client.name}`);
            }} catch (err) {{
                console.error('Error generating QR code:', err);
            }}
        }});

        // Authentication success
        client.on('authenticated', () => {{
            console.log(`WhatsApp authenticated successfully for {client.name}`);
        }});

        // Ready event
        client.on('ready', async () => {{
            console.log(`WhatsApp client is ready for {client.name}!`);
            isConnected = true;
            qrCodeData = null;
            
            try {{
                const info = client.info;
                connectedUser = {{
                    name: info.pushname || 'WhatsApp User',
                    phone: info.wid.user || 'Unknown',
                    profileImage: null,
                    connectedAt: new Date().toISOString()
                }};
                
                console.log(`Connected user for {client.name}:`, connectedUser);
            }} catch (err) {{
                console.error('Error getting user info:', err);
            }}
        }});

        // Disconnection handling - ROBUST RECOVERY
        client.on('disconnected', async (reason) => {{
            console.log(`🔄 WhatsApp disconnected for {client.name}:`, reason);
            isConnected = false;
            connectedUser = null;
            qrCodeData = null;
            isInitializing = false;
            
            // Immediate reconnection with exponential backoff
            const reconnectDelay = Math.min(5000 * Math.pow(2, reconnectAttempts), 60000);
            console.log(`🔄 Auto-reconnecting {client.name} in ${{reconnectDelay/1000}}s (attempt ${{reconnectAttempts + 1}})`);
            
            setTimeout(async () => {{
                try {{
                    await initializeWhatsApp();
                }} catch (error) {{
                    console.error(`❌ Reconnection failed for {client.name}:`, error);
                    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {{
                        setTimeout(() => initializeWhatsApp(), 15000);
                    }}
                }}
            }}, reconnectDelay);
        }});

        // Authentication failure - IMMEDIATE RECOVERY
        client.on('auth_failure', async (msg) => {{
            console.log(`❌ Auth failed for {client.name}:`, msg);
            qrCodeData = null;
            isConnected = false;
            connectedUser = null;
            isInitializing = false;
            
            // Clear corrupted session immediately
            try {{
                if (fs.existsSync(sessionDir)) {{
                    const sessionFiles = fs.readdirSync(sessionDir);
                    sessionFiles.forEach(file => {{
                        const filePath = path.join(sessionDir, file);
                        if (fs.statSync(filePath).isDirectory()) {{
                            fs.rmSync(filePath, {{ recursive: true, force: true }});
                        }} else {{
                            fs.unlinkSync(filePath);
                        }}
                    }});
                    console.log(`🧹 Cleared session for {client.name}`);
                }}
            }} catch (cleanError) {{
                console.log('Error clearing session (safe to ignore):', cleanError.message);
            }}
            
            // Force restart with clean session
            console.log(`🔄 Force restarting {client.name} with clean session`);
            setTimeout(() => {{
                initializeWhatsApp();
            }}, 5000);
        }});

        // Message received event
        client.on('message', async (message) => {{
            if (!message.fromMe && message.body) {{
                // Only respond to private messages
                if (message.from.includes('-') || message.from.includes('@g.us')) {{
                    console.log(`Ignored group message for {client.name} from ${{message.from}}: ${{message.body}}`);
                    return;
                }}
                
                if (!message.from.includes('@c.us')) {{
                    console.log(`Ignored non-private message for {client.name} from ${{message.from}}`);
                    return;
                }}
                
                console.log(`Message for {client.name} from ${{message.from}}: ${{message.body}}`);
                
                try {{
                    // Send message to FastAPI for processing
                    const response = await axios.post(`${{FASTAPI_URL}}/api/client/${{CLIENT_ID}}/process-message`, {{
                        phone_number: message.from.split('@')[0],
                        message: message.body,
                        message_id: message.id.id,
                        timestamp: message.timestamp
                    }});

                    // Send AI response back to WhatsApp if there's a reply
                    if (response.data.reply) {{
                        await message.reply(response.data.reply);
                        console.log(`Reply sent for {client.name}:`, response.data.reply);
                    }} else if (response.data.paused) {{
                        console.log(`Conversation is paused for {client.name}, no automatic reply sent`);
                    }}
                }} catch (error) {{
                    console.error(`Error processing message for {client.name}:`, error);
                    try {{
                        await message.reply('Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.');
                    }} catch (replyError) {{
                        console.error(`Error sending fallback message for {client.name}:`, replyError);
                    }}
                }}
            }}
        }});

        // Initialize the client
        console.log(`Starting WhatsApp client initialization for {client.name}...`);
        await client.initialize();

    }} catch (error) {{
        console.error(`Error initializing WhatsApp for {client.name}:`, error);
        isInitializing = false;
        
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {{
            reconnectAttempts++;
            console.log(`Initialization retry ${{reconnectAttempts}}/${{MAX_RECONNECT_ATTEMPTS}} for {client.name}`);
            
            setTimeout(() => {{
                initializeWhatsApp();
            }}, 10000);
        }}
    }}
}}

// API Routes
app.get('/qr', async (req, res) => {{
    try {{
        if (qrCodeData) {{
            const qrDataUrl = await qrcode.toDataURL(qrCodeData);
            res.json({{ 
                qr: qrDataUrl,
                raw: qrCodeData
            }});
        }} else {{
            res.json({{ qr: null }});
        }}
    }} catch (error) {{
        console.error('Error generating QR:', error);
        res.status(500).json({{ error: error.message }});
    }}
}});

app.get('/status', (req, res) => {{
    res.json({{
        connected: isConnected,
        user: connectedUser,
        hasQR: !!qrCodeData
    }});
}});

app.get('/health', (req, res) => {{
    res.json({{
        status: 'running',
        connected: isConnected,
        client: '{client.name}',
        port: PORT,
        timestamp: new Date().toISOString()
    }});
}});

app.get('/logout', (req, res) => {{
    res.json({{
        success: true,
        message: 'Logout initiated for {client.name}',
        instructions: 'Please wait while we disconnect your device from WhatsApp.'
    }});
    
    setTimeout(async () => {{
        try {{
            console.log(`Initiating complete WhatsApp logout for {client.name}...`);
            
            if (client) {{
                await client.logout();
                console.log(`WhatsApp logout completed for {client.name}`);
                
                isConnected = false;
                connectedUser = null;
                qrCodeData = null;
                
                if (fs.existsSync(sessionDir)) {{
                    console.log(`Removing all session data for {client.name}...`);
                    fs.rmSync(sessionDir, {{ recursive: true, force: true }});
                }}
                
                console.log(`Complete logout and cleanup finished for {client.name}`);
                client = null;
            }}
        }} catch (error) {{
            console.error(`Error during logout for {client.name}:`, error);
        }}
    }}, 1000);
}});

// Force restart endpoint - EMERGENCY RECOVERY
        app.get('/force-restart', async (req, res) => {{
            console.log(`🚨 FORCE RESTART requested for {client.name}`);
            
            try {{
                // Destroy existing client
                if (client) {{
                    await client.destroy().catch(e => console.log('Destroy error (safe):', e.message));
                    client = null;
                }}
                
                // Reset all states
                isConnected = false;
                connectedUser = null;
                qrCodeData = null;
                isInitializing = false;
                reconnectAttempts = 0;
                
                // Clear session
                if (fs.existsSync(sessionDir)) {{
                    fs.rmSync(sessionDir, {{ recursive: true, force: true }});
                }}
                
                // Immediate restart
                console.log(`🔄 IMMEDIATE restart {client.name}...`);
                setTimeout(() => {{
                    initializeWhatsApp();
                }}, 2000);
                
                res.json({{ success: true, message: `Force restart initiated for {client.name}` }});
            }} catch (error) {{
                console.error('Force restart error:', error);
                res.json({{ success: false, error: error.message }});
            }}
        }});

// Start server
const server = app.listen(PORT, '0.0.0.0', () => {{
    console.log(`Individual WhatsApp service for {client.name} running on port ${{PORT}}`);
    
    // Initialize WhatsApp after server starts
    setTimeout(() => {{
        initializeWhatsApp();
    }}, 2000);
}});

// Graceful shutdown
const gracefulShutdown = async () => {{
    console.log(`Shutting down individual service for {client.name}...`);
    
    if (client) {{
        console.log(`Destroying WhatsApp client for {client.name}...`);
        try {{
            await client.destroy();
        }} catch (error) {{
            console.error(`Error destroying client for {client.name}:`, error);
        }}
    }}
    
    if (server) {{
        console.log(`Closing HTTP server for {client.name}...`);
        server.close(() => {{
            console.log(`HTTP server closed for {client.name}`);
            process.exit(0);
        }});
        
        setTimeout(() => {{
            console.log(`Forcing shutdown for {client.name}...`);
            process.exit(1);
        }}, 30000);
    }} else {{
        process.exit(0);
    }}
}};

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);
"""
            
            return client_service
            
        except Exception as e:
            print(f"Error generating client service: {{str(e)}}")
            # Fallback simple service with correct port
            return f"""const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = {port};

app.get('/status', (req, res) => {{
    res.json({{ connected: false, user: null, hasQR: false }});
}});

app.get('/qr', (req, res) => {{
    res.json({{ qr: null }});
}});

app.get('/health', (req, res) => {{
    res.json({{ status: 'error', message: 'Fallback service', port: PORT }});
}});

app.listen(PORT, '0.0.0.0', () => {{
    console.log(`Fallback service for {client.name} running on port ${{PORT}}`);
}});
"""
    
    async def _copy_dependencies(self, service_dir: str):
        """Copy necessary dependencies to service directory"""
        try:
            # Copy package.json
            original_package = "/app/whatsapp-service/package.json"
            target_package = f"{service_dir}/package.json"
            
            if os.path.exists(original_package):
                shutil.copy2(original_package, target_package)
            
            # Copy deploy-config.js
            original_deploy_config = "/app/whatsapp-service/deploy-config.js"
            target_deploy_config = f"{service_dir}/deploy-config.js"
            
            if os.path.exists(original_deploy_config):
                shutil.copy2(original_deploy_config, target_deploy_config)
            
            # Copy .env.deploy
            original_env_deploy = "/app/whatsapp-service/.env.deploy"
            target_env_deploy = f"{service_dir}/.env.deploy"
            
            if os.path.exists(original_env_deploy):
                shutil.copy2(original_env_deploy, target_env_deploy)
                
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