"""LLM providers for plugent."""

from plugent.llm.base import BaseLLM, Message
from plugent.llm.openai_provider import OpenAILLM
from plugent.llm.anthropic_provider import AnthropicLLM
from plugent.llm.gemini_provider import GeminiLLM
from plugent.llm.groq_provider import GroqLLM
from plugent.llm.ollama_provider import OllamaLLM
from plugent.llm.lmstudio_provider import LMStudioLLM
from plugent.llm.together_provider import TogetherLLM
from plugent.llm.cohere_provider import CohereLLM
from plugent.llm.opencode_provider import OpenCodeLLM

# Optional imports for GGUF (requires llama-cpp-python)
try:
    from plugent.llm.gguf_provider import GGUF_LLM
except ImportError:
    GGUF_LLM = None

from plugent.llm.router import get_llm, list_providers, test_connection

__all__ = [
    "BaseLLM",
    "Message",
    "OpenAILLM",
    "AnthropicLLM",
    "GeminiLLM",
    "GroqLLM",
    "OllamaLLM",
    "GGUF_LLM",
    "LMStudioLLM",
    "TogetherLLM",
    "CohereLLM",
    "OpenCodeLLM",
    "get_llm",
    "list_providers",
    "test_connection",
]