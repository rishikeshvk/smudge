"""The film user's own API session: moves the clock and checks in between takes."""

import os
import re
import subprocess
from pathlib import Path

import httpx2

from kindred_contracts import (
    AdvanceClock,
    AuthToken,
    CheckIn,
    ClockView,
    Feeling,
    JumpToDay,
    RedeemInvite,
    RoadmapView,
)
from kindred_film.settings import get_settings

CODE = re.compile(r"^([A-Z0-9]{4}-[A-Z0-9]{4})\s", re.MULTILINE)
# The Curator and the Reflector run inside these calls.
TICK_TIMEOUT = 600


def _token_path() -> Path:
    return get_settings().raw_dir / ".owner-token"


def _new_owner_code() -> str:
    settings = get_settings()
    database_url = (
        f"postgresql+psycopg://kindred:kindred@localhost:5432/{settings.database}"
    )
    result = subprocess.run(
        ["uv", "run", "python", "-m", "kindred_api.accounts", "invite", "--user", "1"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "DATABASE_URL": database_url},
    )
    match = CODE.search(result.stdout)
    if match is None:
        raise RuntimeError(f"no invite code in: {result.stdout!r}")
    return match.group(1)


class FilmApi:
    def __init__(self) -> None:
        self._client = httpx2.Client(
            base_url=get_settings().api_url, timeout=TICK_TIMEOUT
        )
        self._client.headers["Authorization"] = f"Bearer {self._token()}"

    def _token(self) -> str:
        path = _token_path()
        if path.exists():
            return path.read_text().strip()
        response = self._client.post(
            "/auth/redeem",
            json=RedeemInvite(code=_new_owner_code()).model_dump(),
        )
        response.raise_for_status()
        token = AuthToken.model_validate(response.json()).token
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(token)
        return token

    def _post(self, path: str, body: dict[str, object] | None = None) -> ClockView:
        response = self._client.post(path, json=body)
        response.raise_for_status()
        return ClockView.model_validate(response.json())

    def now(self) -> ClockView:
        response = self._client.get("/dev/clock")
        response.raise_for_status()
        return ClockView.model_validate(response.json())

    def advance(self, hours: int) -> ClockView:
        change = AdvanceClock(kind="advance", hours=hours)
        return self._post("/dev/clock", change.model_dump())

    def jump(self, day: int) -> ClockView:
        return self._post(
            "/dev/clock", JumpToDay(kind="jump_to_day", day=day).model_dump()
        )

    def next_ritual(self) -> ClockView:
        return self._post("/dev/next-ritual")

    def study_now(self) -> ClockView:
        return self._post("/dev/study-now")

    def roadmap(self) -> RoadmapView:
        response = self._client.get("/roadmap")
        response.raise_for_status()
        return RoadmapView.model_validate(response.json())

    def check_in(self, feeling: Feeling = Feeling.OKAY) -> None:
        response = self._client.post(
            "/progress/checkins", json=CheckIn(feeling=feeling).model_dump()
        )
        response.raise_for_status()
