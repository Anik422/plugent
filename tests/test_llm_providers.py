"""Tests for LLM providers."""

import pytest
from unittest.mock import MagicMock, patch


class TestOpenAIProvider:
    """Test OpenAI provider."""

    def test_init(self):
        """Test OpenAI provider initialization."""
        from plugent.llm import OpenAILLM

        llm = OpenAILLM(api_key="sk-test", model="gpt-4")

        assert llm.model == "gpt-4"

    def test_chat_message_format(self):
        """Test chat messages are formatted correctly."""
        from plugent.llm import OpenAILLM

        llm = OpenAILLM(api_key="sk-test")

        with patch.object(llm.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="test response"))]
            )

            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"}
            ]

            result = llm.chat(messages)

            # Verify the call was made with correct format
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs['model'] == "gpt-4o-mini"
            assert len(call_kwargs['messages']) == 2

    def test_embed(self):
        """Test embedding generation."""
        from plugent.llm import OpenAILLM

        llm = OpenAILLM(api_key="sk-test")

        with patch.object(llm.client.embeddings, 'create') as mock_create:
            mock_create.return_value = MagicMock(
                data=[MagicMock(embedding=[0.1, 0.2, 0.3])]
            )

            result = llm.embed("test text")

            assert len(result) == 3

    def test_retry_logic(self):
        """Test retry on failure."""
        from plugent.llm import OpenAILLM

        llm = OpenAILLM(api_key="sk-test", max_retries=3)

        with patch.object(llm.client.chat.completions, 'create') as mock_create:
            # Fail twice, then succeed
            mock_create.side_effect = [
                Exception("Network error"),
                Exception("Network error"),
                MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))])
            ]

            result = llm.chat([{"role": "user", "content": "test"}])
            assert mock_create.call_count == 3


class TestAnthropicProvider:
    """Test Anthropic provider."""

    def test_init(self):
        """Test Anthropic provider initialization."""
        from plugent.llm import AnthropicLLM

        llm = AnthropicLLM(api_key="sk-ant-test", model="claude-3")

        assert llm.model == "claude-3"

    def test_chat_message_format(self):
        """Test Anthropic message format."""
        from plugent.llm import AnthropicLLM

        llm = AnthropicLLM(api_key="sk-ant-test")

        with patch.object(llm.client.messages, 'create') as mock_create:
            mock_create.return_value = MagicMock(
                content=[MagicMock(text="response")]
            )

            messages = [
                {"role": "user", "content": "Hello"}
            ]

            result = llm.chat(messages)

            call_kwargs = mock_create.call_args[1]
            assert 'messages' in call_kwargs
            assert call_kwargs['max_tokens'] == 1024

    def test_embed_not_supported(self):
        """Test that Anthropic doesn't support embeddings."""
        from plugent.llm import AnthropicLLM

        llm = AnthropicLLM(api_key="sk-ant-test")

        with pytest.raises(NotImplementedError):
            llm.embed("test")


class TestGeminiProvider:
    """Test Gemini provider."""

    def test_init(self):
        """Test Gemini provider initialization."""
        from plugent.llm import GeminiLLM

        llm = GeminiLLM(api_key="test-key", model="gemini-pro")

        assert llm.model_name == "gemini-pro"

    def test_chat(self):
        """Test Gemini chat."""
        from plugent.llm import GeminiLLM

        llm = GeminiLLM(api_key="test-key")

        with patch.object(llm._client.models, 'generate_content') as mock_generate:
            mock_response = MagicMock()
            mock_response.text = "response"
            mock_generate.return_value = mock_response

            result = llm.chat([{"role": "user", "content": "Hi"}])

            assert "response" in result

    def test_embed(self):
        """Test Gemini embeddings."""
        from plugent.llm import GeminiLLM

        llm = GeminiLLM(api_key="test-key")

        with patch.object(llm._client.models, 'embed_content') as mock_embed:
            mock_response = MagicMock()
            mock_response.embedding = [0.1, 0.2]
            mock_embed.return_value = mock_response

            result = llm.embed("test")

            assert len(result) == 2


class TestGroqProvider:
    """Test Groq provider."""

    def test_init(self):
        """Test Groq provider initialization."""
        from plugent.llm import GroqLLM

        llm = GroqLLM(api_key="gsk_test", model="llama-3")

        assert llm.model == "llama-3"

    def test_chat(self):
        """Test Groq chat."""
        from plugent.llm import GroqLLM

        llm = GroqLLM(api_key="gsk_test")

        with patch.object(llm.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Groq response"))]
            )

            result = llm.chat([{"role": "user", "content": "Hi"}])

            assert "Groq response" in result


