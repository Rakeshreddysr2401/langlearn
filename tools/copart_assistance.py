from langchain_core.tools import tool

from Retrievers.apidata_retriever import apidata_retriever


@tool
def copart_assistance(query: str) -> str:
    """Tool use to get any details regarding lots."""
    response = apidata_retriever(query)
    return response