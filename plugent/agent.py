"""SiteAgent - Main agent class for plugent."""

from typing import Any, Optional


class SiteAgent:
    """Main agent class for plugin-based LLM interactions."""

    def __init__(self, model: str = "gpt-4o-mini", **kwargs):
        self.model = model
        self.config = kwargs

    def run(self, prompt: str, **kwargs) -> str:
        """Run the agent with a prompt."""
        return f"Response to: {prompt}"

    def add_plugin(self, plugin: Any) -> None:
        """Add a plugin to the agent."""
        pass

    def remove_plugin(self, plugin_name: str) -> None:
        """Remove a plugin from the agent."""
        pass