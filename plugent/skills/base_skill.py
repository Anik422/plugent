"""Skill decorator and registry for plugent."""

import inspect
from typing import Any, Callable, get_type_hints
from dataclasses import dataclass

from plugent.core.skill_builder import Skill


# Global skill registry
SKILL_REGISTRY: dict[str, "SkillWrapper"] = {}


@dataclass
class SkillWrapper:
    """Wrapper around a skill function."""

    name: str
    description: str
    parameters: list[dict]
    func: Callable
    is_custom: bool = True

    def execute(self, **kwargs) -> Any:
        """Execute the skill function."""
        try:
            result = self.func(**kwargs)
            if isinstance(result, str):
                return result
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

    def to_skill(self) -> Skill:
        """Convert to Skill dataclass."""
        skill = Skill(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            sql_template="",  # Custom skills don't have SQL
        )
        skill._execute_fn = self.execute
        return skill


def skill(
    name: str = "",
    description: str = "",
):
    """Decorator to register a function as a skill.

    Usage:
        @skill(name="check_delivery", description="Check if we deliver to a district")
        def check_delivery(district: str) -> str:
            '''Check delivery availability.

            Args:
                district: The district to check.
            '''
            if district in ["Downtown", "Uptown"]:
                return f"Yes, we deliver to {district}"
            return f"No delivery to {district}"
    """
    def decorator(func: Callable) -> Callable:
        # Get function metadata
        func_name = name or func.__name__
        func_desc = description or (func.__doc__.strip().split("\n")[0] if func.__doc__ else "")

        # Extract parameters from type hints and docstring
        sig = inspect.signature(func)
        hints = get_type_hints(func) if func.__annotations__ else {}

        parameters = []
        for param_name, param in sig.parameters.items():
            param_type = hints.get(param_name, Any)
            param_desc = ""

            # Try to get description from docstring
            if func.__doc__:
                lines = func.__doc__.split("\n")
                for line in lines:
                    if param_name.lower() in line.lower() and ":" in line:
                        param_desc = line.split(":")[-1].strip()
                        break

            parameters.append({
                "name": param_name,
                "type": param_type.__name__ if hasattr(param_type, "__name__") else "string",
                "description": param_desc,
            })

        # Create wrapper
        wrapper = SkillWrapper(
            name=func_name,
            description=func_desc,
            parameters=parameters,
            func=func,
            is_custom=True,
        )

        # Register in global registry
        SKILL_REGISTRY[func_name] = wrapper

        # Return original function (it can still be called normally)
        return func

    return decorator


def get_skill(name: str) -> SkillWrapper | None:
    """Get a skill by name from registry."""
    return SKILL_REGISTRY.get(name)


def list_skills() -> list[SkillWrapper]:
    """List all registered skills."""
    return list(SKILL_REGISTRY.values())


def clear_registry() -> None:
    """Clear the skill registry."""
    SKILL_REGISTRY.clear()


def import_skills_from_module(module) -> None:
    """Import all @skill decorated functions from a module."""
    for name, obj in inspect.getmembers(module):
        if callable(obj) and hasattr(obj, "__name__"):
            # Check if it's a registered skill
            if name in SKILL_REGISTRY:
                continue
        # Check if function is in registry by checking its wrapper
        for reg_name, wrapper in SKILL_REGISTRY.items():
            if wrapper.func == obj:
                break