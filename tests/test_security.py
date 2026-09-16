import os

os.environ.setdefault("LLM_API_KEY", "test-api-key")
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("APP_API_KEY", "test-app-key")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_does_not_require_api_key():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_rag_requires_api_key():
    response = client.post(
        "/rag/chat",
        json={
            "question": "远程办公制度是什么?",
            "top_k": 3,
        },
    )

    assert response.status_code == 401