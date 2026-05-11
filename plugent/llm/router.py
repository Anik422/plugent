"""LLM provider router for plugent."""

from typing import Any

from plugent.llm.base import BaseLLM
from plugent.llm import (
    OpenAILLM,
    AnthropicLLM,
    GeminiLLM,
    GroqLLM,
    OllamaLLM,
    GGUF_LLM,
    LMStudioLLM,
    TogetherLLM,
    CohereLLM,
    OpenCodeLLM,
)


PROVIDER_CONFIG = {
    "openai": {
        "class": OpenAILLM,
        "required": ["api_key"],
        "optional": ["model"],
        "default_model": "gpt-4o-mini",
    },
    "anthropic": {
        "class": AnthropicLLM,
        "required": ["api_key"],
        "optional": ["model"],
        "default_model": "claude-3-haiku-20240307",
    },
    "gemini": {
        "class": GeminiLLM,
        "required": ["api_key"],
        "optional": ["model"],
        "default_model": "gemini-1.5-flash",
    },
    "groq": {
        "class": GroqLLM,
        "required": ["api_key"],
        "optional": ["model"],
        "default_model": "llama-3.1-70b-versatile",
    },
    "ollama": {
        "class": OllamaLLM,
        "required": [],
        "optional": ["model", "base_url"],
        "default_model": "llama3.1",
        "default_base_url": "http://localhost:11434",
    },
    "lmstudio": {
        "class": LMStudioLLM,
        "required": [],
        "optional": ["model", "base_url", "api_key"],
        "default_model": "llama-3.1-8b",
        "default_base_url": "http://localhost:1234/v1",
    },
    "together": {
        "class": TogetherLLM,
        "required": ["api_key"],
        "optional": ["model"],
        "default_model": "meta-llama/Llama-3.1-8B-Instruct-Turbo",
    },
    "cohere": {
        "class": CohereLLM,
        "required": ["api_key"],
        "optional": ["model"],
        "default_model": "command-r-plus-08-2024",
    },
    "opencode": {
        "class": OpenCodeLLM,
        "required": ["api_key"],
        "optional": ["model", "base_url"],
        "default_model": "gpt-4o",
        "default_base_url": "https://opencode.ai/v1",
    },
}

# Add GGUF provider only if llama-cpp-python is available
if GGUF_LLM is not None:
    PROVIDER_CONFIG["gguf"] = {
        "class": GGUF_LLM,
        "required": ["model_path"],
        "optional": ["n_gpu_layers", "n_ctx", "model"],
        "default_model": "llama",
    }


def get_llm(config: dict) -> BaseLLM:
    """Create LLM provider from config dict.

    Args:
        config: Dict with "provider" key and provider-specific params.

    Returns:
        BaseLLM instance.

    Raises:
        ValueError: If provider unknown or required key missing.
    """
    provider = config.get("provider", "").lower()
    if not provider:
        raise ValueError("Config must include 'provider' key")
    if provider not in PROVIDER_CONFIG:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(PROVIDER_CONFIG.keys())}")

    cfg = PROVIDER_CONFIG[provider]
    kwargs = {k: v for k, v in config.items() if k != "provider"}

    # Apply defaults
    if "default_model" in cfg and "model" not in kwargs:
        kwargs["model"] = cfg["default_model"]
    if "default_base_url" in cfg and "base_url" not in kwargs:
        kwargs["base_url"] = cfg["default_base_url"]

    # Check required keys
    missing = [k for k in cfg["required"] if k not in kwargs]
    if missing:
        raise ValueError(f"Provider '{provider}' requires: {missing}")

    return cfg["class"](**kwargs)


def list_providers() -> dict[str, dict[str, Any]]:
    """Return all available providers with their config schema.

    Returns:
        Dict mapping provider name to config schema.
    """
    return {
        name: {
            "required": cfg["required"],
            "optional": cfg["optional"],
            "default_model": cfg.get("default_model"),
        }
        for name, cfg in PROVIDER_CONFIG.items()
    }


def test_connection(llm: BaseLLM) -> bool:
    """Test LLM connection with a simple prompt.

    Args:
        llm: BaseLLM instance to test.

    Returns:
        True if connection successful, False otherwise.
    """
    try:
        messages = [{"role": "user", "content": "Hi"}]
        response = llm.chat(messages)
        return bool(response) or True
    except Exception:
        return False