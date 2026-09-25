from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx2
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import FixedClock
from kindred_api.ingest import (
    SourceFetcher,
    extract_page,
    ingest_sources,
    reading_list,
)
from kindred_contracts import Curriculum
from kindred_db import Plan, SourceDocument, TopicNode

AddCourse = Callable[[int], Awaitable[Plan]]
NOW = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)

SHARED = "https://docs.test/iam"
S3 = "https://docs.test/s3"
GONE = "https://docs.test/gone"


def page(title: str) -> str:
    return (
        f"<html><head><title>{title}</title></head><body><nav>Home Docs</nav><main>"
        f"<h1>{title}</h1><p>{title} explains how access works in the cloud, with "
        "enough words on the page for an extractor to treat it as the main text.</p>"
        "<p>A second paragraph adds more detail so the article reads as real content "
        "rather than navigation or boilerplate around it.</p></main></body></html>"
    )


def node(day: int, sources: list[str]) -> dict[str, object]:
    return {
        "slug": f"topic-{day}",
        "day": day,
        "title": f"Topic {day}",
        "audit_brief": "Brief.",
        "vocabulary": [{"term": f"term{day}", "kind": "term"}],
        "notes": [{"body": "Notes.", "shaky": ["a gap"], "sources": sources}],
    }


CURRICULUM = Curriculum.model_validate(
    {
        "slug": "t",
        "title": "T",
        "study_time": "19:00",
        "baseline_card": ["Clouds rent computers."],
        "nodes": [
            node(1, [SHARED, f"{SHARED}#roles", GONE]),
            node(2, [SHARED, S3]),
        ],
    }
)


def site() -> tuple[httpx2.AsyncClient, list[str]]:
    fetched: list[str] = []
    pages = {SHARED: page("IAM guide"), S3: page("S3 guide")}

    def handler(request: httpx2.Request) -> httpx2.Response:
        url = str(request.url)
        fetched.append(url)
        if url not in pages:
            return httpx2.Response(404)
        return httpx2.Response(200, text=pages[url])

    return httpx2.AsyncClient(transport=httpx2.MockTransport(handler)), fetched


def test_reading_list_drops_anchors_and_repeats() -> None:
    assert reading_list(CURRICULUM) == {
        "topic-1": [SHARED, GONE],
        "topic-2": [SHARED, S3],
    }


def test_pages_keep_their_title_and_main_text() -> None:
    extracted = extract_page(page("IAM guide"))

    assert extracted is not None
    assert extracted.title == "IAM guide"
    assert "explains how access works" in extracted.text
    assert "Home Docs" not in extracted.text


def test_a_page_without_text_yields_nothing() -> None:
    assert extract_page("<html><body></body></html>") is None


@pytest.mark.anyio
async def test_each_topic_stores_its_pages_and_a_shared_page_is_fetched_once(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(2)
    client, fetched = site()

    report = await ingest_sources(session, plan.id, CURRICULUM, client, NOW)

    assert sorted(fetched) == sorted([SHARED, GONE, S3])
    assert (report.stored, report.skipped, report.failed) == (3, 0, [GONE])
    rows = await session.execute(
        select(TopicNode.slug, SourceDocument.url, SourceDocument.title)
        .join(TopicNode, SourceDocument.node_id == TopicNode.id)
        .order_by(TopicNode.day, SourceDocument.url)
    )
    assert rows.tuples().all() == [
        ("topic-1", SHARED, "IAM guide"),
        ("topic-2", SHARED, "IAM guide"),
        ("topic-2", S3, "S3 guide"),
    ]


@pytest.mark.anyio
async def test_stored_pages_are_not_fetched_again(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(2)
    first, _ = site()
    await ingest_sources(session, plan.id, CURRICULUM, first, NOW)
    again, fetched = site()

    report = await ingest_sources(session, plan.id, CURRICULUM, again, NOW)

    assert fetched == [GONE]
    assert (report.stored, report.skipped) == (0, 3)


@pytest.mark.anyio
async def test_a_new_plan_gets_its_pages_in_the_background(
    session: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    add_course: AddCourse,
    tmp_path: Path,
) -> None:
    plan = await add_course(2)
    await session.commit()
    (tmp_path / "t.yaml").write_text(CURRICULUM.model_dump_json())
    client, _ = site()

    await SourceFetcher(sessions, client, tmp_path, FixedClock(NOW)).fetch_for(
        plan.id, "t"
    )

    urls = await session.scalars(select(SourceDocument.url).order_by(SourceDocument.id))
    assert sorted(set(urls)) == [SHARED, S3]
