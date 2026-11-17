"""Clinical Q&A with separate guideline references and recorded findings."""

from agents.rag_store import retrieve_context
from agents.rule_narrator import generate_rule_narrative
from data.i18n_fallback import SUPPORTED_LANGUAGES


def ask_clinical_question(question: str, analysis: dict | None = None, language: str = "English") -> str:
    if not question or not question.strip():
        return "Please enter a pharmacogenomics question."
    context = retrieve_context(question)
    lines = [
        "**General education**",
        "GenoFingerprint is a research prototype. Use these guideline references to review drug–gene evidence.",
        context or "Enter a supported gene or medication to retrieve its guideline.",
    ]
    if not analysis or not analysis.get("report_ready"):
        lines.append("**Patient findings**\nRun a successful scan to show recorded findings.")
        return "\n\n".join(lines)

    lines.append("**Recorded findings from the current report**")
    for gene, phenotype in analysis["phenotypes"].items():
        lines.append(f"- {gene}: {phenotype} ({analysis['raw_genotype'][gene]})")
    for row in analysis["recommendations"]:
        lines.append(f"- **{row['drug']}** [{row['action']}] {row['detail']} — [{row['guideline']}]({row['source']})")
    lines.extend(analysis.get("assessment_notes", []))
    requested = next((lang for lang in SUPPORTED_LANGUAGES if lang.lower() in question.lower().split()), language)
    lines.append(generate_rule_narrative(analysis, requested)["local_explanation"])
    return "\n\n".join(lines)
