import asyncio
from datetime import datetime, timedelta
from database import get_database_direct
import logging

logger = logging.getLogger(__name__)

class DataCleanupService:
    def __init__(self):
        self.cleanup_interval = 24 * 60 * 60  # 24 hours in seconds
        self.running = False
    
    async def start_cleanup_scheduler(self):
        """Start the automated cleanup scheduler"""
        self.running = True
        logger.info("🧹 Data cleanup scheduler started - running every 24 hours")
        
        while self.running:
            try:
                # Wait 24 hours
                await asyncio.sleep(self.cleanup_interval)
                
                if self.running:  # Check if still running after sleep
                    await self.run_cleanup()
                    
            except asyncio.CancelledError:
                logger.info("Cleanup scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup scheduler: {str(e)}")
                # Continue running even if one cleanup fails
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
    
    async def run_cleanup(self):
        """Run the cleanup process"""
        try:
            logger.info("🧹 Starting automated data cleanup...")
            
            # Get database connection
            db = await get_database_direct()
            
            # Calculate cutoff time (24 hours ago)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            logger.info(f"Cleaning messages older than: {cutoff_time}")
            
            # Clean client messages
            client_messages_deleted = await self._cleanup_client_messages(db, cutoff_time)
            
            # Clean client threads (optional - for performance)
            threads_deleted = await self._cleanup_old_threads(db, cutoff_time)
            
            # Clean old WhatsApp messages (legacy)
            whatsapp_messages_deleted = await self._cleanup_whatsapp_messages(db, cutoff_time)
            
            logger.info(f"✅ Cleanup completed successfully:")
            logger.info(f"   - Client messages deleted: {client_messages_deleted}")
            logger.info(f"   - Threads cleaned: {threads_deleted}")
            logger.info(f"   - Legacy messages deleted: {whatsapp_messages_deleted}")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")
    
    async def _cleanup_client_messages(self, db, cutoff_time: datetime) -> int:
        """Clean old client messages"""
        try:
            client_messages_collection = db.client_messages
            
            # Delete messages older than 24 hours
            result = await client_messages_collection.delete_many({
                "created_at": {"$lt": cutoff_time}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"Deleted {deleted_count} old client messages")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning client messages: {str(e)}")
            return 0
    
    async def _cleanup_old_threads(self, db, cutoff_time: datetime) -> int:
        """Clean old conversation threads"""
        try:
            # Clean client threads
            client_threads_collection = db.client_threads
            
            result = await client_threads_collection.delete_many({
                "last_used": {"$lt": cutoff_time}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"Deleted {deleted_count} old client threads")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning threads: {str(e)}")
            return 0
    
    async def _cleanup_whatsapp_messages(self, db, cutoff_time: datetime) -> int:
        """Clean legacy WhatsApp messages"""
        try:
            whatsapp_messages_collection = db.whatsapp_messages
            
            result = await whatsapp_messages_collection.delete_many({
                "created_at": {"$lt": cutoff_time}
            })
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} legacy WhatsApp messages")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning legacy messages: {str(e)}")
            return 0
    
    async def force_cleanup(self):
        """Force immediate cleanup (for testing/manual trigger)"""
        logger.info("🧹 Force cleanup triggered")
        await self.run_cleanup()
    
    def stop_cleanup_scheduler(self):
        """Stop the cleanup scheduler"""
        self.running = False
        logger.info("Cleanup scheduler stopped")

# Global cleanup service instance
cleanup_service = DataCleanupService()

async def start_cleanup_service():
    """Start the cleanup service in background"""
    asyncio.create_task(cleanup_service.start_cleanup_scheduler())