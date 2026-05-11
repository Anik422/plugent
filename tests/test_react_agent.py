"""Tests for ReactAgent."""

import json
import pytest
from unittest.mock import MagicMock

from plugent.core import ReactAgent


class TestReactAgent:
    """Test ReactAgent functionality."""

    def test_agent_creation(self, mock_llm, sample_skills):
        """Test creating a ReactAgent."""
        agent = ReactAgent(
            llm=mock_llm,
            skills=sample_skills,
        )

        assert agent.llm is not None
        assert len(agent.skills) == 2
        assert "order_lookup" in agent.skills

    def test_agent_with_custom_skills(self, mock_llm, sample_skills):
        """Test agent accepts custom skills."""
        def custom_func(x: str) -> str:
            return f"Custom: {x}"

        agent = ReactAgent(
            llm=mock_llm,
            skills=sample_skills,
            custom_skills=[custom_func],
        )

        assert len(agent.skills) >= 2

    def test_agent_with_knowledge(self, mock_llm, sample_skills, vector_store):
        """Test agent with knowledge store."""
        agent = ReactAgent(
            llm=mock_llm,
            skills=sample_skills,
            knowledge=vector_store,
        )

        assert agent.knowledge is not None

    def test_agent_with_company_config(self, mock_llm, sample_skills, company_config):
        """Test agent with company config."""
        agent = ReactAgent(
            llm=mock_llm,
            skills=sample_skills,
            company_config=company_config,
        )

        assert agent.company_config.name == "Test Corp"
        assert agent.company_config.domain == "ecommerce"

    def test_think_returns_string(self, mock_llm, sample_skills):
        """Test think method returns a string."""
        agent = ReactAgent(llm=mock_llm, skills=sample_skills)

        # Mock LLM to return a final answer
        mock_llm.chat.return_value = json.dumps({
            "thought": "I should provide the answer",
            "action": "final_answer",
            "action_input": {"answer": "Hello, user!"}
        })

        result = agent.think("Hello")

        assert isinstance(result, str)

    def test_think_with_history(self, mock_llm, sample_skills):
        """Test think method uses history."""
        agent = ReactAgent(llm=mock_llm, skills=sample_skills)

        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        mock_llm.chat.return_value = json.dumps({
            "thought": "Final answer",
            "action": "final_answer",
            "action_input": {"answer": "Done"}
        })

        result = agent.think("New question", history=history)

        # Verify chat was called with history
        call_args = mock_llm.chat.call_args[0][0]
        assert len(call_args) > 3  # system + history + user

    def test_react_loop_max_steps(self, mock_llm, sample_skills):
        """Test ReAct loop respects max steps."""
        agent = ReactAgent(
            llm=mock_llm,
            skills=sample_skills,
            agent_config={"max_steps": 3},
        )

        # Mock LLM to keep returning non-final actions
        mock_llm.chat.return_value = json.dumps({
            "thought": "Thinking...",
            "action": "order_lookup",
            "action_input": {"order_id": "123"}
        })

        result = agent.think("Test")

        # Should return after max steps
        assert isinstance(result, str)

    def test_execute_skill_action(self, mock_llm, sample_skills):
        """Test executing a skill action."""
        agent = ReactAgent(llm=mock_llm, skills=sample_skills)

        # Mock LLM to call a skill
        mock_llm.chat.return_value = json.dumps({
            "thought": "Looking up order",
            "action": "order_lookup",
            "action_input": {"order_id": "123"}
        })

        # The second call returns final answer
        mock_llm.chat.return_value += "\n" + json.dumps({
            "thought": "Found it",
            "action": "final_answer",
            "action_input": {"answer": "Order 123: pending"}
        })

        # Since skill returns on first call, we need different mock
        # Let's test action execution directly
        observation = agent._execute_action("order_lookup", {"order_id": "123"})

        assert "Order 123" in observation or "pending" in observation

    def test_execute_knowledge_action(self, mock_llm, sample_skills, vector_store):
        """Test executing knowledge search."""
        # Set up mock LLM for embeddings
        mock_llm.embed.return_value = [0.1] * 384

        agent = ReactAgent(
            llm=mock_llm,
            skills=sample_skills,
            knowledge=vector_store,
        )

        # First add some documents
        vector_store.set_llm(mock_llm)
        vector_store.add_documents([
            {"id": "1", "text": "Test document about products", "metadata": {}}
        ], "test")

        # Search
        observation = agent._execute_action("knowledge", {
            "query": "products",
            "collection": "test",
            "n": 3
        })

        assert isinstance(observation, str)

    def test_unknown_action(self, mock_llm, sample_skills):
        """Test handling unknown action."""
        agent = ReactAgent(llm=mock_llm, skills=sample_skills)

        observation = agent._execute_action("nonexistent", {})

        assert "Unknown action" in observation

    def test_error_handling(self, mock_llm, sample_skills):
        """Test graceful error handling."""
        agent = ReactAgent(llm=mock_llm, skills=sample_skills)

        # Mock LLM to return malformed JSON
        mock_llm.chat.return_value = "not valid json at all"

        result = agent.think("Test")

        # Should still return something
        assert isinstance(result, str)

    def test_system_prompt_contains_skills(self, mock_llm, sample_skills):
        """Test system prompt includes skill information."""
        agent = ReactAgent(llm=mock_llm, skills=sample_skills)

        assert "order_lookup" in agent._system_prompt
        assert "user_lookup" in agent._system_prompt


class TestReactAgentEdgeCases:
    """Edge case tests for ReactAgent."""

    def test_empty_skills(self, mock_llm):
        """Test agent with no skills."""
        agent = ReactAgent(llm=mock_llm, skills=[])

        assert len(agent.skills) == 0

    def test_none_skills(self, mock_llm):
        """Test agent with None skills."""
        agent = ReactAgent(llm=mock_llm, skills=None)

        assert len(agent.skills) == 0

    def test_no_knowledge(self, mock_llm, sample_skills):
        """Test agent without knowledge store."""
        agent = ReactAgent(llm=mock_llm, skills=sample_skills, knowledge=None)

        assert agent.knowledge is None

    def test_empty_message(self, mock_llm, sample_skills):
        """Test handling empty message."""
        agent = ReactAgent(llm=mock_llm, skills=sample_skills)

        mock_llm.chat.return_value = json.dumps({
            "thought": "Done",
            "action": "final_answer",
            "action_input": {"answer": "OK"}
        })

        result = agent.think("")

        assert isinstance(result, str)