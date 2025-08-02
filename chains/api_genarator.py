from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Dict

# LLM setup
llm = ChatOpenAI(temperature=0)

# Output schema
class GenerateAPI(BaseModel):
    api: str = Field(description="The API endpoint for the query")
    method: str = Field(description="HTTP method for the API (GET, POST, etc.)")
    path_variables: Dict[str, str] = Field(default_factory=dict, description="Path variables with types or values")
    query_params: Dict[str, str] = Fielult_factory=dict, description="Query parameters with types or values")
    headers: Dict[str, str] = Field(default_factory=dict, description="Headers with values")
    request_body: Dict[str, str] = Field(default_factory=dict, description="JSON request body with keys and types/values")

parser = PydanticOutputParser(pydantic_object=GenerateAPI)
format_instructions = parser.get_format_instructions()

template_string = """
System: You are an assistant that extracts structured API information from natural language.

{format_instructions}

User query:
{query}
"""

api_prompt = PromptTemplate(
    input_variables=["query"],
    template=template_string,
    partial_variables={"format_instructions": format_instructions}
)

# Create the pipeline
api_generator = api_prompt | llm | parser

# Optional: Helper function to reuse
def extract_api_from_text(user_input: str) -> GenerateAPI:
    return api_generator.invoke({"query": user_input})


# Test block
if __name__ == "__main__":
    test_input = (
        "The update vehicle API can be accessed using the PUT /api/vehicles/{vehicleId} endpoint. "
        "The path variable is vehicleId (Long). The request parts include vehicle (JSON) and request (FileUploadRequestDto). "
        "The vehicle JSON should contain fields like custId, vehicleType, make, model, year, color, licensePlate, and vin. "
        "The FileUploadRequestDto includes files (MultipartFile) and updateFiles (int[], optional)."
    )

    try:
        result = extract_api_from_text(test_input)
        print("✅ Parsed Output:\n", result.model_dump())
    except Exception as e:
        print("❌ Error parsing output:", e)
