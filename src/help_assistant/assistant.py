"""Answering one customer message: every step in architecture.md, in order."""

from dataclasses import dataclass, field, replace
from typing import Literal

from help_assistant.core.checks import Broken, check_citations, check_numbers, check_rules
from help_assistant.core.handoff import Reason, handoff_reason
from help_assistant.core.language import Language, check_language, language_of
from help_assistant.core.messages import HANDOFF, I_DONT_KNOW, SECRET_WARNING
from help_assistant.core.secrets import Redacted, redact
from help_assistant.model.answer import ModelAnswer, parse_answer
from help_assistant.model.client import Answerer
from help_assistant.model.request import build_request
from help_assistant.pages.reader import Passage
from help_assistant.search.combined import Mode, Searcher

Kind = Literal["answer", "i_dont_know", "handoff", "with_person"]
Turn = tuple[Literal["customer", "assistant"], Redacted | str]

# How many earlier turns the model sees with each question.
HISTORY_TURNS = 6


@dataclass
class Conversation:
    """One customer's chat. The customer's words are kept only redacted."""

    turns: list[Turn] = field(default_factory=lambda: list[Turn]())
    language: Language | None = None
    i_dont_knows: int = 0
    handed_off: Reason | None = None


@dataclass(frozen=True)
class Reply:
    kind: Kind
    text: str
    cited: list[str] = field(default_factory=lambda: list[str]())
    reason: Reason | None = None
    warned: bool = False
    broken: list[Broken] = field(default_factory=lambda: list[Broken]())
    # The page search found first, for the owner's view of unanswered topics.
    nearest_page: str | None = None


class Assistant:
    """Answers from the help pages, or says "I don't know", or hands off."""

    def __init__(
        self, searcher: Searcher, answerer: Answerer, threshold: float = 0.6, mode: Mode = "combined"
    ) -> None:
        self._searcher = searcher
        self._answerer = answerer
        self._threshold = threshold
        self._mode: Mode = mode

    def respond(self, conversation: Conversation, message: str) -> Reply:
        # 1. Hide secrets; only the hidden text is used from here on (C1).
        hidden = redact(message)
        conversation.language = language_of(hidden.text) or conversation.language
        language: Language = conversation.language or "english"
        history = list(conversation.turns)
        conversation.turns.append(("customer", hidden.text))
        if conversation.handed_off:
            # A person has the chat: the assistant is quiet, except to warn (C2).
            warning = SECRET_WARNING[language] if hidden.warn else ""
            return Reply("with_person", warning, reason=conversation.handed_off, warned=hidden.warn)

        reply = self._answer(conversation, history, hidden.text, language)
        if hidden.warn:  # C2
            reply = Reply(
                reply.kind,
                f"{SECRET_WARNING[language]}\n\n{reply.text}",
                reply.cited,
                reply.reason,
                True,
                reply.broken,
            )
        conversation.turns.append(("assistant", reply.text))
        return reply

    def _answer(
        self,
        conversation: Conversation,
        history: list[Turn],
        question: Redacted,
        language: Language,
    ) -> Reply:
        # 2. Hand-off rules in code, before the model is asked (D1, D2, D4).
        reason = handoff_reason(question)
        if reason:
            return self._hand_off(conversation, reason, language)
        # 3. Search; 4. ask the model with only the hidden text and the passages (B6).
        found = [hit.passage for hit in self._searcher.search(question, 5, mode=self._mode)]
        # The last few turns are enough context; sending all of a long chat would
        # grow every request, and its cost, without limit.
        request = build_request(self._answerer.model, history[-HISTORY_TURNS:], question, found, language)
        parsed = parse_answer(self._answerer.answer(request))
        nearest = found[0].page if found else None
        reply = self._checked(conversation, parsed, found, question, language)
        return replace(reply, nearest_page=nearest)

    def _checked(
        self,
        conversation: Conversation,
        parsed: ModelAnswer | None,
        found: list[Passage],
        question: Redacted,
        language: Language,
    ) -> Reply:
        # 5. Check the answer in code (B1 to B5): any failure is "I don't know" (B3).
        if parsed is None:
            return self._i_dont_know(
                conversation, language, [Broken("unreadable", "the model's answer didn't parse")]
            )
        if parsed.handoff != "none":
            return self._hand_off(conversation, parsed.handoff, language)
        if parsed.confidence < self._threshold:
            return self._i_dont_know(
                conversation, language, [Broken("unsure", f"confidence {parsed.confidence:.2f}")]
            )
        cited = [p for p in found if p.id in parsed.cited]
        broken = [
            *check_citations(parsed.cited, [p.id for p in found]),
            *check_numbers(parsed.reply, cited, question=question),
            *check_rules(parsed.reply),
            *check_language(parsed.reply, conversation.language),
        ]
        if broken:
            return self._i_dont_know(conversation, language, broken)
        return Reply("answer", parsed.reply, cited=list(parsed.cited))

    def _i_dont_know(self, conversation: Conversation, language: Language, broken: list[Broken]) -> Reply:
        conversation.i_dont_knows += 1
        # 6. Two "I don't know"s in one conversation hand off (D3).
        if conversation.i_dont_knows >= 2:
            return self._hand_off(conversation, "not_sure", language, broken)
        return Reply("i_dont_know", I_DONT_KNOW[language], broken=broken)

    def _hand_off(
        self,
        conversation: Conversation,
        reason: Reason,
        language: Language,
        broken: list[Broken] | None = None,
    ) -> Reply:
        conversation.handed_off = reason
        # The message never promises a time (D5).
        return Reply("handoff", HANDOFF[language], reason=reason, broken=broken or [])
