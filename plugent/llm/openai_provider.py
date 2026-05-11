"""OpenAI provider for plugent."""

import time
from typing import Iterator

from openai import OpenAI

from plugent.llm.base import BaseLLM


class OpenAILLM(BaseLLM):
    """OpenAI LLM provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        self.client = OpenAI(api_key=api_key)
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
        raise RuntimeError(f"OpenAI chat failed after {self.max_retries} retries: {last_error}")

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
        raise RuntimeError(f"OpenAI stream failed after {self.max_retries} retries: {last_error}")

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
        raise RuntimeError(f"OpenAI embed failed after {self.max_retries} retries: {last_error}")