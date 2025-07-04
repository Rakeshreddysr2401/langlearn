import os
import redis
import urllib.parse
import ssl
from dotenv import load_dotenv

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver

# Load environment variables from .env
load_dotenv()
redis_url = os.getenv("REDIS_URL", "local")

def get_memory():
    if redis_url == "local":
        print("✅ Using InMemorySaver (local dev)")
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
        print(f"✅ Connected to Redis at {parsed.hostname}:{parsed.port}")
        return RedisSaver(redis_client)

    except Exception as e:
        print("❌ Redis connection failed. Falling back to InMemorySaver.")
        print(f"Error: {e}")
        return MemorySaver()
