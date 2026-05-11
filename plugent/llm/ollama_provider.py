"""Ollama provider for plugent."""

import time
from typing import Iterator

import ollama

from plugent.llm.base import BaseLLM


class OllamaLLM(BaseLLM):
    """Ollama local LLM provider."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        self.client = ollama.Client(host=base_url)
        self.base_url = base_url
        self.model = model
        self.max_retries = 3

    def chat(self, messages: list[dict]) -> str:
        """Send chat request with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                )
                return response["message"]["content"]
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Ollama chat failed after {self.max_retries} retries: {last_error}")

    def stream(self, messages: list[dict]) -> Iterator[str]:
        """Stream chat response with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=True,
                )
                for chunk in response:
                    if chunk["message"]["content"]:
                        yield chunk["message"]["content"]
                return
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Ollama stream failed after {self.max_retries} retries: {last_error}")

    def embed(self, text: str) -> list[float]:
        """Generate embeddings with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings(
                    model=self.model,
                    prompt=text,
                )
                return response["embedding"]
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"Ollama embed failed after {self.max_retries} retries: {last_error}")