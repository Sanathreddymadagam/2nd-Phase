"""
MongoDB database models and connection management.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    connected: bool = False
    
    @classmethod
    async def connect(cls, mongodb_url: str, db_name: str):
        """Connect to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(
                mongodb_url,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000
            )
            cls.db = cls.client[db_name]
            
            # Test connection
            await cls.client.admin.command('ping')
            cls.connected = True
            logger.info(f"✅ Connected to MongoDB: {db_name}")
            
            # Create indexes
            await cls.create_indexes()
            
        except Exception as e:
            cls.connected = False
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB."""
        if cls.client:
            cls.client.close()
            logger.info("👋 Disconnected from MongoDB")
    
    @classmethod
    async def create_indexes(cls):
        """Create necessary indexes for collections."""
        if not cls.db:
            return
        
        try:
            # Conversations collection indexes
            await cls.db.conversations.create_indexes([
                IndexModel([("session_id", ASCENDING)], unique=True),
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("language", ASCENDING)]),
            ])
            
            # FAQs collection indexes
            await cls.db.faqs.create_indexes([
                IndexModel([("category", ASCENDING)]),
                IndexModel([("language", ASCENDING)]),
                IndexModel([("keywords", ASCENDING)]),
                IndexModel([("question", TEXT), ("answer", TEXT)]),
            ])
            
            # Documents collection indexes
            await cls.db.documents.create_indexes([
                IndexModel([("filename", ASCENDING)], unique=True),
                IndexModel([("uploaded_at", DESCENDING)]),
                IndexModel([("category", ASCENDING)]),
            ])
            
            # Analytics collection indexes
            await cls.db.analytics.create_indexes([
                IndexModel([("date", DESCENDING)]),
            ])
            
            logger.info("✅ Database indexes created")
            
        except Exception as e:
            logger.warning(f"⚠️ Error creating indexes: {e}")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if not cls.db:
            raise Exception("Database not connected")
        return cls.db


# ===========================================
# Collection Names
# ===========================================

class Collections:
    """Collection name constants."""
    CONVERSATIONS = "conversations"
    FAQS = "faqs"
    DOCUMENTS = "documents"
    USERS = "users"
    ANALYTICS = "analytics"
    LOGS = "conversation_logs"


# ===========================================
# Database Operations Helper
# ===========================================

class DatabaseOperations:
    """Helper class for common database operations."""
    
    @staticmethod
    async def insert_one(collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document."""
        db = MongoDB.get_db()
        result = await db[collection].insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    async def find_one(collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        db = MongoDB.get_db()
        return await db[collection].find_one(query)
    
    @staticmethod
    async def find_many(
        collection: str, 
        query: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        db = MongoDB.get_db()
        cursor = db[collection].find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return await cursor.to_list(length=limit)
    
    @staticmethod
    async def update_one(
        collection: str, 
        query: Dict[str, Any], 
        update: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """Update a single document."""
        db = MongoDB.get_db()
        result = await db[collection].update_one(query, {"$set": update}, upsert=upsert)
        return result.modified_count > 0 or result.upserted_id is not None
    
    @staticmethod
    async def delete_one(collection: str, query: Dict[str, Any]) -> bool:
        """Delete a single document."""
        db = MongoDB.get_db()
        result = await db[collection].delete_one(query)
        return result.deleted_count > 0
    
    @staticmethod
    async def count(collection: str, query: Dict[str, Any] = None) -> int:
        """Count documents matching query."""
        db = MongoDB.get_db()
        if query is None:
            query = {}
        return await db[collection].count_documents(query)
    
    @staticmethod
    async def aggregate(collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline."""
        db = MongoDB.get_db()
        cursor = db[collection].aggregate(pipeline)
        return await cursor.to_list(length=None)
