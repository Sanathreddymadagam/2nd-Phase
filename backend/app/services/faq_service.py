"""
FAQ Service - Manages frequently asked questions.
"""

from typing import Dict, List, Optional, Any
import logging
import json
import os
from pathlib import Path
from datetime import datetime

from app.config import settings
from app.models.database import MongoDB, Collections, DatabaseOperations
from app.models.schemas import FAQCreate, FAQResponse
from app.utils.helpers import extract_keywords, generate_session_id

logger = logging.getLogger(__name__)


class FAQService:
    """
    Service for managing and searching FAQs.
    
    Supports:
    - CRUD operations for FAQs
    - Keyword-based search
    - Category filtering
    - Multi-language FAQs
    """
    
    def __init__(self):
        self.faqs_dir = Path("./data/faqs")
        self._cached_faqs: Dict[str, List[Dict]] = {}
        self._last_cache_update = None
    
    async def search_faqs(
        self,
        query: str,
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search FAQs matching the query.
        
        Args:
            query: Search query
            category: Optional category filter
            language: Language code
            limit: Maximum results
            
        Returns:
            Dictionary with matching FAQs
        """
        try:
            # Get FAQs (from cache or load)
            faqs = await self._get_faqs(language)
            
            if not faqs:
                return {"matches": [], "total": 0}
            
            # Extract keywords from query
            query_keywords = set(extract_keywords(query.lower()))
            
            # Score each FAQ
            scored_faqs = []
            for faq in faqs:
                # Filter by category if specified
                if category and faq.get("category", "").lower() != category.lower():
                    continue
                
                # Calculate match score
                faq_keywords = set(k.lower() for k in faq.get("keywords", []))
                question_keywords = set(extract_keywords(faq.get("question", "").lower()))
                all_faq_keywords = faq_keywords.union(question_keywords)
                
                # Count matching keywords
                matches = query_keywords.intersection(all_faq_keywords)
                
                if matches:
                    # Score based on matches and priority
                    score = len(matches) / max(len(query_keywords), 1)
                    priority_boost = faq.get("priority", 0) * 0.1
                    final_score = min(score + priority_boost, 1.0)
                    
                    scored_faqs.append({
                        "question": faq["question"],
                        "answer": faq["answer"],
                        "category": faq.get("category", "general"),
                        "score": final_score,
                        "matched_keywords": list(matches)
                    })
            
            # Sort by score
            scored_faqs.sort(key=lambda x: x["score"], reverse=True)
            
            return {
                "matches": scored_faqs[:limit],
                "total": len(scored_faqs)
            }
            
        except Exception as e:
            logger.error(f"FAQ search error: {e}")
            return {"matches": [], "total": 0, "error": str(e)}
    
    async def get_faq_by_id(self, faq_id: str) -> Optional[Dict]:
        """Get a specific FAQ by ID."""
        try:
            db = MongoDB.get_db()
            faq = await db[Collections.FAQS].find_one({"_id": faq_id})
            return faq
        except Exception as e:
            logger.error(f"Error getting FAQ: {e}")
            return None
    
    async def create_faq(self, faq: FAQCreate) -> Dict[str, Any]:
        """
        Create a new FAQ.
        
        Args:
            faq: FAQ data
            
        Returns:
            Created FAQ with ID
        """
        try:
            # Auto-generate keywords if not provided
            keywords = faq.keywords
            if not keywords:
                keywords = extract_keywords(faq.question)
            
            faq_doc = {
                "_id": generate_session_id(),
                "question": faq.question,
                "answer": faq.answer,
                "category": faq.category,
                "language": faq.language.value,
                "keywords": keywords,
                "priority": faq.priority,
                "views": 0,
                "helpful_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            db = MongoDB.get_db()
            await db[Collections.FAQS].insert_one(faq_doc)
            
            # Invalidate cache
            self._cached_faqs = {}
            
            logger.info(f"Created FAQ: {faq.question[:50]}...")
            
            return {
                "success": True,
                "id": faq_doc["_id"],
                "message": "FAQ created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating FAQ: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_faq(
        self,
        faq_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing FAQ."""
        try:
            updates["updated_at"] = datetime.utcnow()
            
            db = MongoDB.get_db()
            result = await db[Collections.FAQS].update_one(
                {"_id": faq_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                self._cached_faqs = {}  # Invalidate cache
                return {"success": True, "message": "FAQ updated"}
            else:
                return {"success": False, "error": "FAQ not found"}
                
        except Exception as e:
            logger.error(f"Error updating FAQ: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_faq(self, faq_id: str) -> Dict[str, Any]:
        """Delete a FAQ."""
        try:
            db = MongoDB.get_db()
            result = await db[Collections.FAQS].delete_one({"_id": faq_id})
            
            if result.deleted_count > 0:
                self._cached_faqs = {}
                return {"success": True, "message": "FAQ deleted"}
            else:
                return {"success": False, "error": "FAQ not found"}
                
        except Exception as e:
            logger.error(f"Error deleting FAQ: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_all_faqs(
        self,
        language: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get all FAQs with optional filtering.
        
        Args:
            language: Filter by language
            category: Filter by category
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated FAQs
        """
        try:
            db = MongoDB.get_db()
            
            # Build query
            query = {}
            if language:
                query["language"] = language
            if category:
                query["category"] = category
            
            # Get total count
            total = await db[Collections.FAQS].count_documents(query)
            
            # Get paginated results
            skip = (page - 1) * per_page
            cursor = db[Collections.FAQS].find(query).skip(skip).limit(per_page)
            faqs = await cursor.to_list(length=per_page)
            
            return {
                "faqs": faqs,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Error getting FAQs: {e}")
            return {"faqs": [], "total": 0, "error": str(e)}
    
    async def get_categories(self, language: str = "en") -> List[str]:
        """Get all FAQ categories."""
        try:
            db = MongoDB.get_db()
            categories = await db[Collections.FAQS].distinct(
                "category",
                {"language": language}
            )
            return categories
        except Exception:
            return []
    
    async def increment_view(self, faq_id: str):
        """Increment view count for a FAQ."""
        try:
            db = MongoDB.get_db()
            await db[Collections.FAQS].update_one(
                {"_id": faq_id},
                {"$inc": {"views": 1}}
            )
        except Exception as e:
            logger.error(f"Error incrementing view: {e}")
    
    async def mark_helpful(self, faq_id: str):
        """Mark a FAQ as helpful."""
        try:
            db = MongoDB.get_db()
            await db[Collections.FAQS].update_one(
                {"_id": faq_id},
                {"$inc": {"helpful_count": 1}}
            )
        except Exception as e:
            logger.error(f"Error marking helpful: {e}")
    
    async def _get_faqs(self, language: str) -> List[Dict]:
        """
        Get FAQs from cache or load from database/files.
        
        First tries database, then falls back to JSON files.
        """
        # Check cache
        if language in self._cached_faqs:
            return self._cached_faqs[language]
        
        faqs = []
        
        # Try database first
        try:
            db = MongoDB.get_db()
            cursor = db[Collections.FAQS].find({"language": language})
            faqs = await cursor.to_list(length=1000)
            
            if faqs:
                self._cached_faqs[language] = faqs
                return faqs
                
        except Exception as e:
            logger.warning(f"Could not load FAQs from database: {e}")
        
        # Fall back to JSON files
        faqs = await self._load_faqs_from_file(language)
        self._cached_faqs[language] = faqs
        
        return faqs
    
    async def _load_faqs_from_file(self, language: str) -> List[Dict]:
        """Load FAQs from JSON file."""
        file_path = self.faqs_dir / f"faqs_{language}.json"
        
        if not file_path.exists():
            # Try English as fallback
            file_path = self.faqs_dir / "faqs_en.json"
        
        if not file_path.exists():
            logger.warning(f"No FAQ file found for language: {language}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                faqs = json.load(f)
                logger.info(f"Loaded {len(faqs)} FAQs from {file_path}")
                return faqs
        except Exception as e:
            logger.error(f"Error loading FAQ file: {e}")
            return []
    
    async def seed_default_faqs(self):
        """Seed default FAQs if database is empty."""
        try:
            db = MongoDB.get_db()
            count = await db[Collections.FAQS].count_documents({})
            
            if count > 0:
                logger.info(f"FAQs already exist: {count}")
                return
            
            # Load from files and insert
            for lang in settings.SUPPORTED_LANGUAGES:
                faqs = await self._load_faqs_from_file(lang)
                
                if faqs:
                    for faq in faqs:
                        faq["_id"] = generate_session_id()
                        faq["language"] = lang
                        faq["views"] = 0
                        faq["helpful_count"] = 0
                        faq["created_at"] = datetime.utcnow()
                        faq["updated_at"] = datetime.utcnow()
                    
                    await db[Collections.FAQS].insert_many(faqs)
                    logger.info(f"Seeded {len(faqs)} FAQs for {lang}")
                    
        except Exception as e:
            logger.error(f"Error seeding FAQs: {e}")


# ===========================================
# Singleton Instance
# ===========================================

faq_service = FAQService()
