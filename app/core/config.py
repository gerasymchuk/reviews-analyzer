from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    llm_provider: str
    llm_model: str = "kimi-k2.5:cloud"
    ollama_url: str = "https://ollama.com/v1"

    max_concurrency: int = 5
    chunk_size: int = 5

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    ollama_api_key: str | None = None

    default_country: str = "us"
    max_reviews: int = 500
    sample_size: int = 100


settings = Settings()