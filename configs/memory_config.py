import logging
import ssl
import urllib.parse

import redis
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver

from config import get_settings

logger = logging.getLogger(__name__)


def get_memory():
    settings = get_settings()
    redis_url = settings.redis_url

    if not redis_url:
        logger.warning("REDIS_URL not set; using in-memory checkpointer (state is lost on restart).")
        return MemorySaver()

    try:
        parsed = urllib.parse.urlparse(redis_url)
        ssl_context = ssl.create_default_context()

        redis_client = redis.Redis(
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            ssl=(parsed.scheme == "rediss"),
            ssl_context=ssl_context
        )

        redis_client.ping()
        logger.info("Connected to Redis checkpointer at %s:%s", parsed.hostname, parsed.port)
        return RedisSaver(redis_client)

    except Exception:
        logger.exception(
            "Redis connection failed; falling back to in-memory checkpointer. "
            "Conversation state will NOT persist across restarts until this is fixed."
        )
        return MemorySaver()
