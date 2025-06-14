# graph.py
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from tools.tavily_tool import tavily_tool


tools = [tavily_tool]

# Initialize LangGraph agent
model = init_chat_model("gpt-4o-mini", temperature=0)
agent = create_react_agent(
    model=model.bind_tools(tools, parallel_tool_calls=False),
    tools=tools
)
