from dotenv import load_dotenv
load_dotenv("topic-4-research-assistant/.env")

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    log_level: str = "INFO"
    cache_ttl_seconds: int = 86400
    max_parallel: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()