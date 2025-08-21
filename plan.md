# RyAgent — Initial Plan (v0)

**Goal:** Build a personal terminal application that hosts multiple LLM agents in tabs. Each tab accepts prompts, can be interrupted, and shows message-level feedback only. Tool calls are first-class. Keep the stack simple and Python-first.

## Project name & branding

* **Name:** RyAgent (brand); `ryagent` (package/import)
* **CLI:** `ry`
* **Tagline:** Your personal multi-agent operator
* **Identity:** Use “RyAgent” in UI headers; prefer lowercase `ryagent` in code and configs.
* **Notes:** Single word, capability-forward branding (not terminal-centric).

---

## 1) Stack and language choices

* **Language:** Python 3.11+
* **Runtime model:** `asyncio` for concurrency. Subprocesses for tools that need system access.
* **UI:** Textual (tabs, layout, input, keybindings). Rich for rendering text.
* **LLM client:** Adapter pattern around providers (OpenAI, Anthropic, local via Ollama). Start with one provider and make the client pluggable.
* **Config:** `config.toml` or `yaml` for model keys, default agent prompts, and tool allowlists.
* **Data:** In-memory state for v0. Add SQLite for transcripts in v0.2.

---

## 2) Scope for v0 (the minimal that is useful)

* Multiple **tabs**, one agent per tab.
* Send a prompt to the active tab. Receive assistant messages.
* **Interrupt** a running task in a tab (cancel LLM stream and kill any subprocesses started by tools).
* **Tool calls** supported via a minimal tool registry and an allowlist. Results appear as messages. No fancy diff panes yet.
* No streaming logs or progress meters in UI beyond messages.

Out of scope for v0:

* GUI control, web browsing panes, cost HUD, diffs, or RAG. Those come later.

---

## 3) Program architecture

### 3.1 High level

* **TextualApp** hosts a TabBar and a TabContent area.
* Each **AgentTab** owns its own inbox, history, tool registry, and a background task runner.
* A small **Event Bus** passes events between UI and runtime: `UserPrompt`, `AgentReply`, `ToolRequest`, `ToolResult`, `Error`, `Interrupt`.

### 3.2 Core modules

* `app/` Textual UI and wiring
* `agents/` Agent base class and concrete agents
* `llm/` Provider adapters and message formatting
* `tools/` Tool contracts and implementations
* `runtime/` Event bus, task runners, cancellation helpers
* `cfg/` Config loader and schema

### 3.3 Data model (v0)

```python
from dataclasses import dataclass, field
from typing import Literal, Dict, Any, List

Role = Literal["user", "assistant", "tool", "system", "error"]

@dataclass
class Message:
    role: Role
    content: str
    meta: Dict[str, Any] = field(default_factory=dict)  # tool name, run id, etc.

@dataclass
class AgentState:
    name: str
    system_prompt: str
    history: List[Message] = field(default_factory=list)
    running: bool = False
    current_task_id: str | None = None
```

---

## 4) Agent and tool execution model

### 4.1 Agent loop (simple and deterministic)

1. Receive `UserPrompt`.
2. Build messages from `history + new prompt` and call the LLM.
3. If the LLM asks for a tool via a structured function call format, dispatch it.
4. Append all outputs as **messages** in the tab.
5. Stop. No autonomous multi-step loops in v0.

### 4.2 Tool contract

```python
from typing import TypedDict, Any

class ToolSpec(TypedDict):
    name: str
    description: str
    schema: dict  # JSON schema for args
    dangerous: bool  # needs explicit allowlist

class Tool:
    spec: ToolSpec
    async def run(self, **kwargs) -> dict: ...  # returns JSON-serializable result
```

**Registry:** map tool name → Tool. Validate against allowlist before running.

**Initial tools (v0):**

