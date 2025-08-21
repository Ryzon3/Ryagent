import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, TypedDict


class ToolSpec(TypedDict):
    name: str
    description: str
    schema: dict
    dangerous: bool


class Tool(ABC):
    @property
    @abstractmethod
    def spec(self) -> ToolSpec:
        pass

    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        pass


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._authorized_tools: List[str] = []

    def register(self, tool: Tool) -> None:
        self._tools[tool.spec["name"]] = tool

    def authorize_tool(self, tool_name: str) -> None:
        if tool_name not in self._authorized_tools:
            self._authorized_tools.append(tool_name)

    def is_authorized(self, tool_name: str) -> bool:
        return tool_name in self._authorized_tools

    def get_tool(self, tool_name: str) -> Tool | None:
        return self._tools.get(tool_name)

    def get_tool_specs(self) -> List[Dict[str, Any]]:
        specs = []
        for tool_name in self._authorized_tools:
            if tool_name in self._tools:
                spec = self._tools[tool_name].spec
                specs.append({
                    "type": "function",
                    "function": {
                        "name": spec["name"],
                        "description": spec["description"],
                        "parameters": spec["schema"]
                    }
                })
        return specs

    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        if not self.is_authorized(tool_name):
            return {
                "error": f"Tool '{tool_name}' is not authorized",
                "success": False
            }

        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "error": f"Tool '{tool_name}' not found",
                "success": False
            }

        try:
            result = await tool.run(**kwargs)
            return {
                "result": result,
                "success": True
            }
        except Exception as e:
            return {
                "error": f"Tool execution failed: {str(e)}",
                "success": False
            }