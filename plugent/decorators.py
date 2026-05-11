"""Decorators for plugent."""

from functools import wraps
from typing import Callable, Any


def skill(func: Callable) -> Callable:
    """Decorator to register a function as a skill/plugin."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        return func(*args, **kwargs)

    wrapper._is_skill = True
    return wrapper