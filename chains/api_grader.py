from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Optional, Literal
import json

llm = ChatOpenAI(temperature=0)

class APIGrader(BaseModel):
    satisfied: Literal[True, False] = Field(description="True if API call has all values filled")
    missing: Optional[str] = Field(default=None, description="List of missing keys and where they were expected")

parser = PydanticOutputParser(pydantic_object=APIGrader)
format_instructions = parser.get_format_instructions()


template_string = """
System: You are an assistant that validates whether an API request contains all the required data to make a real API call.

A value is considered MISSING if:
- The key contains a type like "String", "Long", etc.
- The value is an empty string or null.
- The value appears to be a placeholder or type, not an actual value.

Optional keys can be left out, but required keys (mentioned with types) must be filled.

Return:
- satisfied: true if all required values are filled
- satisfied: false with a clear list of what is missing

Examples:
1. {{ "{{\"api\": \"/v1/gate-access\", \"method\": \"GET\", \"path_variables\": {{}}, \"query_params\": {{}}, \"headers\": {{}}, \"request_body\": {{}}}}" }}  
✅ All data present → satisfied: true

2. {{ "{{\"api\": \"/v1/gate-access/{{customerId}}\", \"method\": \"GET\", \"path_variables\": {{\"customerId\": \"Long\"}}, \"query_params\": {{}}, \"headers\": {{}}, \"request_body\": {{}}}}" }}  
❌ Missing customerId → satisfied: false, missing: "path_variables.customerId"

{format_instructions}

Check the following API input:
{query}
"""

api_grader_prompt = PromptTemplate(
    input_variables=["query"],
    template=template_string,
    partial_variables={"format_instructions": format_instructions},
)

# Final pipeline
api_grader = api_grader_prompt | llm | parser


from api_genarator import api_generator
import json

if __name__ == "__main__":
    user_input = """
    The update vehicle API is accessed via PUT /api/vehicles/{vehicleId}. 
    The path variable is vehicleId (Long). 
    The request body includes vehicle (JSON with custId, model, color) and 
    FileUploadRequestDto (files: MultipartFile, updateFiles: int[], optional).
    """

    # Step 1: Generate structured API representation
    print("🔍 Extracting API structure...")
    api_struct = api_generator.invoke({"query": user_input})
    print("✅ Extracted:\n", api_struct)

    # Step 2: Grade the generated API for readiness
    print("\n🧪 Grading API readiness...")
    api_json = json.dumps(api_struct.model_dump())
    grade = api_grader.invoke({"query": api_json})
    print("🎯 Grading Result:\n", grade)






# # Example
# if __name__ == "__main__":
#     sample_api = {
#         "api": "/v1/gate-access/{customerId}",
#         "method": "GET",
#         "path_variables": {"customerId": "Long"},
#         "query_params": {},
#         "headers": {},
#         "request_body": {}
#     }
#
#     result = api_grader.invoke({"query": json.dumps(sample_api)})
#     print(result)
