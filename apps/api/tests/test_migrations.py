import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, create_engine, inspect, text
from sqlalchemy.exc import DBAPIError

TABLES = {
    "users",
    "plans",
    "topic_nodes",
    "topic_prerequisites",
    "topic_vocabulary",
    "ledger_notes",
    "note_embeddings",
    "turns",
    "dev_clock",
    "buddies",
    "messages",
    "study_checkins",
    "source_documents",
}


def table_names(url: str) -> set[str]:
    engine = create_engine(url)
    names = set(inspect(engine).get_table_names())
    engine.dispose()
    return names


def test_migrations_downgrade_and_upgrade_cleanly(
    database_url: str, migrations: Config
) -> None:
    command.downgrade(migrations, "base")
    assert table_names(database_url).isdisjoint(TABLES)

    command.upgrade(migrations, "head")
    assert table_names(database_url) >= TABLES


def insert_note(connection: Connection) -> None:
    connection.execute(
        text(
            """
            WITH u AS (INSERT INTO users (timezone) VALUES ('UTC') RETURNING id),
            p AS (
                INSERT INTO plans (user_id, curriculum_slug, title, start_date,
                                   study_time, baseline_card)
                SELECT id, 'test', 'Test', '2026-10-01', '19:00', '[]' FROM u
                RETURNING id
            ),
            n AS (
                INSERT INTO topic_nodes (plan_id, slug, day, title, audit_brief,
                                         unlock_at)
                SELECT id, 'node', 1, 'Node', 'Brief', '2026-10-01T13:30Z' FROM p
                RETURNING id
            )
            INSERT INTO ledger_notes (node_id, body, shaky, sources, written_at)
            SELECT id, 'Note', '["shaky"]', '{https://example.com}',
                   '2026-10-01T13:30Z'
            FROM n
            """
        )
    )


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE ledger_notes SET body = 'rewritten'",
        "DELETE FROM ledger_notes",
        "TRUNCATE ledger_notes CASCADE",
    ],
)
def test_ledger_notes_are_append_only(connection: Connection, statement: str) -> None:
    insert_note(connection)

    with pytest.raises(DBAPIError, match="append-only"), connection.begin_nested():
        connection.execute(text(statement))

    assert connection.scalar(text("SELECT body FROM ledger_notes")) == "Note"
