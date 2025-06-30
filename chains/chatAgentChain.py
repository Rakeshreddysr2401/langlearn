from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableLambda
from llm_config import llm_with_tools


# Retry system prompt
def get_retry_prompt(retry_count: int, critique: str, suggestions: list[str] = []) -> SystemMessage:
    suggestion_text = "\n".join(f"- {s}" for s in suggestions) if suggestions else ""
    return SystemMessage(content=f"""
RETRY ATTEMPT #{retry_count + 1}/3

The previous response had issues:
{critique.strip()}

Suggestions for improvement:
{suggestion_text}

Please revise your last response carefully. Keep it concise (<250 words), relevant, and directly address the user's question.
""".strip())

# Optional: wrap in a LangChain-style Runnable if needed
chat_chain = RunnableLambda(lambda messages: llm_with_tools.invoke(messages))
