"""
Shared API dependencies.
"""

from fastapi import Request, HTTPException, Depends
from typing import Optional
import time
import logging
from collections import defaultdict

from app.config import settings

logger = logging.getLogger(__name__)


# ===========================================
# Rate Limiting
# ===========================================

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make a request."""
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_id].append(current_time)
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        current_time = time.time()
        window_start = current_time - 60
        
        recent_requests = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        return max(0, self.requests_per_minute - len(recent_requests))


# Global rate limiter instance
rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MINUTE)


async def check_rate_limit(request: Request):
    """Dependency to check rate limit."""
    # Get client identifier (IP address)
    client_id = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_id):
        remaining = rate_limiter.get_remaining(client_id)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please wait and try again.",
                "remaining_requests": remaining,
                "retry_after_seconds": 60
            }
        )
    
    return client_id


# ===========================================
# Request Logging
# ===========================================

async def log_request(request: Request):
    """Dependency to log requests."""
    logger.info(f"Request: {request.method} {request.url.path}")
    return request


# ===========================================
# Language Detection
# ===========================================

def get_preferred_language(request: Request) -> str:
    """Get preferred language from request headers."""
    accept_language = request.headers.get("Accept-Language", "en")
    
    # Parse first language from header
    if accept_language:
        lang = accept_language.split(",")[0].split("-")[0].lower()
        if lang in settings.SUPPORTED_LANGUAGES:
            return lang
    
    return settings.DEFAULT_LANGUAGE


# ===========================================
# Session Management
# ===========================================

def get_session_id(request: Request) -> Optional[str]:
    """Get session ID from request headers or cookies."""
    # Check header first
    session_id = request.headers.get("X-Session-ID")
    
    # Fall back to cookie
    if not session_id:
        session_id = request.cookies.get("session_id")
    
    return session_id


# ===========================================
# Common Dependencies Bundle
# ===========================================

async def common_dependencies(
    request: Request,
    client_id: str = Depends(check_rate_limit)
):
    """Bundle of common dependencies."""
    return {
        "client_id": client_id,
        "language": get_preferred_language(request),
        "session_id": get_session_id(request)
    }
