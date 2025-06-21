# graph.py
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.types import Command, interrupt

from tools.tavily_tool import tavily_tool
from states.states import State

# Define the tools to use
tools = [tavily_tool]

# Set up persistent memory
memory = MemorySaver()

# Initialize the model and bind the tools
llm = init_chat_model("gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools)


def chatAgent(state: State):
    """
    Model node: processes user input and returns message.
    The model can decide to call tools or respond directly.
    """
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: State):
    """
    Conditional edge function to determine next step.
    Returns "tools" if the last message has tool calls, otherwise "end".
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "end"


# Tool node handles any tools invoked by the model
tool_node = ToolNode(tools=tools)

# Set up the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("agent", chatAgent)
graph_builder.add_node("tools", tool_node)

# Set entry point
graph_builder.set_entry_point("agent")

# Add conditional edges
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)

# After tool execution, return to agent for final response
graph_builder.add_edge("tools", "agent")

# Compile the graph with memory
graph = graph_builder.compile(checkpointer=memory)

#
#
# if __name__ == "__main__":
#     while True:
#         snapshot = graph.get_state(config)
#         # print(f"shot;{snapshot}")
#         if "human_assistance" in snapshot.next:
#             user_input=Command(resume={"data":input("Please Enter your response: ")})
#         else:
#             user_input = {"messages": [{"role": "user", "content": input("User:")}]}
#         for event in graph.invoke(user_input, config,stream_mode="updates"):
#             print("EVENT ",event)
#             print("Event Type:", type(event))
#             if list(event.keys())[0] == "__interrupt__":
#                 print("'__interupt__'",event.get("__interrupt__")[0].value['query'])
#             else:
#                 for value in event.values():
#                     if "messages" in value and isinstance(value["messages"][-1], HumanMessage):
#                         print("Human Message",value["messages"][-1].content)
#                     elif "messages" in value  and isinstance(value["messages"][-1], AIMessage) and not getattr(value["messages"][-1], "tool_calls", []):
#                         print("AI Message:",value["messages"][-1].content)
#                     else:
#                         print("Other Message:", value)