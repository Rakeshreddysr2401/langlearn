from langchain_core.messages import BaseMessage
from langchain_core.messages import AIMessage
from chains.reviewerAgentChain import ReviewFeedback, review_chain
from states.states import State


def reviewerAgent(state: State):
    if state["retry_count"] >= 3:
        return {"review_feedback": None}

    messages = state["messages"]
    user_query = state.get("users_query")
    last_ai = state.get("chatAgentResponse")

    if not last_ai or not user_query:
        return {"review_feedback": None}

    # Convert messages to readable string format
    history_str = "\n".join(
        f"{msg.type.upper()}: {msg.content}" for msg in messages
    )

    # Run review
    feedback: ReviewFeedback = review_chain.invoke({
        "chat_history": history_str,
        "ai_response": last_ai.content,
        "user_query": user_query
    })

    return {"review_feedback": feedback.dict()}
