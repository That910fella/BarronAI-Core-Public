from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = Field(default="dev")
    LOG_LEVEL: str = Field(default="INFO")
    # trading / integrations
    ALPACA_API_KEY_ID: str | None = None
    ALPACA_API_SECRET_KEY: str | None = None
    ALPACA_PAPER_BASE_URL: str = "https://paper-api.alpaca.markets"
    DATABASE_URL: str | None = None
    # feature flags / safety
    PAPER_ONLY: bool | None = True         # hard stop for live trading
    EMAIL_ALERTS: bool | None = False
    NOTION_ENABLED: bool | None = False

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
