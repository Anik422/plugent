"""Cohere provider for plugent (free tier available)."""

import time
from typing import Iterator

from cohere import Client

from plugent.llm.base import BaseLLM


class CohereLLM(BaseLLM):
    """Cohere LLM provider (free tier)."""

    def __init__(
        self,
        api_key: str,
        model: str = "command-r-plus-08-2024",
        **kwargs
    ):
        self.client = Client(api_key=api_key)
        self.model = model
        self.max_retries = 3

    def chat(self, messages: list[dict]) -> str:
        """Send chat request with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat(
                    model=self.model,
                    message=messages[-1]["content"],
                    chat_history=messages[:-1],
                )
                return response.text
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Cohere chat failed after {self.max_retries} retries: {last_error}")

    def stream(self, messages: list[dict]) -> Iterator[str]:
        """Stream chat response with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                stream = self.client.chat_stream(
                    model=self.model,
                    message=messages[-1]["content"],
                    chat_history=messages[:-1],
                )
                for event in stream:
                    if event.event_type == "text-generation":
                        yield event.text
                return
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Cohere stream failed after {self.max_retries} retries: {last_error}")

    def embed(self, text: str) -> list[float]:
        """Generate embeddings with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.embed(
                    texts=[text],
                    model="embed-english-v3.0",
                )
                return response.embeddings[0]
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Cohere embed failed after {self.max_retries} retries: {last_error}")