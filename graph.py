from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from agents.chatAgentNode import chatAgent
from agents.reviewerAgentNode  import reviewerAgent
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

# Conditional edge: chatAgent → (tools or review)
graph_builder.add_conditional_edges(
    "chatAgent",
    lambda s: "tools" if getattr(s["messages"][-1], "tool_calls", None) else "reviewer",
    {"tools": "tools", "reviewer": "reviewerAgent"}
)

# After tool use → back to chatAgent
graph_builder.add_edge("tools", "chatAgent")

# Conditional edge: reviewerAgent → (chatAgent if retry, else END)
graph_builder.add_conditional_edges(
    "reviewerAgent",
    lambda s: "chatAgent" if s.get("review_feedback") and s["review_feedback"].get("satisfied") is False else END,
    {"chatAgent": "chatAgent", END: END}
)

#  Compile graph
graph = graph_builder.compile(checkpointer=memory)
