from graph import graph
from langchain_core.messages import AIMessage

def test_graph_basic():
    input_state = {"messages": [{"role": "user", "content": "What's the capital of France?"}]}
    config = {"configurable": {"thread_id": "test-thread"}}

    outputs = list(graph.stream(input_state, config, stream_mode=["updates"]))
    has_content = any(
        isinstance(event[-1].get("agent", {}).get("messages", [])[-1], AIMessage)
        for event in outputs if event[0] == "updates"
    )
    assert has_content
