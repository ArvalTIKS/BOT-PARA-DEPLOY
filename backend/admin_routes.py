from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
import asyncio
import os
from datetime import datetime, timedelta
from models import Client, ClientCreate, ClientResponse, ClientStatus, ToggleClientRequest
from database import get_database
from email_service import email_service  
from whatsapp_manager import service_manager

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/clients", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate, 
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    """Create new client and send invitation email"""
    try:
        # Get next available port
        port = service_manager.get_next_available_port()
        
        # Create client object
        client = Client(
            name=client_data.name,
            email=client_data.email,
            openai_api_key=client_data.openai_api_key,
            openai_assistant_id=client_data.openai_assistant_id,
            whatsapp_port=port,
            status=ClientStatus.INACTIVE
        )
        
        # Store in database
        clients_collection = db.clients
        await clients_collection.insert_one(client.dict())
        
        # Generate landing URL
        base_url = os.environ.get('BASE_URL', 'https://your-domain.com')
        landing_url = f"{base_url}/client/{client.unique_url}"
        
        # Send email in background
        background_tasks.add_task(
            email_service.send_client_invitation,
            client.email,
            client.name,
            landing_url
        )
        
        print(f"✅ Created client {client.name} with URL: {landing_url}")
        
        return ClientResponse(
            id=client.id,
            name=client.name,
            email=client.email,
            status=client.status,
            connected_phone=client.connected_phone,
            whatsapp_port=client.whatsapp_port,
            unique_url=client.unique_url,
            created_at=client.created_at,
            last_activity=client.last_activity
        )
        
    except Exception as e:
        print(f"❌ Error creating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients", response_model=List[ClientResponse])
async def get_all_clients(db = Depends(get_database)):
    """Get all clients"""
    try:
        clients_collection = db.clients
        clients = await clients_collection.find().to_list(length=None)
        
        result = []
        for client_data in clients:
            # Remove MongoDB _id field
            if '_id' in client_data:
                del client_data['_id']
            
            result.append(ClientResponse(**client_data))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/clients/{client_id}/toggle")
async def toggle_client_service(
    client_id: str, 
    toggle_request: ToggleClientRequest,
    db = Depends(get_database)
):
    """Connect or disconnect client's WhatsApp service"""
    try:
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"id": client_id})
        
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client = Client(**client_data)
        
        if toggle_request.action == "connect":
            # Start WhatsApp service for client
            success = await service_manager.create_service_for_client(client)
            
            if success:
                # Update client status
                await clients_collection.update_one(
                    {"id": client_id},
                    {"$set": {
                        "status": ClientStatus.ACTIVE,
                        "last_activity": datetime.utcnow()
                    }}
                )
                return {"message": f"Client {client.name} service started successfully", "status": "active"}
            else:
                return {"message": f"Failed to start service for {client.name}", "status": "error"}
                
        elif toggle_request.action == "disconnect":
            # Stop WhatsApp service for client
            success = await service_manager.stop_service_for_client(client_id)
            
            if success:
                # Update client status
                await clients_collection.update_one(
                    {"id": client_id},
                    {"$set": {
                        "status": ClientStatus.INACTIVE,
                        "connected_phone": None,
                        "last_activity": datetime.utcnow()
                    }}
                )
                return {"message": f"Client {client.name} service stopped successfully", "status": "inactive"}
            else:
                return {"message": f"Failed to stop service for {client.name}", "status": "error"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'connect' or 'disconnect'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clients/{client_id}")
async def delete_client(client_id: str, db = Depends(get_database)):
    """Delete client and stop their service"""
    try:
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"id": client_id})
        
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Stop service first
        await service_manager.stop_service_for_client(client_id)
        
        # Delete from database
        await clients_collection.delete_one({"id": client_id})
        
        # Delete client messages
        client_messages_collection = db.client_messages
        await client_messages_collection.delete_many({"client_id": client_id})
        
        return {"message": f"Client deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients/{client_id}/status")
async def get_client_status(client_id: str, db = Depends(get_database)):
    """Get detailed status of client's service"""
    try:
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"id": client_id})
        
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get service status
        service_status = service_manager.get_service_status(client_id)
        
        # Get message statistics
        client_messages_collection = db.client_messages
        total_messages = await client_messages_collection.count_documents({"client_id": client_id})
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = await client_messages_collection.count_documents({
            "client_id": client_id,
            "created_at": {"$gte": today_start}
        })
        
        unique_users = len(await client_messages_collection.distinct("phone_number", {"client_id": client_id}))
        
        return {
            "client": ClientResponse(**{k:v for k,v in client_data.items() if k != '_id'}),
            "service": service_status,
            "stats": {
                "total_messages": total_messages,
                "messages_today": messages_today,
                "unique_users": unique_users
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clients/{client_id}/connected")
async def client_connected(client_id: str, phone_data: dict, db = Depends(get_database)):
    """Callback when client's WhatsApp gets connected"""
    try:
        clients_collection = db.clients
        await clients_collection.update_one(
            {"id": client_id},
            {"$set": {
                "connected_phone": phone_data.get("phone"),
                "last_activity": datetime.utcnow()
            }}
        )
        return {"message": "Client connection status updated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clients/{client_id}/disconnected") 
async def client_disconnected(client_id: str, db = Depends(get_database)):
    """Callback when client's WhatsApp gets disconnected"""
    try:
        clients_collection = db.clients
        await clients_collection.update_one(
            {"id": client_id},
            {"$set": {
                "connected_phone": None,
                "last_activity": datetime.utcnow()
            }}
        )
        return {"message": "Client disconnection status updated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))