from app.core.config import settings
from pydantic_ai.models import Model
from pydantic_ai.models.concurrency import ConcurrencyLimitedModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider


def get_model() -> ConcurrencyLimitedModel:
    model = _build_model()
    return ConcurrencyLimitedModel(model, limiter=settings.max_concurrency)

def _build_model() -> Model:
    match settings.llm_provider.lower():
        case 'openai':
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required")
            return OpenAIChatModel(
                model_name=settings.llm_model,
                provider=OpenAIProvider(api_key=settings.openai_api_key)
            )
        case 'google':
            if not settings.google_api_key:
                raise ValueError("GOOGLE_API_KEY is required")
            return GoogleModel(
                model_name=settings.llm_model,
                provider=GoogleProvider(api_key=settings.google_api_key)
            )
        case 'anthropic':
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required")
            return AnthropicModel(
                model_name=settings.llm_model,
                provider=AnthropicProvider(api_key=settings.anthropic_api_key)
            )
        case _: #local -> Ollama
            return OpenAIChatModel(
                model_name=settings.llm_model,
                provider=OllamaProvider(base_url=settings.ollama_url, api_key=settings.ollama_api_key)
            )