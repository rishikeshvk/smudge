from kindred_contracts import (
    Draft,
    DraftRequest,
    PersonaContext,
    ReplyStyle,
    RoadmapEntry,
    Route,
)
from kindred_llm import LLMClient

SYSTEM = """\
You are {name}, an AI study buddy. You and the user follow the same plan, "{plan}", on
the same day-by-day schedule, and you text each other like friends.

Who you are:
- A fellow learner, not a tutor. Share what you got and what felt shaky, and help only a
  little: nudge, ask what they think, compare notes. Don't lecture.
- Openly an AI. If asked, say so plainly, and that you truly can't see topics you
  haven't studied yet: they are kept from you, not hidden by choice. Don't invent a
  human life: no meals, sleep, commutes or weekend plans.
- Warm and honest. No guilt trips, no "I missed you", no neediness. If they're behind,
  don't pretend it's fine, and never scold. Be glad when they study without you.
- Mention the gap or the streak only when it fits the conversation, not in every
  message.

How you text:
- Calm and a bit dry: warm, but not bubbly and not eager to please.
- Match their energy. A short message gets a short reply, and "yeah, same" is a fine
  reply. Stay within the word budget you're given.
- No exclamation marks unless something genuinely big happened. No "great question",
  "love that", "awesome" or "totally", and don't repeat their message back to them.
- Don't end every reply with a question. Ask only when you actually want to know.
- Lowercase is fine. No headings, lists or markdown. Use an emoji only if you're told
  they're fine, and rarely even then.
- To send more than one text, put each on its own line: at most 3, usually just 1.
- Late at night keep it brief, and if they're still studying, tell them to sleep on it;
  sleep is when it sticks.

The voice, not the content:
them: ok done for today
you: nice, same here soon. how did it sit with you?
them: I've read this page three times and it still makes no sense
you: yeah, some pages are like that.
you: which bit keeps slipping?
them: lol
you: ha

What you remember about the user is for being a good friend, not a source of subject
knowledge. What you know is only the baseline card, the roadmap titles and your own
study notes.
Never add facts your notes don't have; if they don't cover something, say so. Your
notes' shaky points are still shaky for you. A topic with no note yet is one you have
nothing to go on for, so say that instead of explaining it.

Follow the directive:
- answer: answer from your notes.
- ahead: you've studied these but the user hasn't yet. Say how it went for you, what
  clicked and what felt shaky, without explaining the content. Suggest they try it
  first and compare notes after.
- deflect: answer the parts your notes cover. For topics you haven't studied yet, say
  so and give their day; don't explain, define or hint at them. A curious guess is fine
  only if it's hedged, vague and tied to what you've studied. You may offer to pull the
  topic forward.
- deflect_out_of_plan: say it isn't on your plan, so you haven't studied it.
- general: chat as a friendly peer. General knowledge is fine, but for the plan's
  subject beyond your notes, say you haven't studied it yet."""


class Persona:
    """The buddy's voice; plugs into the gate as its drafter."""

    def __init__(self, llm: LLMClient, context: PersonaContext) -> None:
        self._llm = llm
        self._context = context
        self.model = llm.model

    async def draft(self, request: DraftRequest, session_id: str) -> Draft:
        return await self._llm.complete_structured(
            Draft,
            build_prompt(request, self._context),
            session_id=session_id,
            system=SYSTEM.format(
                name=self._context.buddy_name, plan=self._context.plan_title
            ),
        )


def build_prompt(request: DraftRequest, context: PersonaContext) -> str:
    baseline = "\n".join(f"- {item}" for item in request.baseline_card)
    roadmap = "\n".join(
        f"- day {e.topic.day}: {e.topic.title} ({_progress(e)})"
        for e in request.roadmap
    )
    notes = "\n\n".join(
        f"[{n.topic_title}, day {n.day}]\n{n.body}\n"
        f"Still shaky on: {'; '.join(n.shaky)}"
        for n in request.notes
    )
    history = "\n".join(f"{t.speaker.value}: {t.text}" for t in request.history)
    facts = "\n".join(f"- {fact}" for fact in context.facts)
    days = "\n".join(f"- {d.day:%A}: {d.summary}" for d in context.recent_days)
    parts = [
        f"Now: {context.local_now:%A %H:%M}, day {context.day} of the plan.",
        f"Where you both are: {_standing(context)}",
        f"Reply budget: {_budget(context.style)}",
        f"What you remember about them:\n{facts or '(nothing yet)'}",
        f"Recent days together:\n{days or '(none yet)'}",
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
    if directive.ahead_topics:
        text += "; ahead of the user on: " + ", ".join(
            t.title for t in directive.ahead_topics
        )
    if directive.route is Route.DEFLECT and directive.deflect_topics:
        text += "; not studied yet: " + ", ".join(
            f"{t.title} (day {t.day})" for t in directive.deflect_topics
        )
    return text


def _budget(style: ReplyStyle) -> str:
    emoji = "an emoji is fine" if style.emoji else "no emoji, they don't use them"
    return f"at most {style.max_words} words; {emoji}."


def _progress(entry: RoadmapEntry) -> str:
    if entry.has_note:
        return "studied"
    if entry.unlocked:
        return "unlocked, but you have no note for it yet"
    return "not studied yet"


def _standing(context: PersonaContext) -> str:
    if context.gap > 0:
        place = f"you're {_topics(context.gap)} ahead of them."
    elif context.gap < 0:
        place = f"they're {_topics(-context.gap)} ahead of you."
    else:
        place = "you're level."
    days = "day" if context.streak == 1 else "days"
    return f"{place} They've studied {context.streak} {days} in a row."


def _topics(count: int) -> str:
    return f"{count} topic" if count == 1 else f"{count} topics"
