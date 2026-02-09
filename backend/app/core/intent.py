"""
Intent Detection Service - Classifies user queries into intents.
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

from app.utils.constants import INTENT_KEYWORDS, SUGGESTED_QUESTIONS

logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Detects user intent from their message.
    
    Uses keyword matching for simplicity. Can be enhanced with:
    - ML-based intent classification
    - Semantic similarity matching
    - LLM-based classification
    """
    
    def __init__(self):
        self.intents = INTENT_KEYWORDS
        self.intent_priority = {
            "greeting": 1,
            "goodbye": 1,
            "fee_query": 2,
            "admission": 2,
            "scholarship": 2,
            "timetable": 2,
            "exam": 2,
            "document": 2,
            "contact": 2,
            "hostel": 2,
            "library": 2
        }
    
    def detect_intent(self, text: str) -> Dict[str, any]:
        """
        Detect intent from user message.
        
        Args:
            text: User message
            
        Returns:
            Dictionary with intent and confidence
        """
        if not text:
            return {
                "intent": "general",
                "confidence": 0.0,
                "matched_keywords": []
            }
        
        text_lower = text.lower()
        
        # Track matches for each intent
        intent_scores = {}
        matched_keywords = {}
        
        for intent, keywords in self.intents.items():
            matches = []
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matches.append(keyword)
            
            if matches:
                # Score based on number of matches and priority
                priority = self.intent_priority.get(intent, 2)
                score = len(matches) * (1 / priority)
                intent_scores[intent] = score
                matched_keywords[intent] = matches
        
        if not intent_scores:
            return {
                "intent": "general",
                "confidence": 0.5,
                "matched_keywords": []
            }
        
        # Get highest scoring intent
        best_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[best_intent]
        
        # Calculate confidence (normalize based on max possible matches)
        max_keywords = len(self.intents.get(best_intent, []))
        confidence = min(max_score / max(max_keywords, 1), 1.0)
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "matched_keywords": matched_keywords.get(best_intent, []),
            "all_matches": matched_keywords
        }
    
    def extract_entities(self, text: str) -> Dict[str, any]:
        """
        Extract entities from user message.
        
        Extracts:
        - Years (2024, 2025, etc.)
        - Amounts (Rs. 5000, ₹5000)
        - Semesters (sem 1, semester 2)
        - Dates
        - Email addresses
        - Phone numbers
        
        Args:
            text: User message
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        # Extract year
        year_match = re.search(r'\b(20\d{2})\b', text)
        if year_match:
            entities['year'] = year_match.group(1)
        
        # Extract amount (Indian currency)
        amount_patterns = [
            r'(?:Rs\.?|₹|INR)\s*(\d+(?:,\d+)*(?:\.\d{2})?)',
            r'(\d+(?:,\d+)*)\s*(?:rupees?|rs)',
        ]
        for pattern in amount_patterns:
            amount_match = re.search(pattern, text, re.IGNORECASE)
            if amount_match:
                # Clean amount string
                amount = amount_match.group(1).replace(',', '')
                entities['amount'] = amount
                break
        
        # Extract semester
        sem_match = re.search(r'(?:sem(?:ester)?)\s*(\d+)', text, re.IGNORECASE)
        if sem_match:
            entities['semester'] = int(sem_match.group(1))
        
        # Extract academic year (e.g., "2024-25", "2024-2025")
        academic_year_match = re.search(r'(20\d{2})[-/](20)?(\d{2})', text)
        if academic_year_match:
            start_year = academic_year_match.group(1)
            end_year = academic_year_match.group(3)
            entities['academic_year'] = f"{start_year}-{end_year}"
        
        # Extract department/branch
        departments = [
            'computer science', 'cs', 'cse', 'it', 'information technology',
            'electronics', 'ece', 'eee', 'mechanical', 'civil', 'chemical',
            'btech', 'mtech', 'mba', 'bba', 'bca', 'mca', 'bsc', 'msc'
        ]
        text_lower = text.lower()
        for dept in departments:
            if dept in text_lower:
                entities['department'] = dept.upper()
                break
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            entities['email'] = email_match.group(0)
        
        # Extract phone number (Indian format)
        phone_match = re.search(r'(?:\+91|0)?[\s-]?[6-9]\d{4}[\s-]?\d{5}', text)
        if phone_match:
            entities['phone'] = phone_match.group(0)
        
        return entities
    
    def get_suggested_questions(self, intent: str) -> List[str]:
        """
        Get suggested follow-up questions based on intent.
        
        Args:
            intent: Detected intent
            
        Returns:
            List of suggested questions
        """
        # Map intents to question categories
        intent_category_map = {
            "fee_query": "fees",
            "admission": "admission",
            "scholarship": "scholarship",
            "exam": "exam",
            "greeting": "general",
            "goodbye": None
        }
        
        category = intent_category_map.get(intent, "general")
        
        if category is None:
            return []
        
        return SUGGESTED_QUESTIONS.get(category, SUGGESTED_QUESTIONS["general"])
    
    def is_greeting(self, text: str) -> bool:
        """Check if the message is a greeting."""
        result = self.detect_intent(text)
        return result["intent"] == "greeting"
    
    def is_goodbye(self, text: str) -> bool:
        """Check if the message is a goodbye."""
        result = self.detect_intent(text)
        return result["intent"] == "goodbye"
    
    def needs_human_fallback(self, text: str, confidence: float) -> bool:
        """
        Determine if the query needs human intervention.
        
        Args:
            text: User message
            confidence: Response confidence score
            
        Returns:
            True if human fallback is recommended
        """
        # Keywords that often need human help
        human_required_keywords = [
            "speak to someone", "talk to human", "real person",
            "manager", "supervisor", "complaint", "urgent",
            "emergency", "help me please", "not working"
        ]
        
        text_lower = text.lower()
        
        # Check for explicit human request
        for keyword in human_required_keywords:
            if keyword in text_lower:
                return True
        
        # Low confidence threshold
        if confidence < 0.3:
            return True
        
        return False


# ===========================================
# Singleton Instance
# ===========================================

intent_detector = IntentDetector()
