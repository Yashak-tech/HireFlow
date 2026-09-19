"""
Anti-Tamper Guard Agent (Phase 5).

Classifies candidate responses for prompt injection, instruction overrides,
jailbreaks, or abusive content. Sets tamper_flag=True and terminates session
on violation per TRD §6.1.
"""
import re
import logging
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

# ─── Injection Pattern Rules ───────────────────────────────────────────
# These patterns cover common prompt injection, jailbreak, and instruction
# override attempts. They are evaluated deterministically without LLM calls
# for speed and reliability.

INJECTION_PATTERNS = [
    # Direct instruction overrides
    (r"ignore\s+(all\s+)?previous\s+instructions?", "instruction_override"),
    (r"ignore\s+(your|the)\s+(system\s+)?prompt", "instruction_override"),
    (r"disregard\s+(all\s+)?prior\s+(instructions?|context)", "instruction_override"),
    (r"forget\s+(everything|all|your)\s+(you\s+)?(were\s+)?told", "instruction_override"),
    (r"override\s+(your\s+)?(system|initial)\s+(prompt|instructions?)", "instruction_override"),
    (r"new\s+instructions?\s*:", "instruction_override"),

    # Prompt extraction attempts
    (r"(repeat|show|reveal|display|print|output)\s+(your\s+)?(system\s+)?prompt", "prompt_extraction"),
    (r"what\s+(are|is)\s+your\s+(system\s+)?(instructions?|prompt|rules)", "prompt_extraction"),
    (r"(tell|show)\s+me\s+(your|the)\s+(system\s+)?(prompt|instructions)", "prompt_extraction"),
    (r"dump\s+(your\s+)?(system\s+)?(prompt|config|instructions)", "prompt_extraction"),

    # Jailbreak patterns
    (r"you\s+are\s+(now\s+)?(DAN|jailbr[eo]ak|unfiltered)", "jailbreak"),
    (r"act\s+as\s+if\s+you\s+have\s+no\s+(restrictions?|rules?|limits?)", "jailbreak"),
    (r"pretend\s+(you\s+)?(are|have)\s+no\s+(ethical|safety|content)\s+(guidelines?|filters?)", "jailbreak"),
    (r"do\s+anything\s+now", "jailbreak"),
    (r"developer\s+mode\s+(enabled|activated|on)", "jailbreak"),

    # Score manipulation
    (r"(give|score|rate|set)\s+(me\s+)?(a\s+)?(\d+|perfect|100|full)\s*(score|marks?|points?|rating)", "score_manipulation"),
    (r"mark\s+(me|my\s+answer)\s+as\s+(correct|perfect|excellent)", "score_manipulation"),
    (r"(my\s+score\s+should\s+be|set\s+score\s+to)\s+\d+", "score_manipulation"),

    # Role confusion / impersonation
    (r"(you\s+are|i\s+am)\s+(the\s+)?(recruiter|interviewer|admin|system)", "role_confusion"),
    (r"switch\s+(to\s+)?(admin|recruiter|system)\s+(mode|role)", "role_confusion"),

    # Abusive / hostile content
    (r"\b(fuck|shit|damn|bitch|asshole|bastard)\b", "abusive_content"),
]

# Compiled patterns for performance
_COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), category)
    for pattern, category in INJECTION_PATTERNS
]


def classify_tamper_attempt(candidate_input: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Evaluate candidate input for adversarial intent.

    Returns:
        (is_tamper, details) — If tampered, details contains category,
        matched_pattern, and the offending input substring.
    """
    if not candidate_input or not candidate_input.strip():
        return False, None

    clean_input = candidate_input.strip()

    # Check against all compiled patterns
    for compiled_pattern, category in _COMPILED_PATTERNS:
        match = compiled_pattern.search(clean_input)
        if match:
            logger.warning(
                "TAMPER DETECTED [%s]: '%s' in input: '%s...'",
                category,
                match.group(0),
                clean_input[:80],
            )
            return True, {
                "category": category,
                "matched_text": match.group(0),
                "input_preview": clean_input[:200],
                "reason": f"Adversarial intent detected: {category.replace('_', ' ')}. "
                          f"Matched pattern: '{match.group(0)}'.",
            }

    # Check for suspiciously long encoded content (potential base64 injection)
    if len(clean_input) > 2000:
        # Check if it's mostly non-alphanumeric / encoded
        non_alpha_ratio = sum(1 for c in clean_input if not c.isalnum() and c not in ' .,!?;:\'-"()\n') / len(clean_input)
        if non_alpha_ratio > 0.4:
            logger.warning("TAMPER DETECTED [encoded_injection]: High non-alpha ratio %.2f", non_alpha_ratio)
            return True, {
                "category": "encoded_injection",
                "matched_text": clean_input[:100],
                "input_preview": clean_input[:200],
                "reason": "Suspiciously encoded or obfuscated content detected.",
            }

    return False, None


def is_empty_or_skip(candidate_input: str) -> bool:
    """Check if the candidate's input is effectively empty or a skip request."""
    clean = candidate_input.strip().lower()
    if not clean:
        return True

    skip_phrases = [
        "skip", "pass", "next", "i don't know", "i dont know",
        "no answer", "n/a", "na", "none", "nothing",
        "i have no answer", "can't answer", "cant answer",
        "no comment", "no response",
    ]
    return clean in skip_phrases or len(clean) < 3
