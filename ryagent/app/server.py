"""RyAgent FastAPI Server - Clean and Simple"""

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from ryagent.config.settings import settings
from ryagent.core.models import Message, Tab, TabCreate

# ============================================================================
# APP SETUP
# ============================================================================

app = FastAPI(title="RyAgent API", version="0.1.0")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files if they exist (production mode)
frontend_dist_path = Path(__file__).parent.parent.parent / "frontend" / "out"
if frontend_dist_path.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(frontend_dist_path / "_next" / "static")),
        name="static",
    )
    app.mount(
        "/_next",
        StaticFiles(directory=str(frontend_dist_path / "_next")),
        name="nextjs",
    )


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


# Request/Response models
class TabCreateRequest(BaseModel):
    name: str
    model: str = "gpt-4o-mini"
    system_prompt: str = "You are a helpful assistant."


class MessageRequest(BaseModel):
    prompt: str


class AuthRequest(BaseModel):
    token: str


# In-memory storage (TODO: Replace with database)
tabs: dict[str, Tab] = {}


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================


@app.post("/api/auth/validate")
async def validate_token(auth_data: AuthRequest):
    """Validate authentication token"""
    if auth_data.token == settings.auth_token:
        return {"valid": True}
    else:
        return {"valid": False}


@app.get("/api/auth/token")
async def get_token():
    """Get the current auth token (for development)"""
    return {"token": settings.auth_token}


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.get("/api/tabs")
async def list_tabs():
    """Get all tabs as JSON"""
    return {"tabs": [tab.model_dump() for tab in tabs.values()]}


@app.get("/api/tabs/{tab_id}")
async def get_tab(tab_id: str):
    """Get a specific tab"""
    if tab_id not in tabs:
        raise HTTPException(status_code=404, detail="Tab not found")

    tab = tabs[tab_id]
    tab.last_accessed = datetime.now()
    return tab.model_dump()


@app.post("/api/tabs")
async def create_tab(tab_data: TabCreateRequest):
    """Create a new tab"""
    try:
        tab_create = TabCreate(
            name=tab_data.name,
            model=tab_data.model,
            system_prompt=tab_data.system_prompt,
        )
        new_tab = Tab(**tab_create.model_dump())
        tabs[new_tab.id] = new_tab
        return new_tab.model_dump()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e


@app.delete("/api/tabs/{tab_id}")
async def delete_tab(tab_id: str):
    """Delete a tab"""
    if tab_id not in tabs:
        raise HTTPException(status_code=404, detail="Tab not found")

    del tabs[tab_id]
    return {"status": "deleted"}


@app.post("/api/tabs/{tab_id}/messages")
async def send_message(tab_id: str, message_data: MessageRequest):
    """Send message to tab (Phase 1: Echo only)"""
    if tab_id not in tabs:
        raise HTTPException(status_code=404, detail="Tab not found")

    tab = tabs[tab_id]

    # Echo message (TODO: Replace with LLM integration)
    user_message = Message(role="user", content=message_data.prompt)
    assistant_message = Message(
        role="assistant",
        content=f"Echo: {message_data.prompt} (LLM integration coming in Phase 2)",
    )

    tab.messages.extend([user_message, assistant_message])
    return {
        "status": "success",
        "messages": [msg.model_dump() for msg in [user_message, assistant_message]],
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "version": "0.1.0", "tabs_count": len(tabs)}


# ============================================================================
# FRONTEND SERVING (Production)
# ============================================================================


@app.get("/")
async def serve_frontend():
    """Serve the React frontend index page"""
    index_path = frontend_dist_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return {
            "message": "RyAgent API is running! Frontend not built yet. Run `bun run build` in the frontend directory."
        }


# Catch-all route for React Router (SPA)
@app.get("/{full_path:path}")
async def serve_frontend_routes(full_path: str):
    """Catch-all route to serve React app for client-side routing"""
    # Don't intercept API routes
    if full_path.startswith("api/") or full_path.startswith("health"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Serve static assets directly
    if full_path.startswith("_next/") or full_path.startswith("static/"):
        file_path = frontend_dist_path / full_path
        if file_path.exists():
            return FileResponse(str(file_path))

    # For all other routes, serve the React app
    index_path = frontend_dist_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")
