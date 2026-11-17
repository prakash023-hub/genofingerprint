"""
GenoFingerprint AI — Bedside pharmacogenomics device demo.
VCF upload · Fingerprint scan · CPIC RAG Q&A · LangGraph pipeline
"""

from __future__ import annotations

import base64
import os
import sys
import tempfile
import html
from pathlib import Path

import gradio as gr

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from agents.pipeline import run_analysis
from agents.claude_narrator import generate_narrative_safe
from agents.qa_agent import ask_clinical_question
from data.cpic_knowledge import GUIDELINES, VARIANTS
from data.snp_reference import DEMO_SCENARIOS
from data.vcf_parser import VCFValidationError, parse_demo_file, parse_vcf_file
from export.pdf_report import build_report_pdf
from ui.render import (
    DISCLAIMER,
    render_fingerprint_card,
    render_recommendations,
    render_vcf_log,
    scanner_active_html,
    scanner_idle_html,
)

from data.i18n_fallback import LANGUAGE_LABELS, SUPPORTED_LANGUAGES

SAMPLES_DIR = os.path.join(ROOT, "data", "samples")
LANG_CHOICES = [LANGUAGE_LABELS[l] for l in SUPPORTED_LANGUAGES]
LANG_MAP = {LANGUAGE_LABELS[l]: l for l in SUPPORTED_LANGUAGES}

JIPMER_DEMO = "Rajesh Kumar — Post-Stent (VCF)"

DEMO_PATIENTS = {
    JIPMER_DEMO: {
        "vcf": "rajesh_post_stent.vcf",
        "patient_id": "PT001",
        "patient_name": "Rajesh Kumar",
        "age": 58,
        "gender": "Male",
        "indication": "ACS requiring clopidogrel after stent placement",
    },
    "Priya Sharma — Breast Cancer (VCF)": {
        "vcf": "priya_tamoxifen.vcf",
        "patient_id": "PT002",
        "patient_name": "Priya Sharma",
        "age": 45,
        "gender": "Female",
        "indication": "Breast cancer requiring tamoxifen",
    },
    "Arjun Patel — Statin (VCF)": {
        "vcf": "arjun_statin.vcf",
        "patient_id": "PT003",
        "patient_name": "Arjun Patel",
        "age": 62,
        "gender": "Male",
        "indication": "Cardiac patient on statin therapy for hyperlipidemia",
    },
}

GENE_VARIANTS = {gene: list(variants) for gene, variants in VARIANTS.items()}
GENE_VARIANTS["CYP2D6"].append("*1/*1x2")
CONTEXT_CHOICES = [
    ("Other or unspecified", ""),
    ("Acute coronary syndrome or PCI", "acs_pci"),
    ("Adjuvant treatment of early-stage ER-positive breast cancer", "early_stage_er_positive"),
]

SAMPLE_VCFS = [
    os.path.join(SAMPLES_DIR, "rajesh_post_stent.vcf"),
    os.path.join(SAMPLES_DIR, "priya_tamoxifen.vcf"),
    os.path.join(SAMPLES_DIR, "arjun_statin.vcf"),
]

CSS = """
.gradio-container { max-width: 1320px !important; background: #030712 !important; }
footer { display: none !important; }
.dark input, .dark textarea, .dark select { background: #0f172a !important; color: #e2e8f0 !important; }
h1, h2, h3, h4, label, p, span, .markdown, .prose { color: #e2e8f0 !important; }
.tab-nav button { font-weight: 600 !important; font-size: 14px !important; color: #94a3b8 !important; }
.tab-nav button.selected { color: #22d3ee !important; border-color: #22d3ee !important; }
button.primary { background: linear-gradient(135deg,#0284c7,#06b6d4) !important; border: none !important; font-weight: 700 !important; }
.block { border-color: #1e293b !important; }
.contain { background: #0f172a !important; border: 1px solid #1e293b !important; border-radius: 12px !important; }
"""

CHAT_WELCOME = [{
    "role": "assistant",
    "content": "Ask about a supported medication or gene to see its guideline. Run a scan to see recorded findings.",
}]


def _fingerprint_b64(path) -> str | None:
    if not path:
        return None
    p = path if isinstance(path, str) else getattr(path, "name", None)
    if not p or not os.path.isfile(p):
        return None
    try:
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return None


