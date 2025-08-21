import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

from ..models import Message


class EventType(Enum):
    USER_PROMPT = "user_prompt"
    AGENT_REPLY = "agent_reply"
    TOOL_REQUEST = "tool_request"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    INTERRUPT = "interrupt"


@dataclass
class Event:
    type: EventType
    tab_id: str
    data: Dict[str, Any]
    task_id: Optional[str] = None


@dataclass
class UserPromptEvent(Event):
    def __init__(self, tab_id: str, prompt: str, task_id: str):
        super().__init__(
            type=EventType.USER_PROMPT,
            tab_id=tab_id,
            data={"prompt": prompt},
            task_id=task_id
        )


@dataclass
class AgentReplyEvent(Event):
    def __init__(self, tab_id: str, message: Message, task_id: str):
        super().__init__(
            type=EventType.AGENT_REPLY,
            tab_id=tab_id,
            data={"message": message},
            task_id=task_id
        )


@dataclass
class ToolRequestEvent(Event):
    def __init__(self, tab_id: str, tool_name: str, args: Dict[str, Any], tool_call_id: str, task_id: str):
        super().__init__(
            type=EventType.TOOL_REQUEST,
            tab_id=tab_id,
            data={
                "tool_name": tool_name,
                "args": args,
                "tool_call_id": tool_call_id
            },
            task_id=task_id
        )


@dataclass
class ToolResultEvent(Event):
    def __init__(self, tab_id: str, tool_call_id: str, result: Dict[str, Any], task_id: str):
        super().__init__(
            type=EventType.TOOL_RESULT,
            tab_id=tab_id,
            data={
                "tool_call_id": tool_call_id,
                "result": result
            },
            task_id=task_id
        )


@dataclass
class ErrorEvent(Event):
    def __init__(self, tab_id: str, error: str, task_id: Optional[str] = None):
        super().__init__(
            type=EventType.ERROR,
            tab_id=tab_id,
            data={"error": error},
            task_id=task_id
        )


@dataclass
class InterruptEvent(Event):
    def __init__(self, tab_id: str, task_id: str):
        super().__init__(
            type=EventType.INTERRUPT,
            tab_id=tab_id,
            data={},
            task_id=task_id
        )


class EventBus:
    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[EventType, List[asyncio.Queue]] = {}

    def get_queue(self, tab_id: str) -> asyncio.Queue:
        if tab_id not in self._queues:
            self._queues[tab_id] = asyncio.Queue()
        return self._queues[tab_id]

    def subscribe(self, event_type: EventType, queue: asyncio.Queue):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(queue)

    async def publish(self, event: Event):
        tab_queue = self.get_queue(event.tab_id)
        await tab_queue.put(event)
        
        if event.type in self._subscribers:
            for subscriber_queue in self._subscribers[event.type]:
                try:
                    await subscriber_queue.put(event)
                except asyncio.QueueFull:
                    pass

    async def get_event(self, tab_id: str) -> Event:
        queue = self.get_queue(tab_id)
        return await queue.get()

    def clear_queue(self, tab_id: str):
        if tab_id in self._queues:
            while not self._queues[tab_id].empty():
                try:
                    self._queues[tab_id].get_nowait()
                except asyncio.QueueEmpty:
                    break