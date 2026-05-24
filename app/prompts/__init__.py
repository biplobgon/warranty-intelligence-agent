"""Prompt registry.

Centralizes prompt templates so we can version, audit, and unit-test them
independently of the agents that consume them.
"""

from app.prompts.registry import PROMPTS, get_prompt

__all__ = ["PROMPTS", "get_prompt"]
