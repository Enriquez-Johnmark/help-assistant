"""The commands:
help-assistant index                 read the help pages into the database
help-assistant search "question"     the passages a question finds
"""

import argparse
import os
from pathlib import Path

from help_assistant.assistant import Assistant, Conversation
from help_assistant.env import load_env
from help_assistant.model.client import HAIKU, SONNET, ClaudeAnswerer
from help_assistant.pages.reader import read_pages
from help_assistant.search.combined import Searcher
from help_assistant.search.embeddings import FastEmbedder
from help_assistant.store.db import open_db
from help_assistant.store.passages import all_passages, save_pages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="help-assistant", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--db", default="data/help.db", help="the database file (default: data/help.db)")
    parser.add_argument("--pages", default="help_pages", help="the help pages folder (default: help_pages)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index", help="read the help pages into the database")
    search = commands.add_parser("search", help="the passages a question finds")
    search.add_argument("question")
    search.add_argument("--mode", choices=["combined", "keyword"], default="combined")
    ask = commands.add_parser("ask", help="the assistant's answer to a question")
    ask.add_argument("question")
    ask.add_argument("--model", choices=["haiku", "sonnet"], default="haiku")
    args = parser.parse_args(argv)

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    db = open_db(args.db)
    if args.command == "index":
        saved = save_pages(db, read_pages(Path(args.pages)))
        print(f"{saved.added} passages added, {saved.changed} changed, {saved.removed} removed")
        return 0
    passages = all_passages(db)
    if not passages:
        parser.error("no passages yet: run `help-assistant index` first")
    if args.command == "ask":
        # The owner's API key, kept out of git in .env; never a Claude subscription.
        load_env()
        if not os.environ.get("ANTHROPIC_API_KEY"):
            parser.error("put your Anthropic API key in .env as ANTHROPIC_API_KEY")
        answerer = ClaudeAnswerer(SONNET if args.model == "sonnet" else HAIKU)
        reply = Assistant(Searcher(passages, FastEmbedder()), answerer).respond(Conversation(), args.question)
        print(reply.text)
        if reply.cited:
            print(f"\nFrom: {', '.join(reply.cited)}")
        if reply.reason:
            print(f"\n(handed to a person: {reply.reason})")
        for broken in reply.broken:
            print(f"(refused: {broken.detail})")
        return 0
    searcher = Searcher(passages, FastEmbedder() if args.mode == "combined" else None)
    for hit in searcher.search(args.question, 5, mode=args.mode):
        print(f"{hit.passage.id}\n  {hit.passage.text.splitlines()[1][:100]}")
    return 0
