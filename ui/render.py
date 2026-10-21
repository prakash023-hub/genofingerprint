"""HTML render helpers for GenoFingerprint bedside device UI."""

from __future__ import annotations

import datetime
import html
from typing import Optional


def scanner_idle_html() -> str:
    return """
    <div style="text-align:center;padding:32px;background:linear-gradient(180deg,#0a1628 0%,#050810 100%);
         border:2px dashed #334155;border-radius:24px;min-height:220px;">
        <div style="width:100px;height:100px;margin:0 auto 16px;border-radius:50%;
             border:3px solid #1e293b;display:flex;align-items:center;justify-content:center;
             background:radial-gradient(circle,#0f172a,#020617);">
            <span style="font-size:44px;opacity:0.5;">👆</span>
        </div>
        <div style="color:#00d4ff;font-size:13px;letter-spacing:4px;font-weight:700;">GENOFINGERPRINT POC</div>
        <div style="color:#64748b;font-size:13px;margin-top:10px;">Place finger · Upload VCF · Tap SCAN</div>
        <div style="color:#475569;font-size:11px;margin-top:6px;">CPIC panel · 5 genes · global + regional allele context</div>
    </div>"""


def scanner_active_html(
    patient_name: str,
    fp_id: str,
    biometric: bool,
    fingerprint_b64: Optional[str] = None,
) -> str:
    bio = "✓ FINGERPRINT IMAGE CAPTURED (DEMO)" if biometric else "DEMO MODE — NO FINGERPRINT"
    bio_color = "#22c55e" if biometric else "#f59e0b"

    fp_img = ""
    if biometric and fingerprint_b64:
        fp_img = f"""
        <div style="margin:12px auto;width:90px;height:90px;border-radius:12px;overflow:hidden;
             border:2px solid #00d4ff;box-shadow:0 0 20px rgba(0,212,255,0.4);">
            <img src="data:image/png;base64,{fingerprint_b64}" style="width:100%;height:100%;object-fit:cover;"
                 alt="fingerprint"/>
        </div>"""

    return f"""
    <div style="text-align:center;padding:28px;background:linear-gradient(180deg,#0f2027,#1a3a4a);
         border:2px solid #00d4ff;border-radius:24px;box-shadow:0 0 48px rgba(0,212,255,0.35);">
        <div style="font-size:10px;color:{bio_color};letter-spacing:2px;font-weight:700;margin-bottom:10px;">{bio}</div>
        {fp_img}
        <div style="font-size:40px;margin:8px 0;">🧬</div>
        <div style="color:#fff;font-size:24px;font-weight:800;letter-spacing:3px;font-family:monospace;">{fp_id}</div>
        <div style="color:#00d4ff;font-size:15px;margin-top:10px;font-weight:600;">{html.escape(patient_name)}</div>
        <div style="color:#94a3b8;font-size:12px;margin-top:6px;">Decoded {datetime.datetime.now().strftime('%d %b %Y · %H:%M:%S')}</div>
        <div style="margin-top:14px;padding:8px 16px;background:rgba(0,212,255,0.1);border-radius:8px;
             display:inline-block;font-size:11px;color:#67e8f9;">DEVICE READY · REPORT ON SCREEN</div>
    </div>"""


def render_fingerprint_card(result: dict, narrative: dict) -> str:
    critical_banner = ""
    if result["summary"].get("critical_alert"):
        critical_banner = (
            "<div style='background:rgba(255,50,50,0.3);border:2px solid #ff3232;border-radius:8px;"
            "padding:10px;margin-top:12px;text-align:center;font-weight:bold;color:#ff6b6b;'>"
            "⚠️ CRITICAL ALERT: HIGH-RISK DRUG INTERACTION DETECTED</div>"
        )

    gene_tags = "".join(
        f'<span style="background:rgba(0,212,255,0.12);border:1px solid #00d4ff;border-radius:6px;'
        f'padding:5px 12px;font-size:12px;margin:4px;display:inline-block;"><b>{gene}</b>: '
        f"{html.escape(str(variant))} → {html.escape(result['phenotypes'].get(gene, '?'))}</span>"
        for gene, variant in result["raw_genotype"].items()
    )

    vcf_badge = ""
    if result.get("data_source") == "vcf":
        vcf_badge = (
            "<span style='background:#22c55e;color:#000;padding:3px 10px;border-radius:6px;"
            "font-size:10px;font-weight:700;margin-left:8px;'>✓ LAB VCF</span>"
        )

    alert_html = ""
    if narrative.get("critical_alert"):
        alert_html = (
            f"<div style='background:rgba(255,50,50,0.2);border:2px solid #ff3232;border-radius:10px;"
            f"padding:14px;color:#ff6b6b;font-weight:bold;font-size:15px;margin-top:16px;'>"
            f"🚨 {html.escape(narrative['critical_alert'])}</div>"
        )

    return f"""
    <div style="background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);border-radius:16px;padding:24px;
         color:white;font-family:system-ui,sans-serif;border:2px solid #00d4ff;
         box-shadow:0 0 30px rgba(0,212,255,0.25);">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <div style="font-size:11px;color:#00d4ff;letter-spacing:3px;">GENOMIC FINGERPRINT {vcf_badge}</div>
                <div style="font-size:32px;font-weight:bold;letter-spacing:3px;font-family:monospace;">{result['fingerprint_id']}</div>
            </div>
            <div style="text-align:right;font-size:12px;color:#aaa;">
                {datetime.datetime.now().strftime('%d %b %Y %H:%M')}
            </div>
        </div>
        <div style="margin:14px 0;font-size:16px;font-weight:600;">{html.escape(result['patient_name'])} · {result['age']}Y {html.escape(result['gender'])}</div>
        <div style="font-size:13px;color:#cbd5e1;margin-bottom:12px;">{html.escape(result['indication'])}</div>
        <div style="margin-bottom:16px;">{gene_tags}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
            <div style="background:rgba(255,50,50,0.2);border:1px solid #ff3232;border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:28px;font-weight:bold;color:#ff6b6b;">{result['summary']['high_risk']}</div>
                <div style="font-size:10px;color:#aaa;">HIGH RISK</div>
            </div>
            <div style="background:rgba(255,165,0,0.2);border:1px solid #ffa500;border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:28px;font-weight:bold;color:#ffa500;">{result['summary']['moderate_risk']}</div>
                <div style="font-size:10px;color:#aaa;">MODERATE</div>
            </div>
            <div style="background:rgba(0,255,100,0.2);border:1px solid #00ff64;border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:28px;font-weight:bold;color:#00ff64;">{result['summary']['low_risk']}</div>
                <div style="font-size:10px;color:#aaa;">LOW RISK</div>
            </div>
        </div>
        {critical_banner}
        {alert_html}
        <div style="margin-top:16px;display:flex;flex-direction:column;gap:10px;">
            <div style="background:#0f2027;border:1px solid #00d4ff;border-radius:10px;padding:14px;">
                <div style="font-size:11px;color:#00d4ff;letter-spacing:2px;margin-bottom:6px;">🩺 AI CLINICAL SUMMARY</div>
                <div style="font-size:14px;color:#e5e7eb;line-height:1.6;">{html.escape(narrative.get('doctor_summary',''))}</div>
            </div>
            <div style="background:#0f2027;border:1px solid #22c55e;border-radius:10px;padding:14px;">
                <div style="font-size:11px;color:#22c55e;letter-spacing:2px;margin-bottom:6px;">👤 PATIENT EXPLANATION</div>
                <div style="font-size:14px;color:#e5e7eb;line-height:1.6;">{html.escape(narrative.get('patient_explanation',''))}</div>
            </div>
            <div style="background:#0f2027;border:1px solid #f59e0b;border-radius:10px;padding:14px;">
                <div style="font-size:11px;color:#f59e0b;letter-spacing:2px;margin-bottom:6px;">🌍 PATIENT — {html.escape(narrative.get('language', 'English'))}</div>
                <div style="font-size:14px;color:#e5e7eb;line-height:1.8;">{html.escape(narrative.get('local_explanation') or narrative.get('tamil_explanation', ''))}</div>
            </div>
        </div>
    </div>"""


