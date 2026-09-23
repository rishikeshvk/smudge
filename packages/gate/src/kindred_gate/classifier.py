from kindred_contracts import ChatTurn, Classification
from kindred_gate.briefing import describe_history, describe_out_of_plan
from kindred_gate.topics import TopicMap
from kindred_llm import LLMClient

SYSTEM = """\
You sort messages sent to an AI study buddy that is learning AWS on a day-by-day plan.
Decide what the latest user message is about. Judge meaning in context, not keywords.

Categories:
- curriculum: asks about or discusses AWS content covered by the plan's topics. List in
  topic_slugs EVERY topic whose content a full answer would need, including later ones.
- out_of_plan: about AWS services or features that no topic covers (see the list).
- off_topic: not about AWS at all, including everyday uses of words that are also AWS
  terms ("bucket list", "role model", "I tore my ACL", "iam so tired").
- meta: about the buddy itself, being an AI, the study plan, roadmap or schedule.
- unsure: you genuinely can't tell.

Words marked * also have everyday meanings, so their presence alone proves nothing."""


class LLMClassifier:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self.model = llm.model

    async def classify(
        self, message: str, history: list[ChatTurn], topics: TopicMap, session_id: str
    ) -> Classification:
        return await self._llm.complete_structured(
            Classification,
            build_prompt(message, history, topics),
            session_id=session_id,
            system=SYSTEM,
        )


def build_prompt(message: str, history: list[ChatTurn], topics: TopicMap) -> str:
    plan = "\n".join(
        f"- {t.slug} (day {t.day}): {t.title}. Terms: "
        + ", ".join(f"{w.term}*" if w.everyday else w.term for w in t.vocabulary)
        for t in topics.topics
    )
    return (
        f"Plan topics:\n{plan}\n\n"
        f"Out of plan:\n{describe_out_of_plan()}\n\n"
        f"Earlier messages:\n{describe_history(history)}\n\n"
        f"Latest user message:\n{message}"
    )
