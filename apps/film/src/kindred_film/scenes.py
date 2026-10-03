from dataclasses import dataclass
from typing import Literal

Ground = Literal["dawn", "day", "dusk", "night"]

# The app's dark ambients, so each cut keeps the phone's own time of day.
GROUNDS: dict[Ground, str] = {
    "dawn": "#1F1813",
    "day": "#121716",
    "dusk": "#18151F",
    "night": "#0F1320",
}

BUDDY = "juno"


@dataclass(frozen=True)
class Cut:
    """A stretch of one take's recording, in seconds from its start."""

    take: str
    start: float
    end: float

    @property
    def seconds(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class Card:
    id: str
    template: Literal["card-open", "card-end"]
    seconds: float
    voice: str


@dataclass(frozen=True)
class Shot:
    id: str
    ground: Ground
    meta: str
    caption: str
    wash: str
    voice: str
    you_day: int
    buddy_day: int
    cuts: tuple[Cut, ...]
    glow: bool = False
    # Seconds into the shot where the slow push starts and ends.
    push: tuple[float, float] | None = None

    @property
    def seconds(self) -> float:
        return sum(cut.seconds for cut in self.cuts)

    @property
    def day(self) -> int:
        return int(self.meta.split()[1])


Scene = Card | Shot

SCENES: tuple[Scene, ...] = (
    Card(
        id="01",
        template="card-open",
        seconds=7,
        voice="This is Smudge. A study buddy… that’s learning it too.",
    ),
    Shot(
        id="02",
        ground="dawn",
        meta="day 0 · 09:27",
        caption="you set the goal. it pushes back if it isn’t realistic.",
        wash="it pushes back",
        voice=(
            "You tell it what you want to learn. A-W-S, in two weeks, three hours a"
            " day. It pushes back — that’s a lot to keep up. So you settle on an "
            "hour, every evening at seven. It drafts the plan with you, and you "
            "give it a name."
        ),
        you_day=0,
        buddy_day=0,
        cuts=(
            Cut("02", 24, 33),
            Cut("02b", 13.5, 16.5),
            Cut("02b", 18, 22.5),
            Cut("02b", 44, 46.5),
            Cut("02b", 59, 62.5),
        ),
    ),
    Shot(
        id="03",
        ground="dawn",
        meta="day 1 · 08:00",
        caption="every morning, it says when it’s studying.",
        wash="",
        voice=(
            "Every morning, it shares what’s on today, and when it’s planning to "
            "study. You tell it when you will."
        ),
        you_day=1,
        buddy_day=1,
        cuts=(Cut("03", 17.5, 22), Cut("03", 25, 30), Cut("03", 51, 53.5)),
    ),
    Shot(
        id="04",
        ground="dusk",
        meta="day 2 · 20:04",
        caption="its notes have smudges. honest ones.",
        wash="smudges",
        voice=(
            "Then it actually studies, from the real A-W-S docs, and writes up its "
            "notes. Where it’s unsure, it leaves a smudge."
        ),
        you_day=2,
        buddy_day=2,
        cuts=(Cut("04", 21, 26.5), Cut("04b", 27.5, 33.5)),
    ),
    Shot(
        id="05",
        ground="dusk",
        meta="day 2 · 20:38",
        caption="it asks for a hand. explain it back.",
        wash="explain it back.",
        voice=(
            "Sometimes it asks you about one. Explaining it back is the best way to"
            " learn it yourself."
        ),
        you_day=2,
        buddy_day=2,
        cuts=(
            Cut("05a", 18, 22),
            Cut("05a", 45, 48),
            Cut("05a", 84.5, 88),
            Cut("05a", 130, 135),
        ),
    ),
    Shot(
        id="05b",
        ground="dawn",
        meta="day 3 · 08:07",
        caption="if you’re right, it’s sorted. and it’s yours.",
        wash="it’s yours.",
        voice=(
            "Overnight, it checks what you said against its sources. You were right"
            " — so the smudge is sorted, and the credit’s yours."
        ),
        you_day=2,
        buddy_day=2,
        cuts=(Cut("05b", 17.5, 21.5), Cut("05b", 40, 46)),
    ),
    Shot(
        id="06",
        ground="dawn",
        meta="day 4 · 10:01",
        caption="ask about tomorrow, and it can’t tell you. it hasn’t studied it.",
        wash="it hasn’t studied it.",
        voice=(
            "Now ask about tomorrow’s topic… It can’t tell you. Not won’t — can’t. "
            "It only knows what it’s studied so far, and every reply is checked for"
            " spoilers before you see it."
        ),
        you_day=4,
        buddy_day=4,
        cuts=(Cut("06", 28, 38), Cut("06", 64, 80)),
        push=(16, 24),
    ),
    Shot(
        id="07",
        ground="dusk",
        meta="day 4 · 19:00",
        caption="19:00. tap study with me. both lamps on.",
        wash="both lamps on.",
        voice=(
            "At seven, its lamp comes on. Tap study with me… and you’re both at "
            "your desks."
        ),
        you_day=4,
        buddy_day=4,
        cuts=(Cut("07", 0, 16),),
        glow=True,
        push=(8, 14),
    ),
    Shot(
        id="08",
        ground="night",
        meta="day 5 · 22:31",
        caption="skip a day and it keeps going. no guilt. no waiting.",
        wash="it keeps going.",
        voice=(
            "Skip a day, and it won’t wait. No guilt trip — it just keeps going, "
            "and the gap shows on the roadmap."
        ),
        you_day=4,
        buddy_day=5,
        cuts=(Cut("08", 0, 5), Cut("08", 8, 16)),
    ),
    Shot(
        id="09",
        ground="dusk",
        meta="day 7 · 20:10",
        caption="catch up, and you’re level again.",
        wash="level",
        voice=(
            "Catch up, and you’re level again. Same plan, same pace — side by side."
        ),
        you_day=7,
        buddy_day=7,
        cuts=(
            Cut("09", 3, 7),
            Cut("09", 15, 18.5),
            Cut("09", 19.5, 22),
            Cut("09", 33, 36),
            Cut("09b", 7.6, 12.6),
        ),
    ),
    Card(
        id="10",
        template="card-end",
        seconds=8,
        voice=(
            "Smudge is invite-only, for now. Watch the full week at smudge dot expo"
            " dot app."
        ),
    ),
)

# The landing page's muted loop: phone footage only, about 24 s.
LOOP: tuple[Cut, ...] = (
    Cut("03", 16, 24),
    Cut("06", 68, 76),
    Cut("07", 3, 11),
)


def shots() -> list[Shot]:
    return [scene for scene in SCENES if isinstance(scene, Shot)]
