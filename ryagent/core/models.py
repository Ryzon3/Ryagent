"""Pydantic data models for RyAgent."""

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

Role = Literal["user", "assistant", "tool", "system", "error"]
TabState = Literal["idle", "running", "completed", "error", "read"]


class Message(BaseModel):
    """A message in the conversation history."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    meta: dict[str, Any] = Field(default_factory=dict)


class TabCreate(BaseModel):
    """Request model for creating a new tab."""

    name: str = Field(..., min_length=1, max_length=100)
    model: str = "gpt-4o-mini"
    system_prompt: str = "You are a helpful assistant."
    tools: list[str] = Field(default_factory=list)


class Tab(BaseModel):
    """A tab representing an agent conversation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    model: str
    system_prompt: str
    tools: list[str]
    messages: list[Message] = Field(default_factory=list)
    running: bool = False
    current_task_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    state: TabState = "idle"
    has_error: bool = False

    @property
    def message_count(self) -> int:
        """Get the number of messages in this tab."""
        return len(self.messages)

    @property
    def status(self) -> str:
        """Get human-readable status."""
        if self.running:
            return "Running"
        elif self.has_error:
            return "Error"
        elif self.messages:
            return f"{self.message_count} messages"
        else:
            return "Empty"

    @property
    def display_state(self) -> TabState:
        """Get the display state for UI coloring."""
        if self.running:
            return "running"
        elif self.has_error:
            return "error"
        elif self.messages:
            # Check if last message is recent (within last hour) to determine if "read"
            from datetime import timedelta

            recent_threshold = datetime.now() - timedelta(hours=1)
            if self.last_accessed < recent_threshold and self.messages:
                return "read"
            else:
                return "completed"
        else:
            return "idle"


class SendMessage(BaseModel):
    """Request model for sending a message to a tab."""

    prompt: str = Field(..., min_length=1)


class Event(BaseModel):
    """Base model for SSE events."""

    type: str
    data: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class MessageEvent(Event):
    """Event for new messages."""

    type: Literal["message"] = "message"

    def __init__(self, message: Message, **kwargs):
        super().__init__(data={"message": message.model_dump()}, **kwargs)


class StatusEvent(Event):
    """Event for status updates."""

    type: Literal["status"] = "status"

    def __init__(self, running: bool, task_id: str | None = None, **kwargs):
        super().__init__(data={"running": running, "task_id": task_id}, **kwargs)


class ErrorEvent(Event):
    """Event for errors."""

    type: Literal["error"] = "error"

    def __init__(self, error: str, **kwargs):
        super().__init__(data={"error": error}, **kwargs)
