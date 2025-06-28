from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_stream_basic():
    response = client.get("/chat_stream/Hello")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    # Optionally read chunks
    events = list(response.iter_lines())
    assert any(b'"type": "content"' in e for e in events)
