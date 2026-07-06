from langchain_tavily import TavilySearch

import config  # noqa: F401 - ensures .env is loaded into process env before TavilySearch reads it

tavily_tool = TavilySearch()

if __name__ == "__main__":
    query = "Latest news in AI"
    results = tavily_tool.invoke({"query": query})
    print(results)
