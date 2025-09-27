import os
from langchain_community.tools.tavily_search import TavilySearchResults

tavily_tool = TavilySearchResults(max_results=2)

if __name__ == "__main__":
    query = "Latest news in AI"
    results = tavily_tool.invoke({"query": query})
    print(results)
