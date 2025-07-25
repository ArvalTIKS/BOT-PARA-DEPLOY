from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import asyncio
from datetime import datetime
import openai
from database import get_database

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# OpenAI client
openai.api_key = os.environ.get('OPENAI_API_KEY')
# Auto-detect WhatsApp service URL based on environment
def get_whatsapp_service_url():
    # Check for explicit environment variable first
    if os.environ.get('WHATSAPP_SERVICE_URL'):
        return os.environ.get('WHATSAPP_SERVICE_URL')
    
    # Check if we're in Emergent deployed environment
    if os.environ.get('EMERGENT_ENV') == 'deploy' or os.environ.get('NODE_ENV') == 'production':
        # In deployed environment, construct the external URL
        # Get the current domain from environment or construct it
        import re
        
        # Try to get the domain from various sources
        domain = None
        
        # Method 1: Check if we have a domain hint in environment
        if os.environ.get('DEPLOYMENT_DOMAIN'):
            domain = os.environ.get('DEPLOYMENT_DOMAIN')
        
        # Method 2: Try to construct from known patterns
        # Emergent uses pattern: https://[app-name].emergent.host
        else:
            # Default to the known deployment domain
            domain = 'whatsapp-qr-link.emergent.host'
        
        # Construct the WhatsApp service URL
        external_whatsapp_url = f"https://{domain}"
        
        print(f"Deploy environment detected, using external URL: {external_whatsapp_url}")
        
        # Try external URL first, then fallback to internal
        service_urls = [
            f"{external_whatsapp_url}:3001",  # External with port
            external_whatsapp_url,            # External without port
            'http://127.0.0.1:3001',          # Internal fallback
            'http://localhost:3001'           # Local fallback
        ]
        
        for url in service_urls:
            try:
                import socket
                from urllib.parse import urlparse
                parsed = urlparse(url)
                
                # For external URLs, assume they're valid in deploy
                if parsed.hostname and not parsed.hostname.startswith('127.') and not parsed.hostname.startswith('localhost'):
                    print(f"Using external URL: {url}")
                    return url
                
                # For internal URLs, test connectivity
                socket.getaddrinfo(parsed.hostname, parsed.port or 80)
                print(f"Internal URL tested successfully: {url}")
                return url
            except Exception as e:
                print(f"URL {url} failed: {e}")
                continue
    
    # Default to localhost for local development
    return 'http://localhost:3001'

WHATSAPP_SERVICE_URL = get_whatsapp_service_url()
print(f"WhatsApp service URL configured: {WHATSAPP_SERVICE_URL}")

class IncomingMessage(BaseModel):
    phone_number: str
    message: str
    message_id: str
    timestamp: int

class MessageResponse(BaseModel):
    reply: Optional[str] = None
    success: bool = True

class OutgoingMessage(BaseModel):
    phone_number: str
    message: str

@router.post("/process-message", response_model=MessageResponse)
async def process_whatsapp_message(
    message_data: IncomingMessage,
    db = Depends(get_database)
):
    """Process incoming WhatsApp messages with OpenAI"""
    try:
        phone_number = message_data.phone_number
        message_text = message_data.message
        
        print(f"Processing message from {phone_number}: {message_text}")
        
        # Store message in database
        await store_message(db, phone_number, message_text, message_data.timestamp)
        
        # Generate response with OpenAI
        ai_response = await generate_ai_response(message_text, phone_number, db)
        
        # Store AI response
        await store_message(db, phone_number, ai_response, timestamp=int(datetime.now().timestamp()), is_from_ai=True)
        
        return MessageResponse(reply=ai_response)
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return MessageResponse(
            reply="Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente.",
            success=False
        )

async def generate_ai_response(message: str, phone_number: str, db) -> str:
    """Generate response using OpenAI Assistant API"""
    try:
        # Get or create thread for this conversation
        thread_id = await get_or_create_thread(db, phone_number)
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        assistant_id = os.environ.get('OPENAI_ASSISTANT_ID')
        
        if not assistant_id:
            print("Error: OPENAI_ASSISTANT_ID not configured")
            return "Lo siento, hay un problema de configuración. Por favor intenta más tarde."
        
        # Add message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Wait for completion
        max_attempts = 30  # 30 seconds max
        attempts = 0
        
        while run.status in ['queued', 'in_progress'] and attempts < max_attempts:
            await asyncio.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            attempts += 1
        
        if run.status == 'completed':
            # Get the assistant's response
            messages = client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=1
            )
            
            if messages.data and messages.data[0].role == 'assistant':
                ai_response = messages.data[0].content[0].text.value
                print(f"Assistant Response: {ai_response}")
                return ai_response
            else:
                print("No assistant response found in thread")
                return "Lo siento, no pude procesar tu mensaje correctamente. ¿Puedes intentar de nuevo?"
        
        elif run.status == 'failed':
            print(f"Assistant run failed: {run.last_error}")
            return "Lo siento, hubo un error procesando tu mensaje. Por favor intenta nuevamente."
        
        else:
            print(f"Assistant run timed out or unexpected status: {run.status}")
            return "Lo siento, la respuesta está tomando más tiempo del esperado. ¿Puedes intentar de nuevo?"
        
    except Exception as e:
        print(f"Error with OpenAI Assistant: {str(e)}")
        return "¡Hola! Gracias por tu mensaje. En este momento estoy procesando tu consulta. ¿En qué puedo ayudarte?"

