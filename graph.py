# graph.py
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage
from tools.tavily_tool import tavily_tool
from states.states import State

# Define the tools to use
tools = [tavily_tool]

# Set up persistent memory
memory = MemorySaver()

# Initialize the model and bind the tools
llm = init_chat_model("gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# Model node: processes user input and returns message
def chatAgent(state: State):
    # Use the latest state["messages"] to get model response
    message = llm.invoke(state["messages"])
    assert len(message.tool_calls) <= 1  # Assuming at most 1 tool call
    return {"messages": state["messages"] + [message]}

# Tool node handles any tools invoked by the model
# tool_node = ToolNode(tools=tools)

# Set up the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("model", chatAgent)
# graph_builder.add_node("tool_node", tool_node)

# Set entry point
graph_builder.set_entry_point("model")

# Route tool calls to "tool_node"
# tool_cond = tools_condition(tools)  # ❌ Removed invalid `default=` argument
# graph_builder.add_conditional_edges("model", tool_cond)
#
# # After tool response, go back to the model
# graph_builder.add_edge("tool_node", "model")

# Compile the graph with memory and automatic message appending
graph = graph_builder.compile(
    checkpointer=memory
)
