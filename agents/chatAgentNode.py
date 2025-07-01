# agents/chatAgentNode.py
from langchain_core.messages import BaseMessage, AIMessage
from chains.chatAgentChain import get_retry_prompt, chat_chain
from states.states import State


def chatAgent(state: State):
    messages = state["messages"]
    review = state.get("review_feedback")
    retry_count = state.get("retry_count", 0)

    full_messages: list[BaseMessage] = []

    if review and review.get("satisfied") is False:
        full_messages.append(
            get_retry_prompt(
                retry_count,
                review.get("critique", ""),
                review.get("suggestions", [])
            )
        )

    full_messages.extend(messages)

    response: AIMessage = chat_chain.invoke(full_messages)

    # Check if this is the final attempt
    next_retry_count = retry_count + 1 if review and review.get("satisfied") is False else retry_count
    is_final = review is None or review.get("satisfied") is True or next_retry_count >= 2

    return {
        "messages": messages + [response],
        "retry_count": next_retry_count,
        "chatAgentResponse": response,
        "final_response": response if is_final else None
    }
