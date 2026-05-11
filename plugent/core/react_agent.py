"""ReAct agent implementation for plugent."""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from plugent.llm.base import BaseLLM
from plugent.core.skill_builder import Skill
from plugent.knowledge.vector_store import VectorStore


@dataclass
class Step:
    """Single ReAct step."""

    thought: str
    action: str | None = None
    action_input: dict | None = None
    observation: str | None = None


@dataclass
class AgentConfig:
    """Agent configuration."""

    max_steps: int = 5
    temperature: float = 0.7
    system_prompt_template: str = ""


@dataclass
class CompanyConfig:
    """Company/organization configuration."""

    name: str = ""
    description: str = ""
    domain: str = ""
    custom_instructions: str = ""


class ReactAgent:
    """ReAct (Reason + Act) agent implementation."""

    TOOL_SCHEMA = '''Available tools:
{skills}

Knowledge search: Use "knowledge" tool to search VectorStore.
Parameters: {{"query": "search text", "collection": "collection_name", "n": 5}}

Execute skill: Use skill name directly as tool.
Parameters: {{"param1": "value1", "param2": "value2"}}
'''

    SYSTEM_PROMPT_TEMPLATE = '''You are a helpful AI assistant for {company_name}.

Company: {company_description}
Domain: {company_domain}

{custom_instructions}

When responding:
1. Use the knowledge tool to find relevant information
2. Use available skills to perform actions
3. Think step by step (ReAct pattern)
4. Provide clear, actionable answers

{tool_schema}

Respond in the following JSON format for tool calls:
{{"thought": "your reasoning", "action": "tool_name", "action_input": {{"param": "value"}}}}

For final answer, respond:
{{"thought": "final reasoning", "action": "final_answer", "action_input": {{"answer": "your response"}}}}
'''

    def __init__(
        self,
        llm: BaseLLM,
        skills: list[Skill] | None = None,
        knowledge: VectorStore | None = None,
        company_config: dict | None = None,
        agent_config: dict | None = None,
        custom_skills: list[Callable] | None = None,
    ):
        """Initialize ReAct agent.

        Args:
            llm: BaseLLM instance.
            skills: List of auto-generated Skill objects from skill builder.
            knowledge: VectorStore for knowledge retrieval.
            company_config: Company configuration dict.
            agent_config: Agent configuration dict.
            custom_skills: List of @skill decorated functions to include.
        """
        self.llm = llm
        self.knowledge = knowledge

        # Build skills dict - start with auto-generated, add custom
        self.skills = {}

        # Add auto-generated skills
        if skills:
            for s in skills:
                self.skills[s.name] = s

        # Add custom @skill decorated functions
        if custom_skills:
            from plugent.skills.base_skill import get_skill, SkillWrapper
            for fn in custom_skills:
                # Get from registry by function name
                wrapper = get_skill(fn.__name__)
                if wrapper:
                    self.skills[wrapper.name] = wrapper.to_skill()
                else:
                    # Create inline wrapper for unregistered functions
                    import inspect
                    sig = inspect.signature(fn)
                    params = []
                    for p in sig.parameters:
                        params.append({"name": p, "type": "string", "description": ""})

                    inline_wrapper = SkillWrapper(
                        name=fn.__name__,
                        description=fn.__doc__.strip().split("\n")[0] if fn.__doc__ else "",
                        parameters=params,
                        func=fn,
                        is_custom=True,
                    )
                    self.skills[fn.__name__] = inline_wrapper.to_skill()

        # Parse configs
        self.company_config = CompanyConfig(
            **(company_config or {})
        )
        self.agent_config = AgentConfig(
            max_steps=agent_config.get("max_steps", 5) if agent_config else 5,
            temperature=agent_config.get("temperature", 0.7) if agent_config else 0.7,
        )

        # Build system prompt
        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build system prompt from configs."""
        # Format skills
        skills_desc = []
        for name, skill in self.skills.items():
            params = ", ".join(
                f"{p['name']}: {p.get('description', '')}"
                for p in skill.parameters
            )
            skills_desc.append(f"- {name}: {skill.description} (params: {params})")

        tool_schema = self.TOOL_SCHEMA.format(
            skills="\n".join(skills_desc) or "No skills available"
        )

        return self.SYSTEM_PROMPT_TEMPLATE.format(
            company_name=self.company_config.name or "the organization",
            company_description=self.company_config.description or "N/A",
            company_domain=self.company_config.domain or "general",
            custom_instructions=self.company_config.custom_instructions or "",
            tool_schema=tool_schema,
        )

    def think(
        self,
        user_message: str,
        history: list[dict] | None = None,
    ) -> str:
        """Run ReAct loop to process user message.

        Args:
            user_message: User's input message.
            history: Previous conversation history.

        Returns:
            Final answer string.
        """
        history = history or []
        steps: list[Step] = []

        # Build initial messages
        messages = [{"role": "system", "content": self._system_prompt}]

        # Add history
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})

        # Add user message with context
        context = self._get_relevant_context(user_message)
        enriched_message = user_message
        if context:
            enriched_message = f'''Relevant knowledge:
{context}

User question: {user_message}'''

        messages.append({"role": "user", "content": enriched_message})

        # ReAct loop
        for step_num in range(self.agent_config.max_steps):
            # Get LLM response
            response = self.llm.chat(messages)
            messages.append({"role": "assistant", "content": response})

            # Parse response
            parsed = self._parse_response(response)
            if not parsed:
                continue

            thought = parsed.get("thought", "")
            action = parsed.get("action")
            action_input = parsed.get("action_input", {})

            step = Step(thought=thought, action=action, action_input=action_input)
            steps.append(step)

            # Check for final answer
            if action == "final_answer":
                return action_input.get("answer", "No answer provided")

            # Execute action
            if action and action != "final_answer":
                observation = self._execute_action(action, action_input)
                step.observation = observation

                # Add observation to messages
                messages.append({
                    "role": "user",
                    "content": f"Observation: {observation}",
                })
            else:
                # No action specified, continue with thought
                messages.append({
                    "role": "user",
                    "content": f"Thought: {thought}. Continue reasoning.",
                })

        # Max steps reached, return last observation or error
        if steps and steps[-1].observation:
            return f"{steps[-1].thought}\n\nResult: {steps[-1].observation}"
        return "Maximum reasoning steps reached. Unable to complete."

    def _get_relevant_context(self, query: str) -> str:
        """Get relevant context from knowledge store."""
        if not self.knowledge:
            return ""

        try:
            results = self.knowledge.search(
                query=query,
                collection="db_knowledge",
                n=3,
            )
            if results:
                return "\n".join(r["text"] for r in results)
        except Exception:
            pass
        return ""

    def _parse_response(self, response: str) -> dict | None:
        """Parse JSON response from LLM."""
        try:
            # Try to extract JSON
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                data = json.loads(match.group())
                if "thought" in data:
                    return data
        except (json.JSONDecodeError, KeyError):
            pass

        # Fallback: try to parse as plain text with action
        return {"thought": response, "action": None, "action_input": {}}

    def _execute_action(self, action: str, action_input: dict) -> str:
        """Execute a tool/action.

        Args:
            action: Action/tool name.
            action_input: Parameters for the action.

        Returns:
            Observation/result string.
        """
        try:
            # Check for knowledge search
            if action == "knowledge":
                query = action_input.get("query", "")
                collection = action_input.get("collection", "db_knowledge")
                n = action_input.get("n", 5)

                if self.knowledge:
                    results = self.knowledge.search(query, collection, n)
                    if results:
                        return "\n".join(
                            f"- {r['text'][:200]}" for r in results
                        )
                return "No relevant knowledge found."

            # Check for skill
            if action in self.skills:
                skill = self.skills[action]
                result = skill.execute(**action_input)
                return result

            # Unknown action
            return f"Unknown action: {action}"

        except Exception as e:
            return f"Error executing {action}: {str(e)}"