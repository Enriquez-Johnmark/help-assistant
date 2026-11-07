"""The SQLite database and its migrations; a released migration is never edited."""

import sqlite3
from types import TracebackType

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
    # Conversations and their messages, secrets already hidden (C3); questions
    # the assistant couldn't answer, for the owner (E4); and the audit log of
    # what people and the assistant did, append-only (E3).
    """
    create table conversations (
      id text primary key,
      status text not null check (status in ('assistant', 'waiting', 'with_agent', 'closed')),
      handoff_reason text,
      money_involved integer not null default 0 check (money_involved in (0, 1)),
      language text,
      i_dont_knows integer not null default 0,
      started_at text not null,
      waiting_since text
    );
    create table messages (
      id integer primary key autoincrement,
      conversation_id text not null references conversations (id) on delete cascade,
      at text not null,
      sender text not null check (sender in ('customer', 'assistant', 'agent')),
      text text not null
    );
    create table unanswered (
      id integer primary key autoincrement,
      conversation_id text not null references conversations (id) on delete cascade,
      at text not null,
      question text not null,
      topic text not null
    );
    create table audit_log (
      id integer primary key autoincrement,
      at text not null,
      actor text not null,
      action text not null,
      conversation_id text not null,
      details text not null default '{}'
    );
    create trigger audit_log_no_update before update on audit_log
      begin select raise(abort, 'the audit log is append-only'); end;
    create trigger audit_log_no_delete before delete on audit_log
      begin select raise(abort, 'the audit log is append-only'); end;
    """,
    # The passages each of the assistant's replies cites, so the chat can show
    # where an answer comes from (B1) after the page reloads.
    """
    alter table messages add column cited text not null default '[]';
    """,
)


def open_db(path: str) -> sqlite3.Connection:
    """Opens the database at `path` (":memory:" for tests) and brings its schema up to date."""
    # The web server answers on a pool of threads; it serialises every use of
    # the connection with one lock, so sharing it between threads is safe.
    db = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
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


class transaction:  # noqa: N801  (used like a function: `with transaction(db):`)
    """Everything inside is stored together or not at all. The connection is in
    autocommit mode, where `with db:` alone would write each statement at once."""

    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def __enter__(self) -> None:
        self._db.execute("begin")

    def __exit__(
        self, kind: type[BaseException] | None, error: BaseException | None, trace: TracebackType | None
    ) -> None:
        self._db.execute("rollback" if kind else "commit")
