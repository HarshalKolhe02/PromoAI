"""
Google Gemini AI provider adapter.
Supports structured JSON output and text generation with exponential backoff and retries.
"""
import json
import time
from typing import Optional, Tuple, Type
import requests
from pydantic import BaseModel
from app.ai.base_provider import BaseAIProvider
from app.config import Config
from app.utils.logging import logger


class GeminiProvider(BaseAIProvider):
    """Google Gemini model adapter using REST API with retries and structured output parsing."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = Config.AI_TEMPERATURE,
        timeout: int = Config.AI_TIMEOUT,
        max_retries: int = Config.AI_MAX_RETRIES
    ):
        model = model_name or Config.AI_MODEL or "gemini-2.5-flash"
        super().__init__(model, temperature, timeout, max_retries)
        self.api_key = api_key or Config.GEMINI_API_KEY

    def check_connection(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "GEMINI_API_KEY is not set."
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}?key={self.api_key}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return True, f"Connected successfully to Gemini model {self.model_name}."
            else:
                return False, f"Gemini API returned status {resp.status_code}: {resp.text[:150]}"
        except Exception as e:
            return False, f"Connection error to Gemini: {str(e)}"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": 4096
            }
        }

        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    return ""
                elif resp.status_code in (429, 500, 503):
                    wait_time = (2 ** attempt) * 2
                    logger.warning(f"Gemini API rate limit/server error {resp.status_code}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise RuntimeError(f"Gemini request failed after {self.max_retries} retries: {e}")
                time.sleep((2 ** attempt) * 2)

        return ""

    def generate_structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        schema_json = json.dumps(schema.model_json_schema())
        augmented_prompt = (
            f"{prompt}\n\nIMPORTANT: You must respond ONLY with a valid JSON object matching this schema:\n"
            f"{schema_json}\nDo not include markdown code fence formatting like ```json. Return pure JSON only."
        )

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": augmented_prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "responseMimeType": "application/json"
            }
        }

        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            raw_text = parts[0].get("text", "").strip()
                            # Clean code fences if present
                            if raw_text.startswith("```"):
                                raw_text = raw_text.strip("`").lstrip("json").strip()
                            parsed_json = json.loads(raw_text)
                            return schema.model_validate(parsed_json)
                elif resp.status_code in (429, 500, 503):
                    time.sleep((2 ** attempt) * 2)
                else:
                    raise RuntimeError(f"Gemini structured output error {resp.status_code}: {resp.text}")
            except Exception as e:
                if attempt == self.max_retries:
                    logger.error(f"Failed to generate structured output from Gemini: {e}")
                    raise
                time.sleep((2 ** attempt) * 2)

        raise RuntimeError("Failed to obtain structured response from Gemini.")
