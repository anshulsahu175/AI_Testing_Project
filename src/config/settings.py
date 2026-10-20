from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    bot_base_url: str = "http://127.0.0.1:8000"
    request_timeout: float = 30.0


settings = Settings()
