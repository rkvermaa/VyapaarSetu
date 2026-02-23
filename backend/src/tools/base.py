"""Base tool class for VyapaarSetu agent tools."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}

    @abstractmethod
    async def execute(self, arguments: dict[str, Any], context: dict[str, Any]) -> dict:
        """Execute the tool with given arguments and context."""
        ...

    def get_definition(self) -> dict[str, Any]:
        """Return OpenAI-compatible tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
