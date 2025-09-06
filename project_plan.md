# RyAgent Project Plan

## Vision

A local Python daemon serving multiple LLM agents through a modern React web interface. The backend provides a robust JSON API while the frontend offers a professional, type-safe UI with real-time capabilities.

## Architecture Overview

### Modern Two-Layer Architecture
1. **Python Backend (FastAPI)**: JSON API server handling agents, LLM communication, and data management
2. **React Frontend (Next.js + TypeScript)**: Modern web application with professional UI components

### How They Work Together

**Python Backend Responsibilities:**
- FastAPI JSON API server with CORS support
- Agent state management and LLM communication
- Tool execution with sandboxing
- WebSocket/SSE for real-time updates (Phase 3)
- Pydantic data validation and serialization
- Token-based authentication

**React Frontend Responsibilities:**
- Professional UI with ShadCN components
- Type-safe API client with full TypeScript coverage
- React Context for state management and authentication
- Real-time updates via WebSocket/SSE integration
- Responsive design with Tailwind CSS
- Hot reload development experience

**Integration Points:**
- React frontend makes HTTP requests to FastAPI JSON API
- TypeScript interfaces match Pydantic models for full type safety
- Authentication handled via React Context and token storage
- API client provides error handling and loading states
- Development: Two-server setup (React dev server + FastAPI)
- Production: Single server serves both API and built frontend

## Project Structure

```
ryagent/
├── pyproject.toml           # Python dependencies and tools
├── README.md                # Complete setup and usage guide
├── CLAUDE.md                # Development guidelines
├── project_plan.md          # This document
├── ryagent/                 # Python backend
│   ├── __init__.py
│   ├── main.py              # CLI entry point (starts uvicorn)
│   ├── app/
│   │   └── server.py        # FastAPI JSON API server
│   ├── core/                # Backend logic
│   │   ├── __init__.py
│   │   ├── models.py        # Pydantic data models
│   │   ├── agents.py        # Agent management (Phase 3)
│   │   ├── llm.py           # LLM client adapters (Phase 3)
│   │   └── tools.py         # Tool registry and execution (Phase 3)
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py      # Configuration with auth token
│   └── utils/
│       ├── __init__.py
│       └── auth.py          # Token handling utilities
├── frontend/                # React + Next.js frontend
│   ├── package.json         # Frontend dependencies
│   ├── next.config.js       # Next.js configuration
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   ├── tsconfig.json        # TypeScript configuration
│   ├── src/
│   │   ├── app/             # Next.js app router
│   │   │   ├── layout.tsx   # Root layout with providers
│   │   │   ├── page.tsx     # Main dashboard component
│   │   │   └── globals.css  # Global styles with CSS variables
│   │   ├── components/
│   │   │   └── ui/          # ShadCN UI components
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── tabs.tsx
│   │   │       └── input.tsx
│   │   ├── lib/
│   │   │   ├── utils.ts     # Utility functions (cn helper)
│   │   │   └── api.ts       # Type-safe API client
│   │   └── contexts/
│   │       └── AuthContext.tsx # Authentication context
└── tests/                   # Comprehensive test suite
    ├── test_api.py          # API endpoint tests (7 tests)
    └── integration/
        └── test_full_flow.py # End-to-end workflow tests (4 tests)
```

## React + FastAPI Integration

### 1. API Client with Full Type Safety

**TypeScript API Client:**
```typescript
// src/lib/api.ts
interface Tab {
  id: string;
  name: string;
  model: string;
  system_prompt: string;
  messages: Message[];
  created_at: string;
  last_accessed: string;
}

class RyAgentAPI {
  async getTabs(): Promise<{ tabs: Tab[] }> {
    return this.request('/api/tabs');
  }
  
  async createTab(data: TabCreateRequest): Promise<Tab> {
    return this.request('/api/tabs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}
```

### 2. React Components with ShadCN UI

**Modern Component Architecture:**
```typescript
// src/app/page.tsx
export default function Dashboard() {
  const { isAuthenticated } = useAuth();
  const [tabs, setTabs] = useState<Tab[]>([]);
  
  const createTab = async () => {
    const newTab = await api.createTab({ name: 'New Tab' });
    setTabs([...tabs, newTab]);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent Tabs</CardTitle>
      </CardHeader>
      <CardContent>
        {tabs.map(tab => (
          <TabItem key={tab.id} tab={tab} />
        ))}
      </CardContent>
    </Card>
  );
}
```

### 3. Authentication with React Context

