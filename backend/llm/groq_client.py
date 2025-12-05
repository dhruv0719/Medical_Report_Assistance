# backend/llm/groq_client.py
"""
Groq API client for LLM inference.
Handles API calls, rate limiting, and error handling.
"""

import os
import time
from typing import List, Dict, Optional
from groq import Groq

from config.settings import ModelConfig
from config.logging_config import get_logger

logger = get_logger(__name__)


class GroqClient:
    """Client for Groq LLM API"""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Model name (defaults to config)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.model = model or ModelConfig.LLM_MODEL
        self.temperature = ModelConfig.LLM_TEMPERATURE
        self.max_tokens = ModelConfig.LLM_MAX_TOKENS
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        
        logger.info(f"✅ Groq client initialized (model: {self.model})")
    
    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API
            
        Returns:
            Generated text
        """
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            duration = time.time() - start_time
            
            # Extract response text
            result = response.choices[0].message.content
            
            # Log usage stats
            if hasattr(response, 'usage'):
                logger.debug(
                    f"LLM call completed in {duration:.2f}s "
                    f"(tokens: {response.usage.total_tokens})"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise
    
    def generate_explanation(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate an explanation using system and user prompts.
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            temperature: Sampling temperature
            
        Returns:
            Generated explanation
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.complete(messages, temperature=temperature)
    
    def test_connection(self) -> bool:
        """
        Test if the Groq API is accessible.
        
        Returns:
            True if connection successful
        """
        try:
            messages = [
                {"role": "user", "content": "Say 'API working'"}
            ]
            response = self.complete(messages, max_tokens=10)
            logger.info(f"✅ Groq API connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Groq API connection test failed: {e}")
            return False


__all__ = ["GroqClient"]