* `shell_run(cmd: str, timeout_s: int=60)` runs a command with an allowlist and a PTY. Captures the final stdout/stderr summary only.
* `fs_read(path: str, bytes: int=65536)` reads small files with size limits.
* `fs_write(path: str, content: str, mode: Literal["create","overwrite"]="create")` guarded by patterns.

**Safety:**

* Command allowlist (e.g., `python`, `pip`, `ls`, `cat`, `rg`, `git status`, no `rm -rf`).
* Path sandbox rooted at the current workspace.
* Timeouts and max output size. Truncate and indicate truncation in the message.

---

## 5) UI plan (Textual)

### 5.1 Layout

* **Header:** RyAgent, current tab name, run/stop indicator.
* **Left:** Tab list (scrollable). Keys: `Ctrl+Tab` next, `Ctrl+Shift+Tab` prev, `t` new tab, `x` close tab.
* **Center:** Conversation view for the active tab. Just messages in v0.
* **Bottom:** Input box + send key `Enter`. `Ctrl+C` interrupts the current run in this tab.

### 5.2 Widgets

* `TabbedContent` or custom tab list + a `ListView` or `RichLog` for messages.
* Input: single-line with history (up/down to cycle recent prompts).
* Status area: a compact spinner when running, nothing fancy beyond that.

### 5.3 Interaction rules

* Sending a prompt posts a `UserPrompt` to the tab’s queue and returns control immediately.
* Interrupt sends `Interrupt(task_id)` and cancels the LLM stream and any child subprocess for that tab.
* Tool results appear as a single `tool` message with a short JSON summary.

---

## 6) Configuration (v0)

Example `config.toml`:

```toml
[app]
workspace = "/path/to/ws"

[models.default]
provider = "openai"
model = "gpt-4o-mini"
max_tokens = 4096

[agents.default]
system_prompt = "You are a helpful coding and ops agent. Prefer tools when appropriate."

authorized_tools = ["shell_run", "fs_read", "fs_write"]

[tools.shell_run]
allow = ["python", "pip", "ls", "cat", "rg", "git", "pytest"]
deny = ["rm", "shutdown", "reboot", "mkfs"]
```

---

## 7) Performance and responsiveness

* Run LLM calls and tools as background tasks; never block Textual’s event loop.
* Use an `asyncio.Queue` to buffer outgoing messages per tab. Batch UI updates at \~30–60 Hz.
* Cap message history length in memory. Rotate older messages to disk when needed.

---

## 8) Testing strategy

* Unit tests for the tool allowlist and sandboxing rules.
* Contract tests for the LLM client adapter (mock responses for tool calls and plain replies).
* UI smoke tests: create tabs, send prompts, interrupt, and verify that the UI remains responsive.

---

## 9) Milestones

* **v0.0.1** — Skeleton: Textual app with tabs, input box, message view. One hard-coded agent. Send and display replies.
* **v0.0.2** — Tools: Implement `shell_run`, `fs_read`, `fs_write` with allowlist and sandbox. Tool results show as messages.
* **v0.0.3** — Multiple agents: per-tab config (system prompt, model, tools). Add interrupt. Basic config loader.
* **v0.1.0** — Polish: error handling, truncation notices, message persistence to disk, minimal keybinding cheatsheet.

---

## 10) Risks and mitigations

* **Runaway tasks**: enforce timeouts and add a hard kill for subprocesses. Cancel LLM streams on interrupt.
* **Prompt injection via tool calls**: require explicit tool invocation formats and validate args against schema.
* **Performance hiccups**: batch UI updates and cap message sizes. Stream to files if needed.

---

## 11) Next steps (actionable)

1. Scaffold Textual app with TabBar, MessageView, and Input.
2. Implement `LLMClient` with one provider and tool-call parsing.
3. Add tool registry and implement `shell_run`, `fs_read`, `fs_write` with safety.
4. Wire interrupt to cancel both LLM and subprocess. Show a concise “Run canceled” message.
5. Add `config.toml` parsing and per-tab agent creation from config.