class TestOllamaProvider:
    """Test Ollama provider."""

    def test_init(self):
        """Test Ollama initialization."""
        from plugent.llm import OllamaLLM

        llm = OllamaLLM(model="llama3", base_url="http://localhost:11434")

        assert llm.model == "llama3"
        assert llm.base_url == "http://localhost:11434"

    def test_chat(self):
        """Test Ollama chat."""
        from plugent.llm import OllamaLLM

        llm = OllamaLLM()

        with patch.object(llm.client, 'chat') as mock_chat:
            mock_chat.return_value = {"message": {"content": "Ollama response"}}

            result = llm.chat([{"role": "user", "content": "Hi"}])

            assert "Ollama response" in result

    def test_embed(self):
        """Test Ollama embeddings."""
        from plugent.llm import OllamaLLM

        llm = OllamaLLM()

        with patch.object(llm.client, 'embeddings') as mock_embed:
            mock_embed.return_value = {"embedding": [0.1, 0.2]}

            result = llm.embed("test")

            assert len(result) == 2


class TestOpenCodeProvider:
    """Test OpenCode Zen provider."""

    def test_init(self):
        """Test OpenCode provider initialization."""
        from plugent.llm import OpenCodeLLM

        llm = OpenCodeLLM(api_key="test-key", model="gpt-4o")

        assert llm.model == "gpt-4o"

    def test_chat(self):
        """Test OpenCode chat."""
        from plugent.llm import OpenCodeLLM

        llm = OpenCodeLLM(api_key="test-key")

        with patch.object(llm.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="OpenCode response"))]
            )

            result = llm.chat([{"role": "user", "content": "Hi"}])

            assert "OpenCode response" in result


class TestGGUFProvider:
    """Test GGUF provider."""

    def test_init(self):
        """Test GGUF initialization."""
        from plugent.llm import GGUF_LLM

        if GGUF_LLM is None:
            pytest.skip("llama-cpp-python not installed")

        with patch('plugent.llm.gguf_provider.Llama'):
            llm = GGUF_LLM(
                model_path="/tmp/model.gguf",
                n_gpu_layers=32,
            )

            assert llm.model_path == "/tmp/model.gguf"

    def test_embed_not_supported(self):
        """Test GGUF doesn't support embeddings."""
        from plugent.llm import GGUF_LLM

        if GGUF_LLM is None:
            pytest.skip("llama-cpp-python not installed")

        with patch('plugent.llm.gguf_provider.Llama'):
            llm = GGUF_LLM(model_path="/tmp/test.gguf")

            with pytest.raises(NotImplementedError):
                llm.embed("test")


class TestRouter:
    """Test LLM router."""

    def test_get_llm_openai(self):
        """Test router creates OpenAI."""
        from plugent.llm import get_llm

        llm = get_llm({"provider": "openai", "api_key": "sk-test"})

        assert llm.__class__.__name__ == "OpenAILLM"

    def test_get_llm_anthropic(self):
        """Test router creates Anthropic."""
        from plugent.llm import get_llm

        llm = get_llm({"provider": "anthropic", "api_key": "sk-ant-test"})

        assert llm.__class__.__name__ == "AnthropicLLM"

    def test_get_llm_ollama(self):
        """Test router creates Ollama."""
        from plugent.llm import get_llm

        llm = get_llm({"provider": "ollama"})

        assert llm.__class__.__name__ == "OllamaLLM"

    def test_get_llm_opencode(self):
        """Test router creates OpenCode."""
        from plugent.llm import get_llm

        llm = get_llm({"provider": "opencode", "api_key": "test-key"})

        assert llm.__class__.__name__ == "OpenCodeLLM"

    def test_get_llm_unknown(self):
        """Test router raises on unknown provider."""
        from plugent.llm import get_llm

        with pytest.raises(ValueError, match="Unknown provider"):
            get_llm({"provider": "unknown"})

    def test_get_llm_missing_provider(self):
        """Test router raises when provider missing."""
        from plugent.llm import get_llm

        with pytest.raises(ValueError, match="provider"):
            get_llm({})

    def test_list_providers(self):
        """Test listing providers."""
        from plugent.llm import list_providers

        providers = list_providers()

        assert "openai" in providers
        assert "anthropic" in providers
        assert "ollama" in providers
        assert "opencode" in providers

    def test_test_connection(self):
        """Test connection testing."""
        from plugent.llm import test_connection, OpenAILLM

        llm = OpenAILLM(api_key="sk-test")

        # Mock to return valid response
        with patch.object(llm, 'chat', return_value="OK"):
            result = test_connection(llm)
            assert result is True

    def test_test_connection_failure(self):
        """Test connection test failure."""
        from plugent.llm import test_connection, OpenAILLM

        llm = OpenAILLM(api_key="sk-test")

        # Mock to raise exception
        with patch.object(llm, 'chat', side_effect=Exception("Error")):
            result = test_connection(llm)
            assert result is False


class TestMessage:
    """Test Message dataclass."""

    def test_message_creation(self):
        """Test creating a message."""
        from plugent.llm import Message

        msg = Message(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_to_dict(self):
        """Test converting to dict."""
        from plugent.llm import Message

        msg = Message(role="user", content="Hello")
        d = msg.to_dict()

        assert d == {"role": "user", "content": "Hello"}

    def test_from_dict(self):
        """Test creating from dict."""
        from plugent.llm import Message

        msg = Message.from_dict({"role": "assistant", "content": "Hi"})

        assert msg.role == "assistant"
        assert msg.content == "Hi"