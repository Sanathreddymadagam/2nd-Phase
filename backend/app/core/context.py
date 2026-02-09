"""
Context Management - Handles conversation context and memory.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from collections import OrderedDict
import asyncio

from app.models.schemas import MessageHistory, MessageRole, LanguageEnum

logger = logging.getLogger(__name__)


class ConversationContext:
    """
    Represents a single conversation's context.
    """
    
    def __init__(
        self,
        session_id: str,
        language: LanguageEnum = LanguageEnum.ENGLISH,
        max_messages: int = 10
    ):
        self.session_id = session_id
        self.language = language
        self.messages: List[Dict] = []
        self.max_messages = max_messages
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.entities: Dict[str, Any] = {}  # Extracted entities across conversation
        self.intent_history: List[str] = []
    
    def add_message(
        self,
        role: str,
        content: str,
        language: str = None,
        metadata: Dict = None
    ):
        """Add a message to the conversation."""
        message = {
            "role": role,
            "content": content,
            "language": language or self.language.value,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Keep only last N messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def add_user_message(self, content: str, language: str = None):
        """Add a user message."""
        self.add_message("user", content, language)
    
    def add_assistant_message(
        self,
        content: str,
        language: str = None,
        sources: List[str] = None,
        confidence: float = None
    ):
        """Add an assistant message."""
        metadata = {}
        if sources:
            metadata["sources"] = sources
        if confidence is not None:
            metadata["confidence"] = confidence
        
        self.add_message("assistant", content, language, metadata)
    
    def get_history(self, limit: int = 5) -> List[Dict]:
        """Get recent conversation history."""
        return self.messages[-limit:]
    
    def get_history_as_text(self, limit: int = 3) -> str:
        """Get conversation history as formatted text."""
        history = self.get_history(limit)
        
        if not history:
            return ""
        
        lines = []
        for msg in history:
            role = msg["role"].capitalize()
            content = msg["content"]
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def update_entities(self, new_entities: Dict[str, Any]):
        """Update extracted entities."""
        self.entities.update(new_entities)
        self.updated_at = datetime.utcnow()
    
    def add_intent(self, intent: str):
        """Track intent history."""
        self.intent_history.append(intent)
        # Keep last 5 intents
        if len(self.intent_history) > 5:
            self.intent_history = self.intent_history[-5:]
    
    def get_dominant_intent(self) -> Optional[str]:
        """Get the most common recent intent."""
        if not self.intent_history:
            return None
        
        # Count intents (excluding greetings/goodbyes)
        intent_counts = {}
        for intent in self.intent_history:
            if intent not in ["greeting", "goodbye", "general"]:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        if not intent_counts:
            return None
        
        return max(intent_counts, key=intent_counts.get)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "language": self.language.value,
            "messages": self.messages,
            "metadata": self.metadata,
            "entities": self.entities,
            "intent_history": self.intent_history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationContext":
        """Create from dictionary."""
        context = cls(
            session_id=data["session_id"],
            language=LanguageEnum(data.get("language", "en"))
        )
        context.messages = data.get("messages", [])
        context.metadata = data.get("metadata", {})
        context.entities = data.get("entities", {})
        context.intent_history = data.get("intent_history", [])
        context.created_at = datetime.fromisoformat(data["created_at"])
        context.updated_at = datetime.fromisoformat(data["updated_at"])
        return context


class ContextManager:
    """
    Manages conversation contexts for multiple sessions.
    
    Uses in-memory storage with optional persistence to MongoDB.
    """
    
    def __init__(
        self,
        max_sessions: int = 1000,
        session_timeout_minutes: int = 30
    ):
        self.sessions: OrderedDict[str, ConversationContext] = OrderedDict()
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._cleanup_task = None
    
    def get_or_create_session(
        self,
        session_id: str,
        language: LanguageEnum = LanguageEnum.ENGLISH
    ) -> ConversationContext:
        """
        Get existing session or create a new one.
        
        Args:
            session_id: Unique session identifier
            language: Default language for the session
            
        Returns:
            ConversationContext instance
        """
        if session_id in self.sessions:
            # Move to end (LRU behavior)
            self.sessions.move_to_end(session_id)
            return self.sessions[session_id]
        
        # Create new session
        context = ConversationContext(session_id, language)
        self.sessions[session_id] = context
        
        # Cleanup old sessions if limit reached
        self._cleanup_old_sessions()
        
        logger.debug(f"Created new session: {session_id}")
        return context
    
    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """Get session by ID, or None if not found."""
        return self.sessions.get(session_id)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        language: str = "en"
    ):
        """Add a message to a session."""
        context = self.get_or_create_session(
            session_id,
            LanguageEnum(language)
        )
        context.add_message(role, content, language)
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Get conversation history for a session."""
        context = self.get_session(session_id)
        if context:
            return context.get_history(limit)
        return []
    
    def get_context_prompt(
        self,
        session_id: str,
        current_query: str
    ) -> str:
        """
        Build a context-aware prompt including conversation history.
        
        Args:
            session_id: Session ID
            current_query: Current user query
            
        Returns:
            Formatted prompt with context
        """
        context = self.get_session(session_id)
        
        if not context or not context.messages:
            return current_query
        
        history_text = context.get_history_as_text(limit=3)
        
        if not history_text:
            return current_query
        
        return f"""Previous conversation:
{history_text}

Current question: {current_query}

Please consider the conversation context when answering."""
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.debug(f"Cleared session: {session_id}")
            return True
        return False
    
    def update_session_language(
        self,
        session_id: str,
        language: LanguageEnum
    ):
        """Update the language for a session."""
        context = self.get_session(session_id)
        if context:
            context.language = language
    
    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self.sessions)
    
    def _cleanup_old_sessions(self):
        """Remove expired or excess sessions."""
        now = datetime.utcnow()
        
        # Remove expired sessions
        expired = [
            sid for sid, ctx in self.sessions.items()
            if now - ctx.updated_at > self.session_timeout
        ]
        
        for sid in expired:
            del self.sessions[sid]
            logger.debug(f"Expired session removed: {sid}")
        
        # Remove oldest sessions if over limit
        while len(self.sessions) > self.max_sessions:
            oldest_sid = next(iter(self.sessions))
            del self.sessions[oldest_sid]
            logger.debug(f"Oldest session removed: {oldest_sid}")
    
    async def save_to_database(self, session_id: str):
        """
        Save session to database for persistence.
        
        Should be called when session ends or periodically.
        """
        from app.models.database import MongoDB, Collections
        
        context = self.get_session(session_id)
        if not context:
            return
        
        try:
            db = MongoDB.get_db()
            await db[Collections.CONVERSATIONS].update_one(
                {"session_id": session_id},
                {"$set": context.to_dict()},
                upsert=True
            )
            logger.debug(f"Saved session to database: {session_id}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    async def load_from_database(self, session_id: str) -> Optional[ConversationContext]:
        """
        Load session from database.
        
        Called when session is not in memory but might exist in DB.
        """
        from app.models.database import MongoDB, Collections
        
        try:
            db = MongoDB.get_db()
            data = await db[Collections.CONVERSATIONS].find_one(
                {"session_id": session_id}
            )
            
            if data:
                context = ConversationContext.from_dict(data)
                self.sessions[session_id] = context
                logger.debug(f"Loaded session from database: {session_id}")
                return context
                
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
        
        return None


# ===========================================
# Singleton Instance
# ===========================================

context_manager = ContextManager()
