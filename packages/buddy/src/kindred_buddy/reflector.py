from kindred_buddy.sources import excerpts
from kindred_contracts import MAX_INSIGHT_WORDS, Reflection, ReflectionBrief, Speaker
from kindred_llm import LLMClient

# Enough of the topic's pages to check an explanation, at half a night's reading.
SOURCE_BUDGET_CHARS = 12_000

SYSTEM = f"""\
You are an AI study buddy learning "{{plan}}" day by day, alongside the user. Earlier
you wrote a note on one topic, with shaky points you didn't get. Today the user talked
with you about that topic. For each shaky point, decide whether what they said sorted
it out for you.

A point is sorted only if the user actually explained or answered it, not just
mentioned or asked about it, and the topic's sources back their explanation up. If the
sources don't back it up, it isn't sorted, however confident they sounded.

For a sorted point, write "insight": what you understand now, in the first person, at
most {MAX_INSIGHT_WORDS} words, using only what the user said and the sources confirm.
Stay inside this topic: don't name or explain anything the sources wander into beyond
it. For a point that isn't sorted, leave insight empty.

Return every shaky point you were given, word for word, in "points"."""


class Reflector:
    """Checks what the user explained against the sources, once a night."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self.model = llm.model

    async def reflect(self, brief: ReflectionBrief, session_id: str) -> Reflection:
        return await self._llm.complete_structured(
            Reflection,
            build_prompt(brief),
            session_id=session_id,
            system=SYSTEM.format(plan=brief.plan_title),
        )


def build_prompt(brief: ReflectionBrief) -> str:
    shaky = "\n".join(f"- {point}" for point in brief.open_shaky)
    chat = "\n".join(
        f"{'them' if turn.speaker is Speaker.USER else 'you'}: {turn.text}"
        for turn in brief.exchanges
    )
    return "\n\n".join(
        [
            f"Topic: day {brief.topic.day}, {brief.topic.title}",
            f"Your shaky points:\n{shaky}",
            f"What you and the user said about it today:\n{chat}",
            f"Sources:\n\n{excerpts(brief.sources, SOURCE_BUDGET_CHARS)}",
        ]
    )
