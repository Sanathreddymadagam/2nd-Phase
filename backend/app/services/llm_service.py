"""
Ollama LLM Service - Integration with Ollama for text generation.
"""

import httpx
from typing import Dict, List, Optional, Any
import logging
import asyncio

from app.config import settings
from app.utils.constants import SYSTEM_PROMPTS

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Service for interacting with Ollama LLM.
    
    Ollama runs locally and provides access to various LLMs like
    llama3.2, mistral, phi3, etc.
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = 60.0  # Longer timeout for LLM generation
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[int]] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: System prompt to guide the model
            context: Previous context for conversation continuity
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0-1)
            top_p: Nucleus sampling parameter
            stream: Whether to stream the response
            
        Returns:
            Dictionary with response and metadata
        """
        if system_prompt is None:
            system_prompt = SYSTEM_PROMPTS["default"]
        
        # Build the full prompt with system context
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": stream,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stop": ["\nUser:", "\n\nUser:"]  # Stop generation at user turn
            }
        }
        
        # Add context if provided (for conversation continuity)
        if context:
            payload["context"] = context
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    logger.error(f"Ollama error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"LLM returned status {response.status_code}",
                        "response": None
                    }
                
                result = response.json()
                
                return {
                    "success": True,
                    "response": result.get("response", "").strip(),
                    "context": result.get("context"),  # For conversation continuity
                    "model": result.get("model"),
                    "total_duration": result.get("total_duration"),
                    "eval_count": result.get("eval_count")
                }
                
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            return {
                "success": False,
                "error": "Request timed out. The model is taking too long.",
                "response": None
            }
        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama")
            return {
                "success": False,
                "error": "Cannot connect to Ollama. Make sure it's running.",
                "response": None
            }
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    async def generate_with_context(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response with RAG context.
        
        Args:
            query: User's question
            context: Retrieved document context
            conversation_history: Previous messages
            
        Returns:
            Generated response with metadata
        """
        # Build context-aware prompt
        system_prompt = SYSTEM_PROMPTS["rag_response"].format(
            context=context,
            question=query
        )
        
        # Add conversation history if available
        if conversation_history:
            history_text = "\n".join([
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in conversation_history[-3:]  # Last 3 messages
            ])
            system_prompt = f"Previous conversation:\n{history_text}\n\n{system_prompt}"
        
        return await self.generate_response(
            prompt=query,
            system_prompt=system_prompt,
            temperature=0.5  # Lower temperature for factual answers
        )
    
    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Generate response using chat format (message history).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Generated response
        """
        # Build conversation prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            prompt_parts.append(f"{role}: {content}")
        
        prompt = "\n".join(prompt_parts)
        
        return await self.generate_response(
            prompt=prompt,
            temperature=0.7
        )
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check if Ollama is running and the model is available.
        
        Returns:
            Health status dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                # Check Ollama is running
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                
                if response.status_code != 200:
                    return {
                        "healthy": False,
                        "error": f"Ollama returned status {response.status_code}"
                    }
                
                # Check if our model is available
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                
                model_available = any(
                    self.model in model or model in self.model
                    for model in models
                )
                
                return {
                    "healthy": True,
                    "model_available": model_available,
                    "available_models": models,
                    "configured_model": self.model
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def pull_model(self) -> bool:
        """
        Pull the configured model if not available.
        
        Returns:
            True if model is available/pulled successfully
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": self.model},
                    timeout=300.0  # 5 minutes for model download
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False


# ===========================================
# Singleton Instance
# ===========================================

ollama_service = OllamaService()
