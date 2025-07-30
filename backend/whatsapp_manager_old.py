import asyncio
import subprocess
import psutil
import signal
import os
from typing import Dict, List
from models import Client, ClientStatus
from consolidated_whatsapp_manager import consolidated_manager

class WhatsAppServiceManager:
    """
    Gestor mejorado que usa arquitectura consolidada para mejor estabilidad
    """
    
    def __init__(self):
        self.services: Dict[str, dict] = {}  # client_id -> service info (legacy)
        self.base_port = 3001
        
    def get_next_available_port(self) -> int:
        """Get next available port starting from base_port (legacy compatibility)"""
        port = self.base_port
        while port in [service['port'] for service in self.services.values()]:
            port += 1
        return port
    
    async def create_service_for_client(self, client: Client) -> bool:
        """
        Crear servicio para cliente usando arquitectura consolidada estable
        """
        try:
            # Registrar cliente en el gestor consolidado
            success = await consolidated_manager.register_client(client)
            
            if success:
                # Marcar como servicio "activo" para compatibilidad con el API existente
                self.services[client.id] = {
                    'port': 3001,  # Puerto del servicio consolidado
                    'process': None,  # No hay proceso separado
                    'service_dir': None,  # No hay directorio separado
                    'status': 'running'
                }
                
                print(f"✅ Cliente {client.name} registrado en el servicio consolidado")
                return True
            else:
                print(f"❌ Error registrando cliente {client.name} en el servicio consolidado")
                return False
            
        except Exception as e:
            print(f"❌ Error creando servicio consolidado para cliente {client.name}: {str(e)}")
            return False
    
    async def stop_service_for_client(self, client_id: str) -> bool:
        """
        Detener servicio para cliente (desregistrar del consolidado)
        """
        try:
            # Desregistrar del gestor consolidado
            success = await consolidated_manager.unregister_client(client_id)
            
            if success:
                # Remover de servicios locales
                if client_id in self.services:
                    del self.services[client_id]
                
                print(f"✅ Cliente {client_id} desregistrado del servicio consolidado")
                return True
            else:
                print(f"❌ Error desregistrando cliente {client_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error parando servicio para cliente {client_id}: {str(e)}")
            return False
    
    def get_service_status(self, client_id: str) -> dict:
        """
        Obtener estado del servicio para un cliente
        """
        if client_id not in self.services:
            return {"status": "stopped", "port": None}
        
        # El servicio consolidado siempre está "running" si está registrado
        service = self.services[client_id]
        return {
            "status": "running",
            "port": 3001,  # Puerto del servicio consolidado
            "pid": "consolidated"  # Identificador especial
        }
    
    async def get_whatsapp_status_for_client(self, client_id: str) -> dict:
        """
        Obtener estado específico de WhatsApp para un cliente
        """
        try:
            # Obtener estado general del servicio WhatsApp consolidado
            status = await consolidated_manager.get_whatsapp_status()
            
            # Verificar si el cliente está registrado
            if client_id in consolidated_manager.active_clients:
                status['client_registered'] = True
                status['client_id'] = client_id
            else:
                status['client_registered'] = False
            
            return status
            
        except Exception as e:
            print(f"❌ Error obteniendo estado de WhatsApp para cliente {client_id}: {str(e)}")
            return {"connected": False, "error": str(e), "client_registered": False}
    
    async def get_qr_code_for_client(self, client_id: str) -> dict:
        """
        Obtener código QR para un cliente (compartido del servicio consolidado)
        """
        try:
            # Todos los clientes comparten el mismo QR del servicio consolidado
            qr_data = await consolidated_manager.get_qr_code()
            
            if client_id in consolidated_manager.active_clients:
                qr_data['client_registered'] = True
                qr_data['client_id'] = client_id
            else:
                qr_data['client_registered'] = False
                qr_data['error'] = 'Client not registered'
            
            return qr_data
            
        except Exception as e:
            print(f"❌ Error obteniendo QR para cliente {client_id}: {str(e)}")
            return {"qr": None, "error": str(e), "client_registered": False}
    
    async def associate_phone_with_client(self, phone_number: str, client_id: str):
        """
        Asociar teléfono conectado con cliente específico
        """
        await consolidated_manager.associate_phone_with_client(phone_number, client_id)
        print(f"📱 Teléfono {phone_number} asociado con cliente {client_id}")
    
    async def get_client_stats(self, client_id: str) -> dict:
        """
        Obtener estadísticas del cliente desde el gestor consolidado
        """
        try:
            return await consolidated_manager.get_client_stats(client_id)
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas para cliente {client_id}: {str(e)}")
            return {"total_messages": 0, "messages_today": 0, "unique_users": 0}

# Global service manager instance
service_manager = WhatsAppServiceManager()