"""
RECOVERY SERVICE PARA WHATSAPP - SOLUCIÓN INMEDIATA
Mantiene los servicios de WhatsApp corriendo y regenera QR automáticamente
"""
import asyncio
import time
import requests
import subprocess
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os

class WhatsAppRecoveryService:
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client.whatsapp_assistant
        self.running = True
        
    async def get_active_clients(self):
        """Obtener clientes activos de la base de datos"""
        clients = await self.db.clients.find({"status": "active"}).to_list(length=None)
        return clients
    
    def check_service_health(self, port):
        """Verificar si un servicio está respondiendo"""
        try:
            response = requests.get(f"http://localhost:{port}/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def restart_service(self, client_id):
        """Reiniciar servicio de un cliente específico"""
        try:
            # Desconectar
            requests.put(f"http://localhost:8001/api/admin/clients/{client_id}/toggle",
                        json={"action": "disconnect"}, timeout=10)
            time.sleep(3)
            
            # Reconectar 
            response = requests.put(f"http://localhost:8001/api/admin/clients/{client_id}/toggle",
                                   json={"action": "connect"}, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Servicio {client_id[:8]} reiniciado exitosamente")
                return True
            else:
                print(f"❌ Error reiniciando {client_id[:8]}: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Excepción reiniciando {client_id[:8]}: {e}")
            return False
    
    async def monitor_loop(self):
        """Loop principal de monitoreo"""
        print("🔄 INICIANDO RECOVERY SERVICE PARA WHATSAPP")
        
        while self.running:
            try:
                # Obtener clientes activos
                active_clients = await self.get_active_clients()
                print(f"📊 Monitoreando {len(active_clients)} clientes activos")
                
                for client in active_clients:
                    client_id = client['id']
                    client_name = client['name']
                    port = client['whatsapp_port']
                    
                    # Verificar salud del servicio
                    if not self.check_service_health(port):
                        print(f"⚠️ Servicio {client_name} (puerto {port}) no responde")
                        
                        # Intentar reiniciar
                        if self.restart_service(client_id):
                            print(f"🔄 Esperando inicialización de {client_name}...")
                            await asyncio.sleep(45)  # Tiempo para inicialización
                        else:
                            print(f"❌ No se pudo reiniciar {client_name}")
                    else:
                        # Verificar que tenga QR si no está conectado
                        try:
                            status_response = requests.get(f"http://localhost:{port}/status", timeout=5)
                            if status_response.status_code == 200:
                                status = status_response.json()
                                if not status.get('connected', False) and not status.get('hasQR', False):
                                    print(f"🔄 {client_name} necesita QR, forzando restart...")
                                    
                                    # Force restart via endpoint
                                    try:
                                        requests.get(f"http://localhost:{port}/force-restart", timeout=10)
                                        print(f"✅ Force restart enviado a {client_name}")
                                    except:
                                        # Fallback: restart completo
                                        self.restart_service(client_id)
                        except:
                            pass  # Continuar con el siguiente cliente
                
                # Esperar antes del próximo check
                await asyncio.sleep(30)  # Check cada 30 segundos
                
            except Exception as e:
                print(f"❌ Error en monitoring loop: {e}")
                await asyncio.sleep(60)  # Esperar más tiempo si hay error
    
    def stop(self):
        """Detener el servicio de recovery"""
        self.running = False
        print("🛑 Recovery service detenido")

# Función para iniciar el servicio
async def start_recovery_service():
    recovery = WhatsAppRecoveryService()
    try:
        await recovery.monitor_loop()
    except KeyboardInterrupt:
        recovery.stop()
        print("👋 Recovery service terminado")

if __name__ == "__main__":
    asyncio.run(start_recovery_service())