# graph.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from agents.chatAgentNode import chatAgent
from agents.reviewerAgentNode import reviewerAgent
from configs.memory_config import get_memory
from states.states import State
from tools import get_tools

# Constants
MAX_RETRIES = 2


def create_chat_graph():
    """Create and return the compiled chat graph."""
    tools = get_tools()
    memory = get_memory()

    # Build the graph
    graph_builder = StateGraph(State)

    # Add nodes
    graph_builder.add_node("chatAgent", chatAgent)
    graph_builder.add_node("reviewerAgent", reviewerAgent)
    graph_builder.add_node("tools", ToolNode(tools=tools))

    # Set entry point
    graph_builder.set_entry_point("chatAgent")

    def chat_agent_transition(state):
        """Determine next step after chatAgent."""
        messages = state.get("messages", [])
        retry_count = state.get("retry_count", 0)

        # Check if last message has tool calls
        if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "tools"

        # Always go to reviewer - let reviewer handle max retries
        return "reviewerAgent"

    def reviewer_transition(state):
        """Determine next step after reviewerAgent."""
        feedback = state.get("review_feedback", {})
        retry_count = state.get("retry_count", 0)
        satisfied = feedback.get("satisfied", True)

        if satisfied or retry_count > MAX_RETRIES:
            return END
        elif not satisfied and retry_count <= MAX_RETRIES:
            return "chatAgent"
        return END

    # Add conditional edges
    graph_builder.add_conditional_edges(
        "chatAgent",
        chat_agent_transition,
        {
            "tools": "tools",
            "reviewerAgent": "reviewerAgent"
        }
    )

    graph_builder.add_edge("tools", "chatAgent")

    graph_builder.add_conditional_edges(
        "reviewerAgent",
        reviewer_transition,
        {
            "chatAgent": "chatAgent",
            END: END
        }
    )

    return graph_builder.compile(checkpointer=memory)


# Create the graph instance
graph = create_chat_graph()