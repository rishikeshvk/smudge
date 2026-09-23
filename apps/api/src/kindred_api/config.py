from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str = Field(min_length=1)
    llm_api_key: SecretStr = Field(min_length=1)
    llm_model_classifier: str = Field(min_length=1)
    llm_model_drafter: str = Field(min_length=1)
    llm_model_auditor: str = Field(min_length=1)
    llm_model_judge: str = Field(min_length=1)

    database_url: str = Field(min_length=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
