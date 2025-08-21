import asyncio
import json
from typing import Any, Dict, List, Optional, AsyncGenerator
from openai import AsyncOpenAI

from ..models import Message


class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", max_tokens: int = 4096):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        formatted = []
        for msg in messages:
            if msg.role in ["user", "assistant", "system"]:
                formatted.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif msg.role == "tool":
                formatted.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.meta.get("tool_call_id", "unknown")
                })
        return formatted

    async def generate_response(self, messages: List[Message], tools: Optional[List[Dict]] = None) -> Message:
        formatted_messages = self._format_messages(messages)
        
        try:
            if tools:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    max_tokens=self.max_tokens,
                    tools=tools,
                    tool_choice="auto"
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    max_tokens=self.max_tokens
                )

            choice = response.choices[0]
            message = choice.message

            if message.tool_calls:
                return Message(
                    role="assistant",
                    content=message.content or "",
                    meta={
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    }
                )
            else:
                return Message(
                    role="assistant",
                    content=message.content or "",
                    meta={"finish_reason": choice.finish_reason}
                )

        except Exception as e:
            return Message(
                role="error",
                content=f"LLM error: {str(e)}",
                meta={"error_type": type(e).__name__}
            )

    async def stream_response(self, messages: List[Message], tools: Optional[List[Dict]] = None) -> AsyncGenerator[str, None]:
        formatted_messages = self._format_messages(messages)
        
        try:
            if tools:
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    max_tokens=self.max_tokens,
                    tools=tools,
                    tool_choice="auto",
                    stream=True
                )
            else:
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    max_tokens=self.max_tokens,
                    stream=True
                )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"Error: {str(e)}"