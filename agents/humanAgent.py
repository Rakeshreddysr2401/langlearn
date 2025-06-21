from langchain_core.messages import HumanMessage, AIMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# highlight-next-line
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_stream_writer


class State(TypedDict):
    input: str
    user_feedback: str


def step_1(state):
    print("---Step 1---")
    pass


def human_feedback(state):
    print("---human_feedback---")
    writer = get_stream_writer()
    writer({"data": "Retrieved 0/100 records", "type": "progress"})
    # highlight-next-line
    feedback = interrupt("Please provide feedback:")
    return {"user_feedback": feedback}


def step_3(state):
    print("---Step 3---")
    writer = get_stream_writer()
    writer({"data": "Retrieved 0/100 records", "type": "progress"})
    pass


builder = StateGraph(State)
builder.add_node("step_1", step_1)
builder.add_node("human_feedback", human_feedback)
builder.add_node("step_3", step_3)
builder.add_edge(START, "step_1")
builder.add_edge("step_1", "human_feedback")
builder.add_edge("human_feedback", "step_3")
builder.add_edge("step_3", END)

# Set up memory
memory = MemorySaver()

# Add
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": 1}}


if __name__ == "__main__":
    while True:

        snapshot = graph.get_state(config)

        print(f"shot;{snapshot}")
        if "__interrupt__" in snapshot.next:
            user_input=Command(resume={"data":input("Please Enter your response: ")})
        else:
            user_input = {"messages": [{"role": "user", "content": input("User:")}]}
        for event in graph.stream(user_input, config,stream_mode=["updates","custom"]):
            print("EVENT ",event)
            print("Event Type:", type(event))


