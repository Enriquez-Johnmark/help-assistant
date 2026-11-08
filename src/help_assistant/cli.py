"""The commands:
help-assistant index                 read the help pages into the database
help-assistant search "question"     the passages a question finds
help-assistant ask "question"        the assistant's answer to one question
help-assistant serve                 the chat page and the staff views, on this computer
help-assistant eval                  score the test set
"""

import argparse
import os
from pathlib import Path

import uvicorn

from help_assistant.assistant import Assistant, Conversation
from help_assistant.clock import SystemClock
from help_assistant.env import load_env
from help_assistant.evaluation.grader import Grade, Grader, load_grading_cases
from help_assistant.evaluation.run import Scores, report, run, score
from help_assistant.evaluation.testset import load_questions
from help_assistant.model.client import (
    HAIKU,
    SONNET,
    Answerer,
    ClaudeAnswerer,
    ClaudeStructured,
    NotRecordedError,
    RecordedAnswerer,
    RecordingAnswerer,
    load_recordings,
)
from help_assistant.pages.reader import Passage, read_pages
from help_assistant.search.combined import Mode, Searcher
from help_assistant.search.embeddings import FastEmbedder
from help_assistant.service import ChatService
from help_assistant.store.db import open_db
from help_assistant.store.passages import all_passages, save_pages
from help_assistant.web.app import create_app


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
    search.add_argument("--mode", choices=["keyword", "combined"], default="keyword")
    ask = commands.add_parser("ask", help="the assistant's answer to a question")
    ask.add_argument("question")
    ask.add_argument("--model", choices=["haiku", "sonnet"], default="haiku")
    ask.add_argument("--mode", choices=["keyword", "combined"], default="keyword", help=SEARCH_HELP)
    serve = commands.add_parser("serve", help="the chat page and the staff views, on this computer only")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--model", choices=["haiku", "sonnet"], default="haiku")
    serve.add_argument("--mode", choices=["keyword", "combined"], default="keyword", help=SEARCH_HELP)
    evaluate = commands.add_parser("eval", help="score the test set (F2, F3)")
    evaluate.add_argument("--record", action="store_true", help="ask Claude live and record its answers")
    evaluate.add_argument("--models", default="haiku,sonnet", help="comma-separated: haiku, sonnet")
    evaluate.add_argument("--modes", default="keyword,combined", help="comma-separated: keyword, combined")
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
    if args.command == "eval":
        return run_eval(parser, passages, args.record, args.models.split(","), args.modes.split(","))
    if args.command in ("ask", "serve"):
        # The owner's API key, kept out of git in .env; never a Claude subscription.
        load_env()
        if not os.environ.get("ANTHROPIC_API_KEY"):
            parser.error(
                "put your Anthropic API key in .env as ANTHROPIC_API_KEY"
                " (in a cloud session: an environment variable, OWNER_ANTHROPIC_API_KEY)"
            )
    if args.command == "serve":
        assistant = Assistant(
            searcher(passages, args.mode), ClaudeAnswerer(MODELS[args.model]), mode=args.mode
        )
        app = create_app(ChatService(db, SystemClock(), assistant))
        print(f"Chat: http://127.0.0.1:{args.port}/   Agents: /agent   Help content: /owner")
        # 127.0.0.1 only: the demo is never reachable from another computer (G1).
        uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
        return 0
    if args.command == "ask":
        answerer = ClaudeAnswerer(MODELS[args.model])
        reply = Assistant(searcher(passages, args.mode), answerer, mode=args.mode).respond(
            Conversation(), args.question
        )
        print(reply.text)
        if reply.cited:
            print(f"\nFrom: {', '.join(reply.cited)}")
        if reply.reason:
            print(f"\n(handed to a person: {reply.reason})")
        for broken in reply.broken:
            print(f"(refused: {broken.detail})")
        return 0
    for hit in searcher(passages, args.mode).search(args.question, 5, mode=args.mode):
        print(f"{hit.passage.id}\n  {hit.passage.text.splitlines()[1][:100]}")
    return 0


RECORDED = Path("evalset/recorded")
# Keyword search alone met the targets on the test set and combined search
# didn't (docs/decisions.md, 2026-11-08), so it is the default.
SEARCH_HELP = "keyword (default, measured best) or combined with the local embedding model"


def searcher(passages: list[Passage], mode: Mode) -> Searcher:
    """The embedding model is loaded only for combined search."""
    return Searcher(passages, FastEmbedder() if mode == "combined" else None)


MODELS = {"haiku": HAIKU, "sonnet": SONNET}


def run_eval(
    parser: argparse.ArgumentParser,
    passages: list[Passage],
    record: bool,
    models: list[str],
    modes: list[str],
) -> int:
    """Scores the test set for each model and search mode and prints the report
    (F3); with `record`, asks Claude live and saves every answer and grade, so
    CI can check the targets without a key (F2)."""
    if any(m not in MODELS for m in models) or any(m not in ("keyword", "combined") for m in modes):
        parser.error("--models takes haiku and sonnet; --modes takes keyword and combined")
    answers_file, grades_file = RECORDED / "answers.json", RECORDED / "grades.json"
    if record:
        load_env()
        if not os.environ.get("ANTHROPIC_API_KEY"):
            parser.error(
                "put your Anthropic API key in .env as ANTHROPIC_API_KEY"
                " (in a cloud session: an environment variable, OWNER_ANTHROPIC_API_KEY)"
            )
        grader = Grader(RecordingAnswerer(ClaudeStructured(SONNET, Grade), grades_file))
    elif not answers_file.exists():
        parser.error("no recorded answers yet: run `help-assistant eval --record` with your API key in .env")
    else:
        grader = Grader(RecordedAnswerer(load_recordings(grades_file), SONNET))
    questions = load_questions(Path("evalset/questions.jsonl"))
    embedder = FastEmbedder() if "combined" in modes else None
    rows: list[tuple[str, Mode, Scores]] = []
    for name in models:
        answerer: Answerer = (
            RecordingAnswerer(ClaudeAnswerer(MODELS[name]), answers_file)
            if record
            else RecordedAnswerer(load_recordings(answers_file), MODELS[name])
        )
        for mode in modes:
            searcher = Searcher(passages, embedder if mode == "combined" else None)
            try:
                rows.append((name, mode, score(run(questions, searcher, answerer, grader, mode))))  # type: ignore[arg-type]
            except NotRecordedError:
                parser.error(f"{name} with {mode} search isn't recorded: run `help-assistant eval --record`")
    if record:
        for case in load_grading_cases(Path("evalset/grading_cases.jsonl")):
            grader.grade(case.question, case.answer, case.reply)
    print(report(rows))
    return 0
