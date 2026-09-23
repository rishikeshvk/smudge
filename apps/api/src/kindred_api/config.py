from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str = Field(min_length=1)
    llm_api_key: SecretStr = Field(min_length=1)
    llm_model_classifier: str = Field(min_length=1)
    llm_model_persona: str = Field(min_length=1)
    llm_model_auditor: str = Field(min_length=1)
    llm_model_judge: str = Field(min_length=1)

    database_url: str = Field(min_length=1)

    embed_base_url: str = Field(min_length=1)
    embed_api_key: SecretStr = Field(min_length=1)
    embed_model: str = Field(min_length=1)

    curricula_dir: Path = Path("curricula")

    # Swaps real time for the persisted dev clock and enables /dev time controls.
    dev_mode: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