**Auth Flow:**
```typescript
// src/contexts/AuthContext.tsx
export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  
  useEffect(() => {
    // Auto-fetch token from server or localStorage
    initializeAuth();
  }, []);
  
  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}
```

## Development Protocol

### Setup and Environment
1. **Python Version**: 3.11+ required
2. **Node Runtime**: Bun (recommended) or Node.js 18+
3. **Package Managers**: `uv` for Python, `bun` for frontend

### Development Workflow

#### Initial Setup
```bash
# Clone and setup
git clone <repo>
cd ryagent

# Backend setup
uv sync                    # Install Python dependencies

# Frontend setup  
cd frontend
bun install               # Install frontend dependencies
```

#### Development Mode (Two Terminals)
```bash
# Terminal 1: Backend API server
uv run python -m ryagent.main --dev

# Terminal 2: Frontend dev server
cd frontend && bun run dev

# Open http://localhost:3000 (dev) or http://localhost:8000 (prod)
```

#### Production Build
```bash
# Build frontend for production
cd frontend && bun run build

# Start unified server (serves API + frontend)
uv run python -m ryagent.main
```

#### Daily Development
```bash
# Format code
uv run ruff format .           # Python
cd frontend && bun run lint    # TypeScript/React

# Run tests
uv run pytest                 # Backend tests
uv run pytest -v             # Verbose output
```

### Code Quality Standards

**Backend (Python):**
- **Formatting**: `ruff format` before committing
- **Linting**: Fix all `ruff check` issues  
- **Type Hints**: Required on all public functions
- **Models**: Use Pydantic for all data validation
- **Error Handling**: Proper HTTP status codes with meaningful messages

**Frontend (React):**
- **TypeScript**: Strict mode enabled, no `any` types
- **Components**: Functional components with hooks
- **Styling**: Tailwind CSS classes, ShadCN variants
- **State**: React Context for global state, useState for local
- **API**: Always use the typed API client

### Testing Protocol

#### Test Categories
1. **Unit Tests (Backend)**: Models, utilities, individual endpoints
2. **Integration Tests**: Complete user workflows, multi-step operations
3. **Type Tests**: TypeScript compilation ensures API contract adherence
4. **Security Tests**: Authentication, input validation

#### Test Coverage (Current: 11 Tests)
```bash
# Quick feedback
uv run pytest tests/test_api.py -v     # API tests only

# Full suite
uv run pytest                         # All tests

# Integration tests  
uv run pytest tests/integration/      # Full workflows

# Specific patterns
uv run pytest -k "auth"               # Authentication tests
uv run pytest -k "crud"               # CRUD operation tests
```

## Key Dependencies

### Python Backend
- `fastapi` - Modern web framework with automatic OpenAPI docs
- `uvicorn` - Fast ASGI server with auto-reload
- `pydantic` - Data validation and serialization
- `python-dotenv` - Environment variable management
- `structlog` - Structured logging
- `httpx` - HTTP client for testing and LLM APIs (Phase 3)

### React Frontend
- `react` + `next.js` - Modern React framework with app router
- `typescript` - Type safety and enhanced development experience
- `@radix-ui/*` - Accessible component primitives for ShadCN
- `tailwindcss` - Utility-first CSS framework
- `lucide-react` - Beautiful icon library
- `class-variance-authority` + `clsx` - Dynamic styling utilities

### Development Tools
- `bun` - Fast package manager and runtime for frontend
- `ruff` - Fast Python linting and formatting
- `pytest` - Testing framework with async support
- `eslint` + `prettier` - Frontend code quality tools

## Development Phases

### ✅ Phase 1: HTMX Foundation (COMPLETED)
- [x] Basic FastAPI server with HTML templates
- [x] HTMX-based dynamic interactions  
- [x] Authentication system
- [x] Basic CRUD operations
- [x] Initial test suite

### ✅ Phase 2: React Migration (COMPLETED)
- [x] React + Next.js + TypeScript frontend
- [x] ShadCN UI component library integration
- [x] FastAPI conversion to JSON API
- [x] Type-safe API client with authentication
- [x] Modern development workflow (Bun, hot reload)
- [x] Updated comprehensive test suite (11 tests)
- [x] Production build and deployment setup

### 🔄 Phase 3: LLM Integration (NEXT)
- [ ] OpenAI/Anthropic API client integration
- [ ] Real message processing (replace echo mode)
- [ ] Streaming responses with Server-Sent Events
- [ ] WebSocket support for real-time updates
- [ ] Message history persistence
- [ ] Multiple model support and configuration

