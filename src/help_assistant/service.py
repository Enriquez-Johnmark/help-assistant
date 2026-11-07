"""The chat as the web pages use it: conversations stored in the database, the
assistant answering, and support agents taking over (E1 to E4)."""

import json
import sqlite3
import uuid
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from help_assistant.assistant import Assistant, Conversation, Reply, Turn
from help_assistant.clock import Clock
from help_assistant.core.handoff import mentions_money
from help_assistant.core.language import Language
from help_assistant.core.secrets import Redacted, redact
from help_assistant.store.db import transaction

Status = Literal["assistant", "waiting", "with_agent", "closed"]
Sender = Literal["customer", "assistant", "agent"]


@dataclass(frozen=True)
class Message:
    sender: Sender
    text: str
    at: str
    cited: list[str]


@dataclass(frozen=True)
class Waiting:
    id: str
    status: Status
    reason: str | None
    money_involved: bool
    waiting_since: str
    messages: list[Message]


@dataclass(frozen=True)
class AuditEntry:
    at: str
    actor: str
    action: str
    conversation_id: str
    details: dict[str, object]


@dataclass(frozen=True)
class OwnerView:
    unanswered_by_topic: dict[str, int]
    handoffs_by_reason: dict[str, int]


def _person(name: str) -> str:
    """A support agent acts by name; the assistant's name is refused."""
    name = name.strip()
    if not name or name.lower() == "assistant":
        raise ValueError("say who you are: an agent acts by name")
    return name


