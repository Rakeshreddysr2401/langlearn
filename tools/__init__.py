from .tavily_tool import tavily_tool
from .twillo_tool import send_whatsapp_message
from  .qdrant_retriver import qdrant_search_tool

def get_tools():
    """Returns a list of all available tools."""
    return [tavily_tool, send_whatsapp_message, qdrant_search_tool]

# You can also export them individually if needed
__all__ = ["tavily_tool", "send_whatsapp_message", "qdrant_search_tool", "get_tools"]
