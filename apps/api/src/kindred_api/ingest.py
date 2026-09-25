import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

import httpx2
import trafilatura
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.catalog import load_curriculum
from kindred_api.clock import Clock, SystemClock
from kindred_api.config import get_settings
from kindred_api.plans import CurrentPlan, load_active_plans
from kindred_contracts import Curriculum
from kindred_db import SourceDocument, TopicNode, create_engine, session_factory

logger = logging.getLogger(__name__)

FETCH_CONCURRENCY = 4
USER_AGENT = f"kindred/{version('kindred-api')} (study notes)"


@dataclass(frozen=True)
class Page:
    title: str
    text: str


@dataclass(frozen=True)
class IngestReport:
    stored: int
    skipped: int
    failed: list[str]


def reading_list(curriculum: Curriculum) -> dict[str, list[str]]:
    """Each topic's pages: whatever its reference notes cite, once, without anchors."""
    return {
        node.slug: list(
            dict.fromkeys(
                str(url).split("#")[0] for note in node.notes for url in note.sources
            )
        )
        for node in curriculum.nodes
    }


def extract_page(html: str) -> Page | None:
    text = trafilatura.extract(html)
    if not text:
        return None
    metadata = trafilatura.extract_metadata(html)
    title = metadata.title if metadata is not None and metadata.title else None
    return Page(title=title or text.splitlines()[0], text=text)


async def fetch_page(client: httpx2.AsyncClient, url: str) -> Page | None:
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx2.HTTPError:
        return None
    return extract_page(response.text)


async def ingest_sources(
    session: AsyncSession,
    plan_id: int,
    curriculum: Curriculum,
    client: httpx2.AsyncClient,
    now: datetime,
) -> IngestReport:
    """Fetch every topic's pages that aren't stored yet; a page shared by topics
    is fetched once and stored for each."""
    rows = await session.execute(
        select(TopicNode.slug, TopicNode.id).where(TopicNode.plan_id == plan_id)
    )
    nodes = {slug: node_id for slug, node_id in rows.tuples()}
    stored = set(
        (
            await session.execute(
                select(SourceDocument.node_id, SourceDocument.url)
                .join(TopicNode, SourceDocument.node_id == TopicNode.id)
                .where(TopicNode.plan_id == plan_id)
            )
        ).tuples()
    )
    wanted = [
        (nodes[slug], url)
        for slug, urls in reading_list(curriculum).items()
        for url in urls
    ]
    missing = [pair for pair in wanted if pair not in stored]
    urls = list(dict.fromkeys(url for _, url in missing))

    limit = asyncio.Semaphore(FETCH_CONCURRENCY)

    async def fetch(url: str) -> Page | None:
        async with limit:
            return await fetch_page(client, url)

    pages = dict(zip(urls, await asyncio.gather(*map(fetch, urls)), strict=True))
    documents = [
        SourceDocument(
            node_id=node_id, url=url, title=page.title, text=page.text, fetched_at=now
        )
        for node_id, url in missing
        if (page := pages[url]) is not None
    ]
    session.add_all(documents)
    await session.flush()
    return IngestReport(
        stored=len(documents),
        skipped=len(wanted) - len(missing),
        failed=[url for url, page in pages.items() if page is None],
    )


class SourceFetcher:
    """Fetches a new plan's pages in the background, so its buddy can study on the
    first night without anyone running `make ingest`."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        client: httpx2.AsyncClient,
        curricula_dir: Path,
        clock: Clock,
    ) -> None:
        self._sessions = sessions
        self._client = client
        self._curricula_dir = curricula_dir
        self._clock = clock

    async def fetch_for(self, plan_id: int, curriculum_slug: str) -> None:
        curriculum = load_curriculum(self._curricula_dir / f"{curriculum_slug}.yaml")
        async with self._sessions() as session:
            report = await ingest_sources(
                session, plan_id, curriculum, self._client, self._clock.now()
            )
            await session.commit()
        # Failed pages are fetched again by `make ingest`.
        logger.info(
            "plan %s: stored %s pages, %s failed",
            plan_id,
            report.stored,
            len(report.failed),
        )


def source_client() -> httpx2.AsyncClient:
    return httpx2.AsyncClient(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30
    )


async def run() -> list[tuple[CurrentPlan, IngestReport]]:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    reports = []
    try:
        async with (
            session_factory(engine)() as session,
            source_client() as client,
        ):
            for plan in await load_active_plans(session):
                curriculum = load_curriculum(
                    settings.curricula_dir / f"{plan.curriculum_slug}.yaml"
                )
                report = await ingest_sources(
                    session, plan.id, curriculum, client, SystemClock().now()
                )
                await session.commit()
                reports.append((plan, report))
    finally:
        await engine.dispose()
    return reports


def main() -> None:
    reports = asyncio.run(run())
    if not reports:
        raise SystemExit("no plans yet; run `make seed` or onboard in the app first")
    for plan, report in reports:
        print(
            f"plan {plan.id} (user {plan.user_id}): stored {report.stored} pages,"
            f" {report.skipped} already stored"
        )
        for url in report.failed:
            print(f"failed: {url}")


if __name__ == "__main__":
    main()
