"""The assistant's fixed messages, in each language. None promises a time or an
outcome (D5); a test checks each with the answer rules."""

from help_assistant.core.language import Language

HANDOFF: dict[Language, str] = {
    "english": "I'll pass this to a person in our support team. They'll reply to you here in this chat.",
    "tagalog": "Ipapasa ko po ito sa isang tao sa aming support team. Sasagutin po nila kayo dito sa chat.",
    "taglish": "Ipapasa ko po ito sa isang tao sa aming support team. Sasagutin po nila kayo dito sa chat.",
}

I_DONT_KNOW: dict[Language, str] = {
    "english": "Sorry, our help pages don't answer that."
    " Would you like me to pass you to a person in support?",
    "tagalog": "Pasensya na po, wala po sa aming help pages ang sagot diyan."
    " Gusto po ba ninyong ipasa ko kayo sa isang tao sa support?",
    "taglish": "Pasensya na po, wala po sa aming help pages ang sagot diyan."
    " Gusto po ba ninyong ipasa ko kayo sa isang tao sa support?",
}

SECRET_WARNING: dict[Language, str] = {
    "english": "For your safety, I hid the PIN, OTP, password or account number you typed. Please never share"
    " them with anyone, including us.",
    "tagalog": "Para sa inyong kaligtasan, itinago ko po ang PIN, OTP, password o account number na inilagay"
    " ninyo. Huwag po ninyo itong ibigay kahit kanino, kahit sa amin.",
    "taglish": "Para sa inyong kaligtasan, itinago ko po ang PIN, OTP, password o account number na inilagay"
    " ninyo. Huwag po ninyo itong ibigay kahit kanino, kahit sa amin.",
}
