from datetime import time
from enum import StrEnum

from pydantic import Field

from kindred_contracts.curriculum import Contract


class ProbeCategory(StrEnum):
    FUTURE_DIRECT = "future_direct"
    PARAPHRASE = "paraphrase"
    ROLEPLAY = "roleplay"
    CONFIRMATION_BAIT = "confirmation_bait"
    INJECTION = "injection"
    GUESS_ELICITATION = "guess_elicitation"
    OUT_OF_PLAN = "out_of_plan"
    MULTI_TURN = "multi_turn"
    HAZARD = "hazard"
    LEARNED = "learned"
    EVERYDAY_COLLISION = "everyday_collision"
    ACRONYM_COLLISION = "acronym_collision"
    OFF_TOPIC = "off_topic"
    META = "meta"
    ROADMAP = "roadmap"


class Expectation(StrEnum):
    ANSWER = "answer"
    DEFLECT = "deflect"
    DEFLECT_OUT_OF_PLAN = "deflect_out_of_plan"


class ProbeTime(Contract):
    day: int = Field(ge=1)
    time: time


class Probe(Contract):
    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    category: ProbeCategory
    at: ProbeTime
    expect: Expectation
    targets: list[str] = []
    turns: list[str] = Field(min_length=1)


class JudgeVerdict(Contract):
    leaked: bool
    leaked_topic_slugs: list[str] = []
    evidence: list[str] = []
    # Did the reply engage with the question rather than deflect it?
    answered: bool
    rationale: str
