# agents/chatAgentNode.py
from langchain_core.messages import BaseMessage, AIMessage
from chains.chatAgentChain import get_retry_prompt, chat_chain
from states.states import State


def chatAgent(state: State):
    messages = state["messages"]
    review = state.get("review_feedback")
    retry_count = state.get("retry_count", 0)

    print(f"Chat Agent called : {retry_count+1} st time")

    full_messages: list[BaseMessage] = []

    # Add retry prompt if we have negative feedback
    if review and review.get("satisfied") is False:
        full_messages.append(
            get_retry_prompt(
                retry_count,
                review.get("critique", ""),
                review.get("suggestions", [])
            )
        )

    full_messages.extend(messages)

    try:
        response: AIMessage = chat_chain.invoke(full_messages)
    except Exception as e:
        print(f"Error in chat_chain.invoke: {e}")
        raise

    return {
        "messages": messages + [response],
        "retry_count": retry_count,
        "chatAgentResponse": response,
    }

