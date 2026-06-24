from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Tool(ABC):
    """Base class for all tools."""

    name: str
    description: str
    parameters: dict

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given arguments."""
        ...


class ToolRegistry:
    """
    Registry for agent tools.

    Allows dynamic registration and execution of tools.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._cached_definitions: Optional[list[Dict[str, Any]]] = None

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        self._cached_definitions = None

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        self._tools.pop(name, None)
        self._cached_definitions = None

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def get_definitions(self) -> list[Dict[str, Any]]:
        """
        Get tool definitions as OpenAI function schemas.
        Result is cached until next register/unregister.
        """
        if self._cached_definitions is not None:
            return self._cached_definitions

        definitions = []
        for tool in self._tools.values():
            definitions.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            })
        definitions.sort(key=lambda d: d["name"])
        self._cached_definitions = definitions
        return definitions

    def execute(self, name: str, args: Dict[str, Any]) -> str:
        """Execute a tool by name with given arguments."""
        tool = self._tools.get(name)
        if not tool:
            return f"Unknown tool: {name}"
        try:
            return tool.execute(**args)
        except TypeError as e:
            return f"Tool {name} called with invalid arguments: {e}"
        except Exception as e:
            return f"Error executing {name}: {e}"


_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global ToolRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