def load_demo(name):
    if not name or name.startswith("Select"):
        return (
            "", "", 0, "Male", "", "Not tested", "Not tested", "Not tested", "Not tested", "Not tested",
            None, [], "",
        )
    p = DEMO_PATIENTS.get(name, {})
    scenario = DEMO_SCENARIOS.get(p.get("patient_id"), {})
    vcf_path = os.path.join(SAMPLES_DIR, p["vcf"]) if p.get("vcf") else None
    return (
        p.get("patient_name", ""),
        p.get("patient_id", ""),
        p.get("age", 0),
        p.get("gender", "Male"),
        p.get("indication", ""),
        "Not tested",
        "Not tested",
        "Not tested",
        "Not tested",
        "Not tested",
        vcf_path if vcf_path and os.path.isfile(vcf_path) else None,
        scenario.get("medications", []),
        scenario.get("clinical_context", ""),
    )


def run_jipmer_demo():
    loaded = load_demo(JIPMER_DEMO)
    return (JIPMER_DEMO,) + loaded


def _resolve_vcf_path(vcf_file, demo_name):
    if vcf_file is not None:
        path = vcf_file if isinstance(vcf_file, str) else getattr(vcf_file, "name", None)
        if path and os.path.isfile(path):
            return path
        raise VCFValidationError("The uploaded VCF is unavailable.")
    if demo_name and not demo_name.startswith("Select"):
        p = DEMO_PATIENTS.get(demo_name, {})
        if p.get("vcf"):
            path = os.path.join(SAMPLES_DIR, p["vcf"])
            if os.path.isfile(path):
                return path
    return None


def _genotype_from_dropdowns(cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9):
    genotype = {}
    mapping = {
        "CYP2C19": cyp2c19,
        "CYP2D6": cyp2d6,
        "SLCO1B1": slco1b1,
        "TPMT": tpmt,
        "CYP2C9": cyp2c9,
    }
    for gene, val in mapping.items():
        if val and val != "Not tested":
            genotype[gene] = val
    return genotype


def run_bedside_scan(
    fingerprint_img,
    vcf_file,
    demo_name,
    patient_name,
    patient_id,
    age,
    gender,
    indication,
    cyp2c19,
    cyp2d6,
    slco1b1,
    tpmt,
    cyp2c9,
    report_language,
    medications=None,
    clinical_context="",
):
    try:
        logs: list[str] = []
        genotype = {}
        meta = {}
        data_source = "manual"

        vcf_path = _resolve_vcf_path(vcf_file, demo_name)
        if vcf_path:
            demo = DEMO_PATIENTS.get(demo_name)
            bundled = Path(SAMPLES_DIR, demo["vcf"]) if demo else None
            # Gradio can copy a bundled file into its cache. Compare bounded bytes.
            if bundled and os.path.getsize(vcf_path) == bundled.stat().st_size and (
                Path(vcf_path).read_bytes() == bundled.read_bytes()
            ):
                genotype, meta, logs = parse_demo_file(bundled, demo["patient_id"])
                data_source = "synthetic_vcf_plus_lab" if meta.get("confirmed_genotype") else "synthetic_vcf"
            else:
                genotype, meta, logs = parse_vcf_file(vcf_path)
                data_source = "vcf"
        else:
            genotype = _genotype_from_dropdowns(cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9)
            if genotype:
                logs.append("Manually entered diplotypes should come from a characterized lab result.")

        if not genotype:
            return (
                scanner_idle_html(),
                "<div style='color:#f87171;padding:16px;'>Upload a synthetic VCF, select a demo or enter a lab-characterized diplotype.</div>",
                "", "", DISCLAIMER, render_vcf_log(logs), None, None,
            )

        fp_b64 = _fingerprint_b64(fingerprint_img)
        biometric = fp_b64 is not None
        if biometric:
            logs.append("Fingerprint image captured (demo only — no biometric matching performed).")

        patient_data = {
            "patient_id": meta.get("patient_id") or patient_id or "PT-DEMO",
            "patient_name": meta.get("patient_name") or patient_name or "Anonymous",
            "age": int(meta.get("age") or age or 0),
            "gender": meta.get("gender") or gender or "Unknown",
            "indication": meta.get("indication") or indication or "Pharmacogenomics screening",
            "genotype": genotype,
            "data_source": data_source,
            "medications": meta.get("medications", []) if medications is None else medications,
            "clinical_context": clinical_context or (meta.get("clinical_context", "") if medications is None else ""),
        }

        result = run_analysis(patient_data)
        if not result["report_ready"]:
            raise VCFValidationError(result["error"])
        lang = LANG_MAP.get(report_language, "English")
        narrative = generate_narrative_safe(result, lang)
        result["narrative"] = narrative
        result["report_language"] = lang

        scanner = scanner_active_html(
            patient_data["patient_name"], result["fingerprint_id"], biometric, fp_b64
        )
        fp_html = render_fingerprint_card(result, narrative)
        rec_html = render_recommendations(result["recommendations"], result["assessment_notes"])
        pop_html = ""

        pdf_path = None
        try:
            pdf_bytes = build_report_pdf(result, narrative)
            fd, pdf_path = tempfile.mkstemp(suffix=".pdf", prefix="genofingerprint_")
            os.close(fd)
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
        except Exception:
            pdf_path = None

        if pdf_path is None:
            logs.append("PDF export failed. The on-screen report is available.")
        return scanner, fp_html, rec_html, pop_html, DISCLAIMER, render_vcf_log(logs), result, pdf_path

    except Exception as exc:
        message = str(exc) if isinstance(exc, VCFValidationError) else "Unable to complete this scan."
        return (
            scanner_idle_html(),
            f"<div style='color:#f87171;padding:16px;'>Error: {html.escape(message)}</div>",
            "", "", DISCLAIMER, "", None, None,
        )


