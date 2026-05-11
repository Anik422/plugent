"""GGUF (llama-cpp-python) provider for plugent."""

import time
from typing import Iterator

from llama_cpp import Llama

from plugent.llm.base import BaseLLM


class GGUF_LLM(BaseLLM):
    """Local GGUF model via llama-cpp-python."""

    def __init__(
        self,
        model_path: str,
        n_gpu_layers: int = 0,
        n_ctx: int = 4096,
        model: str = "llama",
        **kwargs
    ):
        self.model_path = model_path
        self.model = Llama(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            verbose=False,
        )
        self.max_retries = 3

    def chat(self, messages: list[dict]) -> str:
        """Send chat request with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                prompt = self._format_messages(messages)
                response = self.model(
                    prompt,
                    max_tokens=1024,
                    echo=False,
                )
                return response["choices"][0]["text"]
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"GGUF chat failed after {self.max_retries} retries: {last_error}")

    def stream(self, messages: list[dict]) -> Iterator[str]:
        """Stream chat response with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                prompt = self._format_messages(messages)
                response = self.model(
                    prompt,
                    max_tokens=1024,
                    echo=False,
                    stream=True,
                )
                for chunk in response:
                    if chunk["choices"][0]["text"]:
                        yield chunk["choices"][0]["text"]
                return
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        raise RuntimeError(f"GGUF stream failed after {self.max_retries} retries: {last_error}")

    def embed(self, text: str) -> list[float]:
        """Generate embeddings - GGUF models don't typically support this."""
        raise NotImplementedError("GGUF models don't support embeddings via llama-cpp-python")

    def _format_messages(self, messages: list[dict]) -> str:
        """Convert messages to prompt format."""
        formatted = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                formatted.append(f"System: {content}")
            elif role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")
        formatted.append("Assistant:")
        return "\n".join(formatted)