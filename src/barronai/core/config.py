from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = Field(default="dev")
    LOG_LEVEL: str = Field(default="INFO")
    ALPACA_API_KEY_ID: str | None = None
    ALPACA_API_SECRET_KEY: str | None = None
    ALPACA_PAPER_BASE_URL: str = "https://paper-api.alpaca.markets"
    DATABASE_URL: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
