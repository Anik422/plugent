"""Google Gemini provider for plugent."""

import time
from typing import Iterator

import google.genai as genai

from plugent.llm.base import BaseLLM


class GeminiLLM(BaseLLM):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", **kwargs):
        self._client = genai.Client(api_key=api_key)
        self.model_name = model
        self.max_retries = 3

    def _convert_messages(self, messages: list[dict]) -> list:
        """Convert messages to Gemini format."""
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_messages.append({"role": role, "parts": [msg["content"]]})
        return gemini_messages

    def chat(self, messages: list[dict]) -> str:
        """Send chat request with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=messages[-1]["content"],
                )
                return response.text
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Gemini chat failed after {self.max_retries} retries: {last_error}")

    def stream(self, messages: list[dict]) -> Iterator[str]:
        """Stream chat response with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=messages[-1]["content"],
                    stream=True,
                )
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Gemini stream failed after {self.max_retries} retries: {last_error}")

    def embed(self, text: str) -> list[float]:
        """Generate embeddings with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = self._client.models.embed_content(
                    model="models/embedding-001",
                    contents=text,
                )
                return result.embedding
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Gemini embed failed after {self.max_retries} retries: {last_error}")