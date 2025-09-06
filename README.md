# RyAgent

Local Python daemon serving multiple LLM agents with modern React web UI.

**Status**: Phase 2 Complete ✅ - Modern React + TypeScript frontend with FastAPI backend

## Quick Start

### Development Mode (Recommended)

```bash
# 1. Install Python dependencies
uv sync

# 2. Install frontend dependencies
cd frontend && bun install

# 3. Start backend API server (Terminal 1)
uv run python -m ryagent.main --dev

# 4. Start frontend dev server (Terminal 2)
cd frontend && bun run dev

# 5. Open browser to http://localhost:3000
```

### Production Mode

```bash
# 1. Build frontend
cd frontend && bun run build

# 2. Start unified server (serves API + frontend)
uv run python -m ryagent.main

# 3. Open browser to http://127.0.0.1:8000
```

## Current Features (Phase 2)

- ✅ **Modern Stack**: React + TypeScript + ShadCN UI components
- ✅ **Local-first**: Runs locally, no external dependencies  
- ✅ **Tab Management**: Create, view, and delete agent tabs
- ✅ **Message Interface**: Send messages and receive responses (echo mode)
- ✅ **Authentication**: Auto-generated tokens with React context
- ✅ **Type Safety**: Full TypeScript coverage with API client
- ✅ **Professional UI**: ShadCN components with Tailwind CSS
- ✅ **Responsive Design**: Mobile-friendly interface
- ✅ **Development Tools**: Hot reload, linting, formatting

## Technology Stack

### Backend
- **FastAPI**: Modern JSON API server
- **Python 3.11+**: Type-safe Python with Pydantic models
- **uvicorn**: ASGI server with auto-reload

### Frontend  
- **React 19**: Modern React with hooks and context
- **Next.js 15**: App router with TypeScript support
- **ShadCN UI**: Professional component library
- **Tailwind CSS**: Utility-first styling
- **Bun**: Fast package manager and runtime

### Development
- **TypeScript**: Full type safety across frontend
- **Ruff**: Fast Python linting and formatting
- **Prettier**: Code formatting for frontend
- **Pytest**: Comprehensive test suite (11 tests)

## Development Commands

```bash
# Setup
uv sync                              # Install Python dependencies
cd frontend && bun install          # Install frontend dependencies

# Development (Two terminals needed)
# Terminal 1 - Backend API server:
uv run python -m ryagent.main --dev # Start Python API server (localhost:8000)

# Terminal 2 - Frontend dev server: 
cd frontend && bun run dev          # Start React dev server (localhost:3000)

# Production build
cd frontend && bun run build        # Build React app for production
uv run python -m ryagent.main      # Start server (serves API + built frontend)

# Code formatting
uv run ruff format .                # Format Python code
cd frontend && bun run lint         # Lint React code

# Testing
uv run pytest                      # Run Python tests
uv run pytest tests/integration/   # Integration tests only
```

## Project Structure

```
ryagent/
├── ryagent/                        # Python backend
│   ├── app/server.py              # FastAPI JSON API server
│   ├── core/models.py             # Pydantic data models  
│   ├── config/settings.py         # Application settings
│   └── utils/auth.py              # Token authentication
├── frontend/                       # React frontend
│   ├── src/app/                   # Next.js app router pages
│   ├── src/components/            # React components + ShadCN UI
│   ├── src/lib/                   # API client and utilities
│   └── src/contexts/              # React context providers
└── tests/                          # Comprehensive test suite
    ├── test_api.py                # API endpoint tests  
    └── integration/               # Full workflow tests
        └── test_full_flow.py      # End-to-end test scenarios
```

## API Endpoints

### Authentication
- `GET /api/auth/token` - Get authentication token
- `POST /api/auth/validate` - Validate token

### Tab Management  
- `GET /api/tabs` - List all tabs
- `POST /api/tabs` - Create new tab
- `GET /api/tabs/{id}` - Get specific tab
- `DELETE /api/tabs/{id}` - Delete tab

### Messaging
- `POST /api/tabs/{id}/messages` - Send message to tab

### Health
- `GET /health` - Health check

## Coming in Phase 3

- 🔄 **Real LLM Integration**: OpenAI/Anthropic API integration
- 🔄 **Real-time Updates**: WebSocket/SSE for live responses  
- 🔄 **Tool System**: Sandboxed shell and file operations
- 🔄 **Agent Configurations**: Multiple agent types and models
- 🔄 **Message History**: Persistent conversation storage
- 🔄 **Export/Import**: Save and restore conversations

## Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ryagent

# Run specific test categories  
uv run pytest tests/test_api.py                    # API tests
uv run pytest tests/integration/                   # Integration tests
uv run pytest -k "auth"                           # Authentication tests
```

**Test Coverage:**
- ✅ API endpoint testing (CRUD operations)
- ✅ Authentication flow testing
- ✅ Error handling and validation
- ✅ Full user workflow integration tests
- ✅ Multi-tab management scenarios

## Requirements

- **Python**: 3.11 or higher
- **Bun**: Latest version (for frontend development)  
- **OS**: Linux, macOS, Windows (WSL recommended)

## License

AGPL-3.0 - See LICENSE file for details.

Network copyleft license ensuring derivative works remain open source when distributed over a network.