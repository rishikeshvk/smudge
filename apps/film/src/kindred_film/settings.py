from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

FILM_DIR = Path(__file__).resolve().parents[2]


class FilmSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FILM_")

    # The dev API on kindred_film, which the phone reaches over adb reverse.
    api_url: str = "http://127.0.0.1:8000"
    database: str = "kindred_film"
    # The film user's zone, for the status-bar clock.
    timezone: str = "Asia/Kolkata"
    templates_dir: Path = FILM_DIR / "templates"
    raw_dir: Path = FILM_DIR / "raw"
    out_dir: Path = FILM_DIR / "out"


@lru_cache
def get_settings() -> FilmSettings:
    return FilmSettings()