async def get_or_create_thread(db, phone_number: str) -> str:
    """Get existing thread ID or create new one for phone number"""
    try:
        threads_collection = db.whatsapp_threads
        
        # Look for existing thread
        thread_doc = await threads_collection.find_one({"phone_number": phone_number})
        
        if thread_doc and thread_doc.get('thread_id'):
            return thread_doc['thread_id']
        
        # Create new thread
        client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        thread = client.beta.threads.create()
        
        # Store thread ID
        await threads_collection.update_one(
            {"phone_number": phone_number},
            {
                "$set": {
                    "thread_id": thread.id,
                    "created_at": datetime.utcnow(),
                    "last_used": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        print(f"Created new thread {thread.id} for {phone_number}")
        return thread.id
        
    except Exception as e:
        print(f"Error managing thread: {str(e)}")
        # Fallback: create temporary thread
        try:
            client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            thread = client.beta.threads.create()
            return thread.id
        except Exception as fallback_error:
            print(f"Fallback thread creation failed: {str(fallback_error)}")
            raise Exception("Could not create conversation thread")

async def store_message(db, phone_number: str, message: str, timestamp: int, is_from_ai: bool = False):
    """Store message in database"""
    try:
        messages_collection = db.whatsapp_messages
        message_data = {
            "phone_number": phone_number,
            "message": message,
            "timestamp": timestamp,
            "is_from_ai": is_from_ai,
            "created_at": datetime.utcnow()
        }
        await messages_collection.insert_one(message_data)
    except Exception as e:
        print(f"Error storing message: {str(e)}")

async def get_conversation_history(db, phone_number: str, limit: int = 20):
    """Get conversation history for context"""
    try:
        messages_collection = db.whatsapp_messages
        messages = await messages_collection.find({
            "phone_number": phone_number
        }).sort("timestamp", -1).limit(limit).to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for message in messages:
            if '_id' in message:
                message['_id'] = str(message['_id'])
        
        # Reverse to get chronological order
        return list(reversed(messages))
    except Exception as e:
        print(f"Error getting conversation history: {str(e)}")
        return []

@router.get("/qr")
async def get_qr_code():
    """Get current QR code for WhatsApp authentication"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WHATSAPP_SERVICE_URL}/qr", timeout=10.0)
            return response.json()
    except Exception as e:
        print(f"Error getting QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"WhatsApp service error: {str(e)}")

@router.get("/status")
async def get_whatsapp_status():
    """Get WhatsApp connection status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WHATSAPP_SERVICE_URL}/status", timeout=10.0)
            return response.json()
    except Exception as e:
        print(f"Error getting WhatsApp status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"WhatsApp service error: {str(e)}")

@router.post("/send-message")
async def send_whatsapp_message(message: OutgoingMessage):
    """Send message via WhatsApp service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_SERVICE_URL}/send-message",
                json={
                    "phoneNumber": message.phone_number,
                    "message": message.message
                },
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        print(f"Error sending WhatsApp message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"WhatsApp service error: {str(e)}")

@router.get("/messages/{phone_number}")
async def get_messages(phone_number: str, db = Depends(get_database)):
    """Get conversation history for a phone number"""
    try:
        messages = await get_conversation_history(db, phone_number, limit=50)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(db = Depends(get_database)):
    """Get WhatsApp statistics"""
    try:
        messages_collection = db.whatsapp_messages
        
        # Count total messages
        total_messages = await messages_collection.count_documents({})
        
        # Count messages today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = await messages_collection.count_documents({
            "created_at": {"$gte": today_start}
        })
        
        # Count unique users
        unique_users = len(await messages_collection.distinct("phone_number"))
        
        return {
            "total_messages": total_messages,
            "messages_today": messages_today,
            "unique_users": unique_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))