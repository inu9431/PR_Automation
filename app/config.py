from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str
    github_token: str
    github_webhook_secret: str
    discord_webhook_url: str
    database_url: str
    debug: bool = False

    claude_model: str = "claude-sonnet-4-5"
    claude_max_tokens: int = 1500
    claude_input_price: float = 3.0
    claude_output_price: float = 15.0

settings = Settings()

