"""Deterministic panel interpretation and versioned guideline assessment."""

import hashlib
import json
import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from data.cpic_knowledge import CYP2D6_ACTIVITY, GUIDELINES, REVIEW_REASONS, VARIANTS, _RULES


class GenomicState(TypedDict, total=False):
    patient_id: str
    patient_name: str
    age: int
    gender: str
    indication: str
    data_source: str
    medications: list[str]
    clinical_context: str
    raw_genotype: dict
    phenotypes: dict
    activity_scores: dict
    drug_risks: list[dict]
    recommendations: list[dict]
    assessment_notes: list[str]
    fingerprint_id: str
    report_ready: bool
    error: str
    summary: dict
    population_notes: list[str]


def parser_agent(state: GenomicState) -> dict:
    if state["data_source"] not in ("manual", "vcf", "synthetic_vcf", "synthetic_vcf_plus_lab"):
        return {"error": "Unsupported genotype source."}
    raw = state["raw_genotype"]
    if not isinstance(raw, dict):
        return {"error": "Expected a gene-to-genotype mapping."}
    if not isinstance(state["medications"], (list, tuple)) or any(
        not isinstance(drug, str) for drug in state["medications"]
    ):
        return {"error": "Expected a list of medication names."}
    validated = {}
    for gene in VARIANTS:
        variant = raw.get(gene, "Not tested")
        if not isinstance(variant, str) or len(variant) > 180:
            variant = "Indeterminate: invalid diplotype input"
        alleles = variant.split("/")
        matches = [re.fullmatch(r"\*([0-9]+)[A-Z]?(?:x[0-9]+)?", allele) for allele in alleles]
        if len(matches) == 2 and all(matches):
            variant = "/".join(allele for _, allele in sorted(
                (int(match[1]), allele) for match, allele in zip(matches, alleles)
            ))
        if state["data_source"] in {"vcf", "synthetic_vcf"}:
            # The marker panel cannot attest copy number in any CYP2D6 call.
            if gene == "CYP2D6" and variant.startswith("*"):
                variant = "Indeterminate: CYP2D6 VCF copy number is unverified"
            if "*1" in alleles or variant in {"c.521TT", "c.521TC"}:
                variant = "Indeterminate: reference haplotype unconfirmed by this VCF panel"
        validated[gene] = variant
    return {
        "raw_genotype": validated,
        "medications": sorted({drug.strip().lower() for drug in state["medications"] if drug.strip()}),
    }


def _cyp2d6_activity(variant: str) -> float | None:
    alleles = variant.split("/")
    if len(alleles) != 2:
        return None
    score = 0.0
    for allele in alleles:
        match = re.fullmatch(r"(\*\d+)(?:x(2))?", allele)
        if not match or match[1] not in CYP2D6_ACTIVITY:
            return None
        if match[1] == "*5" and match[2]:
            return None
        score += CYP2D6_ACTIVITY[match[1]] * int(match[2] or 1)
    return score


def phenotype_mapper_agent(state: GenomicState) -> dict:
    phenotypes = {}
    activity_scores = {}
    for gene, variant in state["raw_genotype"].items():
        if variant.startswith("Not tested"):
            phenotypes[gene] = "Not tested"
            continue
        score = _cyp2d6_activity(variant) if gene == "CYP2D6" else None
        if score is not None:
            activity_scores[gene] = score
            if score == 0:
                phenotypes[gene] = "Poor Metabolizer"
            elif score < 1.25:
                phenotypes[gene] = "Intermediate Metabolizer"
            elif score <= 2.25:
                phenotypes[gene] = "Normal Metabolizer"
            else:
                phenotypes[gene] = "Ultrarapid Metabolizer"
        else:
            phenotypes[gene] = VARIANTS[gene].get(variant, "Indeterminate")
    return {"phenotypes": phenotypes, "activity_scores": activity_scores}


