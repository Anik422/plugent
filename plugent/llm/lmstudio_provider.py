"""LM Studio provider for plugent (OpenAI-compatible API)."""

import time
from typing import Iterator

from openai import OpenAI

from plugent.llm.base import BaseLLM


class LMStudioLLM(BaseLLM):
    """LM Studio local LLM provider (OpenAI-compatible)."""

    def __init__(
        self,
        model: str = "llama-3.1-8b",
        base_url: str = "http://localhost:1234/v1",
        api_key: str = "not-needed",
        **kwargs
    ):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.max_retries = 3

    def chat(self, messages: list[dict]) -> str:
        """Send chat request with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"LM Studio chat failed after {self.max_retries} retries: {last_error}")

    def stream(self, messages: list[dict]) -> Iterator[str]:
        """Stream chat response with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                )
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"LM Studio stream failed after {self.max_retries} retries: {last_error}")

    def embed(self, text: str) -> list[float]:
        """Generate embeddings with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text,
                )
                return response.data[0].embedding
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"LM Studio embed failed after {self.max_retries} retries: {last_error}")