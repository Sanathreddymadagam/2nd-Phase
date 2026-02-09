"""
FAQ API Routes - Endpoints for FAQ management.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from app.models.schemas import FAQCreate, FAQResponse, FAQListResponse, LanguageEnum
from app.services.faq_service import faq_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=FAQListResponse)
async def list_faqs(
    language: Optional[str] = Query(default=None, description="Language code (en, hi, ta, te, bn, mr)"),
    category: Optional[str] = Query(default=None, description="Category filter"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100)
):
    """
    List all FAQs with optional filtering.
    
    - **language**: Filter by language code
    - **category**: Filter by category (fees, admission, scholarship, etc.)
    - **page**: Page number
    - **per_page**: Items per page
    """
    try:
        result = await faq_service.get_all_faqs(
            language=language,
            category=category,
            page=page,
            per_page=per_page
        )
        
        faqs = []
        for faq in result.get("faqs", []):
            faqs.append(FAQResponse(
                id=str(faq.get("_id", "")),
                question=faq["question"],
                answer=faq["answer"],
                category=faq.get("category", "general"),
                language=LanguageEnum(faq.get("language", "en")),
                keywords=faq.get("keywords", []),
                priority=faq.get("priority", 0),
                views=faq.get("views", 0),
                helpful_count=faq.get("helpful_count", 0),
                created_at=faq.get("created_at"),
                updated_at=faq.get("updated_at")
            ))
        
        return FAQListResponse(
            faqs=faqs,
            total=result.get("total", 0),
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"List FAQs error: {e}")
        return FAQListResponse(faqs=[], total=0, page=1, per_page=per_page)


@router.get("/search")
async def search_faqs(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    category: Optional[str] = Query(default=None),
    language: str = Query(default="en"),
    limit: int = Query(default=5, ge=1, le=20)
):
    """
    Search FAQs by query.
    
    Uses keyword matching to find relevant FAQs.
    
    - **q**: Search query
    - **category**: Optional category filter
    - **language**: Language code
    - **limit**: Maximum results
    """
    try:
        result = await faq_service.search_faqs(
            query=q,
            category=category,
            language=language,
            limit=limit
        )
        
        return {
            "query": q,
            "matches": result.get("matches", []),
            "total": result.get("total", 0)
        }
        
    except Exception as e:
        logger.error(f"Search FAQs error: {e}")
        return {
            "query": q,
            "matches": [],
            "total": 0,
            "error": str(e)
        }


@router.get("/categories")
async def get_categories(
    language: str = Query(default="en")
):
    """
    Get all FAQ categories.
    """
    try:
        categories = await faq_service.get_categories(language)
        return {
            "categories": categories,
            "language": language
        }
    except Exception as e:
        logger.error(f"Get categories error: {e}")
        return {"categories": [], "error": str(e)}


@router.post("/", status_code=201)
async def create_faq(faq: FAQCreate):
    """
    Create a new FAQ.
    
    - **question**: The FAQ question
    - **answer**: The answer
    - **category**: Category (fees, admission, etc.)
    - **language**: Language code
    - **keywords**: Optional list of keywords for matching
    - **priority**: Priority level (0-10)
    """
    try:
        result = await faq_service.create_faq(faq)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to create FAQ")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create FAQ error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create FAQ: {str(e)}"
        )


@router.get("/{faq_id}")
async def get_faq(faq_id: str):
    """
    Get a specific FAQ by ID.
    """
    try:
        faq = await faq_service.get_faq_by_id(faq_id)
        
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        # Increment view count
        await faq_service.increment_view(faq_id)
        
        return FAQResponse(
            id=str(faq.get("_id", "")),
            question=faq["question"],
            answer=faq["answer"],
            category=faq.get("category", "general"),
            language=LanguageEnum(faq.get("language", "en")),
            keywords=faq.get("keywords", []),
            priority=faq.get("priority", 0),
            views=faq.get("views", 0) + 1,
            helpful_count=faq.get("helpful_count", 0),
            created_at=faq.get("created_at"),
            updated_at=faq.get("updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get FAQ error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get FAQ")


@router.put("/{faq_id}")
async def update_faq(faq_id: str, updates: dict):
    """
    Update an existing FAQ.
    
    Only provided fields will be updated.
    """
    try:
        # Validate updates
        allowed_fields = {"question", "answer", "category", "keywords", "priority", "language"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            raise HTTPException(
                status_code=400,
                detail="No valid fields to update"
            )
        
        result = await faq_service.update_faq(faq_id, filtered_updates)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to update FAQ")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update FAQ error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update FAQ: {str(e)}"
        )


@router.delete("/{faq_id}")
async def delete_faq(faq_id: str):
    """
    Delete a FAQ.
    """
    try:
        result = await faq_service.delete_faq(faq_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "FAQ not found")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete FAQ error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete FAQ: {str(e)}"
        )


@router.post("/{faq_id}/helpful")
async def mark_faq_helpful(faq_id: str):
    """
    Mark a FAQ as helpful (like/upvote).
    """
    try:
        await faq_service.mark_helpful(faq_id)
        return {"success": True, "message": "Marked as helpful"}
    except Exception as e:
        logger.error(f"Mark helpful error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/seed")
async def seed_default_faqs():
    """
    Seed the database with default FAQs from JSON files.
    
    This is useful for initial setup.
    """
    try:
        await faq_service.seed_default_faqs()
        return {"success": True, "message": "FAQs seeded successfully"}
    except Exception as e:
        logger.error(f"Seed FAQs error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed FAQs: {str(e)}"
        )
