"""Conversation memory for plugent - supports in-memory and Redis."""

import json
from dataclasses import dataclass
from typing import Any

from plugent.llm.base import BaseLLM


@dataclass
class Message:
    """Conversation message."""

    role: str
    content: str
    timestamp: float | None = None


class ConversationMemory:
    """Conversation memory with in-memory or Redis backend."""

    MAX_MESSAGES = 20

    def __init__(self, redis_url: str | None = None):
        """Initialize memory.

        Args:
            redis_url: Optional Redis URL for persistence.
        """
        self._redis_url = redis_url
        self._redis = None
        self._memory: dict[str, list[dict]] = {}

        if redis_url:
            self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
            self._redis.ping()
        except Exception:
            self._redis = None

    def add(self, session_id: str, role: str, content: str) -> None:
        """Add message to session history.

        Args:
            session_id: Session identifier.
            role: Message role (user/assistant/system).
            content: Message content.
        """
        # Get existing history
        history = self.get_history(session_id)

        # Add new message
        history.append({"role": role, "content": content})

        # Trim if exceeds limit
        if len(history) > self.MAX_MESSAGES:
            # Keep last MAX_MESSAGES, summarize older
            recent = history[-self.MAX_MESSAGES:]
            older = history[:-self.MAX_MESSAGES]

            # Store recent directly
            if self._redis:
                self._redis.set(
                    f"memory:{session_id}",
                    json.dumps(recent),
                )
            else:
                self._memory[session_id] = recent

            # Store summary of older messages separately
            # (caller should call get_summary and store it)
        else:
            if self._redis:
                self._redis.set(
                    f"memory:{session_id}",
                    json.dumps(history),
                )
            else:
                self._memory[session_id] = history

    def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for session.

        Args:
            session_id: Session identifier.

        Returns:
            List of message dicts with role and content.
        """
        if self._redis:
            data = self._redis.get(f"memory:{session_id}")
            if data:
                return json.loads(data)
            return []

        return self._memory.get(session_id, [])

    def clear(self, session_id: str) -> None:
        """Clear session history.

        Args:
            session_id: Session identifier.
        """
        if self._redis:
            self._redis.delete(f"memory:{session_id}")
            self._redis.delete(f"summary:{session_id}")
        else:
            self._memory.pop(session_id, None)

    def get_summary(self, session_id: str, llm: BaseLLM) -> str:
        """Get or generate summary of older messages.

        Args:
            session_id: Session identifier.
            llm: LLM for generating summary.

        Returns:
            Summary string.
        """
        # Check for existing summary
        if self._redis:
            summary = self._redis.get(f"summary:{session_id}")
            if summary:
                return summary
        else:
            # Check memory for summary
            pass

        # Generate summary from older messages
        history = self.get_history(session_id)
        if len(history) <= self.MAX_MESSAGES:
            return "No previous conversation."

        older = history[:-self.MAX_MESSAGES]
        prompt = f"""Summarize this conversation concisely:

{self._format_messages(older)}

Provide a 2-3 sentence summary of key topics and any important information."""

        try:
            summary = llm.chat([{"role": "user", "content": prompt}])

            # Store summary
            if self._redis:
                self._redis.set(f"summary:{session_id}", summary)

            return summary
        except Exception:
            return "Previous conversation summary unavailable."

    def _format_messages(self, messages: list[dict]) -> str:
        """Format messages for summary."""
        lines = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"{role}: {content[:200]}")
        return "\n".join(lines)

    def get_recent(self, session_id: str, n: int = 10) -> list[dict]:
        """Get recent N messages.

        Args:
            session_id: Session identifier.
            n: Number of recent messages.

        Returns:
            List of recent message dicts.
        """
        history = self.get_history(session_id)
        return history[-n:] if len(history) > n else history

    def list_sessions(self) -> list[str]:
        """List all active session IDs.

        Returns:
            List of session IDs.
        """
        if self._redis:
            keys = self._redis.keys("memory:*")
            return [k.replace("memory:", "") for k in keys]
        return list(self._memory.keys())