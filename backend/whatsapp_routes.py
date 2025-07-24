from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import httpx
import os
from datetime import datetime
import openai
from database import get_database

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# OpenAI client
openai.api_key = os.environ.get('OPENAI_API_KEY')
WHATSAPP_SERVICE_URL = os.environ.get('WHATSAPP_SERVICE_URL', 'http://localhost:3001')

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
    """Generate response using OpenAI"""
    try:
        # Get conversation history for context
        conversation_history = await get_conversation_history(db, phone_number)
        
        # Create messages for OpenAI
        messages = [
            {
                "role": "system",
                "content": """Eres un asistente virtual profesional y amable que responde mensajes de WhatsApp. 

Características:
- Siempre responde en español
- Sé cortés, profesional y útil
- Mantén las respuestas concisas pero informativas
- Adapta tu tono al contexto de la conversación
- Si no sabes algo específico del negocio, pregunta amablemente o sugiere contactar directamente
- Puedes ayudar con consultas generales, información, horarios, etc.

Responde de manera natural como si fueras un asistente real del negocio."""
            }
        ]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            role = "assistant" if msg.get('is_from_ai') else "user"
            messages.append({
                "role": role,
                "content": msg['message']
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Generate response with OpenAI
        client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"AI Response: {ai_response}")
        
        return ai_response
        
    except Exception as e:
        print(f"Error generating AI response: {str(e)}")
        return "¡Hola! Gracias por tu mensaje. En este momento estoy procesando tu consulta. ¿En qué puedo ayudarte?"

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