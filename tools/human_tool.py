from langchain_core.tools import tool
from langgraph.types import interrupt



@tool("human_assistance",description="Used to request human assistance for booking a hotel.")
def human_assistance():
   response = interrupt(
       f"Trying to call `book_hotel` with args. "
       "Please accept or reject."
   )
   if response == "accept":
       return f"Successfully booked a stay."
   elif response == "reject":
       return f"booking a stay has been failed."
   else:
       raise ValueError(f"Unknown response type: {response['type']}")


