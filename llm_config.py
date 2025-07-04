# llm_config.py
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import init_chat_model as init_openai_model
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import get_tools
from langchain_community.chat_models import ChatOllama
# Provider-Model registry
PROVIDER_REGISTRY = {
    "openai": {
        "gpt-4o": lambda temperature: init_openai_model("gpt-4o", temperature=temperature),
        "gpt-4-turbo": lambda temperature: init_openai_model("gpt-4-turbo", temperature=temperature),
        "gpt-3.5-turbo": lambda temperature: init_openai_model("gpt-3.5-turbo", temperature=temperature),
        "gpt-4o-mini": lambda temperature: init_openai_model("gpt-4o-mini", temperature=temperature),
        "gpt-4o-mini": lambda temperature: init_openai_model("gpt-4o-mini", temperature=temperature),
    },
    "ollama": {
        "llama3": lambda temperature: ChatOllama(model="llama3", temperature=temperature),
        "mistral": lambda temperature: ChatOllama(model="mistral", temperature=temperature),
        "phi3:mini": lambda temperature: ChatOllama(model="phi3:mini", temperature=temperature),
    },
    "gemini": {
        "gemini-pro": lambda temperature: ChatGoogleGenerativeAI(model="gemini-pro", temperature=temperature),
    },
}


def get_llm(provider: str = "openai", model: str = "gpt-4o-mini", temperature: float = 0):
    provider_models = PROVIDER_REGISTRY.get(provider)
    if not provider_models:
        raise ValueError(f"Unsupported provider: {provider}")

    model_loader = provider_models.get(model)
    if not model_loader:
        raise ValueError(f"Unsupported model '{model}' for provider '{provider}'")

    return model_loader(temperature)


def get_llm_with_tools(provider: str = "openai", model: str = "gpt-4o-mini", temperature: float = 0):
    llm = get_llm(provider, model, temperature)
    tools = get_tools()
    return llm.bind_tools(tools)

llm = get_llm()
llm_with_tools = get_llm_with_tools()


# llm = get_llm(provider="ollama", model="phi3:mini", temperature=0)
# llm_with_tools = initialize_agent(
#     tools=get_tools(),
#     llm=llm,
#     agent=AgentType.OPENAI_FUNCTIONS,  # Simulates tool calling
#     verbose=True
# )

