from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models import Client
from database import get_database
from consolidated_whatsapp_manager import consolidated_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/consolidated", tags=["consolidated"])

@router.post("/phone-connected")
async def phone_connected(connection_data: dict, db = Depends(get_database)):
    """
    Notificación cuando un teléfono se conecta al servicio WhatsApp consolidado.
    Se debe asociar automáticamente con el primer cliente activo disponible.
    """
    try:
        phone_number = connection_data.get("phone_number")
        user_info = connection_data.get("user_info", {})
        
        logger.info(f"📱 Teléfono conectado: {phone_number}")
        
        # Obtener el primer cliente activo para asociar automáticamente
        clients_collection = db.clients
        active_client = await clients_collection.find_one({"status": "active"})
        
        if active_client:
            client = Client(**{k:v for k,v in active_client.items() if k != '_id'})
            
            # Asociar el teléfono con el cliente
            await consolidated_manager.associate_phone_with_client(phone_number, client.id)
            
            # Actualizar la base de datos con el teléfono conectado
            await clients_collection.update_one(
                {"id": client.id},
                {"$set": {"connected_phone": phone_number}}
            )
            
            logger.info(f"✅ Teléfono {phone_number} asociado automáticamente con cliente {client.name}")
            
            return {
                "success": True, 
                "message": f"Phone {phone_number} associated with client {client.name}",
                "client_id": client.id,
                "client_name": client.name
            }
        else:
            logger.warning("⚠️ No hay clientes activos para asociar el teléfono")
            return {
                "success": False,
                "message": "No active clients available for phone association"
            }
            
    except Exception as e:
        logger.error(f"❌ Error en phone-connected: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-message")
async def process_message_consolidated(message_data: dict):
    """
    Procesar mensaje usando el sistema consolidado
    """
    try:
        phone_number = message_data.get("phone_number")
        message = message_data.get("message")
        message_id = message_data.get("message_id")
        timestamp = message_data.get("timestamp", 0)
        
        # Formatear el número de teléfono para el procesamiento
        formatted_phone = f"{phone_number}@c.us"
        
        # Procesar el mensaje usando el gestor consolidado
        result = await consolidated_manager.process_message_for_client(
            formatted_phone, message, message_id, timestamp
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje consolidado: {str(e)}")
        return {"success": False, "error": str(e)}

@router.get("/status")
async def get_consolidated_status():
    """
    Obtener estado del sistema consolidado
    """
    try:
        # Estado del servicio WhatsApp
        whatsapp_status = await consolidated_manager.get_whatsapp_status()
        
        # Información de los clientes activos
        active_clients = len(consolidated_manager.active_clients)
        client_connections = len(consolidated_manager.client_connections)
        
        return {
            "whatsapp_connected": whatsapp_status.get("connected", False),
            "whatsapp_status": whatsapp_status,
            "active_clients": active_clients,
            "phone_connections": client_connections,
            "current_connected_client": consolidated_manager.current_connected_client,
            "client_connections": consolidated_manager.client_connections
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado consolidado: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients")
async def get_active_clients():
    """
    Obtener lista de clientes activos en el sistema consolidado
    """
    try:
        active_clients = []
        
        for client_id, client in consolidated_manager.active_clients.items():
            # Obtener estadísticas del cliente
            stats = await consolidated_manager.get_client_stats(client_id)
            
            active_clients.append({
                "id": client.id,
                "name": client.name,
                "email": client.email,
                "status": client.status,
                "connected_phone": client.connected_phone,
                "stats": stats
            })
        
        return {
            "active_clients": active_clients,
            "total_active": len(active_clients),
            "phone_connections": consolidated_manager.client_connections
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo clientes activos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/associate-phone")
async def manually_associate_phone(association_data: dict, db = Depends(get_database)):
    """
    Asociar manualmente un teléfono con un cliente específico
    """
    try:
        phone_number = association_data.get("phone_number")
        client_id = association_data.get("client_id")
        
        if not phone_number or not client_id:
            raise HTTPException(status_code=400, detail="phone_number and client_id are required")
        
        # Verificar que el cliente existe y está activo
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"id": client_id})
        
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client = Client(**{k:v for k,v in client_data.items() if k != '_id'})
        
        # Asociar en el gestor consolidado
        await consolidated_manager.associate_phone_with_client(phone_number, client_id)
        
        # Actualizar la base de datos
        await clients_collection.update_one(
            {"id": client_id},
            {"$set": {"connected_phone": phone_number}}
        )
        
        return {
            "success": True,
            "message": f"Phone {phone_number} associated with client {client.name}",
            "client_id": client_id,
            "client_name": client.name
        }
        
    except Exception as e:
        logger.error(f"❌ Error en asociación manual: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/qr")
async def get_consolidated_qr():
    """
    Obtener código QR del servicio consolidado
    """
    try:
        qr_data = await consolidated_manager.get_qr_code()
        return qr_data
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo QR consolidado: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))