class ChatService:
    def __init__(self, db: sqlite3.Connection, clock: Clock, assistant: Assistant) -> None:
        self.db = db
        self._clock = clock
        self._assistant = assistant

    def _now(self) -> str:
        return self._clock.now().isoformat()

    def start(self) -> str:
        """A new conversation, answered by the assistant."""
        conversation_id = uuid.uuid4().hex
        self.db.execute(
            "insert into conversations (id, status, started_at) values (?, 'assistant', ?)",
            (conversation_id, self._now()),
        )
        return conversation_id

    def status(self, conversation_id: str) -> Status:
        row = self.db.execute("select status from conversations where id = ?", (conversation_id,)).fetchone()
        if row is None:
            raise ValueError("no such conversation")
        return row["status"]

    def messages(self, conversation_id: str) -> list[Message]:
        rows = self.db.execute(
            "select sender, text, at, cited from messages where conversation_id = ? order by id",
            (conversation_id,),
        )
        return [Message(row["sender"], row["text"], row["at"], json.loads(row["cited"])) for row in rows]

    def _add(
        self, conversation_id: str, sender: Sender, text: Redacted, cited: list[str] | None = None
    ) -> None:
        # Only redacted text is stored (C3): checked at run time too.
        if not isinstance(text, Redacted):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("only redacted text is stored")
        self.db.execute(
            "insert into messages (conversation_id, at, sender, text, cited) values (?, ?, ?, ?, ?)",
            (conversation_id, self._now(), sender, text, json.dumps(cited or [])),
        )

    def _audit(self, actor: str, action: str, conversation_id: str, **details: object) -> None:
        self.db.execute(
            "insert into audit_log (at, actor, action, conversation_id, details) values (?, ?, ?, ?, ?)",
            (self._now(), actor, action, conversation_id, json.dumps(details)),
        )

    def _conversation(self, conversation_id: str) -> tuple[Conversation, Status]:
        row = self.db.execute("select * from conversations where id = ?", (conversation_id,)).fetchone()
        if row is None:
            raise ValueError("no such conversation")
        turns: list[Turn] = [
            ("customer", redact(m.text).text) if m.sender == "customer" else ("assistant", m.text)
            for m in self.messages(conversation_id)
        ]
        language: Language | None = row["language"]
        status: Status = row["status"]
        handed_off = row["handoff_reason"] if status in ("waiting", "with_agent") else None
        return Conversation(turns, language, row["i_dont_knows"], handed_off), status

    def customer_message(self, conversation_id: str, text: str) -> Reply:
        """The customer writes; the assistant answers, or keeps quiet while a person has the chat."""
        with transaction(self.db):
            conversation, status = self._conversation(conversation_id)
            if status == "closed":
                raise ValueError("this conversation is closed")
            before = len(conversation.turns)
            reply = self._assistant.respond(conversation, text)
            for sender, turn in conversation.turns[before:]:
                if sender == "customer":
                    self._add(conversation_id, "customer", redact(str(turn)).text)
                elif turn:
                    self._add(conversation_id, "assistant", redact(str(turn)).text, reply.cited)
            if reply.kind == "with_person" and reply.text:
                self._add(conversation_id, "assistant", redact(reply.text).text)
            self.db.execute(
                "update conversations set language = ?, i_dont_knows = ? where id = ?",
                (conversation.language, conversation.i_dont_knows, conversation_id),
            )
            if reply.kind == "i_dont_know" or (reply.kind == "handoff" and reply.reason == "not_sure"):
                self._unanswered(conversation_id, redact(text).text, reply.nearest_page)
            if reply.kind == "handoff":
                money = reply.reason == "lost_money" or any(
                    mentions_money(str(t)) for s, t in conversation.turns if s == "customer"
                )
                self.db.execute(
                    "update conversations set status = 'waiting', handoff_reason = ?, money_involved = ?,"
                    " waiting_since = ? where id = ?",
                    (reply.reason, int(money), self._now(), conversation_id),
                )
                self._audit("assistant", "handoff", conversation_id, reason=reply.reason)
        return reply

    def _unanswered(self, conversation_id: str, question: Redacted, nearest_page: str | None) -> None:
        topic = "unknown"
        if nearest_page:
            row = self.db.execute("select topic from pages where slug = ?", (nearest_page,)).fetchone()
            topic = row["topic"] if row else "unknown"
        self.db.execute(
            "insert into unanswered (conversation_id, at, question, topic) values (?, ?, ?, ?)",
            (conversation_id, self._now(), question, topic),
        )

    def waiting(self) -> list[Waiting]:
        """Conversations a person has, money issues first, then the longest waiting (E1)."""
        rows = self.db.execute(
            "select id, status, handoff_reason, money_involved, waiting_since from conversations"
            " where status in ('waiting', 'with_agent') order by money_involved desc, waiting_since, id"
        ).fetchall()
        return [
            Waiting(
                row["id"],
                row["status"],
                row["handoff_reason"],
                bool(row["money_involved"]),
                row["waiting_since"],
                self.messages(row["id"]),
            )
            for row in rows
        ]

    def _person_has(self, conversation_id: str) -> None:
        if self.status(conversation_id) not in ("waiting", "with_agent"):
            raise ValueError("this conversation isn't with a person")

    def agent_reply(self, conversation_id: str, agent: str, text: str) -> None:
        """An agent's reply, shown in the customer's chat (E2), redacted like everything stored."""
        name = _person(agent)
        with transaction(self.db):
            self._person_has(conversation_id)
            self._add(conversation_id, "agent", redact(text).text)
            self.db.execute("update conversations set status = 'with_agent' where id = ?", (conversation_id,))
            self._audit(name, "reply", conversation_id)

    def hand_back(self, conversation_id: str, agent: str) -> None:
        """The agent gives the conversation back to the assistant (E2)."""
        name = _person(agent)
        with transaction(self.db):
            self._person_has(conversation_id)
            self.db.execute(
                "update conversations set status = 'assistant', handoff_reason = null, i_dont_knows = 0,"
                " waiting_since = null where id = ?",
                (conversation_id,),
            )
            self._audit(name, "hand_back", conversation_id)

    def close(self, conversation_id: str, agent: str) -> None:
        name = _person(agent)
        with transaction(self.db):
            if self.status(conversation_id) == "closed":
                raise ValueError("this conversation is already closed")
            self.db.execute("update conversations set status = 'closed' where id = ?", (conversation_id,))
            self._audit(name, "close", conversation_id)

    def audit_log(self) -> list[AuditEntry]:
        rows = self.db.execute(
            "select at, actor, action, conversation_id, details from audit_log order by id"
        )
        return [
            AuditEntry(
                row["at"], row["actor"], row["action"], row["conversation_id"], json.loads(row["details"])
            )
            for row in rows
        ]

    def owner_view(self) -> OwnerView:
        """Unanswered questions by topic, and hand-offs by reason, from what is stored (E4)."""
        topics = Counter(row["topic"] for row in self.db.execute("select topic from unanswered"))
        reasons = Counter(
            json.loads(row["details"]).get("reason", "unknown")
            for row in self.db.execute("select details from audit_log where action = 'handoff'")
        )
        return OwnerView(dict(topics), dict(reasons))
