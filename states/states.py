
from typing import Annotated, TypedDict, List, Optional
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import add_messages

class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    chatAgentResponse: Optional[AIMessage]
    users_query: Optional[str]
    retry_count: int
    final_response: Optional[AIMessage]
    review_feedback: Optional[dict]
