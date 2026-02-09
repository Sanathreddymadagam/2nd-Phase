"""
Main Chatbot Service - Orchestrates all components for chat functionality.
"""

from typing import Dict, Optional, List, Any
import logging
from datetime import datetime

from app.config import settings
from app.models.schemas import (
    ChatRequest, ChatResponse, LanguageEnum, MessageRole
)
from app.core.translation import translation_service
from app.core.intent import intent_detector
from app.core.context import context_manager
from app.core.rag import rag_service
from app.services.llm_service import ollama_service
from app.utils.constants import LANGUAGES, CONFIDENCE_THRESHOLDS, SYSTEM_PROMPTS
from app.utils.helpers import generate_session_id

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Main chatbot service that orchestrates:
    - Language detection and translation
    - Intent detection
    - Context management
    - FAQ matching
    - RAG-based document Q&A
    - LLM response generation
    """
    
    def __init__(self):
        self.translation = translation_service
        self.intent = intent_detector
        self.context = context_manager
        self.rag = rag_service
        self.llm = ollama_service
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process a user message and generate a response.
        
        This is the main entry point for chat functionality.
        
        Args:
            request: ChatRequest with message, language, session_id
            
        Returns:
            ChatResponse with bot response and metadata
        """
        start_time = datetime.utcnow()
        
        # Generate session ID if not provided
        session_id = request.session_id or generate_session_id()
        
        # Get or create conversation context
        conversation = self.context.get_or_create_session(
            session_id,
            request.language
        )
        
        try:
            # Step 1: Detect language if not specified or auto-detect
            detected_lang = request.language.value
            original_message = request.message
            
            # Auto-detect language if message might be in different language
            detection = await self.translation.detect_language(request.message)
            if detection["success"] and detection["confidence"] > 0.7:
                detected_lang = detection["language"]
            
            # Step 2: Translate to English for processing
            english_message, source_lang = await self.translation.translate_to_english(
                request.message,
                detected_lang
            )
            
            logger.debug(f"Original: {original_message}")
            logger.debug(f"English: {english_message}")
            logger.debug(f"Detected lang: {detected_lang}")
            
            # Step 3: Detect intent
            intent_result = self.intent.detect_intent(english_message)
            intent = intent_result["intent"]
            
            # Extract entities
            entities = self.intent.extract_entities(english_message)
            conversation.update_entities(entities)
            conversation.add_intent(intent)
            
            # Step 4: Add user message to context
            conversation.add_user_message(original_message, detected_lang)
            
            # Step 5: Check for greetings/goodbyes (simple responses)
            if intent == "greeting":
                response_text = LANGUAGES[detected_lang]["greeting"]
                confidence = 1.0
                sources = None
                
            elif intent == "goodbye":
                # Get goodbye message based on language
                goodbye_messages = {
                    "en": "Goodbye! Feel free to ask if you have more questions.",
                    "hi": "अलविदा! अगर आपके और सवाल हों तो पूछें।",
                    "ta": "போய் வருகிறேன்! உங்களுக்கு மேலும் கேள்விகள் இருந்தால் கேளுங்கள்.",
                    "te": "వీడ్కోలు! మీకు మరిన్ని ప్రశ్నలు ఉంటే అడగండి.",
                    "bn": "বিদায়! আপনার আরও প্রশ্ন থাকলে জিজ্ঞাসা করুন।",
                    "mr": "निरोप! तुमच्या आणखी प्रश्न असल्यास विचारा."
                }
                response_text = goodbye_messages.get(detected_lang, goodbye_messages["en"])
                confidence = 1.0
                sources = None
                
            else:
                # Step 6: Try FAQ matching first
                faq_result = await self._search_faqs(english_message, intent)
                
                if faq_result and faq_result.get("confidence", 0) > 0.7:
                    # Use FAQ answer
                    response_text = faq_result["answer"]
                    confidence = faq_result["confidence"]
                    sources = ["FAQ Database"]
                    
                else:
                    # Step 7: Try RAG-based document search
                    rag_result = await self.rag.generate_answer(
                        english_message,
                        self.llm
                    )
                    
                    if rag_result.get("answer") and rag_result.get("confidence", 0) > 0.4:
                        response_text = rag_result["answer"]
                        confidence = rag_result["confidence"]
                        sources = rag_result.get("sources", [])
                        
                    else:
                        # Step 8: Fall back to LLM generation
                        context_prompt = self.context.get_context_prompt(
                            session_id,
                            english_message
                        )
                        
                        llm_result = await self.llm.generate_response(
                            prompt=context_prompt,
                            system_prompt=SYSTEM_PROMPTS["default"]
                        )
                        
                        if llm_result.get("success"):
                            response_text = llm_result["response"]
                            confidence = 0.6  # Default confidence for LLM
                            sources = None
                        else:
                            # Fallback message
                            response_text = LANGUAGES[detected_lang]["fallback"]
                            confidence = 0.0
                            sources = None
            
            # Step 9: Translate response back to user's language
            if detected_lang != "en" and response_text:
                response_text = await self.translation.translate_from_english(
                    response_text,
                    detected_lang
                )
            
            # Step 10: Determine if fallback is needed
            fallback_required = self.intent.needs_human_fallback(
                request.message,
                confidence
            )
            
            # Step 11: Get suggested questions
            suggested_questions = self.intent.get_suggested_questions(intent)
            
            # Translate suggested questions if needed
            if detected_lang != "en" and suggested_questions:
                translated_questions = []
                for q in suggested_questions[:3]:  # Limit to 3
                    translated_q = await self.translation.translate_from_english(
                        q, detected_lang
                    )
                    translated_questions.append(translated_q)
                suggested_questions = translated_questions
            
            # Step 12: Add assistant response to context
            conversation.add_assistant_message(
                response_text,
                detected_lang,
                sources=sources,
                confidence=confidence
            )
            
            # Calculate response time
            response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Response generated in {response_time_ms:.0f}ms")
            
            return ChatResponse(
                response=response_text,
                language=LanguageEnum(detected_lang),
                session_id=session_id,
                confidence_score=confidence,
                sources=sources,
                suggested_questions=suggested_questions,
                fallback_required=fallback_required,
                intent=intent
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            
            # Return error response
            error_message = LANGUAGES.get(
                request.language.value, LANGUAGES["en"]
            )["error"]
            
            return ChatResponse(
                response=error_message,
                language=request.language,
                session_id=session_id,
                confidence_score=0.0,
                sources=None,
                suggested_questions=None,
                fallback_required=True,
                intent="error"
            )
    
    async def _search_faqs(
        self,
        query: str,
        intent: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search FAQs for a matching answer.
        
        Args:
            query: User's question (in English)
            intent: Detected intent
            
        Returns:
            FAQ match result or None
        """
        from app.services.faq_service import faq_service
        
        try:
            # Map intent to FAQ category
            intent_to_category = {
                "fee_query": "fees",
                "admission": "admission",
                "scholarship": "scholarship",
                "exam": "exam",
                "timetable": "timetable",
                "document": "documents",
                "contact": "contact",
                "hostel": "hostel"
            }
            
            category = intent_to_category.get(intent)
            
            # Search FAQs
            result = await faq_service.search_faqs(
                query=query,
                category=category,
                language="en"  # FAQs are stored in English
            )
            
            if result and result.get("matches"):
                best_match = result["matches"][0]
                return {
                    "answer": best_match["answer"],
                    "question": best_match["question"],
                    "category": best_match.get("category"),
                    "confidence": best_match.get("score", 0.5)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"FAQ search error: {e}")
            return None
    
    async def get_conversation_history(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get conversation history for a session."""
        conversation = self.context.get_session(session_id)
        
        if not conversation:
            return {
                "session_id": session_id,
                "messages": [],
                "exists": False
            }
        
        return {
            "session_id": session_id,
            "messages": conversation.messages,
            "language": conversation.language.value,
            "created_at": conversation.created_at.isoformat(),
            "exists": True
        }
    
    async def clear_conversation(self, session_id: str) -> bool:
        """Clear a conversation session."""
        return self.context.clear_session(session_id)
    
    async def get_supported_languages(self) -> Dict[str, Dict]:
        """Get all supported languages with info."""
        return {
            code: {
                "name": info["name"],
                "native_name": info["native_name"],
                "flag": info["flag"]
            }
            for code, info in LANGUAGES.items()
            if code in settings.SUPPORTED_LANGUAGES
        }


# ===========================================
# Singleton Instance
# ===========================================

chatbot_service = ChatbotService()
