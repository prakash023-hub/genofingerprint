"""Clinical Q&A agent — RAG + patient context + Claude."""

from __future__ import annotations

import json
import os
from typing import Optional

from agents.rag_store import retrieve_context, answer_with_rag_rules


def ask_clinical_question(question: str, analysis: Optional[dict] = None, language: str = "English") -> str:
    if not question or not question.strip():
        return "Please enter a clinical or pharmacogenomics question."

    ctx = retrieve_context(question, n=6)
    analysis_block = ""
    if analysis:
        analysis_block = json.dumps(
            {
                "patient": analysis.get("patient_name"),
                "fingerprint_id": analysis.get("fingerprint_id"),
                "phenotypes": analysis.get("phenotypes"),
                "recommendations": analysis.get("recommendations"),
                "summary": analysis.get("summary"),
            },
            indent=2,
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return answer_with_rag_rules(question, analysis, language)

    try:
        import anthropic

        client = anthropic.Anthropic()
        model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        prompt = f"""You are GenoFingerprint AI clinical assistant at a hospital bedside device.
Answer using ONLY the CPIC context and patient analysis below. If unsure, say so.
Never invent drug recommendations beyond the analysis data.

CPIC RAG CONTEXT:
{ctx}

CURRENT PATIENT ANALYSIS (if any):
{analysis_block or "No patient scanned yet."}

QUESTION: {question}

Give a clear answer for a clinician or pharmacist. Mention CPIC basis.
If the question asks for a patient summary in a specific language, add a short paragraph in that language at the end.
Preferred report language for this session: {language}.
Keep under 250 words."""

        response = client.messages.create(
            model=model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception:
        return answer_with_rag_rules(question, analysis, language)
