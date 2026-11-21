"""
OpenAI & OpenAI-compatible API provider adapter.
Supports OpenAI, Ollama, and vLLM endpoints with structured JSON responses.
"""
import json
import time
from typing import Optional, Tuple, Type
import requests
from pydantic import BaseModel
from app.ai.base_provider import BaseAIProvider
from app.config import Config
from app.utils.logging import logger


class OpenAIProvider(BaseAIProvider):
    """OpenAI / OpenAI-compatible provider adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = Config.AI_TEMPERATURE,
        timeout: int = Config.AI_TIMEOUT,
        max_retries: int = Config.AI_MAX_RETRIES
    ):
        model = model_name or Config.AI_MODEL or "gpt-4o-mini"
        super().__init__(model, temperature, timeout, max_retries)
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.base_url = (base_url or Config.OPENAI_BASE_URL).rstrip("/")

    def check_connection(self) -> Tuple[bool, str]:
        if not self.api_key and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            return False, "OPENAI_API_KEY is not set."
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, f"Connected to OpenAI-compatible endpoint ({self.base_url})."
            return False, f"Endpoint returned status {resp.status_code}: {resp.text[:150]}"
        except Exception as e:
            return False, f"Connection error to {self.base_url}: {e}"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature
        }

        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                elif resp.status_code in (429, 500, 502, 503):
                    time.sleep((2 ** attempt) * 2)
                else:
                    raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise RuntimeError(f"OpenAI request failed: {e}")
                time.sleep((2 ** attempt) * 2)
        return ""

    def generate_structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        schema_json = json.dumps(schema.model_json_schema())
        augmented_prompt = (
            f"{prompt}\n\nRespond strictly with a single JSON object matching this schema:\n{schema_json}"
        )
        messages = []
        sys = (system_prompt or "") + "\nYou are an AI that outputs valid JSON conforming to the requested schema."
        messages.append({"role": "system", "content": sys})
        messages.append({"role": "user", "content": augmented_prompt})

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"}
        }

        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    if content.startswith("```"):
                        content = content.strip("`").lstrip("json").strip()
                    parsed = json.loads(content)
                    return schema.model_validate(parsed)
                elif resp.status_code in (429, 500, 502, 503):
                    time.sleep((2 ** attempt) * 2)
                else:
                    raise RuntimeError(f"OpenAI structured error {resp.status_code}: {resp.text}")
            except Exception as e:
                if attempt == self.max_retries:
                    logger.error(f"Failed to generate structured output from OpenAI: {e}")
                    raise
                time.sleep((2 ** attempt) * 2)

        raise RuntimeError("Failed to obtain structured response from OpenAI.")
