"""
Abstract Base Class for AI Model Providers using the Adapter Pattern.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, Type
from pydantic import BaseModel


class BaseAIProvider(ABC):
    """Abstract interface for all LLM providers."""

    def __init__(self, model_name: str, temperature: float = 0.2, timeout: int = 120, max_retries: int = 2):
        self.model_name = model_name
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates raw text from the model."""
        pass

    @abstractmethod
    def generate_structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        """Generates output adhering to the provided Pydantic schema."""
        pass

    @abstractmethod
    def check_connection(self) -> Tuple[bool, str]:
        """Validates connection and API credentials."""
        pass

    def get_model_name(self) -> str:
        """Returns the active model name."""
        return self.model_name
