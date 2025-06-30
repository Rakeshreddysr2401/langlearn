from langchain_core.messages import BaseMessage, AIMessage
from chains.chatAgentChain import get_retry_prompt, chat_chain
from states.states import State


def chatAgent(state: State):
    messages = state["messages"]
    review = state.get("review_feedback")
    retry_count = state.get("retry_count", 0)

    if retry_count >= 3:
        print("⚠️ Maximum retries reached, providing best possible response")
        review = None

    # Base message list
    full_messages: list[BaseMessage] = []
    # Add retry prompt if needed
    if review and review.get("satisfied") is False:
        full_messages.append(
            get_retry_prompt(
                retry_count,
                review.get("critique", ""),
                review.get("suggestions", [])
            )
        )

    # Append original conversation history
    full_messages += messages

    # Call LLM with tools
    response: AIMessage = chat_chain.invoke(full_messages)

    return {
        "messages": [response],  # will be added to state by add_messages
        "retry_count": retry_count + 1 if review and review.get("satisfied") is False else 0,
        "final_response": response if not review or retry_count >= 3 else None,
        "chatAgentResponse": response,
    }
