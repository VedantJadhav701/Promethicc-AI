"""Medical emergency and mental-health crisis detection.

Runs server-side before any inference call for high-stakes experts.
Biased toward false positives — over-triggering the safe response is
the correct failure mode.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Curated phrase lists — extend as needed
# ---------------------------------------------------------------------------

MEDICAL_EMERGENCY_PHRASES: list[str] = [
    "chest pain",
    "severe bleeding",
    "can't breathe",
    "cannot breathe",
    "cant breathe",
    "difficulty breathing",
    "heart attack",
    "stroke",
    "seizure",
    "overdose",
    "choking",
    "anaphylaxis",
    "unconscious",
    "not breathing",
    "loss of consciousness",
    "severe allergic reaction",
    "severe burn",
    "poisoning",
    "head injury",
    "bleeding heavily",
    "stopped breathing",
    "cardiac arrest",
    "collapsed",
    "convulsion",
    "drug overdose",
    "severe chest pressure",
    "coughing blood",
    "vomiting blood",
    "unresponsive",
]

MENTAL_HEALTH_CRISIS_PHRASES: list[str] = [
    "suicidal",
    "want to die",
    "kill myself",
    "self-harm",
    "self harm",
    "cutting myself",
    "end my life",
    "don't want to live",
    "dont want to live",
    "thinking about suicide",
    "hurting myself",
    "taking my life",
    "no reason to live",
    "wish i was dead",
    "wish i were dead",
    "plan to kill",
    "going to kill myself",
    "harm myself",
    "ending it all",
    "better off dead",
]

# ---------------------------------------------------------------------------
# Fixed safe responses — never model-generated
# ---------------------------------------------------------------------------

SAFE_RESPONSE_MEDICAL: str = (
    "⚠️ This sounds like it could be a medical emergency.\n\n"
    "Please take immediate action:\n"
    "• **Call your local emergency number** (911 in the US, 112 in the EU, "
    "999 in the UK, 108 in India) right now.\n"
    "• **Go to the nearest emergency room** if you can safely do so.\n"
    "• **Do not wait** for an online response — get professional help immediately.\n\n"
    "This AI cannot provide emergency medical care."
)

SAFE_RESPONSE_CRISIS: str = (
    "💙 It sounds like you may be going through a very difficult time. "
    "You are not alone, and help is available right now.\n\n"
    "Please reach out to a crisis service:\n"
    "• **988 Suicide & Crisis Lifeline** — call or text **988** (US)\n"
    "• **Crisis Text Line** — text **HELLO** to **741741** (US)\n"
    "• **International Association for Suicide Prevention**: "
    "https://www.iasp.info/resources/Crisis_Centres/\n\n"
    "A trained counselor is available 24/7. Please talk to someone."
)

# ---------------------------------------------------------------------------
# Pre-compiled patterns for word-boundary matching
# ---------------------------------------------------------------------------


def _compile_patterns(phrases: list[str]) -> re.Pattern[str]:
    """Build a single compiled regex that matches any phrase with word boundaries.

    Args:
        phrases: List of literal phrases to match.

    Returns:
        A compiled, case-insensitive regex pattern.
    """
    escaped = [re.escape(p) for p in phrases]
    combined = "|".join(escaped)
    return re.compile(rf"\b(?:{combined})\b", re.IGNORECASE)


_MEDICAL_RE: re.Pattern[str] = _compile_patterns(MEDICAL_EMERGENCY_PHRASES)
_CRISIS_RE: re.Pattern[str] = _compile_patterns(MENTAL_HEALTH_CRISIS_PHRASES)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def check(message: str) -> tuple[bool, str | None]:
    """Screen a user message for emergency or crisis language.

    Mental-health crisis phrases are checked first so that a combined
    message (e.g. "I want to die, I have chest pain") triggers the
    crisis response, which includes both safety resources.

    Args:
        message: The raw user query text.

    Returns:
        A tuple of (triggered, safe_response_text).  If triggered is
        False, safe_response_text is None.
    """
    if _CRISIS_RE.search(message):
        logger.warning("Mental-health crisis pattern detected")
        return True, SAFE_RESPONSE_CRISIS

    if _MEDICAL_RE.search(message):
        logger.warning("Medical emergency pattern detected")
        return True, SAFE_RESPONSE_MEDICAL

    return False, None
