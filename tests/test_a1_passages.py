from pathlib import Path

import pytest

from help_assistant.pages.reader import NotMadeUpError, read_page, read_pages
from help_assistant.store.db import open_db
from help_assistant.store.passages import all_passages, save_pages

PAGE = """---
title: Fees for sending money
topic: sending-money
made_up: true
---

# Fees for sending money

> Made up for a demo.

## Fees for branch pickup
Up to ₱1,000 costs ₱15.

## The most you can send
You can send up to ₱50,000 in one transfer.
"""


def test_a1_a_page_is_read_into_passages_that_know_their_page_and_heading(tmp_path: Path) -> None:
    file = tmp_path / "send-money-fees.md"
    file.write_text(PAGE)

    page = read_page(file)

    assert page.slug == "send-money-fees"
    assert page.title == "Fees for sending money"
    assert page.topic == "sending-money"
    assert [(p.id, p.heading) for p in page.passages] == [
        ("send-money-fees#fees-for-branch-pickup", "Fees for branch pickup"),
        ("send-money-fees#the-most-you-can-send", "The most you can send"),
    ]
    assert page.passages[0].text == "Fees for branch pickup\nUp to ₱1,000 costs ₱15."


def test_a1_reading_the_pages_again_adds_nothing_new(tmp_path: Path) -> None:
    db = open_db(":memory:")
    pages = read_pages(Path("help_pages"))

    first = save_pages(db, pages)
    again = save_pages(db, read_pages(Path("help_pages")))

    assert len(pages) == 25
    assert first.added == len(all_passages(db)) > 50
    assert (again.added, again.changed, again.removed) == (0, 0, 0)


def test_a1_a_changed_or_removed_section_is_updated_not_duplicated(tmp_path: Path) -> None:
    db = open_db(":memory:")
    file = tmp_path / "send-money-fees.md"
    file.write_text(PAGE)
    save_pages(db, [read_page(file)])

    file.write_text(
        PAGE.replace("₱15", "₱20").replace(
            "## The most you can send\nYou can send up to ₱50,000 in one transfer.\n", ""
        )
    )
    saved = save_pages(db, [read_page(file)])

    assert (saved.added, saved.changed, saved.removed) == (0, 1, 1)
    assert [p.text for p in all_passages(db)] == ["Fees for branch pickup\nUp to ₱1,000 costs ₱20."]


def test_a1_a_page_not_marked_made_up_is_refused(tmp_path: Path) -> None:
    file = tmp_path / "real.md"
    file.write_text(PAGE.replace("made_up: true\n", ""))
    with pytest.raises(NotMadeUpError, match=r"real\.md"):
        read_page(file)


def test_opening_the_database_again_keeps_what_is_stored(tmp_path: Path) -> None:
    path = str(tmp_path / "help.db")
    save_pages(open_db(path), read_pages(Path("help_pages")))
    assert len(all_passages(open_db(path))) > 50
