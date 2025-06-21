import json
from uuid import uuid4
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import  AIMessageChunk
from langgraph.types import Command

# from tools.human_tool import book_hotel

from tools.tavily_tool import tavily_tool

# Load environment variables
load_dotenv()

# Define the state used in the graph
class State(MessagesState):
    context: str = "You are a helpful assistant."

# Define tools
tools = [tavily_tool]  # Add additional tools here if needed

# Initialize model
llm = init_chat_model("gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# LLM node: add assistant's response to the state
def chat_agent(state: State):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": messages + [response]}

# ToolNode handles tool calling and appends tool response
tool_node = ToolNode(tools)

# Build the LangGraph
graph_builder = StateGraph(State)
graph_builder.add_node("model", chat_agent)
graph_builder.add_node("tool_node", tool_node)
graph_builder.set_entry_point("model")

# Conditional edge to decide next node based on tool calls
graph_builder.add_conditional_edges(
    "model",
    lambda state: "tool_node" if any(
        hasattr(msg, "tool_calls") and msg.tool_calls for msg in state["messages"]
    ) else "__end__"
)

# After tool runs, go back to model
graph_builder.add_edge("tool_node", "model")

# Use memory checkpointing
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# # Example usage
# if __name__ == "__main__":
#     thread_id = 1
#     init_state = {
#         "messages": [
#             {"role": "user", "content": input("Enter your message: ")}
#         ]
#     }
#     config = {"configurable": {"thread_id": thread_id}}
#
#     response = ""
#     tool_content = {}
#     tool_name = ""
#
#
#     current_state = init_state
#
#
#     is_intterrupted = False
#     # Check if graph is interrupted
#     try:
#         snapshot = graph.get_state(config)
#         is_interrupted = snapshot.next and len(snapshot.next) > 0
#     except:
#         is_interrupted = False
#
#     # Decide input type based on interrupt status
#     if is_interrupted:
#         # Graph is interrupted, send command to resume
#         current_state = Command(resume=input("Resume graph? (accept/reject): ").strip().lower())
#         print("🔄 Resuming interrupted graph...")
#     else:
#         # Normal flow, send message
#         current_state = init_state
#         print("💬 Starting new conversation...")
#
#
#
#     for chunk, meta in graph.stream(current_state, config=config, stream_mode="messages"):
#
#         # Detect tool call
#         if isinstance(chunk, AIMessageChunk) and chunk.tool_calls:
#             for tool in chunk.tool_calls:
#                 if tool["type"] == "tool_call" and tool["name"]:
#                     tool_name = tool["name"]
#                     print("🔧 Tool name:", tool["name"])
#
#         # Extract content from tool output node
#         if meta.get("langgraph_node") == "tool_node":
#             #print("chunk:", chunk.content)
#             try:
#                 parsed_content = json.loads(chunk.content)
#                 for info in parsed_content:
#                     print("🔧 Tool info:", info)
#                     if "title" in info and "url" in info:
#                         #print("Title vs Content:", info["url"],info["title"])
#                         tool_content[info["title"]] = info["url"]
#             except json.JSONDecodeError as e:
#                 print("❌ Failed to parse JSON from chunk content:", e)
#             print("🔧 Tool content:", tool_content)
#         if meta.get("langgraph_node") == "model" and isinstance(chunk, AIMessageChunk):
#             response += chunk.content
#             print("📨 Model response so far:", response)
#
#
#     # Final output
#     print("\n✅ Final Response:\n", response)
#     print("\n🔗 Final Tool Links:\n", tool_content)
#
