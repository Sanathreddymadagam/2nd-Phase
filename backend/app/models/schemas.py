"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# ===========================================
# Enums
# ===========================================

class LanguageEnum(str, Enum):
    """Supported languages enum."""
    ENGLISH = "en"
    HINDI = "hi"
    TAMIL = "ta"
    TELUGU = "te"
    BENGALI = "bn"
    MARATHI = "mr"


class MessageRole(str, Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ===========================================
# Chat Models
# ===========================================

class ChatRequest(BaseModel):
    """Request model for sending a chat message."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    language: LanguageEnum = Field(default=LanguageEnum.ENGLISH, description="Language code")
    session_id: Optional[str] = Field(default=None, description="Session ID for context")
    user_id: Optional[str] = Field(default=None, description="Optional user identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the admission fee?",
                "language": "en",
                "session_id": None,
                "user_id": None
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat message."""
    response: str = Field(..., description="Bot response message")
    language: LanguageEnum = Field(..., description="Response language")
    session_id: str = Field(..., description="Session ID")
    confidence_score: float = Field(..., ge=0, le=1, description="Response confidence")
    sources: Optional[List[str]] = Field(default=None, description="Source documents")
    suggested_questions: Optional[List[str]] = Field(default=None, description="Follow-up suggestions")
    fallback_required: bool = Field(default=False, description="Whether human fallback is needed")
    intent: Optional[str] = Field(default=None, description="Detected intent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "The admission fee is ₹50,000 per semester.",
                "language": "en",
                "session_id": "abc-123",
                "confidence_score": 0.85,
                "sources": ["admission_policy.pdf"],
                "suggested_questions": ["When is the deadline?"],
                "fallback_required": False,
                "intent": "fee_query"
            }
        }


# ===========================================
# Message & Conversation Models
# ===========================================

class MessageHistory(BaseModel):
    """Single message in conversation history."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    language: LanguageEnum
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: Optional[float] = None
    sources: Optional[List[str]] = None


class Conversation(BaseModel):
    """Complete conversation model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: Optional[str] = None
    messages: List[MessageHistory] = Field(default_factory=list)
    language: LanguageEnum
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    feedback_rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback_comment: Optional[str] = None


# ===========================================
# FAQ Models
# ===========================================

class FAQBase(BaseModel):
    """Base FAQ model."""
    question: str = Field(..., min_length=5, max_length=500)
    answer: str = Field(..., min_length=10, max_length=2000)
    category: str = Field(..., min_length=2, max_length=50)
    language: LanguageEnum
    keywords: List[str] = Field(default_factory=list)
    priority: int = Field(default=0, ge=0, le=10)


class FAQCreate(FAQBase):
    """Model for creating a new FAQ."""
    pass


class FAQResponse(FAQBase):
    """FAQ response model with ID."""
    id: str
    views: int = 0
    helpful_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FAQListResponse(BaseModel):
    """Response model for listing FAQs."""
    faqs: List[FAQResponse]
    total: int
    page: int = 1
    per_page: int = 10


# ===========================================
# Document Models
# ===========================================

class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    success: bool
    document_id: str
    filename: str
    original_name: str
    chunks_processed: int
    message: str


class DocumentInfo(BaseModel):
    """Document information model."""
    id: str
    filename: str
    original_name: str
    content_type: str
    size: int
    uploaded_at: datetime
    processed: bool
    chunk_count: int
    category: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentInfo]
    total: int


# ===========================================
# Admin & Analytics Models
# ===========================================

class AnalyticsQuery(BaseModel):
    """Query parameters for analytics."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    language: Optional[LanguageEnum] = None


class AnalyticsResponse(BaseModel):
    """Analytics data response."""
    total_queries: int
    total_sessions: int
    avg_confidence: float
    languages: Dict[str, int]
    intents: Dict[str, int]
    fallback_count: int
    avg_response_time_ms: float
    top_questions: List[Dict[str, Any]]
    date_range: Dict[str, datetime]


class ConversationLogEntry(BaseModel):
    """Single conversation log entry."""
    timestamp: datetime
    session_id: str
    user_query: str
    bot_response: str
    language: str
    confidence: float
    intent: Optional[str]
    sources: Optional[List[str]]


class LogsResponse(BaseModel):
    """Response for logs endpoint."""
    logs: List[ConversationLogEntry]
    total: int
    page: int
    per_page: int


# ===========================================
# Health & Status Models
# ===========================================

class HealthStatus(BaseModel):
    """Health check status model."""
    status: str
    timestamp: datetime
    services: Dict[str, bool]
    version: str


class ServiceStatus(BaseModel):
    """Individual service status."""
    name: str
    healthy: bool
    latency_ms: Optional[float] = None
    message: Optional[str] = None


# ===========================================
# Feedback Models
# ===========================================

class FeedbackRequest(BaseModel):
    """User feedback request."""
    session_id: str
    message_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=500)


class FeedbackResponse(BaseModel):
    """Feedback submission response."""
    success: bool
    message: str


# ===========================================
# Error Models
# ===========================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
