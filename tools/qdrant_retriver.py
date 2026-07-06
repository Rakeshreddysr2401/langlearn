import logging
from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from langchain_core.tools import tool

from config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_vectorstore() -> Qdrant:
    """Lazily builds the Qdrant vector store on first use, so importing this
    module never requires a reachable Qdrant instance or valid credentials."""
    settings = get_settings()
    embeddings = OpenAIEmbeddings()
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return Qdrant(
        client=client,
        collection_name="personal_knowledge_base",
        embeddings=embeddings,
    )


@tool
def qdrant_search_tool(query: str):
    """Questions about Rakesh (skills, projects, experience)** → Use `qdrant_search_tool` first
       Searches personal knowledge base for boss-related questions."""
    try:
        results = get_vectorstore().similarity_search(query, k=3)
    except Exception:
        logger.exception("Qdrant similarity_search failed for query=%r", query)
        return "I'm having trouble reaching my knowledge base right now."
    if not results:
        return "I couldn't find anything in my knowledge base for that."
    return "\n\n".join([doc.page_content for doc in results])


# ✅ Test from CLI
if __name__ == "__main__":
    query = input("🔍 Enter your query: ")
    result = qdrant_search_tool.invoke(query)
    print("\n🧠 Qdrant Search Results:\n")
    print(result)
