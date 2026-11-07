from help_assistant.core.checks import check_citations, check_numbers, numbers_in
from help_assistant.pages.reader import Passage


def passage(pid: str, text: str) -> Passage:
    return Passage(id=pid, page=pid.split("#")[0], heading=pid, text=text, position=0)


FEES = passage(
    "send-money-fees#fees-for-branch-pickup",
    "Fees for branch pickup\n| Up to ₱1,000 | ₱15 |\n| ₱1,001 to ₱5,000 | ₱35 |",
)
HOURS = passage(
    "branch-hours#opening-hours", "Open Monday to Saturday, 8:00 a.m. to 6:00 p.m., with one break."
)
OTP = passage(
    "login-and-otp#if-the-otp-doesn-t-arrive",
    "Wait 2 minutes, then tap Resend. An OTP expires after 5 minutes.",
)


def test_b1_an_answer_citing_only_passages_search_returned_passes() -> None:
    assert check_citations([FEES.id], retrieved=[FEES.id, HOURS.id]) == []


def test_b1_an_answer_citing_a_passage_search_didnt_return_is_refused() -> None:
    broken = check_citations([FEES.id, "made-up#page"], retrieved=[FEES.id])
    assert [b.rule for b in broken] == ["unknown_citation"]


def test_b1_an_answer_citing_nothing_is_refused() -> None:
    assert [b.rule for b in check_citations([], retrieved=[FEES.id])] == ["no_citation"]


def test_b2_numbers_in_the_cited_passages_are_allowed_however_they_are_written() -> None:
    reply = "Sending ₱3,000 costs ₱35. Sending up to 1000 pesos costs P15.00."
    assert check_numbers(reply.replace("3,000", "1,001"), [FEES]) == []
    assert check_numbers("Branches open at 8:00 a.m., with 1 break.", [HOURS]) == []


def test_b2_a_number_not_in_the_cited_passages_is_refused() -> None:
    broken = check_numbers("Sending ₱3,000 costs ₱25.", [FEES])
    assert [b.rule for b in broken] == ["unsupported_number"]
    assert "25" in broken[0].detail
    assert "3000" in broken[0].detail


def test_b2_a_number_from_a_passage_that_wasnt_cited_is_refused() -> None:
    assert check_numbers("The OTP expires after 5 minutes.", [FEES]) != []
    assert check_numbers("The OTP expires after 5 minutes.", [OTP]) == []


def test_b2_numbers_written_as_words_in_english_or_tagalog_count_too() -> None:
    assert numbers_in("wait two minutes, then limang minuto") == {"2", "5"}
    assert check_numbers("Maghintay ng dalawang minuto, tapos i-tap ang Resend.", [OTP]) == []
    assert check_numbers("Maghintay ng tatlong minuto.", [OTP]) != []


def test_b2_the_customers_own_figures_may_be_repeated() -> None:
    question = "Magkano ang fee pag nagpadala ng 3,000?"
    assert check_numbers("Sending ₱3,000 costs ₱35.", [FEES], question=question) == []
    # A figure in neither the pages nor the question is still refused.
    assert check_numbers("Sending ₱3,000 costs ₱25.", [FEES], question=question) != []
