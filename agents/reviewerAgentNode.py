# agents/reviewerAgentNode.py
from langchain_core.messages import BaseMessage, AIMessage
from chains.reviewerAgentChain import ReviewFeedback, review_chain
from states.states import State


def reviewerAgent(state: State):
    retry_count = state.get("retry_count", 0)

    # Skip review if we've hit the retry limit
    if retry_count > 2:
        return {"review_feedback": {"satisfied": True}}

    messages = state["messages"]
    user_query = state.get("users_query")
    last_ai = state.get("chatAgentResponse")

    if not last_ai or not user_query:
        return {"review_feedback": {"satisfied": True}}

    # Convert messages to readable string format
    history_str = "\n".join(
        f"{msg.type.upper()}: {msg.content}" for msg in messages if hasattr(msg, 'content')
    )

    try:
        # Run review
        feedback: ReviewFeedback = review_chain.invoke({
            "chat_history": history_str,
            "ai_response": last_ai.content,
            "user_query": user_query
        })

        return {"review_feedback": feedback.dict()}
    except Exception as e:
        # If review fails, default to satisfied to prevent infinite loops
        print(f"Review failed: {e}")
        return {"review_feedback": {"satisfied": True}}
