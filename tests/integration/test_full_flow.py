"""Integration tests for full user workflows with JSON API."""

import pytest
from fastapi.testclient import TestClient

from ryagent.app.server import app


@pytest.fixture
def client():
    """Test client for integration tests."""
    return TestClient(app)


def test_complete_user_flow(client):
    """Test complete user workflow: create tab, send message, view responses."""
    # 1. Authenticate and get token
    auth_response = client.get("/api/auth/token")
    assert auth_response.status_code == 200
    token = auth_response.json()["token"]

    # Validate token works
    validate_response = client.post("/api/auth/validate", json={"token": token})
    assert validate_response.status_code == 200
    assert validate_response.json()["valid"] is True

    # 2. Check health
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "healthy"

    # 3. List tabs initially (should be empty or have existing tabs)
    initial_tabs_response = client.get("/api/tabs")
    assert initial_tabs_response.status_code == 200
    initial_tabs = initial_tabs_response.json()["tabs"]
    initial_count = len(initial_tabs)

    # 4. Create a new tab
    tab_data = {
        "name": "Integration Test Tab",
        "model": "gpt-4o-mini",
        "system_prompt": "You are a helpful integration test assistant.",
    }
    create_response = client.post("/api/tabs", json=tab_data)
    assert create_response.status_code == 200

    created_tab = create_response.json()
    assert created_tab["name"] == "Integration Test Tab"
    assert created_tab["model"] == "gpt-4o-mini"
    assert (
        created_tab["system_prompt"] == "You are a helpful integration test assistant."
    )
    assert "id" in created_tab
    assert created_tab["messages"] == []

    tab_id = created_tab["id"]

    # 5. Verify tab appears in list
    tabs_response = client.get("/api/tabs")
    assert tabs_response.status_code == 200
    tabs_data = tabs_response.json()
    assert len(tabs_data["tabs"]) == initial_count + 1

    # Find our tab
    our_tab = next(tab for tab in tabs_data["tabs"] if tab["id"] == tab_id)
    assert our_tab["name"] == "Integration Test Tab"

    # 6. Get individual tab
    tab_response = client.get(f"/api/tabs/{tab_id}")
    assert tab_response.status_code == 200
    tab_data = tab_response.json()
    assert tab_data["id"] == tab_id
    assert tab_data["name"] == "Integration Test Tab"
    assert len(tab_data["messages"]) == 0

    # 7. Send a message
    message_data = {"prompt": "Hello, integration test! How are you?"}
    message_response = client.post(f"/api/tabs/{tab_id}/messages", json=message_data)
    assert message_response.status_code == 200

    message_result = message_response.json()
    assert message_result["status"] == "success"
    assert len(message_result["messages"]) == 2  # User + assistant

    user_msg, assistant_msg = message_result["messages"]
    assert user_msg["role"] == "user"
    assert user_msg["content"] == "Hello, integration test! How are you?"
    assert assistant_msg["role"] == "assistant"
    assert "Echo: Hello, integration test!" in assistant_msg["content"]

    # 8. Verify messages are stored in tab
    updated_tab_response = client.get(f"/api/tabs/{tab_id}")
    updated_tab = updated_tab_response.json()
    assert len(updated_tab["messages"]) == 2
    assert updated_tab["messages"][0]["role"] == "user"
    assert updated_tab["messages"][1]["role"] == "assistant"

    # 9. Send another message to test conversation continuity
    second_message = {"prompt": "What was my first message?"}
    second_response = client.post(f"/api/tabs/{tab_id}/messages", json=second_message)
    assert second_response.status_code == 200

    # 10. Verify conversation has grown
    final_tab_response = client.get(f"/api/tabs/{tab_id}")
    final_tab = final_tab_response.json()
    assert len(final_tab["messages"]) == 4  # 2 user + 2 assistant messages

    # 11. Clean up - delete the tab
    delete_response = client.delete(f"/api/tabs/{tab_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "deleted"

    # 12. Verify tab is deleted
    deleted_tab_response = client.get(f"/api/tabs/{tab_id}")
    assert deleted_tab_response.status_code == 404

    # 13. Verify tab list is back to original count
    final_tabs_response = client.get("/api/tabs")
    final_tabs = final_tabs_response.json()["tabs"]
    assert len(final_tabs) == initial_count


def test_multiple_tabs_workflow(client):
    """Test managing multiple tabs simultaneously."""
    # Create multiple tabs
    tab_names = ["Tab A", "Tab B", "Tab C"]
    created_tabs = []

    for name in tab_names:
        response = client.post("/api/tabs", json={"name": name})
        assert response.status_code == 200
        created_tabs.append(response.json())

    # Verify all tabs exist
    tabs_response = client.get("/api/tabs")
    tabs = tabs_response.json()["tabs"]
    for created_tab in created_tabs:
        found = any(tab["id"] == created_tab["id"] for tab in tabs)
        assert found, f"Tab {created_tab['name']} not found in tab list"

    # Send messages to each tab
    for i, tab in enumerate(created_tabs):
        message = {"prompt": f"Message to {tab['name']} - number {i + 1}"}
        response = client.post(f"/api/tabs/{tab['id']}/messages", json=message)
        assert response.status_code == 200

    # Verify each tab has its message
    for i, tab in enumerate(created_tabs):
        response = client.get(f"/api/tabs/{tab['id']}")
        tab_data = response.json()
        assert len(tab_data["messages"]) == 2  # User + assistant
        assert f"number {i + 1}" in tab_data["messages"][0]["content"]

    # Clean up all tabs
    for tab in created_tabs:
        response = client.delete(f"/api/tabs/{tab['id']}")
        assert response.status_code == 200


def test_error_handling_integration(client):
    """Test error handling in realistic scenarios."""
    # Test frontend serving when frontend not built
    response = client.get("/")
    assert response.status_code == 200
    # Either serves frontend or returns JSON message

    # Test invalid API endpoints
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    assert "API endpoint not found" in response.json()["detail"]

    # Test accessing non-existent tab
    response = client.get("/api/tabs/nonexistent-tab-id")
    assert response.status_code == 404

    # Test sending message to non-existent tab
    response = client.post(
        "/api/tabs/nonexistent-tab-id/messages", json={"prompt": "Test message"}
    )
    assert response.status_code == 404

    # Test deleting non-existent tab
    response = client.delete("/api/tabs/nonexistent-tab-id")
    assert response.status_code == 404

    # Test invalid tab creation
    response = client.post(
        "/api/tabs", json={"model": "gpt-4"}
    )  # Missing required name
    assert response.status_code == 422

    # Test invalid message data
    response = client.post("/api/tabs/any-id/messages", json={})  # Missing prompt
    assert response.status_code == 422


def test_authentication_integration(client):
    """Test authentication flows in integration context."""
    # Get server token
    token_response = client.get("/api/auth/token")
    assert token_response.status_code == 200
    server_token = token_response.json()["token"]

    # Test valid token validation
    validate_response = client.post("/api/auth/validate", json={"token": server_token})
    assert validate_response.status_code == 200
    assert validate_response.json()["valid"] is True

    # Test invalid token validation
    invalid_response = client.post(
        "/api/auth/validate", json={"token": "invalid-token"}
    )
    assert invalid_response.status_code == 200
    assert invalid_response.json()["valid"] is False

    # Test that API endpoints work (no auth enforcement in current implementation)
    response = client.get("/api/tabs")
    assert response.status_code == 200

    # Test health check doesn't require auth
    health_response = client.get("/health")
    assert health_response.status_code == 200
