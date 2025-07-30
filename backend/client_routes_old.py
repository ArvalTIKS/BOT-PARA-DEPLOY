from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import httpx
import asyncio
from datetime import datetime
import openai
from database import get_database
from models import Client, ClientMessage
from consolidated_whatsapp_manager import consolidated_manager
from whatsapp_manager import service_manager

router = APIRouter(prefix="/api/client", tags=["client"])

@router.get("/{unique_url}/status")
async def get_client_landing_status(unique_url: str, db = Depends(get_database)):
    """Get client status for landing page using consolidated system"""
    try:
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"unique_url": unique_url})
        
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client = Client(**{k:v for k,v in client_data.items() if k != '_id'})
        
        # Get WhatsApp status from consolidated manager
        whatsapp_status = await service_manager.get_whatsapp_status_for_client(client.id)
        
        return {
            "client": {
                "name": client.name,
                "status": client.status,
                "connected": whatsapp_status.get("connected", False),
                "registered": whatsapp_status.get("client_registered", False)
            },
            "whatsapp": whatsapp_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{client_id}/process-message", response_model=dict)
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
        thread_id = await get_or_create_client_thread(db, client.id, phone_number)
        
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
        
        # Wait for completion
        max_attempts = 30
        attempts = 0
        
        while run.status in ['queued', 'in_progress'] and attempts < max_attempts:
            await asyncio.sleep(1)
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
        print(f"Error with client OpenAI Assistant ({client.name}): {str(e)}")
        return "¡Hola! Gracias por tu mensaje. En este momento estoy procesando tu consulta. ¿En qué puedo ayudarte?"

@router.post("/{client_id}/process-message")
async def process_client_message(
    client_id: str,
    message_data: dict,
    db = Depends(get_database)
):
    """Process message for specific client"""
    try:
        # Get client data
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"id": client_id})
        
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client = Client(**client_data)
        
        phone_number = message_data["phone_number"]
        message_text = message_data["message"]
        timestamp = message_data["timestamp"]
        
        print(f"Processing message for client {client.name} from {phone_number}: {message_text}")
        
        # Import pause service
        from pause_service import pause_service
        
        # Store original message
        await store_client_message(db, client_id, phone_number, message_text, timestamp)
        
        # Check if it's a pause control command from the client
        if pause_service.is_pause_command(message_text):
            # Assume the client's phone is the connected_phone (when they connect via QR)
            client_phone = client.connected_phone or phone_number  # Fallback for testing
            
            command_response = await pause_service.process_pause_command(
                message_text, client_id, phone_number, client_phone
            )
            
            if command_response:
                # Store command response
                await store_client_message(
                    db, client_id, phone_number, command_response, 
                    timestamp=int(datetime.now().timestamp()), 
                    is_from_ai=True
                )
                return {"reply": command_response, "success": True}
        
        # Check if conversation is paused
        is_paused = await pause_service.is_conversation_paused(client_id, phone_number)
        
        if is_paused:
            # Conversation is paused, don't send to AI
            print(f"Conversation paused for client {client.name}, phone {phone_number}")
            return {"reply": None, "success": True, "paused": True}
        
        # Generate AI response using client's OpenAI config (normal flow)
        ai_response = await generate_client_ai_response(
            message_text, 
            phone_number, 
            client,
            db
        )
        
        # Store AI response
        await store_client_message(
            db, client_id, phone_number, ai_response, 
            timestamp=int(datetime.now().timestamp()), 
            is_from_ai=True
        )
        
        return {"reply": ai_response, "success": True}
        
    except Exception as e:
        print(f"Error processing client message: {str(e)}")
        return {
            "reply": "Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.",
            "success": False
        }

async def generate_client_ai_response(message: str, phone_number: str, client: Client, db) -> str:
    """Generate AI response using client's specific OpenAI configuration"""
    try:
        # Get or create thread for this client-phone combination
        thread_id = await get_or_create_client_thread(db, client.id, phone_number)
        
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
        
        # Wait for completion
        max_attempts = 30
        attempts = 0
        
        while run.status in ['queued', 'in_progress'] and attempts < max_attempts:
            await asyncio.sleep(1)
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
        print(f"Error with client OpenAI Assistant ({client.name}): {str(e)}")
        return "¡Hola! Gracias por tu mensaje. En este momento estoy procesando tu consulta. ¿En qué puedo ayudarte?"

async def get_or_create_client_thread(db, client_id: str, phone_number: str) -> str:
    """Get or create thread for client-phone combination"""
    try:
        threads_collection = db.client_threads
        thread_key = f"{client_id}_{phone_number}"
        
        # Look for existing thread
        thread_doc = await threads_collection.find_one({"thread_key": thread_key})
        
        if thread_doc and thread_doc.get('thread_id'):
            # Get client for OpenAI key
            clients_collection = db.clients
            client_data = await clients_collection.find_one({"id": client_id})
            client = Client(**client_data)
            
            # Verify thread still exists in OpenAI
            try:
                openai_client = openai.OpenAI(api_key=client.openai_api_key)
                thread = openai_client.beta.threads.retrieve(thread_doc['thread_id'])
                return thread.id
            except Exception as e:
                print(f"Thread {thread_doc['thread_id']} no longer exists: {e}")
                # Delete corrupted thread
                await threads_collection.delete_one({"thread_key": thread_key})
        
        # Create new thread
        clients_collection = db.clients
        client_data = await clients_collection.find_one({"id": client_id})
        client = Client(**client_data)
        
        openai_client = openai.OpenAI(api_key=client.openai_api_key)
        thread = openai_client.beta.threads.create()
        
        # Store thread ID
        await threads_collection.update_one(
            {"thread_key": thread_key},
            {
                "$set": {
                    "client_id": client_id,
                    "phone_number": phone_number,
                    "thread_id": thread.id,
                    "created_at": datetime.utcnow(),
                    "last_used": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        print(f"Created new thread {thread.id} for client {client.name} - phone {phone_number}")
        return thread.id
        
    except Exception as e:
        print(f"Error managing client thread: {str(e)}")
        raise Exception("Could not create conversation thread")

async def store_client_message(db, client_id: str, phone_number: str, message: str, timestamp: int, is_from_ai: bool = False):
    """Store message in client_messages collection"""
    try:
        client_messages_collection = db.client_messages
        message_data = ClientMessage(
            client_id=client_id,
            phone_number=phone_number,
            message=message,
            timestamp=timestamp,
            is_from_ai=is_from_ai
        )
        await client_messages_collection.insert_one(message_data.dict())
    except Exception as e:
        print(f"Error storing client message: {str(e)}")

@router.get("/{client_id}/messages/{phone_number}")
async def get_client_messages(client_id: str, phone_number: str, db = Depends(get_database)):
    """Get message history for specific client and phone"""
    try:
        client_messages_collection = db.client_messages
        messages = await client_messages_collection.find({
            "client_id": client_id,
            "phone_number": phone_number
        }).sort("timestamp", -1).limit(50).to_list(length=50)
        
        # Convert ObjectId to string
        for message in messages:
            if '_id' in message:
                message['_id'] = str(message['_id'])
        
        return {"messages": list(reversed(messages))}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))