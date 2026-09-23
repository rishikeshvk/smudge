from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ALEMBIC_INI = Path("apps/api/alembic.ini")


def sibling_url(database_url: str, suffix: str) -> str:
    """A database next to the dev one, such as kindred_eval, so runs never touch it."""
    dev = make_url(database_url)
    return dev.set(database=f"{dev.database}_{suffix}").render_as_string(
        hide_password=False
    )


def recreate_database(url: str) -> None:
    target = make_url(url)
    admin = create_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(
            text(f'DROP DATABASE IF EXISTS "{target.database}" WITH (FORCE)')
        )
        connection.execute(text(f'CREATE DATABASE "{target.database}"'))
    admin.dispose()

    config = Config(ALEMBIC_INI)
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
