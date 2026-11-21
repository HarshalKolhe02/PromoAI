"""
Central factory for creating AI providers.
Allows hot-swapping providers and models via config without modifying pipeline code.
"""
from typing import Optional
from app.ai.anthropic_provider import AnthropicProvider
from app.ai.base_provider import BaseAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.config import Config
from app.utils.logging import logger


class AIProviderFactory:
    """Factory to instantiate AI providers with graceful fallback to mock mode."""

    @classmethod
    def get_provider(
        cls,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> BaseAIProvider:
        provider = (provider_name or Config.AI_PROVIDER or "mock").lower().strip()
        model = model_name or Config.AI_MODEL

        logger.info(f"Initializing AI Provider: '{provider}' with model: '{model}'")

        if provider == "gemini":
            key = api_key or Config.GEMINI_API_KEY
            if not key:
                logger.warning("No GEMINI_API_KEY found. Falling back to MockAIProvider.")
                return MockAIProvider(model_name="mock-fallback")
            return GeminiProvider(api_key=key, model_name=model)

        elif provider in ("openai", "ollama"):
            key = api_key or Config.OPENAI_API_KEY
            base_url = Config.OLLAMA_BASE_URL if provider == "ollama" else Config.OPENAI_BASE_URL
            return OpenAIProvider(api_key=key, model_name=model, base_url=base_url)

        elif provider == "anthropic":
            key = api_key or Config.ANTHROPIC_API_KEY
            if not key:
                logger.warning("No ANTHROPIC_API_KEY found. Falling back to MockAIProvider.")
                return MockAIProvider(model_name="mock-fallback")
            return AnthropicProvider(api_key=key, model_name=model)

        elif provider == "mock":
            return MockAIProvider(model_name=model or "mock-deterministic-v1")

        else:
            logger.warning(f"Unknown AI Provider '{provider}'. Defaulting to MockAIProvider.")
            return MockAIProvider(model_name="mock-deterministic-v1")
