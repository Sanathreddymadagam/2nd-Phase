"""
Admin API Routes - Analytics and administration endpoints.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.models.database import MongoDB, Collections
from app.models.schemas import AnalyticsResponse, LogsResponse
from app.core.context import context_manager
from app.core.rag import rag_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/analytics")
async def get_analytics(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    language: Optional[str] = Query(default=None)
):
    """
    Get analytics data for conversations.
    
    - **start_date**: Start of date range
    - **end_date**: End of date range
    - **language**: Filter by language
    """
    try:
        db = MongoDB.get_db()
        
        # Default to last 7 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Build query
        query = {
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        if language:
            query["language"] = language
        
        # Total conversations
        total_conversations = await db[Collections.CONVERSATIONS].count_documents(query)
        
        # Language breakdown
        language_pipeline = [
            {"$match": query},
            {"$group": {"_id": "$language", "count": {"$sum": 1}}}
        ]
        language_results = await db[Collections.CONVERSATIONS].aggregate(language_pipeline).to_list(100)
        languages = {r["_id"]: r["count"] for r in language_results if r["_id"]}
        
        # Intent breakdown from logs
        intent_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {"_id": "$intent", "count": {"$sum": 1}}}
        ]
        try:
            intent_results = await db[Collections.LOGS].aggregate(intent_pipeline).to_list(100)
            intents = {r["_id"]: r["count"] for r in intent_results if r["_id"]}
        except:
            intents = {}
        
        # Average confidence
        confidence_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {"_id": None, "avg_confidence": {"$avg": "$confidence"}}}
        ]
        try:
            confidence_result = await db[Collections.LOGS].aggregate(confidence_pipeline).to_list(1)
            avg_confidence = confidence_result[0]["avg_confidence"] if confidence_result else 0.0
        except:
            avg_confidence = 0.0
        
        # Fallback count
        try:
            fallback_count = await db[Collections.LOGS].count_documents({
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "fallback_required": True
            })
        except:
            fallback_count = 0
        
        # Top questions
        top_questions_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {"_id": "$user_query", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        try:
            top_questions_results = await db[Collections.LOGS].aggregate(top_questions_pipeline).to_list(10)
            top_questions = [{"query": r["_id"], "count": r["count"]} for r in top_questions_results]
        except:
            top_questions = []
        
        return {
            "total_queries": total_conversations,
            "total_sessions": total_conversations,  # Simplified
            "avg_confidence": round(avg_confidence, 2) if avg_confidence else 0.0,
            "languages": languages,
            "intents": intents,
            "fallback_count": fallback_count,
            "avg_response_time_ms": 0,  # TODO: Implement
            "top_questions": top_questions,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {
            "total_queries": 0,
            "total_sessions": 0,
            "avg_confidence": 0.0,
            "languages": {},
            "intents": {},
            "fallback_count": 0,
            "avg_response_time_ms": 0,
            "top_questions": [],
            "date_range": {},
            "error": str(e)
        }


@router.get("/logs")
async def get_conversation_logs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    session_id: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None)
):
    """
    Get conversation logs.
    
    - **page**: Page number
    - **per_page**: Items per page
    - **session_id**: Filter by session ID
    - **language**: Filter by language
    - **start_date**: Start of date range
    - **end_date**: End of date range
    """
    try:
        db = MongoDB.get_db()
        
        # Build query
        query = {}
        if session_id:
            query["session_id"] = session_id
        if language:
            query["language"] = language
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        # Get total count
        total = await db[Collections.LOGS].count_documents(query)
        
        # Get logs
        skip = (page - 1) * per_page
        cursor = db[Collections.LOGS].find(query).skip(skip).limit(per_page).sort("timestamp", -1)
        logs = await cursor.to_list(length=per_page)
        
        # Format logs
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "timestamp": log.get("timestamp"),
                "session_id": log.get("session_id"),
                "user_query": log.get("user_query"),
                "bot_response": log.get("bot_response"),
                "language": log.get("language"),
                "confidence": log.get("confidence"),
                "intent": log.get("intent"),
                "sources": log.get("sources")
            })
        
        return {
            "logs": formatted_logs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
        
    except Exception as e:
        logger.error(f"Logs error: {e}")
        return {
            "logs": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "error": str(e)
        }


@router.get("/sessions")
async def get_active_sessions():
    """
    Get information about active sessions.
    """
    try:
        session_count = context_manager.get_session_count()
        
        # Get session details
        sessions = []
        for session_id, context in list(context_manager.sessions.items())[:50]:  # Limit to 50
            sessions.append({
                "session_id": session_id,
                "language": context.language.value,
                "message_count": len(context.messages),
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat(),
                "dominant_intent": context.get_dominant_intent()
            })
        
        return {
            "total_active": session_count,
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Sessions error: {e}")
        return {
            "total_active": 0,
            "sessions": [],
            "error": str(e)
        }


@router.get("/dashboard")
async def get_dashboard():
    """
    Get dashboard summary data.
    """
    try:
        db = MongoDB.get_db()
        
        # Today's stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Total conversations today
        today_conversations = await db[Collections.CONVERSATIONS].count_documents({
            "created_at": {"$gte": today_start}
        })
        
        # Total documents
        total_documents = await db[Collections.DOCUMENTS].count_documents({})
        
        # Total FAQs
        total_faqs = await db[Collections.FAQS].count_documents({})
        
        # Active sessions
        active_sessions = context_manager.get_session_count()
        
        # Document chunks
        doc_chunks = await rag_service.get_document_count()
        
        return {
            "today": {
                "conversations": today_conversations
            },
            "totals": {
                "documents": total_documents,
                "faqs": total_faqs,
                "document_chunks": doc_chunks
            },
            "active": {
                "sessions": active_sessions
            },
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return {
            "today": {"conversations": 0},
            "totals": {"documents": 0, "faqs": 0, "document_chunks": 0},
            "active": {"sessions": 0},
            "status": "error",
            "error": str(e)
        }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a specific session.
    """
    try:
        success = context_manager.clear_session(session_id)
        
        if success:
            return {"success": True, "message": "Session deleted"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-old-sessions")
async def clear_old_sessions(
    hours: int = Query(default=24, ge=1, description="Clear sessions older than this many hours")
):
    """
    Clear sessions older than specified hours.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cleared_count = 0
        
        sessions_to_clear = []
        for session_id, context in context_manager.sessions.items():
            if context.updated_at < cutoff:
                sessions_to_clear.append(session_id)
        
        for session_id in sessions_to_clear:
            context_manager.clear_session(session_id)
            cleared_count += 1
        
        return {
            "success": True,
            "cleared_sessions": cleared_count,
            "remaining_sessions": context_manager.get_session_count()
        }
        
    except Exception as e:
        logger.error(f"Clear sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
