import os

# Dummy credentials so importing the app never requires real API keys or a
# reachable Qdrant/Redis/Twilio/Tavily instance. Only set if not already
# present, so a real local .env (if loaded) is never overridden.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("TAVILY_API_KEY", "tvly-test-dummy")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("QDRANT_API_KEY", "test-dummy")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACtestdummy")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-dummy-token")
os.environ.setdefault("TWILIO_FROM_NUMBER", "+10000000000")
os.environ.setdefault("API_KEYS", "")
# Tests must never make real network calls, including tracing.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage


@pytest.fixture(autouse=True)
def mock_llm_chains(monkeypatch):
    """Prevent any test from making a real LLM API call. Patches the chain
    references at the point they're used (agents.*Node modules), not at
    their definition site, since those modules imported the names directly."""
    import agents.chatAgentNode as chat_agent_module
    import agents.reviewerAgentNode as reviewer_agent_module
    from chains.reviewerAgentChain import ReviewFeedback

    fake_ai_message = AIMessage(content="This is a mocked assistant response.")
    mock_chat_chain = MagicMock()
    mock_chat_chain.invoke.return_value = fake_ai_message
    monkeypatch.setattr(chat_agent_module, "chat_chain", mock_chat_chain)

    fake_feedback = ReviewFeedback(satisfied=True, critique=None, suggestions=None)
    mock_review_chain = MagicMock()
    mock_review_chain.invoke.return_value = fake_feedback
    monkeypatch.setattr(reviewer_agent_module, "review_chain", mock_review_chain)
