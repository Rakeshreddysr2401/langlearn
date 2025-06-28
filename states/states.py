# states/states.py

from typing import Annotated, TypedDict, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

class State(TypedDict, total=False):
    # Main conversation history
    messages: Annotated[List[BaseMessage], add_messages]

    # Optional additions
    user_id: Optional[str]                  # If multi-user support is added
    context: Optional[Dict[str, Any]]       # General-purpose scratchpad
    tool_results: Optional[List[Any]]       # Store any tool responses
    approvals: Optional[List[Dict[str, Any]]]  # Store human approval interactions
