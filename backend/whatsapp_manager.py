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
        
    def get_next_available_port(self) -> int:
        """Get next available port starting from base_port"""
        port = self.base_port
        while port in [service['port'] for service in self.services.values()]:
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
                'FASTAPI_URL': 'http://localhost:8001',
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
        """Generate client-specific WhatsApp service based on main service"""
        try:
            with open('/app/whatsapp-service/whatsapp-service.js', 'r') as f:
                main_service = f.read()
            
            # Customize for client with proper port replacement
            client_service = main_service.replace(
                'const PORT = process.env.PORT || 3001;',
                f'const PORT = process.env.CLIENT_PORT || {port};'
            ).replace(
                'FASTAPI_URL = process.env.FASTAPI_URL || \'http://localhost:8001\';',
                f'FASTAPI_URL = \'http://localhost:8001\';'
            ).replace(
                '/api/whatsapp/process-message',
                f'/api/client/{client.id}/process-message'
            )
            
            return client_service
            
        except Exception as e:
            print(f"Error generating client service: {str(e)}")
            # Fallback simple service
            return f"""
const express = require('express');
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

app.listen(PORT, '0.0.0.0', () => {{
    console.log(`Basic service for {client.name} running on port ${{PORT}}`);
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