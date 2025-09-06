# RyAgent — Original Specification (Historical)

> **Note**: This document contains the original HTMX-based specification. The current implementation (Phase 2) uses React + TypeScript frontend with FastAPI JSON API backend. See README.md and project_plan.md for current architecture.

# RyAgent — Daemon + HTMX Plan (v0 Spec & Actionables)

## 0) One‑liner
A local **Python daemon** that runs multiple LLM agents and tools, with a **light HTMX web UI** for tabbed prompts, interrupts, and streaming message updates.

> **Daemon =** a background service/process that listens on localhost and handles requests even when no UI window is focused. We’ll bind to `127.0.0.1` and require a token per request.

---

## 1) Architecture (high level)
- **ryagentd (backend daemon, Python/FastAPI)**
  - Endpoints for tab/agent lifecycle, prompts, interrupts.
  - **SSE (Server‑Sent Events)** stream per tab for live message/tool events.
  - Tool registry (allowlisted, sandboxed) + async execution.
  - Model adapters (OpenAI first; later Anthropic/Ollama) with streaming.
  - In‑memory state for v0; file persistence later.
- **Web UI (HTMX + Jinja2 templates)**
  - Dashboard lists tabs; detail page per tab.
  - Forms send prompts, buttons interrupt; SSE appends messages.
  - Minimal JS (HTMX) + optional Tailwind for styling.

```
Browser (HTMX) <──HTTP POST──> ryagentd (FastAPI)
Browser (hx-sse) <──SSE stream── ryagentd (EventSourceResponse)
                                   ├─ Agent runtime (asyncio tasks)
                                   ├─ Tool workers (subprocess/threads)
                                   └─ Model adapters (httpx → LLM APIs)
```

---

## 2) Language & libraries
- **Python 3.11+** (asyncio, faster I/O)
- **FastAPI** (REST + WebSockets, but v0 uses **SSE**) + **uvicorn**
- **sse‑starlette** (EventSourceResponse) for SSE convenience
- **httpx** (async client) for LLM calls
- **Pydantic v2** for schemas
- **Jinja2** for HTML templates (server‑side rendered fragments)
- **HTMX** on the client (CDN script, no build step)
- **(Optional)** Tailwind via CDN for lightweight styling
- **tenacity** (retry) and **python‑dotenv** (env)

---

## 3) API design (v0)
**Auth:** `Authorization: Bearer <token>` on all POST/DELETE; SSE uses `?token=` or header.

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/tabs` | `{name?, model?, system_prompt?, tools?}` | `{id, name, created_at}` |
| GET | `/api/tabs` | — | `[{id, name, running, count}]` |
| GET | `/api/tabs/{id}` | — | `{id, name, messages:[…], running}` (limited window) |
| DELETE | `/api/tabs/{id}` | — | `{ok:true}` |
| POST | `/api/tabs/{id}/send` | `{prompt}` | `{task_id}` (immediate) |
| POST | `/api/tabs/{id}/interrupt` | — | `{ok:true}` |
| GET | `/api/tabs/{id}/events` | SSE | `event: message/tool/status/error` lines |

**SSE events (examples):**
```text
event: status
data: {"running": true, "task_id": "..."}

event: message
data: {"role":"assistant","content":"…","id":"m_…"}

event: tool_start
data: {"tool":"shell_run","args":{…},"run_id":"…"}

event: tool_end
data: {"tool":"shell_run","ok":true,"summary":"…","run_id":"…"}

event: error
data: {"message":"timeout","run_id":"…"}
```

---

## 4) Data model (v0)
```python
from typing import Literal, Dict, Any
from pydantic import BaseModel
Role = Literal["user","assistant","tool","system","error"]

class Message(BaseModel):
    role: Role
    content: str
    meta: Dict[str, Any] = {}

class AgentState(BaseModel):
    id: str
    name: str
    model: str
    system_prompt: str
    history: list[Message] = []
    running: bool = False
    current_task_id: str | None = None
```

---

## 5) Tool calls (focus area)
**Contract:**
```python
class ToolSpec(BaseModel):
    name: str
    description: str
    schema: dict  # JSON Schema for args
    dangerous: bool = False

class Tool:
    spec: ToolSpec
    async def run(self, **kwargs) -> dict: ...  # JSON result