def chat_ask(message, history, analysis_state, report_language):
    if not message.strip():
        return history, ""
    lang = LANG_MAP.get(report_language, "English")
    answer = ask_clinical_question(message, analysis_state, lang)
    history = (history or []) + [{"role": "user", "content": message}, {"role": "assistant", "content": answer}]
    return history, ""


with gr.Blocks(title="GenoFingerprint AI", css=CSS, theme=gr.themes.Base(primary_hue="cyan")) as app:
    analysis_state = gr.State(None)

    gr.HTML("""
    <div style="text-align:center;padding:28px 0 12px;">
        <div style="font-size:10px;letter-spacing:5px;color:#00d4ff;font-weight:600;">GLOBAL CPIC · MULTI-LANGUAGE · CLINICIAN-FIRST</div>
        <div style="font-size:40px;font-weight:900;background:linear-gradient(90deg,#22d3ee,#818cf8);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;">🧬 GenoFingerprint AI</div>
        <div style="font-size:14px;color:#94a3b8;max-width:780px;margin:8px auto 0;">
            Bedside pharmacogenomics · Single-sample GRCh38 research panel · CPIC rules · Doctor + patient reports in 8 languages</div>
    </div>""")

    with gr.Tabs():
        with gr.Tab("🔬 Bedside Device"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🌍 Report language")
                    report_lang = gr.Dropdown(
                        choices=LANG_CHOICES,
                        value=LANG_CHOICES[0],
                        label="Patient explanation language (doctor summary stays English)",
                    )

                    gr.Markdown("### ⚡ Quick demo")
                    jipmer_btn = gr.Button("▶ Run Rajesh Post-Stent Case", variant="secondary", size="lg")

                    gr.Markdown("### Step 1 — Research VCF\nUse synthetic files, names and images.")
                    demo_dd = gr.Dropdown(
                        choices=["Select demo case..."] + list(DEMO_PATIENTS.keys()),
                        label="Demo cases (auto-loads anonymized VCF)",
                        value="Select demo case...",
                    )
                    vcf_upload = gr.File(
                        label="Or upload a synthetic research VCF",
                        file_types=[".vcf"],
                        type="filepath",
                    )
                    gr.File(
                        label="Download sample VCF files (research / anonymized)",
                        value=SAMPLE_VCFS,
                        file_count="multiple",
                        interactive=False,
                    )

                    gr.Markdown("### Step 2 — Fingerprint scanner")
                    fingerprint_in = gr.Image(
                        label="Place finger on scanner (webcam or upload)",
                        type="filepath",
                        sources=["upload", "webcam"],
                        height=160,
                    )

                    gr.Markdown("### Step 3 — Patient (auto-filled for demo cases)")
                    pname = gr.Textbox(label="Patient Name")
                    with gr.Row():
                        pid = gr.Textbox(label="Patient ID")
                        page = gr.Number(label="Age", value=0)
                    pgender = gr.Radio(["Male", "Female", "Other"], label="Gender", value="Male")
                    pind = gr.Textbox(label="Clinical Indication", lines=2)

                    meds = gr.Dropdown(list(GUIDELINES), multiselect=True, value=[], label="Medications to assess")
                    context = gr.Dropdown(CONTEXT_CHOICES, value="", label="Guideline context")
                    with gr.Accordion("Lab-confirmed diplotypes (used without a VCF)", open=False):
                        cyp2c19 = gr.Dropdown(["Not tested"] + GENE_VARIANTS["CYP2C19"], label="CYP2C19", value="Not tested")
                        cyp2d6 = gr.Dropdown(["Not tested"] + GENE_VARIANTS["CYP2D6"], label="CYP2D6", value="Not tested")
                        slco1b1 = gr.Dropdown(["Not tested"] + GENE_VARIANTS["SLCO1B1"], label="SLCO1B1", value="Not tested")
                        tpmt = gr.Dropdown(["Not tested"] + GENE_VARIANTS["TPMT"], label="TPMT", value="Not tested")
                        cyp2c9 = gr.Dropdown(["Not tested"] + GENE_VARIANTS["CYP2C9"], label="CYP2C9", value="Not tested")

                    scan_btn = gr.Button("🧬 SCAN — Decode Genomic Fingerprint", variant="primary", size="lg")

                with gr.Column(scale=2):
                    scanner_status = gr.HTML(scanner_idle_html())
                    fingerprint_out = gr.HTML()
                    recs_out = gr.HTML()
                    pop_out = gr.HTML()
                    vcf_log_out = gr.HTML()
                    pdf_out = gr.File(label="Download PDF report (clinician)", interactive=False)
                    disc_out = gr.HTML(DISCLAIMER)

        with gr.Tab("💬 Clinical Q&A (RAG Agent)"):
            gr.HTML("""
            <div style="background:#0f172a;border:1px solid #334155;border-radius:12px;padding:14px;margin-bottom:12px;">
              <div style="color:#22d3ee;font-weight:700;font-size:13px;">CLINICAL Q&A AGENT</div>
              <div style="color:#94a3b8;font-size:13px;margin-top:6px;">
                Ask CPIC / pharmacogenomics questions. Run a <b>Bedside scan</b> first for patient-specific answers.
              </div>
            </div>""")
            chatbot = gr.Chatbot(label="Clinical Assistant", height=440, value=CHAT_WELCOME, type="messages")
            with gr.Row():
                chat_in = gr.Textbox(
                    label="Question",
                    placeholder="Why avoid clopidogrel? CPIC alternative? Patient summary in Hindi?",
                    scale=4,
                )
                chat_btn = gr.Button("Ask", variant="primary", scale=1)
            gr.Examples(
                examples=[
                    "Why should this patient avoid clopidogrel?",
                    "What alternative antiplatelet does CPIC recommend for CYP2C19 poor metabolizers?",
                    "Show the CYP2C19 and clopidogrel guideline.",
                    "Is this tool CDSCO approved?",
                    "Summarize risks in Spanish for the patient.",
                ],
                inputs=chat_in,
            )

    jipmer_btn.click(
        run_jipmer_demo,
        outputs=[demo_dd, pname, pid, page, pgender, pind, cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9, vcf_upload, meds, context],
    ).then(
        run_bedside_scan,
        inputs=[fingerprint_in, vcf_upload, demo_dd, pname, pid, page, pgender, pind, cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9, report_lang, meds, context],
        outputs=[scanner_status, fingerprint_out, recs_out, pop_out, disc_out, vcf_log_out, analysis_state, pdf_out],
    )

    demo_dd.change(
        load_demo,
        inputs=[demo_dd],
        outputs=[pname, pid, page, pgender, pind, cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9, vcf_upload, meds, context],
    )

    scan_btn.click(
        run_bedside_scan,
        inputs=[
            fingerprint_in, vcf_upload, demo_dd, pname, pid, page, pgender, pind,
            cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9, report_lang, meds, context,
        ],
        outputs=[scanner_status, fingerprint_out, recs_out, pop_out, disc_out, vcf_log_out, analysis_state, pdf_out],
    )

    chat_btn.click(chat_ask, inputs=[chat_in, chatbot, analysis_state, report_lang], outputs=[chatbot, chat_in])
    chat_in.submit(chat_ask, inputs=[chat_in, chatbot, analysis_state, report_lang], outputs=[chatbot, chat_in])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("GRADIO_SERVER_PORT", "7860")))
    app.launch(server_name="0.0.0.0", server_port=port)
