"""Base LLM classes for plugent."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator


@dataclass
class Message:
    """Chat message."""

    role: str
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(role=data["role"], content=data["content"])


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        """Send chat messages and get response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Returns:
            Response content as string.
        """
        raise NotImplementedError

    @abstractmethod
    def stream(self, messages: list[dict]) -> Iterator[str]:
        """Stream chat response token by token.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Yields:
            Response chunks as strings.
        """
        raise NotImplementedError

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Input text to embed.

        Returns:
            List of embedding floats.
        """
        raise NotImplementedError