import anthropic
import json
import os

from agents.rule_narrator import generate_rule_narrative
from data.i18n_fallback import FALLBACK_PATIENT, SUPPORTED_LANGUAGES


def generate_clinical_narrative(result: dict, language: str = "English") -> dict:
    lang = language if language in SUPPORTED_LANGUAGES else "English"
    client = anthropic.Anthropic()
    phenotype_text = "\n".join([f"- {gene}: {phenotype}" for gene, phenotype in result["phenotypes"].items()])
    rec_text = "\n".join([f"- {r['drug']}: {r['action']} (Risk: {r['risk']}) — {r['detail']}" for r in result["recommendations"]])
    prompt = f"""You are a clinical pharmacogenomics AI assistant. CPIC international guidelines.

PATIENT: {result['patient_name']}, {result['age']}Y, {result['gender']}
INDICATION: {result['indication']}
FINGERPRINT ID: {result['fingerprint_id']}

GENOMIC PHENOTYPES:
{phenotype_text}

DRUG RECOMMENDATIONS:
{rec_text}

RISK SUMMARY: {result['summary']['high_risk']} HIGH, {result['summary']['moderate_risk']} MODERATE, {result['summary']['low_risk']} LOW

Generate JSON with exactly these 4 keys:
{{
  "doctor_summary": "2-3 sentences for the treating physician in English. Medical terminology. CPIC basis. Most critical finding first.",
  "critical_alert": "1 sentence urgent alert if HIGH risk, else empty. Start with ALERT: if critical.",
  "patient_explanation": "2-3 sentences in simple English for the patient.",
  "local_explanation": "Same patient explanation in {lang}. Use native script for non-Latin languages."
}}
Return ONLY JSON. No markdown."""

    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(raw)
    data["tamil_explanation"] = data.get("local_explanation", "") if lang == "Tamil" else ""
    data["language"] = lang
    data["narrator"] = "claude"
    return data


def generate_narrative_safe(result: dict, language: str = "English") -> dict:
    """CPIC rule narrative always; Claude only when ANTHROPIC_API_KEY is set."""
    lang = language if language in SUPPORTED_LANGUAGES else "English"
    rule = generate_rule_narrative(result, lang)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return rule

    try:
        ai = generate_clinical_narrative(result, lang)
        if not ai.get("doctor_summary"):
            return rule
        return ai
    except Exception:
        high_risk_drugs = [r["drug"] for r in result["recommendations"] if r["risk"] == "HIGH"]
        if rule.get("doctor_summary") and "Key finding" in rule["doctor_summary"]:
            return rule
        return {
            "doctor_summary": (
                f"CPIC pharmacogenomics review for {result['patient_name']}: "
                f"{result['summary']['high_risk']} high-risk interaction(s). "
                f"Review urgently: {', '.join(high_risk_drugs) if high_risk_drugs else 'none'}."
            ),
            "critical_alert": (
                f"ALERT: Avoid {', '.join(high_risk_drugs)} — genomic contraindication per CPIC."
                if high_risk_drugs else ""
            ),
            "patient_explanation": rule.get("patient_explanation") or FALLBACK_PATIENT["English"],
            "local_explanation": rule.get("local_explanation") or FALLBACK_PATIENT.get(lang, FALLBACK_PATIENT["English"]),
            "tamil_explanation": rule.get("tamil_explanation", ""),
            "language": lang,
            "narrator": "fallback",
        }
