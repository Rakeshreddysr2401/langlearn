from fastapi import FastAPI
from langgraph.types import Command
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from dotenv import load_dotenv
from graph import graph  # This is your compiled LangGraph
from langchain_core.messages import BaseMessage, AIMessageChunk
import json
from agents import api_agent

load_dotenv()

app = FastAPI()

# Allow all CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Safe utility to extract tool name
def extract_tool_name(call: dict) -> str:
    try:
        if isinstance(call, dict):
            if "function" in call:
                return call["function"].get("name", "unknown_function")
            elif "name" in call:
                return call["name"]
        return str(call)
    except Exception as e:
        print("❌ Error extracting tool name:", e)
        return "unknown_tool"

# ✅ SSE endpoint
@app.get("/chat_stream/{msg}")
async def event_generator(msg: str):
    async def generate():
        thread_id = str(uuid4())
        init_state = {
            "messages": [
                {"role": "user", "content": msg}
            ]
        }
        config = {"configurable": {"thread_id": thread_id}}

        response = ""
        tool_content = {}
        tool_name = ""

        current_state = init_state

        async for chunk, meta in api_agent.astream(current_state, config=config, stream_mode="messages"):

            # Detect tool call
            if isinstance(chunk, AIMessageChunk) and chunk.tool_calls:
                for tool in chunk.tool_calls:
                    if tool.get("type") == "tool_call" and tool.get("name"):
                        tool_name = tool["name"]
                        yield f"event: tool_name\ndata: {tool_name}\n\n"

            # Extract content from tool output node
            if meta.get("langgraph_node") == "tool_node":
                try:
                    parsed_content = json.loads(chunk.content)
                    for info in parsed_content:
                        if "title" in info and "url" in info:
                            tool_content[info["title"]] = info["url"]
                            yield f"event: tool_content\ndata: {json.dumps(tool_content)}\n\n"
                except json.JSONDecodeError as e:
                    print("❌ Failed to parse JSON from chunk content:", e)
                    print("🔧 Tool content:", tool_content)

            # Stream model response
            if meta.get("langgraph_node") == "model" and isinstance(chunk, AIMessageChunk):
                response += chunk.content
                yield f"event: model_response\ndata: {response}\n\n"

    return EventSourceResponse(generate())