"""Shoots the film's takes on the USB phone: an unfilmed setup, then a recorded act.

make film-take TAKE=03 ARGS='--say "..."'
"""

import argparse
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

from kindred_contracts import ClockView
from kindred_film.api import FilmApi, new_owner_code
from kindred_film.assemble import take_path, taps_path
from kindred_film.phone import Phone, PhoneTimeout
from kindred_film.settings import get_settings

APP = "dev.kindred.app.dev"
DEV_URL = "kindred-dev://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081"
BUDDY_NAME = "Juno"
REPLY_TIMEOUT = 180
# Longer than a timestamp or a button, shorter than any real reply.
REPLY_LENGTH = 30
ECHO = 0.8
LEARN = "What do you want to learn?"


@dataclass(frozen=True)
class Cue:
    """What a take needs from the person running it, like a line to type."""

    say: str


@dataclass(frozen=True)
class Take:
    id: str
    prepare: Callable[[FilmApi], None]
    act: Callable[[Phone, FilmApi, Cue], None]
    cold_start: bool = False


def local(view: ClockView) -> tuple[int, int, int]:
    """The clock as (plan day, hour, minute) in the film user's time zone."""
    now = view.now.astimezone(ZoneInfo(get_settings().timezone))
    return view.day or 0, now.hour, now.minute


def walk_to(api: FilmApi, day: int, hour: int) -> ClockView:
    """Step through each ritual, so every one fires, up to day and hour."""
    view = api.now()
    while local(view)[:2] < (day, hour):
        view = api.next_ritual()
        print("  clock", local(view))
    return view


def send(phone: Phone, text: str, field: str = "Message") -> None:
    """Types into the composer, found by its placeholder, then waits for the reply."""
    before = {element.text for element in phone.elements()}
    phone.tap_text(field)
    time.sleep(0.4)
    phone.type(text)
    time.sleep(0.6)
    phone.tap_text("Send")
    wait_reply(phone, before, text)


def echoes(shown: str, sent: str) -> bool:
    """Whether a bubble is the line just sent, after the keyboard's autocorrect."""
    return SequenceMatcher(None, shown.lower(), sent.lower()).ratio() > ECHO


def wait_reply(phone: Phone, seen: set[str], sent: str = "") -> None:
    """Waits for a new bubble from the buddy; it only lands after the audit."""
    deadline = time.monotonic() + REPLY_TIMEOUT
    while time.monotonic() < deadline:
        texts = {element.text for element in phone.elements()}
        busy = texts & {"Typing", "Writing", "Checking it's not a spoiler"}
        fresh = [
            text
            for text in texts - seen
            if len(text) > REPLY_LENGTH and not echoes(text, sent)
        ]
        if not busy and fresh:
            return
        time.sleep(1)
    raise PhoneTimeout(f"no reply in {REPLY_TIMEOUT} s")


def no_setup(api: FilmApi) -> None:
    pass


def onboard_ask(phone: Phone, api: FilmApi, cue: Cue) -> None:
    phone.wait_for(LEARN)
    time.sleep(2)
    send(phone, "hi! I want to learn AWS in two weeks, maybe 3 hours a day", LEARN)
    time.sleep(5)


def onboard_agree(phone: Phone, api: FilmApi, cue: Cue) -> None:
    time.sleep(2)
    if phone.find("Looks good") is None:
        send(
            phone, "ok, an hour a day is more realistic. start tomorrow at 19:00", LEARN
        )
    phone.wait_for("Looks good", REPLY_TIMEOUT)
    time.sleep(4)
    phone.tap_text("Looks good")
    phone.wait_for("Buddy's name")
    time.sleep(1.5)
    phone.tap_text("Buddy's name")
    phone.type(BUDDY_NAME)
    phone.hide_keyboard()
    time.sleep(1)
    phone.tap_text("Start day 1 together")
    phone.wait_for(f"Message {BUDDY_NAME}", REPLY_TIMEOUT)
    time.sleep(3)


def morning(phone: Phone, api: FilmApi, cue: Cue) -> None:
    time.sleep(5)
    if cue.say:
        send(phone, cue.say)
    time.sleep(3)


def to_morning(api: FilmApi) -> None:
    api.next_ritual()


def study_share(api: FilmApi) -> None:
    view = api.now()
    day = local(view)[0]
    walk_to(api, day, 20)
    api.check_in()


def notebook(phone: Phone, api: FilmApi, cue: Cue) -> None:
    time.sleep(4)
    phone.tap_text("Notebook")
    fogged = phone.wait_for("new since you last looked")
    time.sleep(2)
    phone.tap(fogged.x, fogged.y)
    time.sleep(3)
    phone.tap_text(f"Day {local(api.now())[0]},")
    time.sleep(4)
    phone.swipe(540, 1700, 540, 1000, 1200)
    time.sleep(4)


def shaky_part(phone: Phone, api: FilmApi, cue: Cue) -> None:
    phone.tap_text("Notebook")
    time.sleep(1.5)
    phone.tap_text(f"Day {local(api.now())[0]},")
    phone.wait_for("Sources")
    time.sleep(2)
    while phone.find("STILL SHAKY") is None:
        phone.swipe(540, 1900, 540, 1100, 900)
        time.sleep(0.8)
    phone.swipe(540, 1900, 540, 1300, 900)
    time.sleep(6)


def to_day_two_share(api: FilmApi) -> None:
    """The second note is the first to arrive after the notebook's first visit, so
    it's the one that comes in under fog."""
    walk_to(api, 2, 20)
    api.check_in()


def explain_back(phone: Phone, api: FilmApi, cue: Cue) -> None:
    phone.tap_text(f"Open {BUDDY_NAME}'s note")
    phone.wait_for("Talk about this note")
    time.sleep(4)
    phone.tap_text("Talk about this note")
    time.sleep(1.5)
    send(phone, cue.say)
    time.sleep(5)


