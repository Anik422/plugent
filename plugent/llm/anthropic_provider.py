"""Anthropic provider for plugent."""

import time
from typing import Iterator

from anthropic import Anthropic

from plugent.llm.base import BaseLLM


class AnthropicLLM(BaseLLM):
    """Anthropic LLM provider (Claude)."""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307", **kwargs):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_retries = 3

    def chat(self, messages: list[dict]) -> str:
        """Send chat request with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=1024,
                )
                return response.content[0].text
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Anthropic chat failed after {self.max_retries} retries: {last_error}")

    def stream(self, messages: list[dict]) -> Iterator[str]:
        """Stream chat response with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                with self.client.messages.stream(
                    model=self.model,
                    messages=messages,
                    max_tokens=1024,
                ) as stream:
                    for chunk in stream.text_stream:
                        yield chunk
                return
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Anthropic stream failed after {self.max_retries} retries: {last_error}")

    def embed(self, text: str) -> list[float]:
        """Anthropic doesn't provide embeddings API - raise error."""
        raise NotImplementedError("Anthropic API does not support embeddings")