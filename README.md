# langlearn (Rakhi 2.0 backend)

A LangGraph + FastAPI backend for a personal conversational assistant. It streams
responses over Server-Sent Events (SSE), can search the web (Tavily), look up a
personal knowledge base (Qdrant RAG), and send WhatsApp messages (Twilio) with a
human-in-the-loop approval step. Frontend lives in a separate repo (LangLearnUI).

<img width="1440" alt="Screenshot 2025-07-05 at 8 41 11 AM" src="https://github.com/user-attachments/assets/2c524589-6a1e-4c5f-81ae-db81863cd25d" />
<img width="1440" alt="Screenshot 2025-07-05 at 9 05 27 AM" src="https://github.com/user-attachments/assets/7f9cc6d7-6238-4c25-8fa2-07321982ecae" />
<img width="1440" alt="Screenshot 2025-07-05 at 9 08 36 AM" src="https://github.com/user-attachments/assets/bb2e93c5-609b-4860-82d5-5597be8326b4" />

## Architecture

```
main.py            FastAPI app: /chat_stream (SSE), /health, auth + rate limiting
graph.py            LangGraph StateGraph wiring: chatAgent -> reviewerAgent -> tools
agents/              Graph node implementations (chat + reviewer/"reflection" loop)
chains/              LangChain runnables (LLM invocation chains) used by the nodes
tools/               LangChain tools: web search, WhatsApp send, knowledge-base RAG
configs/             Memory/checkpointer selection (Redis or in-memory), shared constants
states/              LangGraph state schema
config.py            Centralized settings (env-driven, via pydantic-settings)
logging_config.py    Logging setup
```

## Setup

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill in real values (see comments in the file for what each is for)
4. `uvicorn main:app --reload`

## Running tests

```
pytest tests/ -v
```

Tests never make real LLM/API calls — `tests/conftest.py` mocks the chat/review
LLM chains and sets dummy credentials so nothing needs a live OpenAI/Qdrant/Twilio
account.

## Docker

```
docker build -t langlearn-backend .
docker run -p 8080:8080 --env-file .env langlearn-backend
```

## Notes on production deployment

- **Auth**: set `API_KEYS` (comma-separated) to require an API key on `/chat_stream`.
  Since the frontend uses the browser's native `EventSource` (which cannot set
  custom headers), the key can be passed as `?api_key=...` or via an `X-API-Key`
  header for non-browser clients. Prefer HTTPS always, since a query-param key is
  visible in server access logs.
- **CORS**: set `CORS_ALLOW_ORIGINS` to your real frontend origin(s) — do not use `*`.
- **Persistence**: set `REDIS_URL` for conversation state to survive restarts;
  without it, the app silently falls back to a non-persistent in-memory
  checkpointer (fine for local dev, not for production).
- **Rate limiting** is a simple in-memory sliding window (`RATE_LIMIT_PER_MINUTE`)
  — adequate for a single-instance deployment, not for multiple replicas behind a
  load balancer (would need a shared/Redis-backed limiter for that).
