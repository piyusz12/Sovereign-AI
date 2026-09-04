import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_models_list():
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert "data" in data
    
    # We should have our 5 default models
    assert len(data["data"]) >= 5
    assert data["data"][0]["object"] == "model"
    assert data["data"][0]["owned_by"] == "sovereign"


def test_chat_completions_requires_user_message():
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "qwen3:14b",
            "messages": [{"role": "system", "content": "Hello"}]
        }
    )
    assert response.status_code == 400
    assert "No user message provided" in response.json()["detail"]


@pytest.mark.asyncio
async def test_chat_completions_valid_request(monkeypatch):
    """Test that a standard OpenAI payload returns a standard OpenAI response."""
    
    # Mock the router.route method to avoid actually calling the LLM
    async def mock_route(*args, **kwargs):
        return {
            "response": "Hello from mock",
            "classification": {"task_type": "reasoning"},
            "model_used": {"model_id": "qwen3:14b"},
            "metrics": {"eval_count": 10, "prompt_eval_count": 5}
        }
        
    from backend.router.router import ModelRouter
    monkeypatch.setattr(ModelRouter, "route", mock_route)
    
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "qwen3:14b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hi"}
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert "id" in data
    assert data["model"] == "qwen3:14b"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert data["choices"][0]["message"]["content"] == "Hello from mock"
    assert data["usage"]["prompt_tokens"] == 5
    assert data["usage"]["completion_tokens"] == 10
    assert data["usage"]["total_tokens"] == 15
