from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.study import (
    StudyComponents,
    StudyStatus,
    due_topics,
    study_topic,
)
from kindred_contracts import AuditVerdict, NoteDraft, StudyBrief, Verdict
from kindred_db import (
    EMBEDDING_DIMENSIONS,
    Plan,
    SourceDocument,
    StudySession,
    TopicNode,
    TopicVocabulary,
)
from kindred_gate import TopicMap, list_notes
from kindred_llm import LLMUnavailableError, StructuredOutputError

AddCourse = Callable[[int], Awaitable[Plan]]
# Day 1 unlocks at 13:30Z (19:00 in Kolkata); day 2 a day later.
DAY_1 = datetime(2026, 10, 1, 13, 30, tzinfo=UTC)
NOW = DAY_1 + timedelta(minutes=5)
PASS = AuditVerdict(verdict=Verdict.PASS, rationale="fine")


def note(body: str, shaky: str = "why regions?", share: str = "went ok") -> NoteDraft:
    return NoteDraft(
        body=body, shaky=[shaky], sources=["https://docs.test/1"], share=share
    )


class FakeCurator:
    model = "fake-curator"

    def __init__(self, *drafts: NoteDraft | Exception) -> None:
        self._drafts = list(drafts)
        self.briefs: list[StudyBrief] = []

    async def study(self, brief: StudyBrief, session_id: str) -> NoteDraft:
        self.briefs.append(brief)
        draft = self._drafts.pop(0)
        if isinstance(draft, Exception):
            raise draft
        return draft


class FakeAuditor:
    model = "fake-auditor"

    def __init__(self, *verdicts: AuditVerdict) -> None:
        self._verdicts = list(verdicts)
        self.notes: list[str] = []

    async def audit_note(
        self, note: str, topics: TopicMap, now: datetime, session_id: str
    ) -> AuditVerdict:
        self.notes.append(note)
        return self._verdicts.pop(0)


class FakeEmbedder:
    model = "fake-embed"

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.5] * EMBEDDING_DIMENSIONS for _ in texts]


async def course(session: AsyncSession, add_course: AddCourse) -> list[TopicNode]:
    """Two topics; day 1 has a source page and day 2 owns the term "Glacier"."""
    await add_course(2)
    nodes = list(await session.scalars(select(TopicNode).order_by(TopicNode.day)))
    session.add_all(
        [
            SourceDocument(
                node_id=nodes[0].id,
                url="https://docs.test/1",
                title="Regions",
                text="AWS runs in regions.",
                fetched_at=DAY_1,
            ),
            SourceDocument(
                node_id=nodes[1].id,
                url="https://docs.test/2",
                title="Storage",
                text="Glacier is cold storage.",
                fetched_at=DAY_1,
            ),
            TopicVocabulary(
                node_id=nodes[1].id, term="Glacier", kind="term", everyday=False
            ),
        ]
    )
    await session.flush()
    return nodes


def components(curator: FakeCurator, auditor: FakeAuditor) -> StudyComponents:
    return StudyComponents(curator=curator, auditor=auditor, embedder=FakeEmbedder())


async def session_row(session: AsyncSession, node: TopicNode) -> StudySession | None:
    row: StudySession | None = await session.scalar(
        select(StudySession).where(StudySession.node_id == node.id)
    )
    return row


@pytest.mark.anyio
async def test_only_unlocked_unstudied_topics_are_due(
    session: AsyncSession, add_course: AddCourse
) -> None:
    day_1, _ = await course(session, add_course)

    assert [n.day for n in await due_topics(session, day_1.plan_id, NOW)] == [1]

    await study_topic(
        session, day_1, NOW, components(FakeCurator(note("regions")), FakeAuditor(PASS))
    )

    assert await due_topics(session, day_1.plan_id, NOW) == []


@pytest.mark.anyio
async def test_an_audited_note_is_written_to_the_ledger(
    session: AsyncSession, add_course: AddCourse
) -> None:
    day_1, _ = await course(session, add_course)
    curator = FakeCurator(note("AWS runs in regions."))

    outcome = await study_topic(
        session, day_1, NOW, components(curator, FakeAuditor(PASS))
    )

    assert outcome.status is StudyStatus.WRITTEN
    [written] = await list_notes(session, plan_id=day_1.plan_id, now=NOW)
    assert (written.body, written.written_at) == ("AWS runs in regions.", NOW)
    row = await session_row(session, day_1)
    assert row is not None and row.note_id == written.note_id
    [brief] = curator.briefs
    assert (brief.topic.day, brief.focus) == (1, "Brief for topic 1.")
    assert [s.title for s in brief.sources] == ["Regions"]


