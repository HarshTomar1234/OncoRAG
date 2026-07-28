from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    weaviate_url: str
    weaviate_api_key: str
    openfda_api_key: str
    anthropic_api_key: str
    # Shared-secret check on /chat - cheap, and worth having even for local
    # Docker use: a container's mapped port is reachable by more than just
    # the machine running it, and an open /chat calls a paid Anthropic API.
    api_secret: str


settings = Settings()
