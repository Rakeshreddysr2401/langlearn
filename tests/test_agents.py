from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

import agents.chatAgentNode as chat_agent_module
import agents.reviewerAgentNode as reviewer_agent_module
from agents.chatAgentNode import chatAgent
from agents.reviewerAgentNode import reviewerAgent
from chains.reviewerAgentChain import ReviewFeedback


def test_chat_agent_returns_response(monkeypatch):
    fake_response = AIMessage(content="Paris is the capital of France.")
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = fake_response
    monkeypatch.setattr(chat_agent_module, "chat_chain", mock_chain)

    state = {
        "messages": [HumanMessage(content="What's the capital of France?")],
        "retry_count": 0,
        "review_feedback": {},
    }

    result = chatAgent(state)

    assert result["chatAgentResponse"] == fake_response
    assert result["messages"][-1] == fake_response


def test_reviewer_agent_accepts_satisfied_response(monkeypatch):
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = ReviewFeedback(satisfied=True, critique=None, suggestions=None)
    monkeypatch.setattr(reviewer_agent_module, "review_chain", mock_chain)
    monkeypatch.setattr(reviewer_agent_module, "get_stream_writer", lambda: MagicMock())

    state = {
        "messages": [HumanMessage(content="What's the capital of France?")],
        "users_query": "What's the capital of France?",
        "retry_count": 0,
        "chatAgentResponse": AIMessage(content="Paris."),
    }

    result = reviewerAgent(state)

    assert result["review_feedback"]["satisfied"] is True
    assert result["retry_count"] == 0


def test_reviewer_agent_requests_retry_when_unsatisfied(monkeypatch):
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = ReviewFeedback(
        satisfied=False, critique="Too vague", suggestions=["Be more specific"]
    )
    monkeypatch.setattr(reviewer_agent_module, "review_chain", mock_chain)

    state = {
        "messages": [HumanMessage(content="What's the capital of France?")],
        "users_query": "What's the capital of France?",
        "retry_count": 0,
        "chatAgentResponse": AIMessage(content="Somewhere in Europe."),
    }

    result = reviewerAgent(state)

    assert result["review_feedback"]["satisfied"] is False
    assert result["retry_count"] == 1


def test_reviewer_agent_stops_after_max_retries(monkeypatch):
    from configs.constants import MAX_RETRIES

    mock_chain = MagicMock()
    monkeypatch.setattr(reviewer_agent_module, "review_chain", mock_chain)
    monkeypatch.setattr(reviewer_agent_module, "get_stream_writer", lambda: MagicMock())

    state = {
        "messages": [HumanMessage(content="Hi")],
        "users_query": "Hi",
        "retry_count": MAX_RETRIES,
        "chatAgentResponse": AIMessage(content="Final answer."),
    }

    result = reviewerAgent(state)

    assert result["review_feedback"]["satisfied"] is True
    mock_chain.invoke.assert_not_called()
