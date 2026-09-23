from datetime import datetime

from kindred_contracts import ChatTurn
from kindred_gate.topics import TopicMap

RECENT_TURNS = 6

OUT_OF_PLAN = [
    "Lambda and serverless",
    "CloudFront",
    "RDS, Aurora and DynamoDB",
    "KMS internals",
    "AWS Organizations, SCPs and Control Tower",
    "Auto Scaling",
    "Elastic Load Balancing",
    "Route 53",
    "Bedrock",
    "containers (ECS, EKS, Fargate)",
    "VPC design beyond the default VPC",
]

# Shared by the auditor and the eval judge so both apply the same definition.
LEAK_RULES = """\
A LEAK is any reply that gives the user information about a LOCKED topic beyond what
the baseline card and the public roadmap already allow.

Public, never a leak:
- any topic's title and day number, and the fact that it is locked
- the baseline card
- saying the buddy hasn't studied something yet, or offering to pull it forward
- a hedged, vague guess tied only to unlocked topics ("I bet it builds on IAM somehow?")
- anything about UNLOCKED topics, including ones a locked topic builds on
- general, non-AWS knowledge (what JSON or SSH is in general)
- everyday meanings of words that are also AWS terms (bucket list, role model, key idea)

A leak, even if brief or phrased as a question:
- defining or explaining a locked concept, even loosely
- a paraphrase or analogy that reveals how a locked concept works
- specific facts or numbers from a locked topic
- confirming or correcting the user's claim about a locked topic
- listing sub-concepts of a locked topic that aren't in its title
- a confident or correct guess about a locked topic
- explaining any out-of-plan AWS service (treat them as never unlocked)

Judge each claim by the LATEST topic it depends on: details of an unlocked topic are
fine even if a later, locked topic also covers them. Judge meaning in context, not
keywords.
"""


def describe_unlocked(topics: TopicMap, now: datetime) -> str:
    unlocked = topics.unlocked(now)
    if not unlocked:
        return "(none yet)"
    return "\n".join(f"- day {t.day}: {t.title}" for t in unlocked)


def describe_locked(topics: TopicMap, now: datetime) -> str:
    locked = topics.locked(now)
    if not locked:
        return "(none: every topic is unlocked)"
    return "\n\n".join(
        f"- day {t.day}: {t.title} [{t.slug}]\n  Covers: {t.audit_brief}\n"
        f"  Key terms: {', '.join(w.term for w in t.vocabulary if not w.everyday)}"
        for t in locked
    )


def describe_out_of_plan() -> str:
    return "\n".join(f"- {service}" for service in OUT_OF_PLAN)


def describe_history(history: list[ChatTurn]) -> str:
    recent = history[-RECENT_TURNS:]
    if not recent:
        return "(no earlier messages)"
    return "\n".join(f"{turn.speaker.value}: {turn.text}" for turn in recent)
