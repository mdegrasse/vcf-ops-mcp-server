from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VCFOPS_", env_file=".env", extra="ignore")

    base_url: str
    username: str
    password: str
    auth_source: str = "LOCAL"
    verify_ssl: bool = False
    timeout: float = 30.0


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VCFOPS_MCP_", env_file=".env", extra="ignore")

    transport: Literal["stdio", "streamable-http"] = "streamable-http"
    host: str = "127.0.0.1"
    port: int = 8000
    bearer_token: str | None = None


def load_settings() -> Settings:
    return Settings()


def load_server_settings() -> ServerSettings:
    return ServerSettings()
