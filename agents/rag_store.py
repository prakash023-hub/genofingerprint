"""Lightweight CPIC RAG — keyword retrieval (fast on HuggingFace, no model download)."""

from __future__ import annotations

import re
from typing import Optional

from data.cpic_knowledge import CPIC_DATA, INDIAN_ALLELE_FREQUENCIES, GLOBAL_ALLELE_FREQUENCIES
from data.i18n_fallback import FALLBACK_PATIENT, SUPPORTED_LANGUAGES

_DOCS: list[tuple[str, dict]] | None = None


def _build_documents() -> list[tuple[str, dict]]:
    docs: list[tuple[str, dict]] = []
    for gene, gdata in CPIC_DATA.items():
        for variant, phenotype in gdata.get("variants", {}).items():
            docs.append(
                (
                    f"Gene {gene} variant {variant} maps to phenotype {phenotype}. "
                    f"CPIC pharmacogenomics guideline cpicpgx.org.",
                    {"gene": gene, "type": "variant"},
                )
            )
        for drug, pheno_map in gdata.get("drugs", {}).items():
            for phenotype, info in pheno_map.items():
                docs.append(
                    (
                        f"CPIC {gene} drug {drug} phenotype {phenotype} risk {info['risk']}. "
                        f"Recommendation: {info['recommendation']} Rationale: {info['rationale']}",
                        {"gene": gene, "drug": drug, "type": "recommendation"},
                    )
                )
    for gene, freqs in INDIAN_ALLELE_FREQUENCIES.items():
        for pheno, pct in freqs.items():
            global_pct = GLOBAL_ALLELE_FREQUENCIES.get(gene, {}).get(pheno, "varies")
            docs.append(
                (
                    f"Population genetics {gene} {pheno}: South Asian ~{pct}, global reference ~{global_pct}. "
                    f"CPIC pharmacogenomics clopidogrel CYP2C19.",
                    {"gene": gene, "type": "population"},
                )
            )
    docs.append(
        (
            "GenoFingerprint is clinical decision support only. Not CDSCO or FDA approved diagnostic. "
            "Clinician must confirm all prescribing. DPDP Act: demo uses anonymized synthetic VCF.",
            {"type": "compliance"},
        )
    )
    docs.append(
        (
            "CYP2C19 poor metabolizer clopidogrel avoid use prasugrel ticagrelor CPIC antiplatelet stent ACS. "
            "13-23 percent Indian population poor metabolizer.",
            {"gene": "CYP2C19", "drug": "clopidogrel", "type": "recommendation"},
        )
    )
    return docs


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9*]+", text.lower()))


def get_rag_collection():
    """Compatibility shim — returns doc list length for warmup."""
    global _DOCS
    if _DOCS is None:
        _DOCS = _build_documents()
    return _DOCS


def retrieve_context(query: str, n: int = 6) -> str:
    docs = get_rag_collection()
    q_tokens = _tokenize(query)
    if not q_tokens:
        return ""

    scored: list[tuple[float, str]] = []
    for text, _meta in docs:
        d_tokens = _tokenize(text)
        overlap = len(q_tokens & d_tokens)
        if overlap == 0:
            continue
        scored.append((overlap / (len(d_tokens) ** 0.5), text))

    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        # broad fallback for generic questions
        return "\n\n".join(d[0] for d in docs[:4])
    return "\n\n".join(t for _, t in scored[:n])


def answer_with_rag_rules(query: str, analysis: Optional[dict] = None, language: str = "English") -> str:
    ctx = retrieve_context(query, n=5)
    lines = [f"**CPIC knowledge (retrieved):**\n{ctx}"]

    if analysis:
        lines.append(
            f"\n**Patient {analysis.get('patient_name')}** · Fingerprint `{analysis.get('fingerprint_id')}` · "
            f"Source: {analysis.get('data_source', 'manual')}"
        )
        for gene, pheno in analysis.get("phenotypes", {}).items():
            lines.append(f"- {gene}: {pheno} ({analysis.get('raw_genotype', {}).get(gene, '?')})")
        lines.append("\n**Drug actions (CPIC rules engine):**")
        for rec in analysis.get("recommendations", [])[:8]:
            lines.append(f"- **{rec['drug']}** → {rec['action']}: {rec['detail']}")

        lang = language if language in SUPPORTED_LANGUAGES else "English"
        q_lower = query.lower()
        wants_local = any(
            l.lower() in q_lower or l in query
            for l in SUPPORTED_LANGUAGES
        ) or lang != "English"
        if wants_local:
            narrative = analysis.get("narrative") or {}
            local = narrative.get("local_explanation") or FALLBACK_PATIENT.get(lang, FALLBACK_PATIENT["English"])
            lines.append(f"\n**Patient ({lang}):** {local}")
    else:
        lines.append("\n*Run a bedside scan first to attach patient-specific CPIC results.*")

    return "\n".join(lines)
