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


@dataclass(frozen=True)
class Shot:
    id: str
    ground: Ground
    meta: str
    caption: str
    wash: str
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
    Card(id="01", template="card-open", seconds=7),
    Shot(
        id="02",
        ground="dawn",
        meta="day 0 · 09:30",
        caption="you set the goal. it pushes back if it isn’t realistic.",
        wash="it pushes back",
        you_day=0,
        buddy_day=0,
        cuts=(Cut("02", 0, 17),),
    ),
    Shot(
        id="03",
        ground="dawn",
        meta="day 1 · 09:00",
        caption="every morning, it says when it’s studying.",
        wash="",
        you_day=1,
        buddy_day=1,
        cuts=(Cut("03", 0, 12),),
    ),
    Shot(
        id="04",
        ground="night",
        meta="day 1 · 21:00",
        caption="its notes have smudges. honest ones.",
        wash="smudges",
        you_day=1,
        buddy_day=1,
        cuts=(Cut("04", 0, 17),),
    ),
    Shot(
        id="05",
        ground="dusk",
        meta="day 2 · 20:00",
        caption="explain it back. if you’re right, it’s sorted, and it’s yours.",
        wash="it’s yours",
        you_day=2,
        buddy_day=2,
        cuts=(Cut("05a", 0, 12), Cut("05b", 0, 8)),
    ),
    Shot(
        id="06",
        ground="dawn",
        meta="day 4 · 10:00",
        caption="ask about tomorrow, and it can’t tell you. it hasn’t studied it.",
        wash="it hasn’t studied it.",
        you_day=4,
        buddy_day=4,
        cuts=(Cut("06", 0, 18),),
        push=(9, 14),
    ),
    Shot(
        id="07",
        ground="dusk",
        meta="day 4 · 19:00",
        caption="19:00. tap study with me. both lamps on.",
        wash="both lamps on.",
        you_day=4,
        buddy_day=4,
        cuts=(Cut("07", 0, 18),),
        glow=True,
        push=(10, 15),
    ),
    Shot(
        id="08",
        ground="night",
        meta="day 5 · 22:00",
        caption="skip a day and it keeps going. no guilt. no waiting.",
        wash="it keeps going.",
        you_day=4,
        buddy_day=5,
        cuts=(Cut("08", 0, 17),),
    ),
    Shot(
        id="09",
        ground="day",
        meta="day 7 · 13:00",
        caption="catch up, and you’re level again.",
        wash="level",
        you_day=7,
        buddy_day=7,
        cuts=(Cut("09", 0, 14),),
    ),
    Card(id="10", template="card-end", seconds=8),
)

# The landing page's muted loop: phone footage only, about 24 s.
LOOP: tuple[Cut, ...] = (
    Cut("03", 2, 10),
    Cut("06", 2, 10),
    Cut("07", 2, 10),
)


def shots() -> list[Shot]:
    return [scene for scene in SCENES if isinstance(scene, Shot)]
