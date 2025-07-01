from langchain_core.messages import BaseMessage, AIMessage
from chains.reviewerAgentChain import ReviewFeedback, review_chain
from states.states import State


def reviewerAgent(state: State):
    retry_count = state.get("retry_count", 0)
    messages = state["messages"]
    user_query = state.get("users_query")
    last_ai = state.get("chatAgentResponse")

    # if not last_ai or not user_query:
    #     return {
    #         "review_feedback": {"satisfied": True},
    #         "retry_count": retry_count
    #     }

    history_str = "\n".join(
        f"{msg.type.upper()}: {msg.content}" for msg in messages if hasattr(msg, 'content')
    )

    feedback: ReviewFeedback = review_chain.invoke({
        "chat_history": history_str,
        "ai_response": last_ai.content,
        "user_query": user_query
    })

    feedback_dict = feedback.dict()
    satisfied = feedback_dict.get("satisfied", True)

    return {
        "review_feedback": feedback_dict,
        "retry_count": retry_count + 1 if satisfied is False else retry_count
    }
