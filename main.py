# main.py
import json
from uuid import uuid4
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from graph import agent  # Import from graph.py
from langchain_core.messages import AIMessage

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
            yield {"data": json.dumps({"type": "checkpoint", "content": thread_id})}

        config = {"configurable": {"thread_id": thread_id}}
        init_state = {"messages": [{"role": "user", "content": message}]}

        async for event in agent.astream(init_state, config=config, stream_mode="updates"):
            for value in event.values():
                if "messages" in value and isinstance(value["messages"][-1], AIMessage):
                    msg = value["messages"][-1]
                    if not getattr(msg, "tool_calls", []):
                        yield {"data": json.dumps({"type": "content", "content": msg.content})}

    return EventSourceResponse(event_generator())
