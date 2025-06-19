from langchain_core.tools import tool
from langgraph.types import interrupt



@tool("book_hotel")

def book_hotel(hotel_name: str):
   """Book a hotel"""
   response = interrupt(
       f"Trying to call `book_hotel` with args {{'hotel_name': {hotel_name}}}. "
       "Please accept or reject."
   )
   if response == "accept":
       return f"Successfully booked a stay at {hotel_name}."
   elif response == "reject":
       return f"booking a stay at {hotel_name} has been failed."
   else:
       raise ValueError(f"Unknown response type: {response['type']}")


