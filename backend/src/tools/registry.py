"""Tool registry — loads and manages agent tools."""

import importlib
import pkgutil
from typing import Any

from src.tools.base import BaseTool
from src.core.logging import log


class ToolRegistry:
    """Registry for all available agent tools."""

    def __init__(self):
        self._all_tools: dict[str, BaseTool] = {}
        self._enabled_tools: dict[str, BaseTool] = {}
        self._load_all_tools()

    def _load_all_tools(self) -> None:
        """Auto-discover and load all tools from tools/core/."""
        try:
            import src.tools.core as tools_pkg
            for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
                if module_name.startswith("_"):
                    continue
                try:
                    module = importlib.import_module(f"src.tools.core.{module_name}")
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseTool)
                            and attr is not BaseTool
                        ):
                            instance = attr()
                            if instance.name:
                                self._all_tools[instance.name] = instance
                                log.debug(f"Loaded tool: {instance.name}")
                except Exception as e:
                    log.warning(f"Failed to load tool module {module_name}: {e}")
        except Exception as e:
            log.error(f"Tool discovery failed: {e}")

    def enable_tools_for_skill(self, tool_names: list[str], skill_slug: str = "") -> int:
        """Enable specific tools for the current skill."""
        self._enabled_tools = {}
        count = 0
        for name in tool_names:
            if name in self._all_tools:
                self._enabled_tools[name] = self._all_tools[name]
                count += 1
            else:
                log.warning(f"Tool {name!r} not found for skill {skill_slug!r}")
        return count

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions for LLM."""
        return [t.get_definition() for t in self._enabled_tools.values()]

    def get_enabled_tools(self) -> list[str]:
        return list(self._enabled_tools.keys())

    async def execute_tool(
        self, name: str, arguments: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        if name not in self._enabled_tools:
            raise ValueError(f"Tool {name!r} is not enabled")
        return await self._enabled_tools[name].execute(arguments, context)
