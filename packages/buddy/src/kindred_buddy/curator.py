from kindred_contracts import MAX_NOTE_WORDS, NoteDraft, SourceExcerpt, StudyBrief
from kindred_llm import LLMClient

# About 6k tokens of reading a night: enough for the key pages, cheap by default.
SOURCE_BUDGET_CHARS = 24_000

SYSTEM = f"""\
You are an AI study buddy writing tonight's study notes for your own notebook. You are
learning "{{plan}}" day by day, and today's topic is the only new one you may study.

Write like a real learner, in the first person, in plain markdown:
- Explain today's topic in your own words from the sources given, nothing else. Don't
  add facts they don't contain.
- Stay inside today's topic. If the sources wander into other services or features,
  leave those out entirely: don't name, explain or preview them.
- Connect to what you studied on earlier days where it helps.
- At most {MAX_NOTE_WORDS} words.

Leave real gaps. Pick 1 to 3 things from today's topic that a learner would genuinely
find confusing or not fully get on a first pass, list them in "shaky" as honest
questions or doubts, and don't resolve them in the body. Never write something wrong on
purpose; the gaps are things you're unsure of, not mistakes.

In "sources", list the URLs of the pages you actually used."""


class Curator:
    """Writes the buddy's nightly study note from the topic's gated sources."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self.model = llm.model

    async def study(self, brief: StudyBrief, session_id: str) -> NoteDraft:
        draft = await self._llm.complete_structured(
            NoteDraft,
            build_prompt(brief),
            session_id=session_id,
            system=SYSTEM.format(plan=brief.plan_title),
        )
        return _cite_only_given_pages(draft, brief)


def build_prompt(brief: StudyBrief) -> str:
    baseline = "\n".join(f"- {item}" for item in brief.baseline_card)
    earlier = "\n".join(
        f"- day {note.topic.day}: {note.topic.title}. Still shaky: "
        + "; ".join(note.shaky)
        for note in brief.earlier
    )
    parts = [
        f"Today: day {brief.topic.day}, {brief.topic.title}",
        f"What today's topic covers:\n{brief.focus}",
        f"What you knew before day 1:\n{baseline}",
        f"Your earlier notes:\n{earlier or '(none yet: this is your first day)'}",
        f"Sources:\n\n{_excerpts(brief.sources)}",
    ]
    if brief.feedback:
        parts.append(f"Feedback on your last draft:\n{brief.feedback}")
    return "\n\n".join(parts)


def _excerpts(sources: list[SourceExcerpt]) -> str:
    # Split the budget evenly so one long page can't crowd out the rest.
    share = SOURCE_BUDGET_CHARS // len(sources)
    return "\n\n".join(
        f"[{source.title}]({source.url})\n{source.text[:share]}" for source in sources
    )


def _cite_only_given_pages(draft: NoteDraft, brief: StudyBrief) -> NoteDraft:
    given = [source.url for source in brief.sources]
    cited = [url for url in draft.sources if url in given]
    # The note was written from these pages, so a bad citation falls back to them.
    return draft.model_copy(update={"sources": cited or given})
