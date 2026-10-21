"""Deterministic CPIC narratives — case-specific, no API key required."""

from __future__ import annotations

from data.i18n_fallback import DRUG_PATIENT_ALERTS, SUPPORTED_LANGUAGES


def _primary_rec(recommendations: list[dict]) -> dict | None:
    for risk in ("HIGH", "MODERATE", "LOW"):
        for rec in recommendations:
            if rec.get("risk") == risk:
                return rec
    return recommendations[0] if recommendations else None


def _alternatives_text(rec: dict) -> str:
    detail = rec.get("detail", "")
    if "prasugrel" in detail.lower() or "ticagrelor" in detail.lower():
        return "Consider prasugrel or ticagrelor per CPIC antiplatelet guidance."
    if "aromatase" in detail.lower():
        return "Consider an aromatase inhibitor per CPIC breast cancer guidance."
    if "pravastatin" in detail.lower() or "rosuvastatin" in detail.lower():
        return "Consider pravastatin or rosuvastatin per CPIC statin guidance."
    if "non-opioid" in detail.lower():
        return "Consider non-opioid analgesics per CPIC opioid guidance."
    return detail


def generate_rule_narrative(result: dict, language: str = "English") -> dict:
    lang = language if language in SUPPORTED_LANGUAGES else "English"
    name = result.get("patient_name", "Patient")
    age = result.get("age", "")
    gender = result.get("gender", "")
    indication = result.get("indication", "Pharmacogenomics review")
    fp = result.get("fingerprint_id", "")
    recs = result.get("recommendations", [])
    high = [r for r in recs if r.get("risk") == "HIGH"]
    primary = _primary_rec(recs)

    gene_lines = ", ".join(
        f"{g} {result['raw_genotype'].get(g, '?')} ({result['phenotypes'].get(g, '?')})"
        for g in result.get("raw_genotype", {})
    )

    if primary:
        doctor_summary = (
            f"CPIC pharmacogenomics review for {name} ({age}Y {gender}), indication: {indication}. "
            f"Key finding: {primary['gene']} {primary['variant']} → {primary['phenotype']}; "
            f"{primary['drug']} — {primary['action']}. {primary['detail']} "
            f"Rationale: {primary['rationale']} "
            f"Profile: {gene_lines}. Fingerprint {fp}."
        )
    else:
        doctor_summary = (
            f"CPIC review for {name}: no actionable high-risk interactions in this 5-gene panel "
            f"for the stated indication. Profile: {gene_lines}."
        )

    critical_alert = ""
    if high:
        drugs = ", ".join(r["drug"] for r in high)
        critical_alert = f"ALERT: {drugs} — genomic contraindication or major CPIC action required."

    drug_key = primary["drug"].lower() if primary else ""
    patient_en = DRUG_PATIENT_ALERTS.get(drug_key, {}).get(
        "English",
        (
            f"Your doctor reviewed your pharmacogenomics report ({fp}). "
            f"Some medicines may need to be changed based on your genes — follow your clinician's advice."
        ),
    )
    local = DRUG_PATIENT_ALERTS.get(drug_key, {}).get(lang, patient_en)
    if lang == "English":
        local = patient_en

    return {
        "doctor_summary": doctor_summary,
        "critical_alert": critical_alert,
        "patient_explanation": patient_en,
        "local_explanation": local,
        "tamil_explanation": DRUG_PATIENT_ALERTS.get(drug_key, {}).get("Tamil", local),
        "language": lang,
        "narrator": "cpic_rules",
    }
