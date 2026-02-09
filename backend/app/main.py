"""
Language Agnostic Chatbot - FastAPI Application Entry Point

This is the main entry point for the chatbot API.
Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from app.config import settings
from app.models.database import MongoDB
from app.api.routes import health, chat, documents, faqs, admin

# ===========================================
# Logging Configuration
# ===========================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# ===========================================
# Application Lifespan
# ===========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 50)
    logger.info("🚀 Starting Language Agnostic Chatbot API...")
    logger.info("=" * 50)
    
    try:
        # Try to connect to MongoDB (optional)
        try:
            await MongoDB.connect(
                mongodb_url=settings.MONGODB_URL,
                db_name=settings.MONGODB_DB_NAME
            )
            logger.info(f"📊 MongoDB connected: {settings.MONGODB_DB_NAME}")
        except Exception as db_error:
            logger.warning(f"⚠️ MongoDB not available: {db_error}")
            logger.warning("⚠️ Running without database - some features will be limited")
        
        # Log configuration
        logger.info(f"🤖 LLM Model: {settings.OLLAMA_MODEL}")
        logger.info(f"🌐 Supported Languages: {', '.join(settings.SUPPORTED_LANGUAGES)}")
        logger.info(f"📁 Upload Directory: {settings.UPLOAD_DIR}")
        logger.info(f"🔒 Debug Mode: {settings.DEBUG}")
        
        logger.info("✅ All services initialized successfully!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down...")
    try:
        await MongoDB.disconnect()
    except:
        pass
    logger.info("✅ Cleanup complete")


# ===========================================
# FastAPI Application
# ===========================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
## Language Agnostic Chatbot API

A multilingual conversational AI chatbot for campus/college queries.

### Features
- 🌐 **Multilingual Support**: Hindi, English, Tamil, Telugu, Bengali, Marathi
- 📄 **Document Q&A**: Upload PDFs and ask questions (RAG-based)
- 💬 **Context Awareness**: Maintains conversation context
- 📊 **Analytics**: Track usage and improve responses

### API Sections
- **/api/chat**: Send messages and get responses
- **/api/documents**: Upload and manage documents
- **/api/faqs**: Manage FAQs
- **/api/admin**: Analytics and administration
- **/api/health**: Health check
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ===========================================
# CORS Middleware
# ===========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================
# Global Exception Handler
# ===========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )


# ===========================================
# Include Routers
# ===========================================

# Health check routes
app.include_router(
    health.router,
    prefix="/api",
    tags=["Health"]
)

# Chat routes
app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["Chat"]
)

# Document routes
app.include_router(
    documents.router,
    prefix="/api/documents",
    tags=["Documents"]
)

# FAQ routes
app.include_router(
    faqs.router,
    prefix="/api/faqs",
    tags=["FAQs"]
)

# Admin routes
app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Admin"]
)


# ===========================================
# Root Endpoint
# ===========================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "Multilingual chatbot API for campus queries",
        "documentation": "/docs",
        "health_check": "/api/health",
        "supported_languages": settings.SUPPORTED_LANGUAGES
    }


# ===========================================
# Development Entry Point
# ===========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
