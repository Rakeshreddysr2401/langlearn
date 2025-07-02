import json
from uuid import uuid4
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import Command

from prompts import identity_prompt
from graph import graph  # Import your graph here

# -----------------------------------
# FastAPI App Setup
# -----------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# Custom Event Handler
# -----------------------------------
def handle_custom_event(event_data):
    if event_data.get("type") == "final_response":
        return {
            "type": "content",
            "content": event_data.get("data").content
        }
    return None

# -----------------------------------
# Update Event Handler
# -----------------------------------
async def handle_update_event(event_data):
    if "__interrupt__" in event_data:
        interrupt_obj = event_data["__interrupt__"][0]
        yield {"data": json.dumps({"type": "interrupt_request", "payload": interrupt_obj.value})}
        return

    for node_name, node_value in event_data.items():
        if "messages" not in node_value:
            continue

        last_message = node_value["messages"][-1]

        if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", []):
            for tool_call in last_message.tool_calls:
                query = tool_call.get("args", {}).get("query")
                if query:
                    yield {"data": json.dumps({"type": "tool_calling", "query": query})}

        elif isinstance(last_message, ToolMessage):
            raw_content = last_message.content
            try:
                results = json.loads(raw_content)
                urls = [info["url"] for info in results if isinstance(info, dict) and "url" in info]
                if urls:
                    yield {"data": json.dumps({"type": "search_urls", "urls": urls})}
            except json.JSONDecodeError:
                pass

# -----------------------------------
# Main Event Stream Handler
# -----------------------------------
async def handle_event_stream(init_state, config):
    try:
        for event in graph.stream(init_state, config=config, stream_mode=["updates", "custom"]):
            event_type, event_data = event

            if event_type == "updates":
                async for update in handle_update_event(event_data):
                    yield update

            elif event_type == "custom":
                custom_response = handle_custom_event(event_data)
                if custom_response:
                    yield {"data": json.dumps(custom_response)}

        yield {"data": json.dumps({"type": "end"})}

    except (StopIteration, GeneratorExit):
        print("Generator ended normally")
    except Exception as e:
        print(f"Error in stream: {e}")
        yield {"data": json.dumps({"type": "error", "error": str(e)})}

# -----------------------------------
# Endpoint: /chat_stream
# -----------------------------------
@app.get("/chat_stream/{message}")
async def stream_chat(
    message: str,
    checkpoint_id: str = Query(default=None),
    interrupt: bool = Query(default=False)
) -> EventSourceResponse:

    async def event_generator():
        thread_id = checkpoint_id or str(uuid4())

        if checkpoint_id is None:
            yield {"data": json.dumps({"type": "checkpoint", "checkpoint": thread_id})}

        config = {"configurable": {"thread_id": thread_id}}

        init_state = {
            "messages": [identity_prompt, {"role": "user", "content": message}],
            "users_query": message
        }

        if interrupt:
            parsed_data = json.loads(message)
            init_state = Command(resume=parsed_data)

        async for event in handle_event_stream(init_state, config):
            yield event

    return EventSourceResponse(event_generator())
