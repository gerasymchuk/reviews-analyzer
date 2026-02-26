from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    llm_provider: str
    llm_model: str = "llama3.1:latest"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

settings = Settings()