```

**Registry & safety:**
- Allowlist tool names per tab; validate args with schema.
- `shell_run(cmd, timeout_s=60)`: exec via subprocess with **allowlisted binaries** only; capture **summary** (truncate > N KB); no live stream in v0.
- `fs_read(path, bytes=65536)`: read small files within sandbox root.
- `fs_write(path, content, mode=create|overwrite)`: pattern‑guarded writes.
- Timeouts, size caps, and path sandboxing to current workspace.

**LLM tool routing (v0):** support structured tool calls via your LLM’s function/tool schema; one tool call per prompt cycle (no autonomous loops yet).

---

## 6) Web UI (HTMX) — pages & flows
**Dashboard `/`:**
- List tabs (`GET /api/tabs` rendered server‑side).
- “New Tab” form (hx‑post to `/api/tabs`, hx‑swap to append row).

**Tab view `/tabs/{id}`:**
- SSE region: `<div hx-sse="connect:/api/tabs/{id}/events">` that appends incoming messages via server-rendered HTML fragments.
- Prompt form: `<form hx-post="/api/tabs/{id}/send" hx-include="#prompt" hx-swap="none">` (no full reload).
- Interrupt button: `<button hx-post="/api/tabs/{id}/interrupt">Stop</button>`

**Templates (Jinja2):** partials for `message.html`, `tool_event.html`, `status.html`. SSE handlers emit pre-rendered HTML fragments to minimize client logic.

---

## 7) Security & sandboxing (v0)
- **Bind:** `127.0.0.1` only.
- **Auth:** random token in `~/.ryagent/token`; clients send `Authorization: Bearer …`.
- **CSRF:** not required if you rely solely on Authorization header and no cookies; if you add session cookies later, add CSRF tokens.
- **Sandbox:** workspace root; denylist/allowlist for shell commands; no network tools by default.

---

## 8) Performance guardrails
- Background tasks for LLM/tool runs; never block request threads.
- SSE batching: coalesce events to ~30–60 Hz; ring buffers per tab.
- Truncate large outputs; provide a “download full” link later.

---

## 9) Repo layout
```
ryagent/
  app/                 # FastAPI app
    main.py            # routes, SSE
    auth.py            # token middleware
    templates/         # Jinja2 templates (partials)
    static/            # CSS (Tailwind via CDN for now)
  core/
    agents.py          # Agent base + manager
    llm_client.py      # OpenAI adapter (stream + tool calls)
    tools.py           # Tool registry + shell/fs tools
    events.py          # Event types, SSE serialization
    state.py           # In-memory store (v0)
  tests/
  pyproject.toml
  README.md
```

---

## 10) Actionable items (checklist)
**A. Bootstrap**
- [ ] Create repo, `pyproject.toml`, Poetry/uv setup, `README`.
- [ ] Add Apache‑2.0 or AGPL‑3.0 `LICENSE` (per your final choice).

**B. Backend core**
- [ ] FastAPI app skeleton with auth middleware (Bearer token).
- [ ] Tab CRUD endpoints (`/api/tabs*`).
- [ ] SSE endpoint with `EventSourceResponse`.
- [ ] Agent manager (`send`, `interrupt`, background tasks).
- [ ] OpenAI client adapter (non‑stream → stream), tool‑call parsing.
- [ ] Tool registry + `shell_run`, `fs_read`, `fs_write` with allowlists.

**C. Web UI (HTMX)**
- [ ] Base layout, dashboard list (server-rendered).
- [ ] Tab page with SSE region and prompt form.
- [ ] Message/Tool partials; SSE emits HTML fragments.
- [ ] Keyboard UX: focus prompt on load; `Ctrl+Enter` to send (progressive enhancement later).

**D. Safety & tests**
- [ ] Unit tests for tool arg validation and sandbox boundaries.
- [ ] Integration tests for prompt → tool call → message pipeline.
- [ ] Load test SSE (fake event burst) to check UI smoothness.

**E. Packaging & DX**
- [ ] `ryagentd` entry point (uvicorn runner) and `.env` loading.
- [ ] Simple `.service` example (user-level) for auto‑start (Linux/macOS launchd later).
- [ ] Makefile/justfile with `dev`, `format`, `test`, `lint`.

---

## 11) Milestones & DoD
- **v0.0.1**: Create/list tabs; send prompt; assistant reply appears; interrupt works; SSE streams messages.
- **v0.0.2**: Tool registry wired; `shell_run`/`fs_*` tools usable; allowlists enforced; errors surfaced as events.
- **v0.1.0**: Auth token + sandbox defaults; truncation indicators; basic styling; smoke tests passing.

**Definition of Done (v0.1):** In a fresh shell, `ryagentd` starts; open `http://127.0.0.1:8000/`; create a tab; send prompt that triggers a tool call; see tool events and assistant message; interrupt stops a long tool; no server exceptions; SSE keeps UI responsive.

---

## 12) Next (post‑v0) options
- WebSocket upgrade for bidirectional streaming and fine‑grained progress.
- Message persistence (SQLite) and search.
- Diff/preview panes and richer tool outputs (HTML renderers).
- Multi‑model routing and cost/token HUD.
- Remote client auth and port‑forward (if you ever want to use it from another machine).

---

## TLDR
We’ll run **ryagentd** (FastAPI) as a local daemon with **SSE** for live updates, a **Tool Registry** for safe shell/fs access, and a minimal **HTMX** UI for tabs, prompts, and interrupts. Start with in‑memory state, OpenAI adapter, and three safe tools; ship v0.1 once creating tabs, sending prompts, streaming messages, and interrupts are solid.

