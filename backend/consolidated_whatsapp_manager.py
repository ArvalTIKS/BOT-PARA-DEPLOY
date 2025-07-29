import asyncio
import json
import aiohttp
from typing import Dict, Optional, List
from datetime import datetime
from models import Client, ClientStatus
from database import get_database
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class ConsolidatedWhatsAppManager:
    """
    Gestor consolidado que maneja múltiples clientes usando un solo servicio WhatsApp
    con routing inteligente basado en el número de teléfono conectado
    """
    
    def __init__(self):
        self.active_clients: Dict[str, Client] = {}  # client_id -> Client
        self.client_connections: Dict[str, str] = {}  # phone_number -> client_id
        self.whatsapp_service_url = "http://localhost:3001"
        self.current_connected_client: Optional[str] = None
        
    async def register_client(self, client: Client) -> bool:
        """Registrar un cliente en el sistema consolidado"""
        try:
            self.active_clients[client.id] = client
            logger.info(f"✅ Cliente {client.name} registrado en el sistema consolidado")
            return True
        except Exception as e:
            logger.error(f"❌ Error registrando cliente {client.name}: {str(e)}")
            return False
    
    async def unregister_client(self, client_id: str) -> bool:
        """Desregistrar un cliente del sistema"""
        try:
            if client_id in self.active_clients:
                client = self.active_clients[client_id]
                del self.active_clients[client_id]
                
                # Remover conexiones de teléfono asociadas
                phones_to_remove = [phone for phone, cid in self.client_connections.items() if cid == client_id]
                for phone in phones_to_remove:
                    del self.client_connections[phone]
                
                # Si era el cliente conectado actualmente, limpiar
                if self.current_connected_client == client_id:
                    self.current_connected_client = None
                
                logger.info(f"✅ Cliente {client.name} desregistrado del sistema")
                return True
            return True
        except Exception as e:
            logger.error(f"❌ Error desregistrando cliente {client_id}: {str(e)}")
            return False
    
    async def get_whatsapp_status(self) -> dict:
        """Obtener el estado del servicio WhatsApp consolidado"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.whatsapp_service_url}/status") as response:
                    if response.status == 200:
                        status = await response.json()
                        return status
                    else:
                        return {"connected": False, "error": "Service unavailable"}
        except Exception as e:
            logger.error(f"Error obteniendo estado de WhatsApp: {str(e)}")
            return {"connected": False, "error": str(e)}
    
    async def get_qr_code(self) -> dict:
        """Obtener el código QR del servicio WhatsApp"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.whatsapp_service_url}/qr") as response:
                    if response.status == 200:
                        qr_data = await response.json()
                        return qr_data
                    else:
                        return {"qr": None, "error": "QR not available"}
        except Exception as e:
            logger.error(f"Error obteniendo QR: {str(e)}")
            return {"qr": None, "error": str(e)}
    
    async def associate_phone_with_client(self, phone_number: str, client_id: str):
        """Asociar un número de teléfono con un cliente específico"""
        self.client_connections[phone_number] = client_id
        self.current_connected_client = client_id
        logger.info(f"📱 Teléfono {phone_number} asociado con cliente {client_id}")
    
    def get_client_for_phone(self, phone_number: str) -> Optional[Client]:
        """Obtener el cliente asociado a un número de teléfono"""
        # Limpiar el número de teléfono para comparación
        clean_phone = phone_number.replace("@c.us", "").replace("@s.whatsapp.net", "")
        
        # Buscar en las conexiones existentes
        if clean_phone in self.client_connections:
            client_id = self.client_connections[clean_phone]
            return self.active_clients.get(client_id)
        
        # Si no hay asociación específica, usar el cliente conectado actual
        if self.current_connected_client:
            return self.active_clients.get(self.current_connected_client)
        
        return None
    
    async def process_message_for_client(self, phone_number: str, message: str, message_id: str, timestamp: int) -> dict:
        """Procesar un mensaje para el cliente apropiado"""
        try:
            client = self.get_client_for_phone(phone_number)
            
            if not client:
                logger.warning(f"No se encontró cliente para el teléfono {phone_number}")
                return {"success": False, "error": "No client found"}
            
            # Verificar si la conversación está pausada (usando el sistema existente)
            from pause_service import pause_service
            is_paused = await pause_service.is_conversation_paused(client.id, phone_number.split('@')[0])
            
            # Manejar comandos de pausa específicos del cliente
            normalized_message = message.lower().strip()
            pause_commands = ['pausar', 'reactivar', 'pausar todo', 'activar todo', 'estado']
            
            if normalized_message in pause_commands:
                response = await self._handle_pause_command(client.id, phone_number, normalized_message)
                return response
            
            # Si está pausado, no procesar con OpenAI
            if is_paused:
                return {"success": True, "paused": True, "reply": None}
            
            # Procesar con OpenAI usando las credenciales del cliente
            response = await self._process_with_openai(client, phone_number, message, message_id, timestamp)
            return response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje para cliente: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _handle_pause_command(self, client_id: str, phone_number: str, command: str) -> dict:
        """Manejar comandos de pausa usando el sistema existente"""
        try:
            from pause_service import pause_service
            clean_phone = phone_number.split('@')[0]
            
            if command == 'pausar':
                await pause_service.pause_conversation(client_id, clean_phone)
                return {"success": True, "reply": "⏸️ Conversación pausada. Para reactivar, escribe 'reactivar'."}
            
            elif command == 'reactivar':
                await pause_service.reactivate_conversation(client_id, clean_phone)
                return {"success": True, "reply": "✅ Conversación reactivada. El asistente responderá automáticamente."}
            
            elif command == 'pausar todo':
                await pause_service.pause_all_conversations(client_id)
                return {"success": True, "reply": "⏸️ Todas las conversaciones pausadas. Para reactivar todo, escribe 'activar todo'."}
            
            elif command == 'activar todo':
                await pause_service.reactivate_all_conversations(client_id)
                return {"success": True, "reply": "✅ Todas las conversaciones reactivadas."}
            
            elif command == 'estado':
                status = await pause_service.get_conversation_status(client_id, clean_phone)
                status_text = "⏸️ Pausada" if status else "✅ Activa"
                return {"success": True, "reply": f"Estado de la conversación: {status_text}"}
            
            return {"success": False, "error": "Comando no reconocido"}
            
        except Exception as e:
            logger.error(f"Error manejando comando de pausa: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _process_with_openai(self, client: Client, phone_number: str, message: str, message_id: str, timestamp: int) -> dict:
        """Procesar mensaje con OpenAI usando las credenciales del cliente específico"""
        try:
            # Configurar OpenAI con las credenciales del cliente
            openai_client = OpenAI(api_key=client.openai_api_key)
            
            # Obtener o crear thread para esta conversación
            clean_phone = phone_number.split('@')[0]
            thread_id = await self._get_or_create_thread(client.id, clean_phone)
            
            # Agregar mensaje al thread
            await asyncio.to_thread(
                openai_client.beta.threads.messages.create,
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            # Ejecutar con el asistente del cliente
            run = await asyncio.to_thread(
                openai_client.beta.threads.runs.create,
                thread_id=thread_id,
                assistant_id=client.openai_assistant_id
            )
            
            # Esperar respuesta
            while run.status in ['queued', 'in_progress', 'cancelling']:
                await asyncio.sleep(1)
                run = await asyncio.to_thread(
                    openai_client.beta.threads.runs.retrieve,
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                # Obtener mensajes del thread
                messages = await asyncio.to_thread(
                    openai_client.beta.threads.messages.list,
                    thread_id=thread_id
                )
                
                # Obtener la respuesta más reciente del asistente
                for msg in messages.data:
                    if msg.role == 'assistant':
                        reply = msg.content[0].text.value
                        
                        # Guardar en base de datos
                        await self._save_message_to_db(client.id, clean_phone, message, reply, timestamp)
                        
                        return {"success": True, "reply": reply}
            
            return {"success": False, "error": "OpenAI processing failed"}
            
        except Exception as e:
            logger.error(f"Error procesando con OpenAI: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_or_create_thread(self, client_id: str, phone_number: str) -> str:
        """Obtener o crear thread de OpenAI para la conversación"""
        try:
            db = await get_database()
            threads_collection = db.openai_threads
            
            # Buscar thread existente
            thread_doc = await threads_collection.find_one({
                "client_id": client_id,
                "phone_number": phone_number
            })
            
            if thread_doc:
                return thread_doc["thread_id"]
            
            # Crear nuevo thread
            client = self.active_clients[client_id]
            openai_client = OpenAI(api_key=client.openai_api_key)
            
            thread = await asyncio.to_thread(openai_client.beta.threads.create)
            thread_id = thread.id
            
            # Guardar en base de datos
            await threads_collection.insert_one({
                "client_id": client_id,
                "phone_number": phone_number,
                "thread_id": thread_id,
                "created_at": datetime.utcnow()
            })
            
            return thread_id
            
        except Exception as e:
            logger.error(f"Error creando thread: {str(e)}")
            raise
    
    async def _save_message_to_db(self, client_id: str, phone_number: str, user_message: str, ai_reply: str, timestamp: int):
        """Guardar mensaje en la base de datos"""
        try:
            db = await get_database()
            client_messages_collection = db.client_messages
            
            message_doc = {
                "client_id": client_id,
                "phone_number": phone_number,
                "user_message": user_message,
                "ai_reply": ai_reply,
                "timestamp": timestamp,
                "created_at": datetime.utcnow()
            }
            
            await client_messages_collection.insert_one(message_doc)
            
        except Exception as e:
            logger.error(f"Error guardando mensaje: {str(e)}")
    
    async def get_client_stats(self, client_id: str) -> dict:
        """Obtener estadísticas de un cliente específico"""
        try:
            db = await get_database()
            client_messages_collection = db.client_messages
            
            total_messages = await client_messages_collection.count_documents({"client_id": client_id})
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            messages_today = await client_messages_collection.count_documents({
                "client_id": client_id,
                "created_at": {"$gte": today_start}
            })
            
            unique_users = len(await client_messages_collection.distinct("phone_number", {"client_id": client_id}))
            
            return {
                "total_messages": total_messages,
                "messages_today": messages_today,
                "unique_users": unique_users
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {"total_messages": 0, "messages_today": 0, "unique_users": 0}

# Instancia global del gestor consolidado
consolidated_manager = ConsolidatedWhatsAppManager()