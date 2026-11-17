"""Optional Claude presentation choice. Model text never reaches the report."""

import os

import anthropic

from agents.rule_narrator import generate_rule_narrative
from data.i18n_fallback import SUPPORTED_LANGUAGES


def generate_clinical_narrative(result: dict, language: str = "English") -> dict:
    lang = language if language in SUPPORTED_LANGUAGES else "English"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return generate_rule_narrative(result, lang)

    client = anthropic.Anthropic(timeout=3.0, max_retries=0)
    response = client.messages.create(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=32,
        messages=[{
            "role": "user",
            "content": f"Choose an ordering for an educational report read alongside {lang} patient text. "
                       "Return exactly FINDINGS_FIRST or PROFILE_FIRST. Include no report text.",
        }],
    )
    choice = response.content[0].text.strip()
    return generate_rule_narrative(result, lang, profile_first=choice == "PROFILE_FIRST")


def generate_narrative_safe(result: dict, language: str = "English") -> dict:
    try:
        return generate_clinical_narrative(result, language)
    except (anthropic.APIError, ValueError, AttributeError, IndexError, TypeError):
        return generate_rule_narrative(result, language)
