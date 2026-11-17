"""Deterministic clinical and patient presentation of the same results."""

from data.i18n_fallback import FALLBACK_PATIENT


def generate_rule_narrative(result: dict, language: str = "English", *, profile_first: bool = False) -> dict:
    lang = language if language in FALLBACK_PATIENT else "English"
    recommendations = result.get("recommendations", [])
    profile = ", ".join(f"{gene} ({phenotype})" for gene, phenotype in result.get("phenotypes", {}).items())
    profile_line = f"Panel findings: {profile or 'unavailable'}."
    findings = [
        f"{row['gene']} {row['phenotype']}: {row['drug']} {row['action']}. {row['detail']}"
        for row in recommendations
    ] or ["No drug action could be established for the selected scenario."]
    if profile_first:
        findings.insert(0, profile_line)
    else:
        findings.append(profile_line)

    high = [r["drug"] for r in recommendations if r["risk"] == "HIGH"]
    actions = ", ".join(f"{row['drug']} [{row['action']}]" for row in recommendations)
    if actions:
        actions = "\n" + actions
    return {
        "doctor_summary": " ".join(findings),
        "critical_alert": f"High-priority review: {', '.join(high)}." if high else "",
        "patient_explanation": FALLBACK_PATIENT["English"] + actions,
        "local_explanation": FALLBACK_PATIENT[lang] + actions,
        "tamil_explanation": FALLBACK_PATIENT["Tamil"] + actions if lang == "Tamil" else "",
        "language": lang,
        "narrator": "cpic_rules",
    }
