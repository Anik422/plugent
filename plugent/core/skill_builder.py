"""Skill builder for plugent - generates SQL-based skills dynamically."""

import os
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from plugent.db.schema_parser import SchemaInfo, to_prompt_string
from plugent.core.business_detector import BusinessContext
from plugent.db.sql_connector import SQLConnector
from plugent.llm.base import BaseLLM


@dataclass
class Skill:
    """Executable skill with SQL backend."""

    name: str
    description: str
    parameters: list[dict] = field(default_factory=list)
    sql_template: str = ""
    _execute_fn: Callable | None = field(default=None, repr=False)

    def execute(self, **kwargs) -> str:
        """Execute skill with provided parameters."""
        if self._execute_fn:
            return self._execute_fn(**kwargs)
        raise NotImplementedError("Skill not properly initialized")


class SkillBuilder:
    """Build skills from business context using LLM."""

    def __init__(self, output_dir: str = None):
        """Initialize skill builder.

        Args:
            output_dir: Directory to save generated skill files.
        """
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(__file__),
                "..",
                "skills",
                "generated",
            )
        self.output_dir = output_dir

    def build(
        self,
        schema: SchemaInfo,
        business: BusinessContext,
        connector: SQLConnector,
        llm: BaseLLM,
    ) -> list[Skill]:
        """Build skills from schema and business context.

        Args:
            schema: Database schema.
            business: Detected business context.
            connector: SQLConnector for executing queries.
            llm: LLM for generating SQL templates.

        Returns:
            List of generated Skill objects.
        """
        skills = []

        for skill_name in business.suggested_skills:
            skill = self._build_single_skill(
                skill_name, schema, business, connector, llm
            )
            if skill:
                skills.append(skill)
                self._save_skill(skill)

        return skills

    def _build_single_skill(
        self,
        skill_name: str,
        schema: SchemaInfo,
        business: BusinessContext,
        connector: SQLConnector,
        llm: BaseLLM,
    ) -> Skill | None:
        """Build a single skill using LLM."""
        from plugent.db.schema_parser import to_prompt_string

        schema_str = to_prompt_string(schema)

        prompt = f'''Generate a SQL-based skill for: "{skill_name}"

Business Type: {business.business_type}
Key Entities: {json.dumps(business.key_entities, indent=2)}

Schema:
{schema_str}

Respond with JSON only:
{{
  "name": "skill_name",
  "description": "what this skill does",
  "parameters": [
    {{"name": "param_name", "type": "string", "description": "what this param does"}}
  ],
  "sql_template": "SELECT ... WHERE param = :param_name"
}}
'''

        try:
            messages = [{"role": "user", "content": prompt}]
            response = llm.chat(messages)

            # Parse JSON response
            data = json.loads(self._extract_json(response))

            skill = Skill(
                name=data.get("name", skill_name),
                description=data.get("description", ""),
                parameters=data.get("parameters", []),
                sql_template=data.get("sql_template", ""),
            )

            # Create execute function
            skill._execute_fn = self._create_execute_fn(skill, connector)

            return skill

        except Exception as e:
            # Fallback: create basic skill
            return Skill(
                name=skill_name,
                description=f"Skill for {skill_name}",
                parameters=[],
                sql_template="",
            )

    def _create_execute_fn(
        self, skill: Skill, connector: SQLConnector
    ) -> Callable:
        """Create execution function for skill."""
        template = skill.sql_template

        def execute_fn(**kwargs) -> str:
            try:
                # Replace placeholders with values
                query = template
                for key, value in kwargs.items():
                    query = query.replace(f":{key}", f"'{value}'")

                # Execute query
                results = connector.execute_query(query)

                # Format results
                if not results:
                    return "No results found."

                lines = [f"Found {len(results)} results:"]
                for row in results[:10]:  # Limit to 10 rows
                    lines.append(str(row))

                if len(results) > 10:
                    lines.append(f"... and {len(results) - 10} more rows")

                return "\n".join(lines)

            except Exception as e:
                return f"Error executing skill: {str(e)}"

        return execute_fn

    def _extract_json(self, response: str) -> str:
        """Extract JSON from LLM response."""
        import re

        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            return match.group()
        return response

    def _save_skill(self, skill: Skill) -> None:
        """Save skill metadata to file."""
        os.makedirs(self.output_dir, exist_ok=True)

        # Save as JSON
        filepath = os.path.join(self.output_dir, f"{skill.name}.json")
        data = {
            "name": skill.name,
            "description": skill.description,
            "parameters": skill.parameters,
            "sql_template": skill.sql_template,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load_skill(self, name: str, connector: SQLConnector) -> Skill | None:
        """Load a saved skill from file."""
        filepath = os.path.join(self.output_dir, f"{name}.json")

        if not os.path.exists(filepath):
            return None

        with open(filepath) as f:
            data = json.load(f)

        skill = Skill(
            name=data["name"],
            description=data.get("description", ""),
            parameters=data.get("parameters", []),
            sql_template=data.get("sql_template", ""),
        )

        skill._execute_fn = self._create_execute_fn(skill, connector)
        return skill