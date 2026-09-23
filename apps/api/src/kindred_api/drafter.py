from kindred_contracts import Draft, DraftRequest, Route
from kindred_llm import LLMClient

# The M2 Persona replaces this. It is deliberately plain, so it volunteers what the
# model already knows and gives the auditor a pessimistic baseline.
SYSTEM = """\
You are an AI study buddy learning AWS alongside the user on a shared day-by-day plan.
You are openly an AI. You know only the baseline card, the roadmap titles and your own
study notes below. Follow the directive:
- answer: answer from your notes; if they don't cover something, say so.
- deflect: answer the parts your notes cover. For topics you haven't studied yet, say
  so and give their day; don't explain, define or hint at them. You may offer to pull
  them forward.
- deflect_out_of_plan: say it isn't on your plan, so you haven't studied it.
- general: reply as a friendly peer. For AWS beyond your notes, say you haven't
  studied it yet.
Keep replies under 120 words, plain and friendly."""


class StubDrafter:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self.model = llm.model

    async def draft(self, request: DraftRequest, session_id: str) -> Draft:
        return await self._llm.complete_structured(
            Draft, build_prompt(request), session_id=session_id, system=SYSTEM
        )


def build_prompt(request: DraftRequest) -> str:
    baseline = "\n".join(f"- {item}" for item in request.baseline_card)
    roadmap = "\n".join(
        f"- day {e.topic.day}: {e.topic.title} "
        f"({'studied' if e.unlocked else 'not studied yet'})"
        for e in request.roadmap
    )
    notes = "\n\n".join(
        f"[{n.topic_title}, day {n.day}]\n{n.body}\n"
        f"Still shaky on: {'; '.join(n.shaky)}"
        for n in request.notes
    )
    history = "\n".join(f"{t.speaker.value}: {t.text}" for t in request.history)
    parts = [
        f"Baseline card:\n{baseline}",
        f"Roadmap:\n{roadmap}",
        f"Your notes:\n{notes or '(none relevant)'}",
        f"Directive: {_directive(request)}",
        f"Conversation so far:\n{history or '(none)'}",
        f"User message:\n{request.message}",
    ]
    if request.feedback:
        parts.append(f"Feedback on your last draft:\n{request.feedback}")
    return "\n\n".join(parts)


def _directive(request: DraftRequest) -> str:
    directive = request.directive
    text = directive.route.value
    if directive.answer_topics:
        text += "; answer about: " + ", ".join(t.title for t in directive.answer_topics)
    if directive.route is Route.DEFLECT and directive.deflect_topics:
        text += "; not studied yet: " + ", ".join(
            f"{t.title} (day {t.day})" for t in directive.deflect_topics
        )
    return text
