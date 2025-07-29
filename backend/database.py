from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

client = AsyncIOMotorClient(mongo_url)
database = client[db_name]

async def get_database():
    """Dependency to get database instance"""
    return database

async def get_database_direct():
    """Direct database access for services"""
    return database

async def close_database():
    """Close database connection"""
    client.close()