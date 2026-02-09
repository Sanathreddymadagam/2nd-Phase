"""
Health check endpoint.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict
import httpx
import logging

from app.config import settings
from app.models.schemas import HealthStatus, ServiceStatus
from app.models.database import MongoDB

router = APIRouter()
logger = logging.getLogger(__name__)


async def check_ollama_health() -> ServiceStatus:
    """Check if Ollama service is healthy."""
    try:
        async with httpx.AsyncClient() as client:
            start_time = datetime.utcnow()
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0
            )
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return ServiceStatus(
                    name="ollama",
                    healthy=True,
                    latency_ms=latency,
                    message="Ollama is running"
                )
            else:
                return ServiceStatus(
                    name="ollama",
                    healthy=False,
                    message=f"Ollama returned status {response.status_code}"
                )
    except Exception as e:
        return ServiceStatus(
            name="ollama",
            healthy=False,
            message=f"Cannot connect to Ollama: {str(e)}"
        )


async def check_mongodb_health() -> ServiceStatus:
    """Check if MongoDB is healthy."""
    try:
        start_time = datetime.utcnow()
        if MongoDB.client:
            await MongoDB.client.admin.command('ping')
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ServiceStatus(
                name="mongodb",
                healthy=True,
                latency_ms=latency,
                message="MongoDB is connected"
            )
        else:
            return ServiceStatus(
                name="mongodb",
                healthy=False,
                message="MongoDB client not initialized"
            )
    except Exception as e:
        return ServiceStatus(
            name="mongodb",
            healthy=False,
            message=f"MongoDB error: {str(e)}"
        )


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Health check endpoint.
    
    Returns the status of all services.
    """
    # Check individual services
    ollama_status = await check_ollama_health()
    mongodb_status = await check_mongodb_health()
    
    # Determine overall status
    all_healthy = ollama_status.healthy and mongodb_status.healthy
    status = "healthy" if all_healthy else "degraded"
    
    return HealthStatus(
        status=status,
        timestamp=datetime.utcnow(),
        services={
            "ollama": ollama_status.healthy,
            "mongodb": mongodb_status.healthy
        },
        version="1.0.0"
    )


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with service information.
    """
    ollama_status = await check_ollama_health()
    mongodb_status = await check_mongodb_health()
    
    return {
        "status": "healthy" if (ollama_status.healthy and mongodb_status.healthy) else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "ollama": {
                "healthy": ollama_status.healthy,
                "latency_ms": ollama_status.latency_ms,
                "message": ollama_status.message,
                "url": settings.OLLAMA_BASE_URL,
                "model": settings.OLLAMA_MODEL
            },
            "mongodb": {
                "healthy": mongodb_status.healthy,
                "latency_ms": mongodb_status.latency_ms,
                "message": mongodb_status.message,
                "database": settings.MONGODB_DB_NAME
            }
        },
        "config": {
            "supported_languages": settings.SUPPORTED_LANGUAGES,
            "default_language": settings.DEFAULT_LANGUAGE,
            "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
            "debug_mode": settings.DEBUG
        }
    }


@router.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "Multilingual chatbot API for campus queries",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }
