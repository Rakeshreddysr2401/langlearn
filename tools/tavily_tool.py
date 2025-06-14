import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()

tavily_tool = TavilySearchResults()

if __name__ == "__main__":
    query = "Latest news in AI"
    results = tavily_tool.invoke({"query": query})
    print(results)
