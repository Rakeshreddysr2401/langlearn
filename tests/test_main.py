from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_stream_basic():
    """API_KEYS is empty in the test environment (see conftest.py), so auth
    is disabled and this exercises the full request path with the chat/review
    LLM chains mocked."""
    response = client.get("/chat_stream/Hello")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = list(response.iter_lines())
    assert any('"type": "content"' in e for e in events)


def test_chat_stream_requires_api_key_when_configured(monkeypatch):
    import config
    config.get_settings.cache_clear()
    monkeypatch.setenv("API_KEYS", "secret-key")
    import main
    main.settings = config.get_settings()

    try:
        response = client.get("/chat_stream/Hello")
        assert response.status_code == 401
    finally:
        monkeypatch.delenv("API_KEYS", raising=False)
        config.get_settings.cache_clear()
        main.settings = config.get_settings()
