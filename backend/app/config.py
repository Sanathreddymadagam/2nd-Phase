"""
Configuration settings for the Language Agnostic Chatbot.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ===========================================
    # API Settings
    # ===========================================
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Language Agnostic Chatbot"
    DEBUG: bool = True
    
    # ===========================================
    # MongoDB Configuration
    # ===========================================
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "chatbot_db"
    
    # ===========================================
    # Ollama LLM Configuration
    # ===========================================
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    
    # ===========================================
    # Vector Database (ChromaDB)
    # ===========================================
    CHROMA_PERSIST_DIR: str = "./data/vectorstore"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # ===========================================
    # Supported Languages
    # ===========================================
    SUPPORTED_LANGUAGES: List[str] = ["en", "hi", "ta", "te", "bn", "mr"]
    DEFAULT_LANGUAGE: str = "en"
    
    # ===========================================
    # File Upload Settings
    # ===========================================
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "docx"]
    UPLOAD_DIR: str = "./data/documents"
    
    # ===========================================
    # Rate Limiting
    # ===========================================
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # ===========================================
    # Logging
    # ===========================================
    LOG_LEVEL: str = "INFO"
    
    # ===========================================
    # CORS Settings
    # ===========================================
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ===========================================
# Language Configuration
# ===========================================
LANGUAGES = {
    "en": {
        "name": "English",
        "native_name": "English",
        "flag": "🇬🇧"
    },
    "hi": {
        "name": "Hindi",
        "native_name": "हिंदी",
        "flag": "🇮🇳"
    },
    "ta": {
        "name": "Tamil",
        "native_name": "தமிழ்",
        "flag": "🇮🇳"
    },
    "te": {
        "name": "Telugu",
        "native_name": "తెలుగు",
        "flag": "🇮🇳"
    },
    "bn": {
        "name": "Bengali",
        "native_name": "বাংলা",
        "flag": "🇮🇳"
    },
    "mr": {
        "name": "Marathi",
        "native_name": "मराठी",
        "flag": "🇮🇳"
    }
}

# ===========================================
# Intent Categories
# ===========================================
INTENT_CATEGORIES = {
    "greeting": {
        "keywords": ["hello", "hi", "hey", "namaste", "good morning", "good evening"],
        "priority": 1
    },
    "fee_query": {
        "keywords": ["fee", "fees", "payment", "amount", "cost", "tuition", "charges"],
        "priority": 2
    },
    "admission": {
        "keywords": ["admission", "apply", "application", "eligibility", "seat", "enroll"],
        "priority": 2
    },
    "scholarship": {
        "keywords": ["scholarship", "financial aid", "grant", "stipend", "merit"],
        "priority": 2
    },
    "timetable": {
        "keywords": ["timetable", "schedule", "class timing", "lecture", "period"],
        "priority": 2
    },
    "exam": {
        "keywords": ["exam", "examination", "test", "marks", "result", "grade"],
        "priority": 2
    },
    "document": {
        "keywords": ["document", "certificate", "transcript", "bonafide", "letter"],
        "priority": 2
    },
    "contact": {
        "keywords": ["contact", "phone", "email", "address", "office", "location"],
        "priority": 2
    },
    "goodbye": {
        "keywords": ["bye", "goodbye", "see you", "thank you", "thanks"],
        "priority": 1
    }
}


# Create settings instance
settings = Settings()
