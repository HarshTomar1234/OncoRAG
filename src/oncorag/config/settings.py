from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    weaviate_url: str
    weaviate_api_key: str
    openfda_api_key: str
    anthropic_api_key: str


settings = Settings()
