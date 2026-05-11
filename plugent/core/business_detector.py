"""Business context detector for plugent."""

import json
import re
from dataclasses import dataclass

from plugent.db.schema_parser import SchemaInfo
from plugent.llm.base import BaseLLM


@dataclass
class BusinessContext:
    """Detected business context from schema."""

    business_type: str
    key_entities: list[dict]
    suggested_skills: list[str]
    primary_language: str
    confidence: float


class BusinessDetector:
    """Detect business context from database schema using LLM."""

    PROMPT_TEMPLATE = '''Analyze this database schema and identify the business domain.

Schema:
{schema}

Respond with JSON only (no other text):
{{
  "business_type": "one of: ecommerce, restaurant, hospital, saas, crm, accounting, inventory, logistics, education, social_media, or other",
  "key_entities": [
    {{"table": "table_name", "description": "what this entity represents"}}
  ],
  "suggested_skills": [
    "skill_name1", "skill_name2"
  ],
  "primary_language": "detected language from table/column names (en/zh/es/ja/etc)",
  "confidence": 0.0-1.0
}}
'''

    def __init__(self):
        pass

    def detect(self, schema: SchemaInfo, llm: BaseLLM) -> BusinessContext:
        """Detect business context from schema.

        Args:
            schema: SchemaInfo from SchemaParser.
            llm: BaseLLM instance for inference.

        Returns:
            BusinessContext with detected information.
        """
        from plugent.db.schema_parser import to_prompt_string

        schema_str = to_prompt_string(schema)
        prompt = self.PROMPT_TEMPLATE.format(schema=schema_str)

        messages = [{"role": "user", "content": prompt}]
        response = llm.chat(messages)

        return self._parse_response(response)

    def _parse_response(self, response: str) -> BusinessContext:
        """Parse LLM JSON response into BusinessContext."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            return BusinessContext(
                business_type=data.get("business_type", "other"),
                key_entities=data.get("key_entities", []),
                suggested_skills=data.get("suggested_skills", []),
                primary_language=data.get("primary_language", "en"),
                confidence=data.get("confidence", 0.5),
            )
        except (json.JSONDecodeError, KeyError):
            # Fallback on parse failure
            return BusinessContext(
                business_type="unknown",
                key_entities=[],
                suggested_skills=[],
                primary_language="en",
                confidence=0.0,
            )