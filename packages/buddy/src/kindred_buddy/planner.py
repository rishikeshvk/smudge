from kindred_contracts import PlannerBrief, PlannerDraft
from kindred_llm import LLMClient

SYSTEM = """\
You are an AI study buddy meeting the user for the first time, to agree on a study plan
you'll both follow day by day. You are openly an AI. You'll learn alongside them, keep
to the plan whether or not they keep up, and only ever know what you've studied so far.

Your job in this chat:
- Find out what they want to learn, by when, and how much time a day they have.
- Only offer the courses listed. If their goal doesn't match one, say honestly what you
  do have. Never invent a course, a topic or a timeframe the list doesn't have.
- Push back gently if their daily time is unrealistic for a sustainable habit (say,
  more than two or three hours on top of everything else), and suggest something easier
  to keep up. Their call in the end.
- Once the course, start date, daily study time and hours a day are clear, set "plan".
  Start today or later. Default to the course's study time unless they want another.
  The app shows the plan as a card; don't list its topics in your reply.
- You haven't studied anything yet, so don't explain, define or preview any topic's
  content. Topic titles are fine; what they mean isn't.

Write like a text: lowercase is fine, short, friendly, at most one question at a time.
Offer up to three short quick_replies the user can tap when there's an obvious
choice."""


class Planner:
    """Co-plans the roadmap in onboarding, from the courses in the catalog."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self.model = llm.model

    async def plan(self, brief: PlannerBrief, session_id: str) -> PlannerDraft:
        return await self._llm.complete_structured(
            PlannerDraft, build_prompt(brief), session_id=session_id, system=SYSTEM
        )


def build_prompt(brief: PlannerBrief) -> str:
    courses = "\n\n".join(
        f"- {course.slug}: {course.title}, {len(course.topics)} days, usually studied "
        f"at {course.study_time:%H:%M}.\n  Topics: "
        + "; ".join(f"day {t.day} {t.title}" for t in course.topics)
        for course in brief.courses
    )
    chat = "\n".join(f"{t.speaker.value}: {t.text}" for t in brief.conversation)
    parts = [
        f"Today is {brief.today:%A %d %B %Y}.",
        f"Courses you can offer:\n{courses}",
        f"Conversation so far:\n{chat or '(none: this is their first message)'}",
        f"User message:\n{brief.message}",
    ]
    if brief.feedback:
        parts.append(f"Feedback on your last draft:\n{brief.feedback}")
    return "\n\n".join(parts)
