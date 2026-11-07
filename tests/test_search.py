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
    assert fused[0] == "b"
    assert set(fused) == {"a", "b", "c"}


def test_keyword_only_mode_needs_no_embedding_model() -> None:
    searcher = Searcher(PASSAGES, embedder=None)
    assert searcher.search("branch fees", 2, mode="keyword")[0].passage.id == "fees#branch"


def test_keyword_search_matches_simple_english_word_forms() -> None:
    page = [passage("billers#kinds", "You can pay schools and cancelling is free.")]
    index = KeywordIndex(page)
    assert index.search("school", 1) != []
    assert index.search("cancel", 1) != []


def test_the_glossary_adds_english_for_tagalog_money_words() -> None:
    from help_assistant.search.glossary import expand

    assert "pawn" in expand("Paano mag-sangla ng alahas?")
    assert "redeem" in expand("Pwede bang tumubos?")
    assert expand("When are branches open?") == "When are branches open?"
