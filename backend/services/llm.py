"""
finLine LLM Service

Abstracted LLM interface - supports multiple providers.
Change provider via config, code stays the same.
"""

import logging
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMClient:
    """Abstracted LLM client supporting multiple providers."""

    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key

        logger.info(f"LLM Client initialized: provider={self.provider}, model={self.model}")

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """
        Send a chat completion request.

        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            **kwargs: Additional provider-specific parameters

        Returns:
            Assistant's response text
        """
        if self.provider == "gemini":
            return await self._gemini_chat(messages, **kwargs)
        elif self.provider == "claude":
            return await self._claude_chat(messages, **kwargs)
        elif self.provider == "openai":
            return await self._openai_chat(messages, **kwargs)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def _gemini_chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Google Gemini API."""
        if not self.api_key:
            raise ValueError("LLM_API_KEY not set for Gemini")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        payload = {"contents": contents}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                params={"key": self.api_key},
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

        # Extract text from response
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")

        return ""

    async def _claude_chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Anthropic Claude API."""
        if not self.api_key:
            raise ValueError("LLM_API_KEY not set for Claude")

        url = "https://api.anthropic.com/v1/messages"

        # Separate system message if present
        system = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": chat_messages,
        }
        if system:
            payload["system"] = system

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            data = response.json()

        # Extract text
        content = data.get("content", [])
        if content:
            return content[0].get("text", "")

        return ""

    async def _openai_chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """OpenAI API."""
        if not self.api_key:
            raise ValueError("LLM_API_KEY not set for OpenAI")

        url = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")

        return ""


# Singleton instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
