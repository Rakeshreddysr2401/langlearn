# main.py
import json
from uuid import uuid4
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from graph import graph  # Import from graph.py
from langchain_core.messages import AIMessage, AIMessageChunk

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/chat_stream/{message}")
async def stream_chat(message: str, checkpoint_id: str = Query(default=None)) -> EventSourceResponse:
    async def event_generator():
        thread_id = checkpoint_id or str(uuid4())
        if checkpoint_id is None:
            yield {"data": json.dumps({"type": "checkpoint", "checkpoint": thread_id})}

        config = {"configurable": {"thread_id": thread_id}}
        init_state = {"messages": [{"role": "user", "content": message}]}

        async for chunk,meta in graph.astream(init_state, config=config, stream_mode="messages"):
            if meta.get("langgraph_node") == "agent" and isinstance(chunk, AIMessage) and chunk.content:
                yield {"data":json.dumps({"type": "content", "content": chunk.content})}
            if meta.get("langgraph_node") == "agent" and isinstance(chunk, AIMessage) and chunk.tool_calls:
                for tool_call in chunk.tool_calls:
                    if tool_call.get("args") and tool_call.get("args").get("query") and tool_call.get("name"):
                        args = tool_call.get("args").get("query")
                        print("args",args)
                        yield {"data":json.dumps({"type": "tool_calling", "query": args})}
            if meta.get("langgraph_node") == "tool_node":
                urls=[]
                try:
                    parsed_content = json.loads(chunk.content)
                    for info in parsed_content:
                        if "title" in info and "url" in info:
                            urls.append(info["url"])
                            yield {"data": json.dumps({"type": "search_urls", "urls": urls})}
                except json.decoder.JSONDecodeError as e:
                    print("Failed to decode", chunk.content,e)

    return EventSourceResponse(event_generator())
