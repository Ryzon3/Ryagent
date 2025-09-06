"""Test FastAPI JSON API endpoints."""

import pytest
from fastapi.testclient import TestClient

from ryagent.app.server import app
from ryagent.config.settings import settings


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "tabs_count" in data
    assert "version" in data


def test_auth_endpoints(client):
    """Test authentication endpoints."""
    # Test token validation
    response = client.post("/api/auth/validate", json={"token": settings.auth_token})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True

    # Test invalid token
    response = client.post("/api/auth/validate", json={"token": "invalid"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False

    # Test get token
    response = client.get("/api/auth/token")
    assert response.status_code == 200
    data = response.json()
    assert "token" in data


def test_tabs_crud_operations(client):
    """Test complete CRUD operations for tabs."""
    # 1. List tabs (should be empty initially)
    response = client.get("/api/tabs")
    assert response.status_code == 200
    initial_tabs = response.json()["tabs"]

    # 2. Create a tab
    tab_data = {
        "name": "Test Tab",
        "model": "gpt-4o-mini",
        "system_prompt": "You are a test assistant.",
    }
    response = client.post("/api/tabs", json=tab_data)
    assert response.status_code == 200

    created_tab = response.json()
    assert created_tab["name"] == "Test Tab"
    assert created_tab["model"] == "gpt-4o-mini"
    assert created_tab["system_prompt"] == "You are a test assistant."
    assert "id" in created_tab
    assert "created_at" in created_tab
    assert created_tab["messages"] == []

    tab_id = created_tab["id"]

    # 3. List tabs (should now have one)
    response = client.get("/api/tabs")
    assert response.status_code == 200
    tabs = response.json()["tabs"]
    assert len(tabs) == len(initial_tabs) + 1

    # 4. Get specific tab
    response = client.get(f"/api/tabs/{tab_id}")
    assert response.status_code == 200
    tab = response.json()
    assert tab["id"] == tab_id
    assert tab["name"] == "Test Tab"

    # 5. Delete the tab
    response = client.delete(f"/api/tabs/{tab_id}")
    assert response.status_code == 200
    delete_result = response.json()
    assert delete_result["status"] == "deleted"

    # 6. Verify tab is deleted
    response = client.get(f"/api/tabs/{tab_id}")
    assert response.status_code == 404


def test_messaging(client):
    """Test messaging functionality."""
    # Create a tab first
    tab_data = {"name": "Chat Tab", "model": "gpt-4o-mini"}
    response = client.post("/api/tabs", json=tab_data)
    tab_id = response.json()["id"]

    # Send a message
    message_data = {"prompt": "Hello, world!"}
    response = client.post(f"/api/tabs/{tab_id}/messages", json=message_data)
    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "success"
    assert "messages" in result
    assert len(result["messages"]) == 2  # User + assistant message

    # Check the messages
    user_msg, assistant_msg = result["messages"]
    assert user_msg["role"] == "user"
    assert user_msg["content"] == "Hello, world!"
    assert assistant_msg["role"] == "assistant"
    assert "Echo: Hello, world!" in assistant_msg["content"]

    # Verify messages are stored in the tab
    response = client.get(f"/api/tabs/{tab_id}")
    tab = response.json()
    assert len(tab["messages"]) == 2


def test_error_handling(client):
    """Test error handling for various scenarios."""
    # Test getting non-existent tab
    response = client.get("/api/tabs/nonexistent")
    assert response.status_code == 404

    # Test deleting non-existent tab
    response = client.delete("/api/tabs/nonexistent")
    assert response.status_code == 404

    # Test sending message to non-existent tab
    response = client.post("/api/tabs/nonexistent/messages", json={"prompt": "test"})
    assert response.status_code == 404

    # Test invalid tab creation (missing name)
    response = client.post("/api/tabs", json={"model": "gpt-4"})
    assert response.status_code == 422


def test_frontend_serving(client):
    """Test frontend serving endpoints."""
    # Test main route returns either frontend or API message
    response = client.get("/")
    assert response.status_code == 200
    # Will return either the React app or a message about frontend not built

    # Test API routes are not intercepted by frontend catch-all
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "API endpoint not found"


def test_tab_data_validation(client):
    """Test tab data validation."""
    # Test with minimal valid data
    response = client.post("/api/tabs", json={"name": "Minimal Tab"})
    assert response.status_code == 200
    tab = response.json()
    assert tab["model"] == "gpt-4o-mini"  # Default model
    assert tab["system_prompt"] == "You are a helpful assistant."  # Default prompt

    # Test with all fields
    tab_data = {"name": "Full Tab", "model": "gpt-4", "system_prompt": "Custom prompt"}
    response = client.post("/api/tabs", json=tab_data)
    assert response.status_code == 200
    tab = response.json()
    assert tab["name"] == "Full Tab"
    assert tab["model"] == "gpt-4"
    assert tab["system_prompt"] == "Custom prompt"
