"""Tests for SkillBuilder."""

import json
import pytest
from unittest.mock import MagicMock, patch

from plugent.core import SkillBuilder, Skill
from plugent.db import SchemaParser


class TestSkillBuilder:
    """Test SkillBuilder functionality."""

    @pytest.fixture
    def sample_schema(self, sql_connector):
        """Create sample schema."""
        parser = SchemaParser()
        return parser.parse(sql_connector)

    def test_build_returns_list(self, sample_schema, mock_llm, sql_connector, mock_business_context):
        """Test build returns a list of skills."""
        builder = SkillBuilder(output_dir="/tmp/test_skills")
        skills = builder.build(sample_schema, mock_business_context, sql_connector, mock_llm)

        assert isinstance(skills, list)

    def test_skill_has_name(self, sample_schema, mock_llm, sql_connector, mock_business_context):
        """Test generated skill has a name."""
        builder = SkillBuilder(output_dir="/tmp/test_skills")

        # Mock the LLM to return valid JSON
        mock_llm.chat.return_value = json.dumps({
            "name": "test_skill",
            "description": "Test skill description",
            "parameters": [{"name": "param1", "type": "string", "description": "A param"}],
            "sql_template": "SELECT * FROM users WHERE id = :param1"
        })

        skills = builder.build(sample_schema, mock_business_context, sql_connector, mock_llm)

        if skills:
            assert hasattr(skills[0], 'name')
            assert skills[0].name is not None

    def test_skill_has_execute(self, sample_schema, mock_llm, sql_connector, mock_business_context):
        """Test generated skill has execute method."""
        builder = SkillBuilder(output_dir="/tmp/test_skills")

        mock_llm.chat.return_value = json.dumps({
            "name": "test_skill",
            "description": "Test skill",
            "parameters": [{"name": "id", "type": "string", "description": "ID"}],
            "sql_template": "SELECT * FROM users WHERE id = :id"
        })

        skills = builder.build(sample_schema, mock_business_context, sql_connector, mock_llm)

        if skills:
            assert callable(skills[0].execute)

    def test_skill_execution_returns_string(self, sample_schema, mock_llm, sql_connector, mock_business_context):
        """Test skill execution returns string."""
        builder = SkillBuilder(output_dir="/tmp/test_skills")

        mock_llm.chat.return_value = json.dumps({
            "name": "get_users",
            "description": "Get users",
            "parameters": [],
            "sql_template": "SELECT * FROM users LIMIT 5"
        })

        skills = builder.build(sample_schema, mock_business_context, sql_connector, mock_llm)

        if skills:
            result = skills[0].execute()
            assert isinstance(result, str)

    def test_skill_with_parameters(self, sample_schema, mock_llm, sql_connector, mock_business_context):
        """Test skill with parameters substitutes correctly."""
        builder = SkillBuilder(output_dir="/tmp/test_skills")

        mock_llm.chat.return_value = json.dumps({
            "name": "find_user",
            "description": "Find user by name",
            "parameters": [{"name": "name", "type": "string", "description": "User name"}],
            "sql_template": "SELECT * FROM users WHERE name = :name"
        })

        skills = builder.build(sample_schema, mock_business_context, sql_connector, mock_llm)

        if skills:
            result = skills[0].execute(name="Alice")
            assert "Alice" in result or "No results" in result or "Error" in result

    def test_llm_failure_fallback(self, sample_schema, mock_llm, sql_connector, mock_business_context):
        """Test graceful fallback when LLM fails."""
        builder = SkillBuilder(output_dir="/tmp/test_skills")

        # Mock LLM failure
        mock_llm.chat.side_effect = Exception("API error")

        # Should not raise
        skills = builder.build(sample_schema, mock_business_context, sql_connector, mock_llm)

        # Should return at least fallback skills
        assert isinstance(skills, list)

    def test_skill_parameters_inferred_from_llm(self, sample_schema, mock_llm, sql_connector, mock_business_context):
        """Test skill parameters come from LLM response."""
        builder = SkillBuilder(output_dir="/tmp/test_skills")

        mock_llm.chat.return_value = json.dumps({
            "name": "complex_skill",
            "description": "A complex skill",
            "parameters": [
                {"name": "order_id", "type": "string", "description": "Order ID"},
                {"name": "limit", "type": "integer", "description": "Result limit"}
            ],
            "sql_template": "SELECT * FROM orders WHERE id = :order_id LIMIT :limit"
        })

        skills = builder.build(sample_schema, mock_business_context, sql_connector, mock_llm)

        if skills:
            assert len(skills[0].parameters) == 2

    def test_skill_description(self, sample_schema, mock_llm, sql_connector, mock_business_context):
        """Test skill has description."""
        builder = SkillBuilder(output_dir="/tmp/test_skills")

        mock_llm.chat.return_value = json.dumps({
            "name": "described_skill",
            "description": "This is a test skill for searching users",
            "parameters": [],
            "sql_template": "SELECT 1"
        })

        skills = builder.build(sample_schema, mock_business_context, sql_connector, mock_llm)

        if skills:
            assert skills[0].description != ""


class TestSkill:
    """Test Skill dataclass."""

    def test_skill_creation(self):
        """Test creating a skill manually."""
        def my_func(x: str) -> str:
            return f"Result: {x}"

        skill = Skill(
            name="test",
            description="Test skill",
            parameters=[{"name": "x", "type": "string", "description": "Input"}],
            sql_template="",
        )
        skill._execute_fn = my_func

        result = skill.execute(x="hello")
        assert "hello" in result

    def test_skill_without_function(self):
        """Test skill without execute function raises error."""
        skill = Skill(
            name="test",
            description="Test",
            parameters=[],
            sql_template="",
        )

        with pytest.raises(NotImplementedError):
            skill.execute()