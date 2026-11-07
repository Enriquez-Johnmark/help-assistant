"""Storing help pages and their passages."""

import sqlite3
from dataclasses import dataclass

from help_assistant.pages.reader import HelpPage, Passage


@dataclass(frozen=True)
class Saved:
    added: int
    changed: int
    removed: int


def save_pages(db: sqlite3.Connection, pages: list[HelpPage]) -> Saved:
    """Stores `pages`. A passage already stored with the same text is left as it is,
    so reading the pages again adds nothing (A1); a changed one is updated, and
    one no longer on its page is removed."""
    added = changed = removed = 0
    db.execute("begin")
    try:
        for page in pages:
            db.execute(
                """insert into pages (slug, title, topic) values (?, ?, ?)
                   on conflict (slug) do update set title = excluded.title, topic = excluded.topic""",
                (page.slug, page.title, page.topic),
            )
            stored = {
                row["id"]: row["text"]
                for row in db.execute("select id, text from passages where page = ?", (page.slug,))
            }
            for passage in page.passages:
                if passage.id not in stored:
                    added += 1
                elif stored[passage.id] != passage.text:
                    changed += 1
                db.execute(
                    """insert into passages (id, page, heading, text, position) values (?, ?, ?, ?, ?)
                       on conflict (id) do update set heading = excluded.heading, text = excluded.text,
                         position = excluded.position""",
                    (passage.id, page.slug, passage.heading, passage.text, passage.position),
                )
            gone = set(stored) - {passage.id for passage in page.passages}
            for passage_id in gone:
                db.execute("delete from passages where id = ?", (passage_id,))
            removed += len(gone)
        db.execute("commit")
    except BaseException:
        db.execute("rollback")
        raise
    return Saved(added=added, changed=changed, removed=removed)


def all_passages(db: sqlite3.Connection) -> list[Passage]:
    """Every stored passage, in page order then position."""
    rows = db.execute("select id, page, heading, text, position from passages order by page, position")
    return [Passage(**dict(row)) for row in rows]
