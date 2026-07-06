# llm_config.py
import logging
from functools import lru_cache

from langchain.chat_models import init_chat_model as init_openai_model
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from config import get_settings
from tools import get_tools

logger = logging.getLogger(__name__)

settings = get_settings()

# Provider-Model registry. Each loader is only called (and only requires its
# provider's credentials) when that provider/model is actually requested.
PROVIDER_REGISTRY = {
    "openai": {
        "gpt-4o": lambda temperature: init_openai_model("gpt-4o", temperature=temperature),
        "gpt-4-turbo": lambda temperature: init_openai_model("gpt-4-turbo", temperature=temperature),
        "gpt-3.5-turbo": lambda temperature: init_openai_model("gpt-3.5-turbo", temperature=temperature),
        "gpt-4o-mini": lambda temperature: init_openai_model("gpt-4o-mini", temperature=temperature),
    },
    "ollama": {
        "qwen2.5vl:7b": lambda temperature: ChatOllama(model="qwen2.5vl:7b", temperature=temperature),
        "qwen2.5:7b": lambda temperature: ChatOllama(
            model="qwen2.5:7b", temperature=temperature, base_url=f"http://{settings.ollama_host}"
        ),
        "llama3": lambda temperature: ChatOllama(model="llama3", temperature=temperature),
        "mistral": lambda temperature: ChatOllama(model="mistral", temperature=temperature),
        "phi3:mini": lambda temperature: ChatOllama(model="phi3:mini", temperature=temperature),
    },
    "gemini": {
        "gemini-pro": lambda temperature: ChatGoogleGenerativeAI(model="gemini-pro", temperature=temperature),
    },
}


def get_llm(provider: str = None, model: str = None, temperature: float = 0):
    provider = provider or settings.llm_provider
    model = model or settings.llm_model

    provider_models = PROVIDER_REGISTRY.get(provider)
    if not provider_models:
        raise ValueError(f"Unsupported provider: {provider}")

    model_loader = provider_models.get(model)
    if not model_loader:
        raise ValueError(f"Unsupported model '{model}' for provider '{provider}'")

    logger.info("Initializing LLM provider=%s model=%s", provider, model)
    return model_loader(temperature)


def get_llm_with_tools(provider: str = None, model: str = None, temperature: float = 0):
    llm = get_llm(provider, model, temperature)
    tools = get_tools()
    return llm.bind_tools(tools)


@lru_cache
def get_default_llm():
    """Lazily-created, memoized default LLM client (no tools bound)."""
    return get_llm()


@lru_cache
def get_default_llm_with_tools():
    """Lazily-created, memoized default LLM client with tools bound."""
    return get_llm_with_tools()
