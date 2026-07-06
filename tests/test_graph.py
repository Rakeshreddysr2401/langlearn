from langchain_core.messages import AIMessage

from graph import graph


def test_graph_basic():
    """Runs the compiled graph end-to-end with the chat/review LLM chains
    mocked (see conftest.py) so no real LLM API call is made."""
    input_state = {
        "messages": [{"role": "user", "content": "What's the capital of France?"}],
        "users_query": "What's the capital of France?",
        "retry_count": 0,
        "review_feedback": {},
    }
    config = {"configurable": {"thread_id": "test-thread"}}

    outputs = list(graph.stream(input_state, config, stream_mode=["updates"]))

    has_ai_response = any(
        isinstance(msg, AIMessage)
        for _, event_data in outputs
        for node_value in event_data.values()
        for msg in node_value.get("messages", [])
    )
    assert has_ai_response
