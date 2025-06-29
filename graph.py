import json
from typing import Annotated, TypedDict, List, Optional
from uuid import uuid4

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from prompts import identity_prompt, get_retry_prompt, review_prompt

# Tools
from tools.tavily_tool import tavily_tool
from tools.twillo_tool import send_whatsapp_message
from Retrievers.qdrant_retriver import qdrant_search_tool

tools = [tavily_tool, send_whatsapp_message, qdrant_search_tool]

llm = init_chat_model("gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools)
memory = MemorySaver()




class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    chatAgentResponse: Optional[AIMessage]
    review_feedback: Optional[dict]
    retry_count: int
    final_response: Optional[AIMessage]
    users_query: Optional[str]

def chatAgent(state: State):
    messages = state["messages"]
    review = state.get("review_feedback")
    retry_count = state.get("retry_count", 0)

    if retry_count >= 3:
        print("⚠️ Maximum retries reached, providing best possible response")
        review = None  # Bypass further review

    # Prepare messages
    full_messages = messages
    if review and review.get("verdict") == "RETRY":
        full_messages=[get_retry_prompt(retry_count, review["critique"])]+messages

    # Generate response
    response = llm_with_tools.invoke(full_messages)

    return {
        "messages": [response],
        "retry_count": retry_count + 1 if review else 0,
        "final_response": response if not review or retry_count >= 3 else None,
        "chatAgentResponse": response,
    }



def reviewerAgent(state: State):
    if state["retry_count"] >= 3:
        # If max retries reached, skip review
        return {"review_feedback": None}

    messages = state["messages"]
    last_user = state["users_query"]
    last_ai = state["chatAgentResponse"]
    review = llm.invoke([
        review_prompt,
        {
            "role": "user",
            "content": f"User Question: {last_user}\n\nAI Response: {last_ai.content}"
        }
    ])

    if "OK" in review.content and "NEEDS_IMPROVEMENT" not in review.content:
        return {"review_feedback": None}
    else:
        return {
            "review_feedback": {
                "verdict": "RETRY",
                "critique": review.content.strip(),
                "suggestions": [
                    "Stay relevant to question",
                    "Keep under 250 words",
                ]
            }
        }


graph_builder = StateGraph(State)

graph_builder.add_node("agent", chatAgent)
graph_builder.add_node("review", reviewerAgent)
graph_builder.add_node("tools", ToolNode(tools=tools))

graph_builder.set_entry_point("agent")

graph_builder.add_conditional_edges(
    "agent",
    lambda s: "tools" if getattr(s["messages"][-1], "tool_calls", None) else "review",
    {"tools": "tools", "review": "review"}
)

graph_builder.add_edge("tools", "agent")

graph_builder.add_conditional_edges(
    "review",
    lambda s: "agent" if s.get("review_feedback") and s["review_feedback"].get("verdict") == "RETRY" else END,
    {"agent": "agent", END: END}
)

graph = graph_builder.compile(checkpointer=memory)
#
# if __name__ == "__main__":
#     config = {"configurable": {"thread_id": 1}}
#
#     while True:
#         snapshot = graph.get_state(config)
#
#         # Only show interrupt if the graph says so
#         if "__interrupt__" in snapshot.next:
#             user_input = Command(resume={"approved": input("Enter correction: ")})
#         else:
#             user_input = {"messages": [identity_prompt,{"role": "user", "content": input("You: ")}]}
#
#         for event in graph.stream(user_input, config, stream_mode=["updates"]):
#             if event[0] == "updates":
#                 data = event[1]
#                 for node_name, node_val in data.items():
#                     if "messages" in node_val:
#                         last = node_val["messages"][-1]
#                         if isinstance(last, AIMessage):
#                             print("🤖", last.content)
#                         elif isinstance(last, HumanMessage):
#                             print("🧑", last.content)
#                     if node_name == "review" and node_val.get("review_feedback"):
#                         if node_val["review_feedback"].get("verdict") == "RETRY":
#                             print(f"🔁 Retry {node_val['retry_count']}/3 based on review...")
