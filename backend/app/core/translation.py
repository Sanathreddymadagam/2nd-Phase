"""
Translation Service - Handles language translation and detection.

Uses deep-translator for reliability and compatibility.
Can be replaced with IndicTrans2 for better Indian language support.
"""

from typing import Dict, Optional, Tuple
import logging
import asyncio

from app.config import settings
from app.utils.constants import LANGUAGES

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Service for language translation and detection.
    
    Currently uses deep-translator library. For production, consider:
    - IndicTrans2 (AI4Bharat) for better Indian language support
    - LibreTranslate (self-hosted, free)
    - AWS Translate / Google Cloud Translate (paid but reliable)
    """
    
    def __init__(self):
        self.supported_languages = settings.SUPPORTED_LANGUAGES
        self.default_language = settings.DEFAULT_LANGUAGE
        self._translator = None
    
    def _get_translator(self):
        """Lazy initialization of translator."""
        if self._translator is None:
            try:
                from deep_translator import GoogleTranslator
                self._translator = GoogleTranslator
            except ImportError:
                logger.warning("deep-translator not installed. Translation will be disabled.")
                self._translator = None
        return self._translator
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Dict[str, any]:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'hi', 'en')
            target_lang: Target language code
            
        Returns:
            Dictionary with translated text and metadata
        """
        # If same language, return as is
        if source_lang == target_lang:
            return {
                "success": True,
                "translated_text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "was_translated": False
            }
        
        # Validate languages
        if source_lang not in self.supported_languages:
            logger.warning(f"Source language '{source_lang}' not supported")
            source_lang = "auto"  # Let translator detect
        
        if target_lang not in self.supported_languages:
            logger.warning(f"Target language '{target_lang}' not supported")
            target_lang = self.default_language
        
        try:
            TranslatorClass = self._get_translator()
            if TranslatorClass is None:
                return {
                    "success": False,
                    "translated_text": text,
                    "error": "Translation service not available"
                }
            
            # Run translation in thread pool (deep-translator is sync)
            loop = asyncio.get_event_loop()
            translator = TranslatorClass(
                source=source_lang if source_lang != "auto" else "auto",
                target=target_lang
            )
            result = await loop.run_in_executor(
                None,
                lambda: translator.translate(text)
            )
            
            return {
                "success": True,
                "translated_text": result,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "was_translated": True,
                "confidence": None
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "success": False,
                "translated_text": text,  # Return original on failure
                "source_lang": source_lang,
                "target_lang": target_lang,
                "error": str(e)
            }
    
    async def detect_language(self, text: str) -> Dict[str, any]:
        """
        Detect the language of the given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detected language info
        """
        if not text or len(text.strip()) < 3:
            return {
                "success": False,
                "language": self.default_language,
                "confidence": 0.0,
                "error": "Text too short for detection"
            }
        
        try:
            # Use langdetect for language detection
            from langdetect import detect, detect_langs
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: detect_langs(text)
            )
            
            if result:
                detected_lang = result[0].lang
                confidence = result[0].prob
            else:
                return self._heuristic_detect(text)
            
            # Map to supported languages
            if detected_lang not in self.supported_languages:
                # Try to find closest match
                detected_lang = self._map_language(detected_lang)
            
            return {
                "success": True,
                "language": detected_lang,
                "confidence": confidence,
                "raw_detection": result[0].lang if result else None
            }
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return self._heuristic_detect(text)
    
    def _heuristic_detect(self, text: str) -> Dict[str, any]:
        """
        Simple heuristic-based language detection.
        
        Uses character patterns to detect Indian languages.
        """
        # Character ranges for Indian scripts
        script_patterns = {
            "hi": (0x0900, 0x097F),  # Devanagari (Hindi, Marathi)
            "ta": (0x0B80, 0x0BFF),  # Tamil
            "te": (0x0C00, 0x0C7F),  # Telugu
            "bn": (0x0980, 0x09FF),  # Bengali
        }
        
        # Count characters in each script
        script_counts = {lang: 0 for lang in script_patterns}
        ascii_count = 0
        
        for char in text:
            code_point = ord(char)
            
            for lang, (start, end) in script_patterns.items():
                if start <= code_point <= end:
                    script_counts[lang] += 1
                    break
            else:
                if code_point < 128:
                    ascii_count += 1
        
        # Determine language
        total_chars = len(text.replace(" ", ""))
        if total_chars == 0:
            return {
                "success": True,
                "language": self.default_language,
                "confidence": 0.5
            }
        
        # Check for dominant script
        for lang, count in script_counts.items():
            if count / total_chars > 0.3:
                # Special case: Devanagari can be Hindi or Marathi
                # For now, default to Hindi
                return {
                    "success": True,
                    "language": lang,
                    "confidence": count / total_chars
                }
        
        # Default to English if mostly ASCII
        if ascii_count / total_chars > 0.7:
            return {
                "success": True,
                "language": "en",
                "confidence": ascii_count / total_chars
            }
        
        return {
            "success": True,
            "language": self.default_language,
            "confidence": 0.5
        }
    
    def _map_language(self, detected_lang: str) -> str:
        """Map detected language to supported language."""
        # Common mappings
        language_map = {
            "hin": "hi",
            "tam": "ta",
            "tel": "te",
            "ben": "bn",
            "mar": "mr",
            "eng": "en"
        }
        
        if detected_lang in language_map:
            return language_map[detected_lang]
        
        if detected_lang in self.supported_languages:
            return detected_lang
        
        return self.default_language
    
    async def translate_to_english(self, text: str, source_lang: str = None) -> Tuple[str, str]:
        """
        Convenience method to translate any text to English.
        
        Args:
            text: Text to translate
            source_lang: Source language (auto-detect if None)
            
        Returns:
            Tuple of (translated_text, detected_source_language)
        """
        if source_lang is None:
            detection = await self.detect_language(text)
            source_lang = detection["language"]
        
        if source_lang == "en":
            return text, "en"
        
        result = await self.translate(text, source_lang, "en")
        return result["translated_text"], source_lang
    
    async def translate_from_english(self, text: str, target_lang: str) -> str:
        """
        Convenience method to translate from English to target language.
        
        Args:
            text: English text
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        if target_lang == "en":
            return text
        
        result = await self.translate(text, "en", target_lang)
        return result["translated_text"]
    
    def get_language_info(self, lang_code: str) -> Dict[str, str]:
        """Get language information."""
        if lang_code in LANGUAGES:
            return LANGUAGES[lang_code]
        return {
            "name": "Unknown",
            "native_name": "Unknown",
            "flag": "🌐"
        }
    
    def get_supported_languages(self) -> Dict[str, Dict]:
        """Get all supported languages with info."""
        return {
            code: LANGUAGES.get(code, {"name": code})
            for code in self.supported_languages
        }


# ===========================================
# Singleton Instance
# ===========================================

translation_service = TranslationService()
