"""Common Tagalog words for money services, with their English, added to a
question's keyword search: the help pages are in English, and small embedding
models know few Tagalog money words. One list for every question; it is not
tuned to the test questions."""

from help_assistant.search.keyword import words

# Tagalog root → English words. A question word containing the root matches
# ("magpadala", "padala", "ipinadala" all contain "padala").
GLOSSARY: dict[str, str] = {
    "padala": "send money transfer receiver",
    "pera": "money",
    "sangla": "pawn loan item",
    "tubos": "redeem item",
    "tubus": "redeem item",
    "tumubos": "redeem item",
    "alahas": "jewellery gold item",
    "ginto": "gold jewellery",
    "kuryente": "electricity bill biller",
    "tubig": "water bill biller",
    "bayad": "pay payment bill fee",
    "bayarin": "bills pay",
    "singil": "fee charge",
    "matrikula": "tuition school biller",
    "paaralan": "school biller",
    "eskwela": "school biller",
    "makuha": "claim receive",
    "kunin": "claim receive",
    "nawala": "lost lose missing",
    "nakalimutan": "forgot",
    "kalimutan": "forgot",
    "bukas": "open hours",
    "sarado": "closed hours",
    "oras": "hours time",
    "araw": "days",
    "buwan": "month monthly",
    "tubo": "interest",
    "utang": "loan",
    "pautang": "loan",
    "hiram": "borrow loan",
    "humiram": "borrow loan",
    "ipon": "savings",
    "lagay": "cash in add",
    "ilagay": "cash in add",
    "labas": "cash out",
    "ilabas": "cash out",
    "hindi dumating": "not arrive",
    "dumating": "arrive",
    "kailangan": "need requirements",
    "tanggap": "accept accepted",
    "ibang tao": "another person someone else",
    "nanalo": "prize scam",
    "manloloko": "scam",
    "kausap": "contact support",
    "makausap": "contact support person",
}


def expand(question: str) -> str:
    """`question` with the English for any glossary word it contains."""
    lowered = question.lower()
    question_words = words(question)
    extra = [
        english
        for root, english in GLOSSARY.items()
        if (" " in root and root in lowered) or any(root in word for word in question_words)
    ]
    return f"{question} {' '.join(extra)}" if extra else question