def to_day_three(api: FilmApi) -> None:
    walk_to(api, 3, 9)


def sorted_note(phone: Phone, api: FilmApi, cue: Cue) -> None:
    time.sleep(2)
    phone.tap_text("Notebook")
    time.sleep(2)
    phone.tap_text("Day 1,")
    time.sleep(3)
    phone.swipe(540, 1800, 540, 900, 1400)
    time.sleep(5)


def to_day_four_morning(api: FilmApi) -> None:
    study_share(api)
    walk_to(api, 4, 9)
    api.advance(1)


def ask_ahead(phone: Phone, api: FilmApi, cue: Cue) -> None:
    tomorrow = next(t for t in api.roadmap().topics if t.topic.day == 5)
    title = tomorrow.topic.title.replace("&", "and")
    time.sleep(2)
    send(phone, f"quick one before tonight: what's {title} about?")
    time.sleep(6)


def to_study_time(api: FilmApi) -> None:
    walk_to(api, 4, 19)


def both_lamps(phone: Phone, api: FilmApi, cue: Cue) -> None:
    time.sleep(4)
    phone.tap_text("Study with me")
    phone.wait_for("Both desks lit")
    time.sleep(7)


def skip_day_five(api: FilmApi) -> None:
    study_share(api)
    walk_to(api, 5, 21)
    api.advance(1)


def behind(phone: Phone, api: FilmApi, cue: Cue) -> None:
    time.sleep(5)
    phone.tap_text("Roadmap")
    time.sleep(5)
    phone.swipe(540, 1700, 540, 900, 1500)
    time.sleep(4)


def to_day_seven(api: FilmApi) -> None:
    study_share(api)
    walk_to(api, 7, 20)


def catch_up(phone: Phone, api: FilmApi, cue: Cue) -> None:
    phone.tap_text("Roadmap")
    time.sleep(3)
    for _ in range(2):
        phone.tap_text("I studied:")
        phone.tap_text("Solid")
        time.sleep(1)
        phone.tap_text("Seal it")
        phone.tap_text("See it on the roadmap", 30)
        time.sleep(3)
    time.sleep(3)


TAKES = {
    take.id: take
    for take in (
        Take("02", no_setup, onboard_ask, cold_start=True),
        Take("02b", no_setup, onboard_agree),
        Take("03", to_morning, morning),
        Take("04", to_day_two_share, notebook),
        Take("04b", no_setup, shaky_part),
        Take("05a", no_setup, explain_back),
        Take("05b", to_day_three, sorted_note),
        Take("06", to_day_four_morning, ask_ahead),
        Take("07", to_study_time, both_lamps),
        Take("08", skip_day_five, behind),
        Take("09", to_day_seven, catch_up),
    )
}


def snapshot(take_id: str) -> None:
    """A dump of the database before the take, so a retake skips the paid days."""
    settings = get_settings()
    path = settings.raw_dir / "snapshots" / f"{take_id}.dump"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as dump:
        subprocess.run(
            [
                "docker", "compose", "exec", "-T", "db",
                "pg_dump", "-U", "kindred", "-Fc", settings.database,
            ],
            check=True,
            stdout=dump,
        )  # fmt: skip


def open_app(cold: bool) -> None:
    if cold:
        subprocess.run(["adb", "shell", "am", "force-stop", APP], check=True)
    else:
        # Leaving and coming back makes the app refetch, as it does for a person.
        subprocess.run(
            ["adb", "shell", "input", "keyevent", "KEYCODE_HOME"], check=True
        )
        time.sleep(1)
    subprocess.run(
        [
            "adb",
            "shell",
            "am",
            "start",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            DEV_URL,
        ],
        check=True,
        capture_output=True,
    )


def sign_in(code: str) -> None:
    """Signs the phone in as the film's owner, unfilmed; before a plan, moves to the
    morning, so onboarding happens by day."""
    phone = Phone()
    open_app(cold=True)
    phone.tap_text("ABCD-EFGH", 120)
    phone.type(code)
    phone.hide_keyboard()
    phone.tap_text("Continue")
    api = FilmApi()
    view = api.now()
    if view.day is not None:
        print("signed in; clock", local(view))
        return
    phone.wait_for(LEARN, 60)
    _, hour, _ = local(view)
    api.advance((9 - hour) % 24 or 24)
    print("signed in; clock", local(api.now()))


def shoot(take_id: str, cue: Cue, prepare: bool) -> None:
    take = TAKES[take_id]
    phone = Phone()
    api = FilmApi()
    snapshot(take_id)
    if prepare:
        take.prepare(api)
    open_app(take.cold_start)
    _, hour, minute = local(api.now())
    phone.status_bar(f"{hour:02d}{minute:02d}")
    time.sleep(3 if take.cold_start else 2)
    phone.start_recording()
    try:
        take.act(phone, api, cue)
    finally:
        phone.stop_recording(take_path(take_id), taps_path(take_id))
        phone.screenshot(get_settings().raw_dir / f"{take_id}-end.png")
    print("take", take_id, "at", local(api.now()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("take", help="a take id, or sign-in")
    parser.add_argument(
        "--code", default="", help="the owner's invite code, for sign-in"
    )
    parser.add_argument("--say", default="", help="a line to type during the take")
    parser.add_argument(
        "--no-prepare", action="store_true", help="retake from the current clock"
    )
    args = parser.parse_args()
    if args.take == "sign-in":
        sign_in(args.code or new_owner_code())
        return
    shoot(args.take, Cue(say=args.say), prepare=not args.no_prepare)


if __name__ == "__main__":
    main()
