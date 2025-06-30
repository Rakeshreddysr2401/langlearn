# llm_config.py

from langchain.chat_models import init_chat_model
from tools import get_tools

llm = init_chat_model("gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(get_tools())
