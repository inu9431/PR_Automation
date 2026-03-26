from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str
    github_token: str
    discord_webhook_url: str
    database_url: str
    debug: bool = False

settings = Settings()

