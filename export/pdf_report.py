"""Clinician research PDF. Local patient text renders where the font supports it."""

from __future__ import annotations

import io
from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


def build_report_pdf(result: dict, narrative: dict | None = None) -> bytes:
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin = 2 * cm
    y = height - margin
    narrative = narrative or {}

    def line(text: str, size: int = 11, bold: bool = False):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        safe = text.encode("cp1252", errors="replace").decode("cp1252")
        for paragraph in safe.splitlines() or [""]:
            # Start with a character bound, then measure to handle wide glyphs.
            pending = wrap(paragraph, 88) or [""]
            while pending:
                chunk = pending.pop(0)
                end = len(chunk)
                while stringWidth(chunk[:end], font, size) > width - 2 * margin:
                    end -= 1
                if end < len(chunk):
                    split = chunk.rfind(" ", 0, end)
                    end = split if split > 0 else end
                    pending.insert(0, chunk[end:].lstrip())
                if y < margin:
                    pdf.showPage()
                    y = height - margin
                pdf.setFont(font, size)
                pdf.drawString(margin, y, chunk[:end])
                y -= size * 1.25

    line("GenoFingerprint AI — Research pharmacogenomics report", 16, True)
    line("Research and education only. Review findings with a qualified clinician.", 10)
    line(f"Report ID: {result.get('fingerprint_id', '')}", 12, True)
    line(f"Patient: {result.get('patient_name')} | {result.get('age')}Y {result.get('gender')}")
    line(f"Indication: {result.get('indication', '')}")
    line(f"Data source: {result.get('data_source', 'manual')}")
    line(f"Guideline context: {result.get('clinical_context') or 'unspecified'}")

    line("Panel findings", 12, True)
    for gene, variant in result.get("raw_genotype", {}).items():
        phenotype = result.get("phenotypes", {}).get(gene, "Indeterminate")
        line(f"{gene}: {variant} — {phenotype}")
    line("Guideline assessment", 12, True)
    for rec in result.get("recommendations", []):
        line(f"{rec['drug']} [{rec['action']}] ({rec['risk']}): {rec['detail']}")
        line(f"{rec['guideline']} — {rec['source']}", 9)
    for note in result.get("assessment_notes", []):
        line(note)
    for label, field in (
        ("High-priority findings", "critical_alert"),
        ("Clinical summary", "doctor_summary"),
        ("Patient explanation (English)", "patient_explanation"),
    ):
        if narrative.get(field):
            line(label, 12, True)
            line(narrative[field])
    language = narrative.get("language", "English")
    local = narrative.get("local_explanation")
    if local and language != "English":
        try:
            local.encode("cp1252")
        except UnicodeEncodeError:
            line(f"Patient explanation ({language}) is available in the app. This PDF uses English for that text.")
        else:
            line(f"Patient explanation ({language})", 12, True)
            line(local)

    pdf.save()
    return buf.getvalue()
