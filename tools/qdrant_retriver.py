import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from langchain_core.tools import tool

load_dotenv()

# Initialize OpenAI embedding
embeddings = OpenAIEmbeddings()

# Connect to Qdrant
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Initialize vector store
vectorstore = Qdrant(
    client=client,
    collection_name="personal_knowledge_base",
    embeddings=embeddings  # ✅ correct param name
)


@tool
def qdrant_search_tool(query: str):
    """Questions about Rakesh (skills, projects, experience)** → Use `qdrant_search_tool` first
       Searches personal knowledge base for boss-related questions."""
    results = vectorstore.similarity_search(query, k=5)
    if not results:
        return "I couldn’t find anything in my knowledge base for that."
    return "\n\n".join([doc.page_content for doc in results])


# ✅ Test from CLI
if __name__ == "__main__":
    query = input("🔍 Enter your query: ")
    result = qdrant_search_tool.invoke(query)
    print("\n🧠 Qdrant Search Results:\n")
    print(result)