def render_recommendations(recommendations: list) -> str:
    colors = {
        "AVOID": ("#ff3232", "#2a0000", "🚫"),
        "CAUTION": ("#ffa500", "#2a1a00", "⚠️"),
        "USE": ("#00ff64", "#002a10", "✅"),
    }
    html_out = "<div style='display:flex;flex-direction:column;gap:12px;margin-top:12px;'>"
    for rec in recommendations:
        color, bg, icon = colors.get(rec["action"], ("#aaa", "#111", "ℹ️"))
        html_out += f"""
        <div style="background:{bg};border:1px solid {color};border-radius:10px;padding:16px;border-left:4px solid {color};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <div style="font-size:18px;font-weight:bold;color:{color};">{icon} {rec['drug']}</div>
                <span style="background:{color};color:#000;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:bold;">{rec['action']}</span>
            </div>
            <div style="font-size:13px;color:#ddd;margin-bottom:6px;"><b>Gene:</b> {rec['gene']} | <b>Variant:</b> {html.escape(str(rec['variant']))} | <b>Phenotype:</b> {html.escape(rec['phenotype'])}</div>
            <div style="font-size:14px;color:#fff;margin-bottom:6px;">📋 {html.escape(rec['detail'])}</div>
            <div style="font-size:12px;color:#aaa;">🔬 {html.escape(rec['rationale'])}</div>
        </div>"""
    html_out += "</div>"
    return html_out


def render_population_notes(notes: list) -> str:
    html_out = "<div style='background:#1a1a2e;border-radius:10px;padding:16px;margin-top:12px;'>"
    html_out += "<div style='font-size:14px;font-weight:bold;color:#00d4ff;margin-bottom:10px;'>🌍 Global Population Context (CPIC / gnomAD)</div>"
    for note in notes:
        html_out += f"<div style='font-size:13px;color:#ddd;margin-bottom:6px;'>• {html.escape(note)}</div>"
    html_out += (
        "<div style='font-size:11px;color:#aaa;margin-top:10px;'>"
        "Reference frequencies help clinicians interpret phenotype prevalence across regions. "
        "Patient-specific decisions use this individual's VCF only.</div></div>"
    )
    return html_out


def render_vcf_log(logs: list) -> str:
    if not logs:
        return ""
    items = "".join(
        f"<div style='font-size:11px;color:#9ca3af;font-family:monospace;'>› {html.escape(l)}</div>"
        for l in logs[-10:]
    )
    return (
        f"<div style='background:#0f172a;border:1px solid #334155;border-radius:8px;padding:12px;margin-top:12px;'>"
        f"<div style='font-size:10px;color:#00d4ff;letter-spacing:2px;margin-bottom:6px;'>VCF PIPELINE LOG</div>{items}</div>"
    )


DISCLAIMER = """
<div style='background:#1a1000;border:1px solid #664400;border-radius:8px;padding:12px;margin-top:12px;'>
<div style='font-size:12px;color:#ffaa44;'>⚕️ <b>CLINICAL DISCLAIMER:</b> GenoFingerprint AI is CPIC-based decision SUPPORT only.
Final prescribing is by a qualified clinician. Not CDSCO/FDA approved. Demo uses anonymized research VCF files.</div></div>"""
