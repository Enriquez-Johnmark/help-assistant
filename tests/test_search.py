from help_assistant.pages.reader import Passage
from help_assistant.search.combined import Searcher, fuse
from help_assistant.search.keyword import KeywordIndex


def passage(pid: str, text: str) -> Passage:
    return Passage(id=pid, page=pid.split("#")[0], heading=pid, text=text, position=0)


PASSAGES = [
    passage("fees#branch", "Fees for branch pickup. Up to 1,000 costs 15 pesos."),
    passage("otp#late", "If the OTP doesn't arrive, wait 2 minutes and tap Resend."),
    passage("hours#open", "Most branches are open Monday to Saturday."),
]


def test_keyword_search_ranks_the_passage_with_the_words_first() -> None:
    hits = KeywordIndex(PASSAGES).search("my otp did not arrive", 3)
    assert hits[0].passage.id == "otp#late"
    assert all(hit.score > 0 for hit in hits)


def test_keyword_search_finds_nothing_for_words_no_passage_has() -> None:
    assert KeywordIndex(PASSAGES).search("zzz", 3) == []


def test_reciprocal_rank_fusion_rewards_a_passage_both_searches_rank_highly() -> None:
    fused = fuse([["a", "b", "c"], ["b", "c", "a"]])
    assert fused[0][0] == "b"
    assert {item for item, _ in fused} == {"a", "b", "c"}


def test_keyword_only_mode_needs_no_embedding_model() -> None:
    searcher = Searcher(PASSAGES, embedder=None)
    assert searcher.search("branch fees", 2, mode="keyword")[0].passage.id == "fees#branch"


def test_keyword_search_matches_simple_english_word_forms() -> None:
    page = [passage("billers#kinds", "You can pay schools and cancelling is free.")]
    index = KeywordIndex(page)
    assert index.search("school", 1) != []
    assert index.search("cancel", 1) != []
    assert KeywordIndex([passage("otp#late", "If the OTP doesn't arrive.")]).search("arriving", 1) != []
    assert KeywordIndex([passage("cash-out#fees", "Fees for cashing out.")]).search("fee", 1) != []


def test_the_glossary_adds_english_for_tagalog_money_words() -> None:
    from help_assistant.search.glossary import expand

    assert "pawn" in expand("Paano mag-sangla ng alahas?")
    assert "redeem" in expand("Pwede bang tumubos?")
    assert expand("When are branches open?") == "When are branches open?"
    assert "send" in expand("Paano magpadala?")
    # A root inside an English word doesn't count: "operator" holds "pera".
    assert expand("Who is the operator here?") == "Who is the operator here?"


class FixedEmbedder:
    """A stand-in model with chosen vectors: the OTP passage looks most like any
    question, the fees passage least."""

    def embed(self, texts: list[str]) -> list[object]:
        import numpy as np

        def vector(text: str) -> object:
            if "OTP" in text:
                return np.array([1.0, 0.0], dtype=np.float32)
            if "Fees" in text:
                return np.array([0.1, 1.0], dtype=np.float32)
            return np.array([0.7, 0.7], dtype=np.float32)

        return [vector(text) for text in texts]


def test_combined_search_scores_follow_its_order() -> None:
    # Keyword search finds only the fees passage; meaning search likes it least.
    hits = Searcher(PASSAGES, embedder=FixedEmbedder()).search("fees", 3, mode="combined")  # type: ignore[arg-type]
    scores = [hit.score for hit in hits]
    assert scores == sorted(scores, reverse=True)
