"""Export CPIC report as PDF for clinical sharing."""

from __future__ import annotations

import io
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def build_report_pdf(result: dict, narrative: Optional[dict] = None) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 2 * cm
    narrative = narrative or {}

    def line(text: str, size: int = 11, bold: bool = False):
        nonlocal y
        if y < 2 * cm:
            c.showPage()
            y = h - 2 * cm
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        safe = text.encode("latin-1", errors="replace").decode("latin-1")
        for chunk in _wrap(safe, 90):
            c.drawString(2 * cm, y, chunk)
            y -= size * 0.5

    line("GenoFingerprint AI — Pharmacogenomics Report", 16, True)
    line(f"Fingerprint ID: {result.get('fingerprint_id', '')}", 12, True)
    line(f"Patient: {result.get('patient_name')} | {result.get('age')}Y {result.get('gender')}")
    line(f"Indication: {result.get('indication', '')}")
    line(f"Data source: {result.get('data_source', 'manual')}")
    y -= 0.3 * cm

    line("Genomic profile:", 12, True)
    for gene, variant in result.get("raw_genotype", {}).items():
        pheno = result.get("phenotypes", {}).get(gene, "?")
        line(f"  {gene}: {variant} -> {pheno}")

    y -= 0.2 * cm
    line("CPIC drug recommendations:", 12, True)
    for rec in result.get("recommendations", []):
        line(f"  {rec['drug']} — {rec['action']} ({rec['risk']}): {rec['detail']}")

    if narrative.get("critical_alert"):
        y -= 0.2 * cm
        line("Critical alert:", 12, True)
        line(narrative["critical_alert"])

    if narrative.get("doctor_summary"):
        y -= 0.2 * cm
        line("Clinical summary (English):", 12, True)
        line(narrative["doctor_summary"])

    if narrative.get("patient_explanation"):
        y -= 0.2 * cm
        line("Patient explanation (English):", 12, True)
        line(narrative["patient_explanation"])

    lang = narrative.get("language", "English")
    local = narrative.get("local_explanation") or narrative.get("tamil_explanation")
    if local and lang != "English":
        y -= 0.2 * cm
        line(f"Patient explanation ({lang}):", 12, True)
        line(local)

    line("", 8)
    line("DISCLAIMER: CPIC decision support only. Not CDSCO/FDA approved. Clinician must confirm.", 9)
    line("CPIC guidelines · GenoFingerprint AI · Prakash Raj K, M.Pharm", 9)

    c.save()
    return buf.getvalue()


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = f"{cur} {w}".strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]
