"""The SQLite database and its migrations; a released migration is never edited."""

import sqlite3

MIGRATIONS: tuple[str, ...] = (
    """
    create table pages (
      slug text primary key,
      title text not null,
      topic text not null
    );
    create table passages (
      id text primary key,
      page text not null references pages (slug) on delete cascade,
      heading text not null,
      text text not null,
      position integer not null
    );
    """,
)


def open_db(path: str) -> sqlite3.Connection:
    """Opens the database at `path` (":memory:" for tests) and brings its schema up to date."""
    db = sqlite3.connect(path, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("pragma foreign_keys = on")
    db.execute("create table if not exists schema_migrations (version integer primary key)")
    done = {row[0] for row in db.execute("select version from schema_migrations")}
    for version, sql in enumerate(MIGRATIONS, start=1):
        if version in done:
            continue
        # One script, in one transaction: a migration is applied whole or not at all.
        db.executescript(
            f"begin;\n{sql}\ninsert into schema_migrations (version) values ({version});\ncommit;"
        )
    return db