def risk_scorer_agent(state: GenomicState) -> dict:
    risks = []
    notes = []
    if not state["medications"]:
        notes.append("Select a medication explicitly to assess a guideline scenario.")
    for drug in state["medications"]:
        if drug not in GUIDELINES:
            notes.append(f"{drug.upper()}: {REVIEW_REASONS.get(drug, 'Unsupported medication.')}")
            continue
        gene, version, source, context = GUIDELINES[drug]
        phenotype = state["phenotypes"][gene]
        if drug in {"warfarin", "azathioprine"}:
            reason = REVIEW_REASONS[drug]
            if drug == "azathioprine" and phenotype in {"Low Activity", "Intermediate Activity"}:
                reason = f"TPMT {phenotype.lower()} raises myelosuppression risk. " + reason
            if drug == "warfarin" and phenotype in {"Poor Metabolizer", "Intermediate Metabolizer"}:
                reason = f"CYP2C9 {phenotype.lower()} status can reduce clearance. " + reason
        elif not isinstance(state["age"], (int, float)) or not 18 <= state["age"] <= 120:
            reason = "Adult age must be established for the implemented scenario."
        elif context and state["clinical_context"] != context:
            reason = "The applicable clinical context was not selected."
        elif phenotype in {"Indeterminate", "Not tested"}:
            reason = f"{gene} evidence is {phenotype.lower()}."
        else:
            rule = _RULES[drug].get(phenotype)
            reason = "" if rule else REVIEW_REASONS.get(drug, "No implemented recommendation for this phenotype.")
        if reason:
            notes.append(f"{drug.upper()}: {reason} ({version}; {source})")
            continue
        action, risk, detail = rule
        risks.append({
            "gene": gene, "drug": drug, "phenotype": phenotype, "variant": state["raw_genotype"][gene],
            "risk_level": risk, "action": action, "recommendation": detail,
            "guideline": version, "source": source,
        })
    order = {"HIGH": 0, "MODERATE": 1, "LOW": 2}
    risks.sort(key=lambda row: (order[row["risk_level"]], row["drug"]))
    return {"drug_risks": risks, "assessment_notes": notes}


def recommendation_agent(state: GenomicState) -> dict:
    recommendations = [
        {
            "drug": row["drug"].upper(), "gene": row["gene"], "action": row["action"],
            "risk": row["risk_level"], "detail": row["recommendation"], "rationale": row["recommendation"],
            "phenotype": row["phenotype"], "variant": row["variant"],
            "guideline": row["guideline"], "source": row["source"],
        }
        for row in state["drug_risks"]
    ]
    identity = json.dumps([state["patient_id"], state["raw_genotype"]], sort_keys=True)
    fingerprint = "GFP-" + hashlib.sha256(identity.encode()).hexdigest()[:8].upper()
    counts = {level.lower() + "_risk": sum(r["risk"] == level for r in recommendations)
              for level in ("HIGH", "MODERATE", "LOW")}
    return {
        "recommendations": recommendations,
        "fingerprint_id": fingerprint,
        "summary": {**counts, "total_drugs_assessed": len(recommendations), "critical_alert": bool(counts["high_risk"])},
        "report_ready": True,
    }


def build_pipeline():
    workflow = StateGraph(GenomicState)
    workflow.add_node("parser", parser_agent)
    workflow.add_node("phenotype_mapper", phenotype_mapper_agent)
    workflow.add_node("risk_scorer", risk_scorer_agent)
    workflow.add_node("recommendation", recommendation_agent)
    workflow.set_entry_point("parser")
    workflow.add_conditional_edges("parser", lambda state: "stop" if state["error"] else "continue",
                                   {"stop": END, "continue": "phenotype_mapper"})
    workflow.add_edge("phenotype_mapper", "risk_scorer")
    workflow.add_edge("risk_scorer", "recommendation")
    workflow.add_edge("recommendation", END)
    return workflow.compile()


def run_analysis(patient_data: dict) -> dict:
    initial_state = GenomicState(
        patient_id=patient_data.get("patient_id", "PT001"),
        patient_name=patient_data.get("patient_name", "Patient"),
        age=patient_data.get("age", 0),
        gender=patient_data.get("gender", "Unknown"),
        indication=patient_data.get("indication", ""),
        raw_genotype=patient_data.get("genotype", {}),
        data_source=patient_data.get("data_source", "manual"),
        medications=patient_data.get("medications", []),
        clinical_context=patient_data.get("clinical_context", ""),
        phenotypes={}, activity_scores={}, drug_risks=[], recommendations=[],
        assessment_notes=[], fingerprint_id="", report_ready=False, error="", summary={}, population_notes=[],
    )
    # Prevent optional SDK tracing from exporting patient state if tracing is
    # enabled in the host environment.
    from langsmith import tracing_context

    with tracing_context(enabled=False):
        return build_pipeline().invoke(initial_state)
