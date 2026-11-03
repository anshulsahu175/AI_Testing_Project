from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    bot_base_url: str = "http://127.0.0.1:8000"
    request_timeout: float = 30.0
    max_latency_ms: float = 10000.0
    min_fact_coverage: float = 1.0
    min_similarity: float = 0.15
    judge_pass_threshold: float = 4.0
    judge_delay_seconds: float = 4.0
    judge_timeout: float = 90.0
    judge_cache_dir: str = ".cache/judge"
    use_mocks: bool = False
    bot_autostart: bool = True

    @model_validator(mode="after")
    def keys_required_without_mocks(self) -> "Settings":
        """API keys are only needed for real models; mock mode (CI) runs without them."""
        if not self.use_mocks:
            missing = [n for n in ("groq_api_key", "gemini_api_key") if not getattr(self, n)]
            if missing:
                raise ValueError(f"missing {missing}: set them in .env, or set USE_MOCKS=true")
        return self


settings = Settings()
