from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    firebase_credentials_path: str = ""
    # When True the backend decodes the JWT locally without signature verification.
    # Safe for local dev; never use in production.
    dev_skip_auth: bool = False
    gemini_api_key: str = ""
    # When True mDNS advertisement is skipped entirely.
    # Set automatically by the test suite (tests restart the app many times
    # and Zeroconf raises NonUniqueNameException on re-registration).
    # Do NOT set this in your dev .env — mDNS is how the Flutter app finds your Mac.
    skip_mdns: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
