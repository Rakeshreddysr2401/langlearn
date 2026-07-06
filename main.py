import json
import logging
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import Command

from config import get_settings
from logging_config import setup_logging
from prompts import identity_prompt
from graph import graph  # Import your graph here

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

# -----------------------------------
# FastAPI App Setup
# -----------------------------------
app = FastAPI(title="Rakhi 2.0 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# -----------------------------------
# Auth
# -----------------------------------
def verify_api_key(request: Request, api_key: str = Query(default=None)):
    """Accepts the key via X-API-Key header (preferred) or api_key query param
    (needed because browser EventSource cannot set custom headers).
    If no API keys are configured, auth is disabled (dev mode)."""
    allowed = settings.api_key_list
    if not allowed:
        return  # auth disabled, e.g. local dev
    supplied = request.headers.get("X-API-Key") or api_key
    if supplied not in allowed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


# -----------------------------------
# Minimal in-memory rate limiter
# -----------------------------------
_request_log: dict[str, list[float]] = {}


def rate_limit(request: Request):
    limit = settings.rate_limit_per_minute
    if limit <= 0:
        return
    client_key = request.headers.get("X-API-Key") or (request.client.host if request.client else "unknown")
    now = time.monotonic()
    window_start = now - 60
    timestamps = [t for t in _request_log.get(client_key, []) if t > window_start]
    if len(timestamps) >= limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    timestamps.append(now)
    _request_log[client_key] = timestamps


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
        logger.info("Stream generator ended normally")
    except Exception:
        logger.exception("Error while streaming graph events")
        yield {"data": json.dumps({"type": "error", "error": "Something went wrong processing your request."})}

# -----------------------------------
# Endpoint: /health
# -----------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# -----------------------------------
# Endpoint: /chat_stream
# -----------------------------------
@app.get("/chat_stream/{message}", dependencies=[Depends(verify_api_key), Depends(rate_limit)])
async def stream_chat(
    message: str,
    checkpoint_id: str = Query(default=None),
    interrupt: bool = Query(default=False)
) -> EventSourceResponse:
    logger.info("Received message (checkpoint_id=%s, interrupt=%s)", checkpoint_id, interrupt)

    async def event_generator():
        thread_id = checkpoint_id or str(uuid4())

        if checkpoint_id is None:
            yield {"data": json.dumps({"type": "checkpoint", "checkpoint": thread_id})}

        config = {"configurable": {"thread_id": thread_id}}

        init_state = {
            "messages": [identity_prompt, {"role": "user", "content": message}],
            "users_query": message,
            "retry_count": 0,
            "review_feedback": {}
        }

        if interrupt:
            try:
                parsed_data = json.loads(message)
            except json.JSONDecodeError:
                yield {"data": json.dumps({"type": "error", "error": "Invalid interrupt payload."})}
                return
            init_state = Command(resume=parsed_data)

        async for event in handle_event_stream(init_state, config):
            yield event

    return EventSourceResponse(event_generator())
