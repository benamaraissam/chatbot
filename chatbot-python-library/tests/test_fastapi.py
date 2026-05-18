"""FastAPI adapter tests."""


import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot import Chatbot
from chatbot.integrations.fastapi import create_router
from chatbot.protocol.schemas import PROTOCOL_VERSION


@pytest.fixture
def client():
    bot = Chatbot(default_provider="mock", storage="memory")
    app = FastAPI()
    app.include_router(create_router(bot), prefix="/api/chat")
    return TestClient(app)


def test_health(client):
    r = client.get("/api/chat/health")
    assert r.status_code == 200
    assert r.json()["protocol"] == PROTOCOL_VERSION


def test_chat_sse_with_zero_arg_user_context():
    """Regression: FastAPI must not pass ``request`` to callbacks that ignore it."""

    def get_user_context():
        return {"user_id": "user_42"}

    bot = Chatbot(default_provider="mock", storage="memory")
    app = FastAPI()
    app.include_router(create_router(bot, user_context=get_user_context), prefix="/api/chat")
    client = TestClient(app)

    payload = {
        "messages": [
            {"id": "m1", "role": "user", "parts": [{"type": "text", "text": "Hello"}]},
        ],
    }
    with client.stream("POST", "/api/chat/chat", json=payload) as response:
        assert response.status_code == 200


def test_chat_sse(client):
    payload = {
        "messages": [
            {"id": "m1", "role": "user", "parts": [{"type": "text", "text": "Hello"}]},
        ],
        "conversationId": "conv_1",
    }
    with client.stream("POST", "/api/chat/chat", json=payload) as response:
        assert response.status_code == 200
        assert response.headers.get("x-chatbot-protocol-version") == PROTOCOL_VERSION
        body = "".join(response.iter_text())
        assert "text_delta" in body
        assert "done" in body
