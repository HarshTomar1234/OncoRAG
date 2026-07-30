from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    weaviate_url: str
    weaviate_api_key: str
    openfda_api_key: str
    anthropic_api_key: str
    # Admin bypass for /chat's rate limits (Authorization: Bearer <secret>) -
    # used by this project's own eval/red-team scripts to call the paid
    # Anthropic API without hitting the anonymous-visitor daily caps.
    api_secret: str


settings = Settings()
