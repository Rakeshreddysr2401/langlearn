
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
load_dotenv()

tavily_tool = TavilySearch()

if __name__ == "__main__":
    query = "Latest news in AI"
    results = tavily_tool.invoke({"query": query})
    print(results)
