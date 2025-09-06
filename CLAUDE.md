# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RyAgent is a local Python daemon that runs multiple LLM agents with a modern React web UI. Uses React + TypeScript + ShadCN for professional frontend interactions with FastAPI JSON backend.

## Project Status

**Current State:** Phase 2 Complete! ✅ Full React + Next.js frontend with TypeScript, ShadCN UI, and FastAPI backend.

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

## Key Architecture Decisions

- **Backend**: FastAPI JSON API server with CORS support
- **Frontend**: React + Next.js + TypeScript with ShadCN UI components 
- **Build Tool**: Bun for fast package management and development
- **Real-time**: Ready for SSE/WebSocket integration (Phase 3)
- **Styling**: Tailwind CSS with professional component library
- **API Style**: RESTful JSON API with proper error handling
- **Auth**: Token-based authentication with auto-token generation
- **Production**: Single server serves both API and static frontend

## Development Guidelines

### When working on this codebase:

1. **Frontend**: Use React + TypeScript with ShadCN UI components
2. **API Integration**: Always use the typed API client for backend calls
3. **State Management**: Use React hooks and context for state management  
4. **Error Handling**: Implement proper error boundaries and user feedback
5. **Styling**: Use Tailwind CSS classes with ShadCN component variants
6. **Development**: Use Bun for frontend, uv for Python backend
7. **Testing**: Maintain comprehensive test coverage for both frontend and backend

### Current File Organization:
- `project_plan.md` - Development plan with phases completion status
- `quick_notes.md` - Original specification document  
- `ryagent/app/server.py` - FastAPI JSON API server with frontend serving
- `ryagent/core/models.py` - Pydantic data models
- `ryagent/utils/auth.py` - Token-based authentication
- `frontend/` - Complete React + Next.js application
  - `frontend/src/app/` - Next.js app router pages
  - `frontend/src/components/` - React components and ShadCN UI
  - `frontend/src/lib/` - API client and utilities
  - `frontend/src/contexts/` - React context providers
- `tests/` - Unit and integration tests

### Phase 2 Accomplishments:
- ✅ **React + Next.js frontend** with TypeScript and ShadCN UI
- ✅ **FastAPI JSON API** with CORS and proper error handling
- ✅ **Authentication system** with React context and token management
- ✅ **Modern development stack** (Bun, Tailwind, professional components)
- ✅ **Production deployment** (single server serves API + frontend)
- ✅ **Type-safe API client** with full TypeScript integration

## Important Notes

- **License:** AGPL-3.0 (network copyleft)  
- **Python:** 3.11+ required
- **Node.js:** Bun runtime for optimal frontend development
- **Philosophy:** Local-first, security by design, modern web stack
- **Status:** Phase 2 complete, ready for Phase 3 (LLM + real-time features)
- Modern React frontend with production-ready FastAPI backend