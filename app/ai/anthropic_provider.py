"""
Anthropic Claude AI provider adapter.
"""
import json
import time
from typing import Optional, Tuple, Type
import requests
from pydantic import BaseModel
from app.ai.base_provider import BaseAIProvider
from app.config import Config
from app.utils.logging import logger


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = Config.AI_TEMPERATURE,
        timeout: int = Config.AI_TIMEOUT,
        max_retries: int = Config.AI_MAX_RETRIES
    ):
        model = model_name or Config.AI_MODEL or "claude-3-5-sonnet-20241022"
        super().__init__(model, temperature, timeout, max_retries)
        self.api_key = api_key or Config.ANTHROPIC_API_KEY

    def check_connection(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "ANTHROPIC_API_KEY is not set."
        return True, f"Anthropic adapter initialized for {self.model_name}."

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature
        }
        if system_prompt:
            payload["system"] = system_prompt

        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["content"][0]["text"]
                elif resp.status_code in (429, 500, 529):
                    time.sleep((2 ** attempt) * 2)
                else:
                    raise RuntimeError(f"Anthropic error {resp.status_code}: {resp.text}")
            except Exception as e:
                if attempt == self.max_retries:
                    raise
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
            f"{prompt}\n\nIMPORTANT: Return ONLY a valid JSON object matching this schema:\n{schema_json}"
        )
        sys = (system_prompt or "") + "\nRespond with valid JSON only. Do not wrap in markdown quotes."
        raw_output = self.generate_text(augmented_prompt, system_prompt=sys)
        clean = raw_output.strip()
        if clean.startswith("```"):
            clean = clean.strip("`").lstrip("json").strip()
        parsed = json.loads(clean)
        return schema.model_validate(parsed)
