"""
Chat API Routes - Endpoints for chat functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from app.models.schemas import (
    ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse
)
from app.core.chatbot import chatbot_service
from app.core.context import context_manager
from app.api.dependencies import check_rate_limit

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    client_id: str = Depends(check_rate_limit)
):
    """
    Send a message to the chatbot and get a response.
    
    This is the main endpoint for chat functionality.
    
    - **message**: The user's message (required)
    - **language**: Language code (en, hi, ta, te, bn, mr)
    - **session_id**: Optional session ID for context continuity
    - **user_id**: Optional user identifier
    
    Returns the bot's response with metadata including:
    - Confidence score
    - Source documents (if RAG was used)
    - Suggested follow-up questions
    - Whether human fallback is recommended
    """
    try:
        response = await chatbot_service.process_message(request)
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to process message", "detail": str(e)}
        )


@router.get("/history/{session_id}")
async def get_conversation_history(
    session_id: str,
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Get conversation history for a session.
    
    - **session_id**: The session ID
    - **limit**: Maximum number of messages to return (default: 20)
    """
    try:
        history = await chatbot_service.get_conversation_history(session_id)
        
        if not history.get("exists"):
            raise HTTPException(
                status_code=404,
                detail={"error": "Session not found"}
            )
        
        # Limit messages
        messages = history.get("messages", [])[-limit:]
        history["messages"] = messages
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to get history"}
        )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear/delete a conversation session.
    
    This removes all messages and context for the session.
    """
    try:
        success = await chatbot_service.clear_conversation(session_id)
        
        if success:
            return {
                "success": True,
                "message": "Session cleared successfully"
            }
        else:
            return {
                "success": False,
                "message": "Session not found or already cleared"
            }
            
    except Exception as e:
        logger.error(f"Clear session error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to clear session"}
        )


@router.get("/languages")
async def get_supported_languages():
    """
    Get all supported languages.
    
    Returns a list of language codes with their names and native names.
    """
    try:
        languages = await chatbot_service.get_supported_languages()
        return {
            "languages": languages,
            "default": "en"
        }
    except Exception as e:
        logger.error(f"Languages error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to get languages"}
        )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit feedback for a conversation or message.
    
    - **session_id**: The session ID
    - **message_id**: Optional specific message ID
    - **rating**: Rating from 1-5
    - **comment**: Optional feedback comment
    """
    try:
        # Get the conversation context
        context = context_manager.get_session(feedback.session_id)
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail={"error": "Session not found"}
            )
        
        # Store feedback in context metadata
        context.metadata["feedback"] = {
            "rating": feedback.rating,
            "comment": feedback.comment,
            "message_id": feedback.message_id
        }
        
        # Save to database
        await context_manager.save_to_database(feedback.session_id)
        
        return FeedbackResponse(
            success=True,
            message="Thank you for your feedback!"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to submit feedback"}
        )


@router.get("/session/{session_id}/context")
async def get_session_context(session_id: str):
    """
    Get context information for a session.
    
    Includes entities, intent history, and metadata.
    Useful for debugging and understanding the conversation state.
    """
    try:
        context = context_manager.get_session(session_id)
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail={"error": "Session not found"}
            )
        
        return {
            "session_id": session_id,
            "language": context.language.value,
            "entities": context.entities,
            "intent_history": context.intent_history,
            "dominant_intent": context.get_dominant_intent(),
            "message_count": len(context.messages),
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to get context"}
        )


@router.get("/stats")
async def get_chat_stats():
    """
    Get chat statistics.
    
    Returns active session count and other stats.
    """
    try:
        return {
            "active_sessions": context_manager.get_session_count(),
            "status": "operational"
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "active_sessions": 0,
            "status": "error",
            "error": str(e)
        }
