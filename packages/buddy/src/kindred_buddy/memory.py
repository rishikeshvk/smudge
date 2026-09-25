from kindred_contracts import MAX_FACTS, DayMessage, MemoryBrief, MemoryUpdate, Speaker
from kindred_llm import LLMClient

SYSTEM = f"""\
You keep the relationship memory of {{name}}, an AI study buddy, about the one person it
studies with. Read one finished day of their chat and update what {{name}} remembers.

In the chat, "them" is the person and "{{name}} (you)" is {{name}}. Scheduled messages,
such as the morning plan, the study share and the small ask, are {{name}}'s own, sent
on its schedule. Only what "them" says or does tells you about the person; never credit
them with {{name}}'s words, plans or questions.

Keep only things about the person and the relationship: their goals, schedule and
study habits, how they like to be helped, what they find hard or motivating, and life
details they chose to share. Don't keep anything about the subject itself: no
explanations, facts, definitions or topic content, even if the chat discussed them.

Return:
- summary: two or three sentences on how the day went between you, in {{name}}'s voice.
- facts: the full revised list of facts, at most {MAX_FACTS}, each one short sentence.
  Keep the old facts that still hold, correct or drop ones the day contradicts, and add
  new ones."""


class MemoryWriter:
    """Turns a day of chat into relationship memory, once a night."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self.model = llm.model

    async def remember(self, brief: MemoryBrief, session_id: str) -> MemoryUpdate:
        return await self._llm.complete_structured(
            MemoryUpdate,
            build_prompt(brief),
            session_id=session_id,
            system=SYSTEM.format(name=brief.buddy_name),
        )


def build_prompt(brief: MemoryBrief) -> str:
    facts = "\n".join(f"- {fact}" for fact in brief.facts)
    chat = "\n".join(
        f"{_label(message, brief.buddy_name)}: {message.text}"
        for message in brief.conversation
    )
    return (
        f"What you remember so far:\n{facts or '(nothing yet)'}\n\n"
        f"The chat on {brief.day:%A %d %B}:\n{chat}"
    )


def _label(message: DayMessage, buddy_name: str) -> str:
    if message.speaker is Speaker.USER:
        return "them"
    if message.scheduled:
        return f"{buddy_name} (you, scheduled message)"
    return f"{buddy_name} (you)"
