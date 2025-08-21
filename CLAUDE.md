# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RyAgent is a personal terminal application that hosts multiple LLM agents in tabs. Each tab accepts prompts, can be interrupted, and shows message-level feedback. Tool calls are first-class citizens.

**Key Details:**
- **Name:** RyAgent (brand); `ryagent` (package/import)
- **CLI:** `ry`
- **Language:** Python 3.11+
- **Package Manager:** uv (fast Python package installer and resolver)
- **UI Framework:** Textual (tabs, layout, input, keybindings) with Rich for text rendering
- **Runtime:** `asyncio` for concurrency, subprocesses for tools requiring system access

## Architecture

### High-Level Structure
- **TextualApp** hosts a TabBar and TabContent area
- Each **AgentTab** owns inbox, history, tool registry, and background task runner
- **Event Bus** passes events between UI and runtime: `UserPrompt`, `AgentReply`, `ToolRequest`, `ToolResult`, `Error`, `Interrupt`

### Core Modules
```
app/        # Textual UI and wiring
agents/     # Agent base class and concrete agents
llm/        # Provider adapters and message formatting
tools/      # Tool contracts and implementations
runtime/    # Event bus, task runners, cancellation helpers
cfg/        # Config loader and schema
```

### Data Model
```python
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
```

## Tool System

### Tool Contract
```python
class ToolSpec(TypedDict):
    name: str
    description: str
    schema: dict  # JSON schema for args
    dangerous: bool  # needs explicit allowlist

class Tool:
    spec: ToolSpec
    async def run(self, **kwargs) -> dict: ...
```

### Core Tools (v0)
- `shell_run(cmd: str, timeout_s: int=60)` - runs commands with allowlist and PTY
- `fs_read(path: str, bytes: int=65536)` - reads files with size limits
- `fs_write(path: str, content: str, mode: Literal["create","overwrite"]="create")` - guarded file writing

### Safety Features
- Command allowlist (e.g., `python`, `uv`, `ls`, `cat`, `rg`, `git status`)
- Path sandbox rooted at current workspace
- Timeouts and max output size with truncation indicators

## Configuration

Uses `config.toml` with structure:
```toml
[app]
workspace = "/path/to/ws"

[models.default]
provider = "openai"
model = "gpt-4o-mini"
max_tokens = 4096

[agents.default]
system_prompt = "You are a helpful coding and ops agent."
authorized_tools = ["shell_run", "fs_read", "fs_write"]

[tools.shell_run]
allow = ["python", "uv", "ls", "cat", "rg", "git", "pytest"]
deny = ["rm", "shutdown", "reboot", "mkfs"]
```

## Agent Execution Model

1. Receive `UserPrompt`
2. Build messages from `history + new prompt` and call LLM
3. If LLM requests tools via structured function calls, dispatch them
4. Append all outputs as messages in the tab
5. Stop (no autonomous multi-step loops in v0)

## UI Design

### Layout
- **Header:** RyAgent, current tab name, run/stop indicator
- **Left:** Tab list (scrollable)
- **Center:** Conversation view for active tab
- **Bottom:** Input box + send key

### Key Bindings
- `Ctrl+Tab` - next tab
- `Ctrl+Shift+Tab` - previous tab
- `t` - new tab
- `x` - close tab
- `Enter` - send prompt
- `Ctrl+C` - interrupt current run

## Development Milestones

### v0.0.1 - Skeleton
Textual app with tabs, input box, message view. One hard-coded agent.

### v0.0.2 - Tools
Implement core tools with allowlist and sandbox. Tool results as messages.

### v0.0.3 - Multiple Agents
Per-tab config (system prompt, model, tools). Add interrupt. Basic config loader.

### v0.1.0 - Polish
Error handling, truncation notices, message persistence, keybinding cheatsheet.

## Development Setup

### Prerequisites
- Python 3.11+
- uv package manager

### Initial Setup
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize Python project with uv
uv init --python 3.11
uv add textual rich

# Add development dependencies
uv add --dev pytest pytest-asyncio black ruff mypy

# Create virtual environment and install dependencies
uv sync
```

### Common Commands
```bash
# Install new dependency
uv add <package-name>

# Install development dependency
uv add --dev <package-name>

# Run the application
uv run python -m ryagent

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .

# Type checking
uv run mypy .

# Update dependencies
uv sync --upgrade
```

## Development Notes

- Run LLM calls and tools as background tasks to avoid blocking Textual's event loop
- Use `asyncio.Queue` to buffer outgoing messages per tab
- Batch UI updates at ~30-60 Hz
- Cap message history length in memory, rotate to disk when needed
- Tool results appear as single `tool` message with JSON summary
- Interrupt cancels both LLM streams and child subprocesses
- Use `uv run` prefix for all Python commands to ensure proper virtual environment activation