from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    firebase_credentials_path: str = ""
    # When True the backend decodes the JWT locally without signature verification.
    # Safe for local dev; never use in production.
    dev_skip_auth: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
