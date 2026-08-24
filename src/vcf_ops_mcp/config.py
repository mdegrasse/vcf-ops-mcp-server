from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VCFOPS_", env_file=".env", extra="ignore")

    base_url: str
    username: str
    password: str
    auth_source: str = "LOCAL"
    verify_ssl: bool = False
    timeout: float = 30.0


def load_settings() -> Settings:
    return Settings()
