from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import httpx
import asyncio
from datetime import datetime
import openai
from database import get_database
from models import Client, ClientMessage
from whatsapp_manager import service_manager

router = APIRouter(prefix="/api/client", tags=["client"])

@router.get("/{unique_url}/status")
async def get_client_landing_status(unique_url: str, db = Depends(get_database)):
    """Get client status for landing page using individual services"""
    try:
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"unique_url": unique_url})
        
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client = Client(**{k:v for k,v in client_data.items() if k != '_id'})
        
        # Get WhatsApp status from individual service
        whatsapp_status = await service_manager.get_whatsapp_status_for_client(client.id)
        
        return {
            "client": {
                "name": client.name,
                "status": client.status,
                "connected": whatsapp_status.get("connected", False)
            },
            "whatsapp": whatsapp_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{unique_url}/qr")
async def get_client_qr(unique_url: str, db = Depends(get_database)):
    """Get QR code for client's individual WhatsApp service"""
    try:
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"unique_url": unique_url})
        
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client = Client(**{k:v for k,v in client_data.items() if k != '_id'})
        
        # Get QR from client's individual service
        qr_data = await service_manager.get_qr_code_for_client(client.id)
        
        if qr_data.get('qr'):
            return {
                "qr": qr_data['qr'],
                "raw": qr_data.get('raw'),
                "client_name": client.name,
                "instructions": "Escanea este código QR con tu WhatsApp para conectar tu asistente personalizado."
            }
        else:
            return {
                "qr": None,
                "error": qr_data.get('error', 'Servicio no disponible. Contacte al administrador.'),
                "retry": True
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{client_id}/process-message")
async def process_client_message(
    client_id: str,
    message_data: dict,
    db = Depends(get_database)
):
    """Process incoming WhatsApp messages for specific client with pause commands and OpenAI"""
    try:
        phone_number = message_data.get("phone_number")
        message_text = message_data.get("message")
        normalized_message = message_text.lower().strip()
        
        print(f"Processing message for client {client_id} from {phone_number}: {message_text}")
        
        # Get client data
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"id": client_id})
        
        if not client_data:
            return {"success": False, "error": "Client not found"}
        
        client = Client(**{k:v for k,v in client_data.items() if k != '_id'})
        
        # 🔥 PAUSE COMMANDS PROCESSING - HANDLE IMMEDIATELY
        pause_commands = ['pausar', 'reactivar', 'pausar todo', 'activar todo', 'estado']
        
        if normalized_message in pause_commands:
            print(f"🎯 PROCESSING PAUSE COMMAND: {normalized_message} for client {client.name}")
            
            # Import pause service
            from pause_service import pause_service
            
            try:
                if normalized_message == 'pausar':
                    await pause_service.pause_conversation(client_id, phone_number)
                    return {"success": True, "reply": "⏸️ Conversación pausada. Para reactivar, escribe 'reactivar'."}
                
                elif normalized_message == 'reactivar':
                    await pause_service.reactivate_conversation(client_id, phone_number)
                    return {"success": True, "reply": "✅ Conversación reactivada. El asistente responderá automáticamente."}
                
                elif normalized_message == 'pausar todo':
                    await pause_service.pause_all_conversations(client_id)
                    return {"success": True, "reply": "⏸️ Todas las conversaciones pausadas. Para reactivar todo, escribe 'activar todo'."}
                
                elif normalized_message == 'activar todo':
                    await pause_service.reactivate_all_conversations(client_id)
                    return {"success": True, "reply": "✅ Todas las conversaciones reactivadas."}
                
                elif normalized_message == 'estado':
                    is_paused = await pause_service.is_conversation_paused(client_id, phone_number)
                    status_text = "⏸️ Pausada" if is_paused else "✅ Activa"
                    return {"success": True, "reply": f"Estado de la conversación: {status_text}"}
                    
            except Exception as pause_error:
                print(f"❌ Error processing pause command: {pause_error}")
                return {"success": True, "reply": "❌ Error procesando comando. Intenta nuevamente."}
        
        # 🔍 CHECK IF CONVERSATION IS PAUSED BEFORE PROCESSING WITH AI
        from pause_service import pause_service
        is_paused = await pause_service.is_conversation_paused(client_id, phone_number)
        
        if is_paused:
            print(f"🔇 Conversation with {phone_number} is PAUSED for client {client.name} - not responding")
            return {"success": True, "reply": None}  # Silent - no response
        
        # 🤖 CONTINUE WITH NORMAL AI PROCESSING IF NOT PAUSED
        print(f"🤖 Processing with OpenAI for client {client.name}")
        
        # Generate response with client's specific OpenAI credentials
        ai_response = await generate_ai_response_for_client(message_text, phone_number, client, db)
        
        return {"success": True, "reply": ai_response}
        
    except Exception as e:
        print(f"❌ Error processing message for client {client_id}: {str(e)}")
        return {"success": False, "reply": "Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente."}

