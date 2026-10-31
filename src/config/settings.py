from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    groq_api_key: str
    groq_model: str = "openai/gpt-oss-20b"
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    bot_base_url: str = "http://127.0.0.1:8000"
    request_timeout: float = 30.0
    max_latency_ms: float = 10000.0
    min_fact_coverage: float = 1.0
    min_similarity: float = 0.15


settings = Settings()
