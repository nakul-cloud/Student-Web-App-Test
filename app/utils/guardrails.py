"""
Safety Guardrails & Gibberish Detector
Runs before retrieval/LLM at 0 token cost, controlled via app/config/settings.py.
"""
import re
from app.config.settings import settings


_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"forget\s+(your\s+)?rules",
    r"act\s+as\s+(a\s+)?(dan|jailbreak|unfiltered|hacker)",
    r"bypass\s+(safety|guardrails|rules)",
]


def is_gibberish(text: str) -> bool:
    """
    Detects keyboard smashing, random character strings, or symbol spam.
    Configured via settings.gibberish_min_vowel_ratio and settings.gibberish_max_repeat_chars.
    """
    if not settings.enable_gibberish_detector:
        return False

    cleaned = text.strip()
    if not cleaned:
        return True

    # 1. Excessive repeated characters (e.g. "aaaaaa", "zzzzzz")
    repeat_limit = settings.gibberish_max_repeat_chars
    if re.search(rf"(.)\1{{{repeat_limit},}}", cleaned.lower()):
        return True

    # 2. Only punctuation / numbers / symbols (no letters at all)
    letters = re.findall(r"[a-zA-Z]", cleaned)
    if len(letters) < 2:
        return True

    # 3. Excessive non-alphanumeric symbol ratio (> 45%)
    non_space = re.sub(r"\s+", "", cleaned)
    if non_space and (len(re.findall(r"[^a-zA-Z0-9.,?!'\"-]", non_space)) / len(non_space)) > 0.45:
        return True

    # 4. Very low vowel ratio on longer strings (e.g. "asdfghjklqwrty")
    if len(letters) >= 6:
        vowels = len(re.findall(r"[aeiouAEIOU]", cleaned))
        if (vowels / len(letters)) < settings.gibberish_min_vowel_ratio:
            return True

    # 5. Single super-long nonsense word (> 22 chars without spaces)
    if " " not in cleaned and len(cleaned) > 22:
        return True

    return False


def check_guardrails(text: str) -> tuple[bool, str]:
    """
    Checks for prompt-injection attempts and off-topic requests.
    Returns (is_blocked, reason).
    """
    if not settings.enable_guardrails:
        return False, ""

    lower = text.strip().lower()

    # 1. Prompt injection / jailbreak check
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, lower):
            return True, "prompt_injection"

    # 2. Off-topic keyword check from settings
    words = set(re.split(r"\W+", lower))
    for kw in settings.blocked_offtopic_keywords:
        if (" " in kw and kw in lower) or (kw in words):
            return True, "out_of_scope"

    return False, ""