### 🔄 Phase 4: Advanced Features
- [ ] Tool system with sandboxed execution
- [ ] Agent configurations and templates
- [ ] Conversation export/import
- [ ] Multi-user support with proper auth
- [ ] Plugin system for custom tools
- [ ] Performance optimization and caching

### 🔄 Phase 5: Production Deployment  
- [ ] Docker containerization
- [ ] Environment-specific configuration
- [ ] Health monitoring and metrics
- [ ] Backup and recovery procedures
- [ ] Security hardening
- [ ] Documentation for production deployment

## 🎉 PHASE 2 COMPLETED!

### Current Implementation Status (2025-09-06)

**✅ Fully Implemented:**
```
ryagent/                     # CURRENT PRODUCTION STRUCTURE
├── pyproject.toml           # Python deps + dev tools (ruff, pytest)
├── README.md                # Complete setup guide with both modes
├── CLAUDE.md                # Updated development guidelines  
├── project_plan.md          # This updated planning document
├── LICENSE                  # AGPL-3.0 network copyleft
├── ryagent/                 # Python backend (JSON API)
│   ├── main.py              # ✅ CLI with FastAPI server
│   ├── app/
│   │   └── server.py        # ✅ Complete JSON API + frontend serving
│   ├── config/
│   │   └── settings.py      # ✅ Configuration with auto-token
│   ├── core/
│   │   └── models.py        # ✅ Pydantic models (Tab, Message)
│   └── utils/
│       └── auth.py          # ✅ Token authentication
├── frontend/                # ✅ React + Next.js + TypeScript
│   ├── package.json         # ✅ Bun-based dependencies
│   ├── next.config.js       # ✅ API proxy and static serving
│   ├── tailwind.config.js   # ✅ ShadCN configuration
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx   # ✅ Root layout with AuthProvider
│   │   │   ├── page.tsx     # ✅ Complete dashboard with tabs
│   │   │   └── globals.css  # ✅ Tailwind + CSS variables
│   │   ├── components/ui/   # ✅ ShadCN components
│   │   │   ├── button.tsx   # ✅ Styled button variants
│   │   │   ├── card.tsx     # ✅ Card layout components
│   │   │   ├── tabs.tsx     # ✅ Radix UI tabs
│   │   │   └── input.tsx    # ✅ Form input components
│   │   ├── lib/
│   │   │   ├── utils.ts     # ✅ Utility functions
│   │   │   └── api.ts       # ✅ Full type-safe API client
│   │   └── contexts/
│   │       └── AuthContext.tsx # ✅ Authentication management
└── tests/                   # ✅ Updated comprehensive test suite
    ├── test_api.py          # ✅ 7 comprehensive API tests
    └── integration/
        └── test_full_flow.py # ✅ 4 integration workflow tests
```

### Working Features:
- ✅ **Modern React Frontend**: TypeScript + ShadCN UI + Tailwind CSS
- ✅ **FastAPI JSON API**: RESTful endpoints with proper error handling
- ✅ **Type Safety**: Full TypeScript coverage with API client
- ✅ **Authentication**: React Context with token management
- ✅ **Development Experience**: Hot reload, linting, formatting
- ✅ **Production Build**: Single server deployment with frontend serving
- ✅ **Tab Management**: Complete CRUD operations with real-time UI updates
- ✅ **Message Interface**: Echo mode ready for LLM integration
- ✅ **Professional UI**: ShadCN components with responsive design
- ✅ **Testing**: 11 comprehensive tests covering API and workflows

### Architecture Benefits:
- **Scalability**: JSON API can support multiple frontend clients
- **Type Safety**: TypeScript interfaces prevent runtime errors
- **Developer Experience**: Modern tooling with fast iteration
- **Maintainability**: Clean separation of concerns
- **Performance**: Optimized builds with static asset serving
- **Accessibility**: ShadCN components with built-in a11y support

### Ready for Phase 3:
- 🔄 **LLM Integration**: API structure ready for OpenAI/Anthropic clients
- 🔄 **Real-time Updates**: WebSocket/SSE infrastructure planned
- 🔄 **Message Streaming**: Frontend ready for streaming responses
- 🔄 **Tool System**: Event models and execution framework ready
- 🔄 **Agent Management**: State management foundation established

**Phase 2 delivered a complete architectural transformation from HTMX to modern React while maintaining full functionality and comprehensive test coverage.**