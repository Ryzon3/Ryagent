from dataclasses import dataclass, field
from typing import Literal, Dict, Any, List

Role = Literal["user", "assistant", "tool", "system", "error"]

@dataclass
class Message:
    role: Role
    content: str
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentState:
    name: str
    system_prompt: str
    history: List[Message] = field(default_factory=list)
    running: bool = False
    current_task_id: str | None = None