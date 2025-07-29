from datetime import datetime
from database import get_database_direct
from models import PausedConversation
import logging

logger = logging.getLogger(__name__)

class ConversationPauseService:
    def __init__(self):
        self.commands = {
            'pausar': self.pause_conversation,
            'reactivar': self.reactivate_conversation,
            'pausar todo': self.pause_all_conversations,
            'activar todo': self.activate_all_conversations,
            'estado': self.get_conversation_status
        }
    
    def is_pause_command(self, message: str) -> bool:
        """Check if message is a pause control command"""
        normalized_message = message.lower().strip()
        return normalized_message in self.commands
    
    async def process_pause_command(self, message: str, client_id: str, phone_number: str, client_phone: str) -> str:
        """Process pause control commands"""
        normalized_message = message.lower().strip()
        
        # Only allow commands from the client (bot owner)
        if phone_number != client_phone:
            return None  # Not from client, ignore command
        
        if normalized_message in self.commands:
            return await self.commands[normalized_message](client_id, phone_number)
        
        return None
    
    async def is_conversation_paused(self, client_id: str, phone_number: str) -> bool:
        """Check if a specific conversation is paused"""
        try:
            db = await get_database_direct()
            paused_conversations = db.paused_conversations
            
            # Check if this specific conversation is paused
            paused = await paused_conversations.find_one({
                "client_id": client_id,
                "phone_number": phone_number
            })
            
            # Check if all conversations are paused for this client
            global_pause = await paused_conversations.find_one({
                "client_id": client_id,
                "phone_number": "ALL",
                "paused_by": "global"
            })
            
            return bool(paused or global_pause)
            
        except Exception as e:
            logger.error(f"Error checking if conversation is paused: {str(e)}")
            return False
    
    async def pause_conversation(self, client_id: str, phone_number: str) -> str:
        """Pause specific conversation"""
        try:
            db = await get_database_direct()
            paused_conversations = db.paused_conversations
            
            # Check if already paused
            existing = await paused_conversations.find_one({
                "client_id": client_id,
                "phone_number": phone_number
            })
            
            if existing:
                return "✅ Esta conversacion ya estaba pausada. Puedes responder directamente."
            
            # Pause this conversation
            pause_data = PausedConversation(
                client_id=client_id,
                phone_number=phone_number,
                paused_by="client"
            )
            
            await paused_conversations.insert_one(pause_data.dict())
            
            logger.info(f"Conversation paused for client {client_id}, phone {phone_number}")
            return "✅ Conversacion pausada. Ahora puedes responder directamente a este usuario."
            
        except Exception as e:
            logger.error(f"Error pausing conversation: {str(e)}")
            return "❌ Error pausando conversacion. Intenta nuevamente."
    
    async def reactivate_conversation(self, client_id: str, phone_number: str) -> str:
        """Reactivate specific conversation"""
        try:
            db = await get_database_direct()
            paused_conversations = db.paused_conversations
            
            # Remove pause for this specific conversation
            result = await paused_conversations.delete_one({
                "client_id": client_id,
                "phone_number": phone_number
            })
            
            if result.deleted_count > 0:
                logger.info(f"Conversation reactivated for client {client_id}, phone {phone_number}")
                return "✅ Conversacion reactivada. El bot volvera a responder automaticamente."
            else:
                return "ℹ️ Esta conversacion no estaba pausada."
                
        except Exception as e:
            logger.error(f"Error reactivating conversation: {str(e)}")
            return "❌ Error reactivando conversacion. Intenta nuevamente."
    
    async def pause_all_conversations(self, client_id: str, phone_number: str) -> str:
        """Pause all conversations for this client"""
        try:
            db = await get_database_direct()
            paused_conversations = db.paused_conversations
            
            # Check if already globally paused
            existing = await paused_conversations.find_one({
                "client_id": client_id,
                "phone_number": "ALL",
                "paused_by": "global"
            })
            
            if existing:
                return "✅ El bot ya estaba completamente pausado."
            
            # Pause all conversations
            pause_data = PausedConversation(
                client_id=client_id,
                phone_number="ALL",
                paused_by="global"
            )
            
            await paused_conversations.insert_one(pause_data.dict())
            
            logger.info(f"All conversations paused for client {client_id}")
            return "✅ Bot completamente pausado. No respondera a ningun usuario automaticamente."
            
        except Exception as e:
            logger.error(f"Error pausing all conversations: {str(e)}")
            return "❌ Error pausando bot completo. Intenta nuevamente."
    
    async def activate_all_conversations(self, client_id: str, phone_number: str) -> str:
        """Activate all conversations for this client"""
        try:
            db = await get_database_direct()
            paused_conversations = db.paused_conversations
            
            # Remove all pauses for this client
            result = await paused_conversations.delete_many({
                "client_id": client_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"All conversations activated for client {client_id}")
                return f"✅ Bot completamente reactivado. Se eliminaron {result.deleted_count} pausas."
            else:
                return "ℹ️ El bot no tenia conversaciones pausadas."
                
        except Exception as e:
            logger.error(f"Error activating all conversations: {str(e)}")
            return "❌ Error reactivando bot completo. Intenta nuevamente."
    
    async def get_conversation_status(self, client_id: str, phone_number: str) -> str:
        """Get status of current conversation and bot"""
        try:
            db = await get_database_direct()
            paused_conversations = db.paused_conversations
            
            # Check specific conversation status
            specific_pause = await paused_conversations.find_one({
                "client_id": client_id,
                "phone_number": phone_number
            })
            
            # Check global pause status
            global_pause = await paused_conversations.find_one({
                "client_id": client_id,
                "phone_number": "ALL",
                "paused_by": "global"
            })
            
            # Count total paused conversations
            total_paused = await paused_conversations.count_documents({
                "client_id": client_id,
                "phone_number": {"$ne": "ALL"}
            })
            
            status_msg = "📊 Estado del Bot:\n"
            
            if global_pause:
                status_msg += "🔴 Bot: COMPLETAMENTE PAUSADO\n"
            elif specific_pause:
                status_msg += "🟡 Esta conversacion: PAUSADA\n"
                status_msg += "🟢 Bot: ACTIVO para otras conversaciones\n"
            else:
                status_msg += "🟢 Esta conversacion: ACTIVA\n"
                status_msg += "🟢 Bot: FUNCIONANDO NORMAL\n"
            
            if total_paused > 0:
                status_msg += f"📱 Conversaciones pausadas: {total_paused}\n"
            
            status_msg += "\nComandos: pausar, reactivar, pausar todo, activar todo"
            
            return status_msg
            
        except Exception as e:
            logger.error(f"Error getting conversation status: {str(e)}")
            return "❌ Error obteniendo estado. Intenta nuevamente."

# Global pause service instance
pause_service = ConversationPauseService()