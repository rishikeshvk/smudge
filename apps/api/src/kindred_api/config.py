from datetime import time
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
    llm_model_curator: str = Field(min_length=1)
    llm_model_planner: str = Field(min_length=1)
    llm_model_judge: str = Field(min_length=1)

    database_url: str = Field(min_length=1)

    embed_base_url: str = Field(min_length=1)
    embed_api_key: SecretStr = Field(min_length=1)
    embed_model: str = Field(min_length=1)

    curricula_dir: Path = Path("curricula")

    # The buddy's rituals, in the user's local time.
    morning_ritual_time: time = time(8)
    night_review_time: time = time(21, 30)
    # Unprompted messages a day at most; replies don't count.
    ritual_daily_cap: int = Field(default=4, ge=1)
    expo_push_url: str = "https://exp.host/--/api/v2/push/send"

    # How long an unredeemed invite code works.
    invite_days: int = Field(default=7, ge=1)

    # The landing page's demo buddy: turns a day for every visitor together, turns an
    # hour per visitor, and the pages allowed to call it.
    demo_daily_turns: int = Field(default=30, ge=0)
    demo_client_turns_per_hour: int = Field(default=5, ge=1)
    demo_origins: list[str] = ["https://smudge.expo.app"]

    # Swaps real time for the persisted dev clock and enables /dev time controls.
    dev_mode: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
