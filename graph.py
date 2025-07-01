from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from agents.chatAgentNode import chatAgent
from agents.reviewerAgentNode import reviewerAgent
from states.states import State
from tools import get_tools

tools = get_tools()
memory = MemorySaver()

# Build the graph
graph_builder = StateGraph(State)

graph_builder.add_node("chatAgent", chatAgent)
graph_builder.add_node("reviewerAgent", reviewerAgent)
graph_builder.add_node("tools", ToolNode(tools=tools))

graph_builder.set_entry_point("chatAgent")


# chatAgent → (tools or reviewer or END)
def chat_agent_transition(state):
    messages = state.get("messages", [])
    retry_count = state.get("retry_count", 0)

    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        return "tools"
    if retry_count > 2:
        return "end"

    return "reviewer"


graph_builder.add_conditional_edges(
    "chatAgent",
    chat_agent_transition,
    {"tools": "tools", "reviewer": "reviewerAgent", "end": END}
)

graph_builder.add_edge("tools", "chatAgent")


# reviewerAgent → (chatAgent if retry, else END)
def reviewer_transition(state):
    feedback = state.get("review_feedback")
    retry_count = state.get("retry_count", 0)

    if feedback and feedback.get("satisfied") is True:
        return END

    if feedback and feedback.get("satisfied") is False:
        if retry_count <= 2:
            return "chatAgent"
        else:
            return END

    return END


graph_builder.add_conditional_edges(
    "reviewerAgent",
    reviewer_transition,
    {"chatAgent": "chatAgent", END: END}
)

graph = graph_builder.compile(checkpointer=memory)
