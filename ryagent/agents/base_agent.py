import asyncio
import json
import uuid
from typing import Dict, Any, Optional

from ..models import Message, AgentState
from ..llm.client import LLMClient
from ..tools.base import ToolRegistry
from ..runtime.events import (
    EventBus, UserPromptEvent, AgentReplyEvent, 
    ToolRequestEvent, ToolResultEvent, ErrorEvent, InterruptEvent
)


class BaseAgent:
    def __init__(
        self, 
        agent_state: AgentState,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        event_bus: EventBus
    ):
        self.state = agent_state
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.event_bus = event_bus
        self._current_task: Optional[asyncio.Task] = None
        self._cancelled = False

    async def process_prompt(self, prompt: str, tab_id: str) -> None:
        task_id = str(uuid.uuid4())
        self.state.current_task_id = task_id
        self.state.running = True
        self._cancelled = False

        try:
            user_message = Message(role="user", content=prompt)
            self.state.history.append(user_message)

            await self.event_bus.publish(
                UserPromptEvent(tab_id, prompt, task_id)
            )

            messages_for_llm = self._prepare_messages_for_llm()
            tool_specs = self.tool_registry.get_tool_specs()

            response = await self.llm_client.generate_response(
                messages_for_llm, 
                tools=tool_specs if tool_specs else None
            )

            if self._cancelled:
                return

            if response.role == "error":
                await self.event_bus.publish(
                    ErrorEvent(tab_id, response.content, task_id)
                )
                return

            if "tool_calls" in response.meta:
                await self._handle_tool_calls(response, tab_id, task_id)
            else:
                self.state.history.append(response)
                await self.event_bus.publish(
                    AgentReplyEvent(tab_id, response, task_id)
                )

        except asyncio.CancelledError:
            await self.event_bus.publish(
                ErrorEvent(tab_id, "Task was cancelled", task_id)
            )
            raise
        except Exception as e:
            await self.event_bus.publish(
                ErrorEvent(tab_id, f"Agent error: {str(e)}", task_id)
            )
        finally:
            self.state.running = False
            self.state.current_task_id = None

    async def _handle_tool_calls(self, response: Message, tab_id: str, task_id: str) -> None:
        self.state.history.append(response)
        await self.event_bus.publish(
            AgentReplyEvent(tab_id, response, task_id)
        )

        tool_calls = response.meta["tool_calls"]
        for tool_call in tool_calls:
            if self._cancelled:
                return

            tool_name = tool_call["function"]["name"]
            tool_call_id = tool_call["id"]
            
            try:
                args = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError as e:
                error_result = {
                    "error": f"Invalid JSON in tool arguments: {str(e)}",
                    "success": False
                }
                await self._send_tool_result(tool_call_id, error_result, tab_id, task_id)
                continue

            await self.event_bus.publish(
                ToolRequestEvent(tab_id, tool_name, args, tool_call_id, task_id)
            )

            result = await self.tool_registry.execute_tool(tool_name, **args)
            await self._send_tool_result(tool_call_id, result, tab_id, task_id)

    async def _send_tool_result(
        self, 
        tool_call_id: str, 
        result: Dict[str, Any], 
        tab_id: str, 
        task_id: str
    ) -> None:
        tool_message = Message(
            role="tool",
            content=json.dumps(result, indent=2),
            meta={"tool_call_id": tool_call_id}
        )
        
        self.state.history.append(tool_message)
        
        await self.event_bus.publish(
            ToolResultEvent(tab_id, tool_call_id, result, task_id)
        )

    def _prepare_messages_for_llm(self) -> list[Message]:
        messages = []
        
        if self.state.system_prompt:
            messages.append(Message(role="system", content=self.state.system_prompt))
        
        messages.extend(self.state.history)
        
        return messages

    async def interrupt(self) -> None:
        self._cancelled = True
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass

    def start_task(self, coro) -> asyncio.Task:
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
        
        self._current_task = asyncio.create_task(coro)
        return self._current_task