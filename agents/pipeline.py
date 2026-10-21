import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from data.cpic_knowledge import CPIC_DATA, INDIAN_ALLELE_FREQUENCIES, GLOBAL_ALLELE_FREQUENCIES

class GenomicState(TypedDict):
    patient_id: str
    patient_name: str
    age: int
    gender: str
    indication: str
    raw_genotype: Dict
    phenotypes: Dict
    drug_risks: List[Dict]
    recommendations: List[Dict]
    fingerprint_id: str
    report_ready: bool
    error: str
    summary: Dict
    population_notes: List[str]

def parser_agent(state: GenomicState) -> GenomicState:
    try:
        raw = state["raw_genotype"]
        validated = {}
        for gene, variant in raw.items():
            if gene in CPIC_DATA:
                validated[gene] = variant
        state["raw_genotype"] = validated
        return state
    except Exception as e:
        state["error"] = str(e)
        return state

def phenotype_mapper_agent(state: GenomicState) -> GenomicState:
    phenotypes = {}
    for gene, variant in state["raw_genotype"].items():
        gene_data = CPIC_DATA.get(gene, {})
        variant_map = gene_data.get("variants", {})
        if variant in variant_map:
            phenotypes[gene] = variant_map[variant]
        else:
            phenotypes[gene] = "Indeterminate"
    state["phenotypes"] = phenotypes
    return state

def risk_scorer_agent(state: GenomicState) -> GenomicState:
    drug_risks = []
    indication = state.get("indication", "").lower()
    priority_drugs = []
    if any(w in indication for w in ["clopidogrel", "acs", "stent", "cardiac", "antiplatelet"]):
        priority_drugs.extend(["clopidogrel", "warfarin", "metoprolol"])
    if any(w in indication for w in ["statin", "cholesterol", "lipid"]):
        priority_drugs.extend(["simvastatin", "atorvastatin"])
    if any(w in indication for w in ["pain", "codeine"]):
        priority_drugs.extend(["codeine"])
    if any(w in indication for w in ["cancer", "tamoxifen", "breast"]):
        priority_drugs.extend(["tamoxifen"])
    if any(w in indication for w in ["transplant", "azathioprine"]):
        priority_drugs.extend(["azathioprine"])
    if not priority_drugs:
        for gene_data in CPIC_DATA.values():
            priority_drugs.extend(gene_data.get("drugs", {}).keys())
    priority_drugs = list(set(priority_drugs))
    for gene, phenotype in state["phenotypes"].items():
        gene_data = CPIC_DATA.get(gene, {})
        drugs = gene_data.get("drugs", {})
        for drug_name, drug_data in drugs.items():
            if drug_name not in priority_drugs:
                continue
            risk_info = drug_data.get(phenotype)
            if risk_info:
                drug_risks.append({
                    "gene": gene, "drug": drug_name, "phenotype": phenotype,
                    "risk_level": risk_info["risk"], "recommendation": risk_info["recommendation"],
                    "rationale": risk_info["rationale"], "variant": state["raw_genotype"].get(gene, "Unknown")
                })
    risk_order = {"HIGH": 0, "MODERATE": 1, "LOW": 2}
    drug_risks.sort(key=lambda x: risk_order.get(x["risk_level"], 3))
    state["drug_risks"] = drug_risks
    return state

def recommendation_agent(state: GenomicState) -> GenomicState:
    import hashlib
    recommendations = []
    high_risk_count = 0
    moderate_risk_count = 0
    for risk in state["drug_risks"]:
        rec = {
            "drug": risk["drug"].upper(), "gene": risk["gene"],
            "action": "AVOID" if risk["risk_level"] == "HIGH" else "CAUTION" if risk["risk_level"] == "MODERATE" else "USE",
            "risk": risk["risk_level"], "detail": risk["recommendation"],
            "rationale": risk["rationale"], "phenotype": risk["phenotype"], "variant": risk["variant"]
        }
        recommendations.append(rec)
        if risk["risk_level"] == "HIGH": high_risk_count += 1
        elif risk["risk_level"] == "MODERATE": moderate_risk_count += 1
    fingerprint_input = f"{state['patient_id']}{json.dumps(state['raw_genotype'])}"
    fingerprint_id = "GFP-" + __import__('hashlib').md5(fingerprint_input.encode()).hexdigest()[:8].upper()
    population_notes = []
    for gene, freq_data in INDIAN_ALLELE_FREQUENCIES.items():
        if gene in state["phenotypes"]:
            phenotype = state["phenotypes"][gene]
            south_asia = freq_data.get(phenotype, "Unknown")
            global_freq = GLOBAL_ALLELE_FREQUENCIES.get(gene, {}).get(phenotype, "Unknown")
            population_notes.append(
                f"{gene} {phenotype}: ~{south_asia} South Asian · ~{global_freq} global reference (CPIC/gnomAD)"
            )
    state["recommendations"] = recommendations
    state["fingerprint_id"] = fingerprint_id
    state["population_notes"] = population_notes
    state["summary"] = {
        "high_risk": high_risk_count, "moderate_risk": moderate_risk_count,
        "low_risk": len(recommendations) - high_risk_count - moderate_risk_count,
        "total_drugs_assessed": len(recommendations), "critical_alert": high_risk_count > 0
    }
    state["report_ready"] = True
    return state

def build_pipeline():
    workflow = StateGraph(GenomicState)
    workflow.add_node("parser", parser_agent)
    workflow.add_node("phenotype_mapper", phenotype_mapper_agent)
    workflow.add_node("risk_scorer", risk_scorer_agent)
    workflow.add_node("recommendation", recommendation_agent)
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "phenotype_mapper")
    workflow.add_edge("phenotype_mapper", "risk_scorer")
    workflow.add_edge("risk_scorer", "recommendation")
    workflow.add_edge("recommendation", END)
    return workflow.compile()

def run_analysis(patient_data: Dict) -> Dict:
    pipeline = build_pipeline()
    initial_state = GenomicState(
        patient_id=patient_data.get("patient_id", "PT001"),
        patient_name=patient_data.get("patient_name", "Patient"),
        age=patient_data.get("age", 0),
        gender=patient_data.get("gender", "Unknown"),
        indication=patient_data.get("indication", ""),
        raw_genotype=patient_data.get("genotype", {}),
        phenotypes={}, drug_risks=[], recommendations=[],
        fingerprint_id="", report_ready=False, error="", summary={}, population_notes=[]
    )
    return pipeline.invoke(initial_state)