async def generate_ai_response_for_client(message: str, phone_number: str, client: Client, db) -> str:
    """Generate AI response using client's specific OpenAI configuration"""
    try:
        # Get or create thread for this client-phone combination
        thread_id = await get_or_create_client_thread(db, client.id, phone_number, client.openai_api_key)
        
        # Use client's OpenAI API key and Assistant ID
        openai_client = openai.OpenAI(api_key=client.openai_api_key)
        
        # Add message to thread
        openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run the client's assistant
        run = openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=client.openai_assistant_id
        )
        
        # Wait for completion with faster polling
        max_attempts = 60  # 30 seconds max (0.5s intervals)
        attempts = 0
        
        while run.status in ['queued', 'in_progress'] and attempts < max_attempts:
            await asyncio.sleep(0.5)  # Faster polling
            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            attempts += 1
        
        if run.status == 'completed':
            # Get the assistant's response
            messages = openai_client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=1
            )
            
            if messages.data and messages.data[0].role == 'assistant':
                ai_response = messages.data[0].content[0].text.value
                print(f"Assistant Response for {client.name}: {ai_response}")
                return ai_response
            else:
                return "Lo siento, no pude procesar tu mensaje correctamente. ¿Puedes intentar de nuevo?"
        
        elif run.status == 'failed':
            print(f"Assistant run failed for {client.name}: {run.last_error}")
            return "Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente."
        
        else:
            return "Lo siento, la respuesta está tomando más tiempo del esperado. ¿Puedes intentar de nuevo?"
        
    except Exception as e:
        print(f"❌ ERROR OpenAI para {client.name}: {str(e)}")
        print(f"API Key: {client.openai_api_key[:20]}...")
        print(f"Assistant ID: {client.openai_assistant_id}")
        import traceback
        traceback.print_exc()
        return "Lo siento, hubo un error temporal. Por favor intenta nuevamente."

async def get_or_create_client_thread(db, client_id: str, phone_number: str, api_key: str) -> str:
    """Get or create OpenAI thread for client-phone combination"""
    try:
        threads_collection = db.openai_threads
        
        # Look for existing thread
        thread_doc = await threads_collection.find_one({
            "client_id": client_id,
            "phone_number": phone_number
        })
        
        if thread_doc:
            return thread_doc["thread_id"]
        
        # Create new thread with client's API key
        openai_client = openai.OpenAI(api_key=api_key)
        thread = openai_client.beta.threads.create()
        thread_id = thread.id
        
        # Store in database
        await threads_collection.insert_one({
            "client_id": client_id,
            "phone_number": phone_number,
            "thread_id": thread_id,
            "created_at": datetime.utcnow()
        })
        
        return thread_id
        
    except Exception as e:
        print(f"Error getting/creating thread: {str(e)}")
        # Create a simple thread without DB storage as fallback
        openai_client = openai.OpenAI(api_key=api_key)
        thread = openai_client.beta.threads.create()
        return thread.id