@pytest.mark.anyio
async def test_the_study_share_is_audited_and_kept_with_the_session(
    session: AsyncSession, add_course: AddCourse
) -> None:
    day_1, _ = await course(session, add_course)
    auditor = FakeAuditor(PASS)

    await study_topic(
        session,
        day_1,
        NOW,
        components(FakeCurator(note("b", share="regions done!")), auditor),
    )

    assert "regions done!" in auditor.notes[0]
    row = await session_row(session, day_1)
    assert row is not None and row.share == "regions done!"


@pytest.mark.anyio
async def test_locked_jargon_in_the_share_is_a_leak(
    session: AsyncSession, add_course: AddCourse
) -> None:
    day_1, _ = await course(session, add_course)
    auditor = FakeAuditor(PASS)
    curator = FakeCurator(note("b", share="next up is Glacier"), note("b"))

    outcome = await study_topic(session, day_1, NOW, components(curator, auditor))

    assert outcome.status is StudyStatus.WRITTEN
    assert len(curator.briefs) == 2 and len(auditor.notes) == 1


@pytest.mark.anyio
async def test_later_topics_see_earlier_gaps(
    session: AsyncSession, add_course: AddCourse
) -> None:
    day_1, day_2 = await course(session, add_course)
    tomorrow = NOW + timedelta(days=1)
    await study_topic(
        session,
        day_1,
        NOW,
        components(FakeCurator(note("regions", "why AZs?")), FakeAuditor(PASS)),
    )
    curator = FakeCurator(note("Glacier is cold storage."))

    await study_topic(session, day_2, tomorrow, components(curator, FakeAuditor(PASS)))

    [earlier] = curator.briefs[0].earlier
    assert (earlier.topic.day, earlier.shaky) == (1, ["why AZs?"])


@pytest.mark.anyio
async def test_locked_jargon_is_redrafted_without_an_llm_audit(
    session: AsyncSession, add_course: AddCourse
) -> None:
    day_1, _ = await course(session, add_course)
    curator = FakeCurator(note("Regions, and Glacier later."), note("Regions."))
    auditor = FakeAuditor(PASS)

    outcome = await study_topic(session, day_1, NOW, components(curator, auditor))

    assert outcome.status is StudyStatus.WRITTEN
    assert auditor.notes == ["Regions.\nwhy regions?\nwent ok"]
    feedback = curator.briefs[1].feedback
    assert feedback is not None
    assert "Topic 2" in feedback
    assert "Don't use these terms: Glacier" in feedback


@pytest.mark.anyio
async def test_a_note_that_keeps_leaking_is_never_written(
    session: AsyncSession, add_course: AddCourse
) -> None:
    day_1, _ = await course(session, add_course)
    leak = AuditVerdict(
        verdict=Verdict.LEAK,
        leaked_topic_slugs=["topic-2"],
        evidence=["Cold storage is cheap."],
        rationale="previews day 2",
    )
    curator = FakeCurator(*[note("Regions. Cold storage is cheap.")] * 3)

    outcome = await study_topic(
        session, day_1, NOW, components(curator, FakeAuditor(leak, leak, leak))
    )

    assert outcome.status is StudyStatus.FAILED
    assert await list_notes(session, plan_id=day_1.plan_id, now=NOW) == []
    row = await session_row(session, day_1)
    assert row is not None and row.status == "failed" and len(row.attempts) == 3
    feedback = curator.briefs[1].feedback
    assert feedback is not None and "- Cold storage is cheap." in feedback


@pytest.mark.anyio
async def test_invalid_curator_output_fails_closed(
    session: AsyncSession, add_course: AddCourse
) -> None:
    day_1, _ = await course(session, add_course)
    curator = FakeCurator(StructuredOutputError("bad json"))

    outcome = await study_topic(session, day_1, NOW, components(curator, FakeAuditor()))

    assert outcome.status is StudyStatus.FAILED
    assert await list_notes(session, plan_id=day_1.plan_id, now=NOW) == []


@pytest.mark.anyio
async def test_a_topic_without_sources_waits(
    session: AsyncSession, add_course: AddCourse
) -> None:
    await add_course(1)
    node = await session.scalar(select(TopicNode))
    assert node is not None

    outcome = await study_topic(
        session, node, NOW, components(FakeCurator(), FakeAuditor())
    )

    assert outcome.status is StudyStatus.NO_SOURCES
    assert await session_row(session, node) is None


@pytest.mark.anyio
async def test_an_unavailable_endpoint_is_left_to_the_caller(
    session: AsyncSession, add_course: AddCourse
) -> None:
    day_1, _ = await course(session, add_course)
    curator = FakeCurator(LLMUnavailableError("usage limit"))

    with pytest.raises(LLMUnavailableError):
        await study_topic(session, day_1, NOW, components(curator, FakeAuditor()))
