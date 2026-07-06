# agents/reviewerAgentNode.py
import logging

from langgraph.config import get_stream_writer

from chains.reviewerAgentChain import ReviewFeedback, review_chain
from configs.constants import MAX_RETRIES
from states.states import State

logger = logging.getLogger(__name__)


def reviewerAgent(state: State):
    retry_count = state.get("retry_count", 0)
    messages = state["messages"]
    user_query = state.get("users_query")
    last_ai = state.get("chatAgentResponse")

    logger.info("reviewerAgent invoked (attempt %d)", retry_count + 1)

    # If we've exceeded max retries, accept the current response and END
    if retry_count >= MAX_RETRIES:
        logger.info("Max retries exceeded; accepting final response as-is.")
        writer = get_stream_writer()
        writer({"data": last_ai, "type": "final_response"})
        return {
            "final_response": last_ai,
            "review_feedback": {"satisfied": True, "reason": "max_retries_exceeded"}
        }

    # Build chat history string
    history_str = "\n".join(
        f"{msg.type.upper()}: {msg.content}"
        for msg in messages
        if hasattr(msg, 'content') and msg.content
    )

    try:
        feedback: ReviewFeedback = review_chain.invoke({
            "chat_history": history_str,
            "ai_response": last_ai.content if last_ai else "",
            "user_query": user_query or ""
        })
    except Exception:
        logger.exception("review_chain.invoke failed")
        # If review fails, accept the response
        return {
            "final_response": last_ai,
            "review_feedback": {"satisfied": True, "reason": "review_error"}
        }

    feedback_dict = feedback.model_dump()
    satisfied = feedback_dict.get("satisfied", False)

    if satisfied:
        logger.info("Response satisfied reviewer")
        writer = get_stream_writer()
        writer({"data": last_ai , "type": "final_response"})

    return {
        "final_response": last_ai if satisfied else state.get("final_response"),
        "review_feedback": feedback_dict,
        "retry_count": retry_count + 1 if not satisfied else retry_count,
    }
