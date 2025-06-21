import json
from uuid import uuid4
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from graph import graph  # Import from graph.py
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/chat_stream/{message}")
async def stream_chat(
    message: str,
    checkpoint_id: str = Query(default=None),
    interrupt: bool = Query(default=False)
) -> EventSourceResponse:
    async def event_generator():
        thread_id = checkpoint_id or str(uuid4())

        # Send checkpoint if new thread
        if checkpoint_id is None:
            yield {"data": json.dumps({"type": "checkpoint", "checkpoint": thread_id})}

        config = {"configurable": {"thread_id": thread_id}}

        # Prepare input
        init_state = Command(resume={"data": message}) if interrupt else {"messages": [{"role": "user", "content": message}]}

        try:
            for event in graph.stream(init_state, config=config, stream_mode=["updates", "custom"]):
                event_type, event_data = event
                print(f"Event: {event}")

                if event_type == "updates":
                    # Handle updates
                    if "__interrupt__" in event_data:
                        interrupt_obj = event_data["__interrupt__"][0]
                        yield {"data": json.dumps({"type": "interrupt_request", "payload": interrupt_obj.value})}
                        continue

                    for node_name, node_value in event_data.items():
                        if "messages" not in node_value:
                            continue
                        last_message = node_value["messages"][-1]

                        if isinstance(last_message, AIMessage) and not getattr(last_message, "tool_calls", []):
                            yield {"data": json.dumps({"type": "content", "content": last_message.content})}
                        elif isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", []):
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
                            except json.JSONDecodeError as e:
                                yield {"data": json.dumps({"type": "tool_error", "error": f"Failed to parse tool results: {e}"})}

                elif event_type == "custom":
                    yield {"data": json.dumps({
                        "type": "interrupt_request",
                        "interruptType": event_data.get("type", "generic"),
                        "payload": event_data,
                    })}

            # End event on successful completion
            yield {"data": json.dumps({"type": "end"})}

        except (StopIteration, GeneratorExit):
            print("Generator ended normally — skipping error event")
        except Exception as e:
            print(f"Error in stream: {e}")
            yield {"data": json.dumps({"type": "error", "error": str(e)})}

    return EventSourceResponse(event_generator())

