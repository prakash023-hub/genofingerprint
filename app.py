"""
GenoFingerprint AI — Bedside pharmacogenomics device demo.
VCF upload · Fingerprint scan · CPIC RAG Q&A · LangGraph pipeline
"""

from __future__ import annotations

import base64
import os
import sys
import tempfile
import traceback

import gradio as gr

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from agents.pipeline import run_analysis
from agents.claude_narrator import generate_narrative_safe
from agents.qa_agent import ask_clinical_question
from data.vcf_parser import parse_vcf_file
from export.pdf_report import build_report_pdf
from ui.render import (
    DISCLAIMER,
    render_fingerprint_card,
    render_population_notes,
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
        "genotype": {"CYP2C19": "*2/*2", "CYP2D6": "*1/*1", "SLCO1B1": "c.521TC", "CYP2C9": "*1/*3"},
    },
    "Priya Sharma — Breast Cancer (VCF)": {
        "vcf": "priya_tamoxifen.vcf",
        "patient_id": "PT002",
        "patient_name": "Priya Sharma",
        "age": 45,
        "gender": "Female",
        "indication": "Breast cancer requiring tamoxifen",
        "genotype": {"CYP2D6": "*4/*4", "CYP2C9": "*1/*1", "TPMT": "*1/*1"},
    },
    "Arjun Patel — Statin (VCF)": {
        "vcf": "arjun_statin.vcf",
        "patient_id": "PT003",
        "patient_name": "Arjun Patel",
        "age": 62,
        "gender": "Male",
        "indication": "Cardiac patient on statin therapy for hyperlipidemia",
        "genotype": {"SLCO1B1": "c.521CC", "CYP2C19": "*1/*17", "CYP2C9": "*1/*1"},
    },
}

GENE_VARIANTS = {
    "CYP2C19": ["*1/*1", "*1/*2", "*1/*3", "*2/*2", "*2/*3", "*3/*3", "*1/*17", "*17/*17"],
    "CYP2D6": ["*1/*1", "*1/*2", "*4/*4", "*4/*5", "*1/*4", "*1xN/*1"],
    "SLCO1B1": ["c.521TT", "c.521TC", "c.521CC"],
    "TPMT": ["*1/*1", "*1/*3A", "*3A/*3A", "*3C/*3C"],
    "CYP2C9": ["*1/*1", "*1/*2", "*1/*3", "*2/*3", "*3/*3"],
}

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

CHAT_WELCOME = [
    [
        "Welcome to GenoFingerprint Clinical Q&A",
        "**How to use:**\n1. Go to **Bedside Device** tab → click **Run Rajesh Post-Stent Case**\n2. Come back here and ask e.g. *Why avoid clopidogrel?*\n\nI'll answer using CPIC guidelines + that patient's scan data.",
    ]
]


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
            None,
        )
    p = DEMO_PATIENTS.get(name, {})
    g = p.get("genotype", {})
    vcf_path = os.path.join(SAMPLES_DIR, p["vcf"]) if p.get("vcf") else None
    return (
        p.get("patient_name", ""),
        p.get("patient_id", ""),
        p.get("age", 0),
        p.get("gender", "Male"),
        p.get("indication", ""),
        g.get("CYP2C19", "Not tested"),
        g.get("CYP2D6", "Not tested"),
        g.get("SLCO1B1", "Not tested"),
        g.get("TPMT", "Not tested"),
        g.get("CYP2C9", "Not tested"),
        vcf_path if vcf_path and os.path.isfile(vcf_path) else None,
    )


def run_jipmer_demo():
    loaded = load_demo(JIPMER_DEMO)
    return (JIPMER_DEMO,) + loaded


def _resolve_vcf_path(vcf_file, demo_name):
    if vcf_file is not None:
        path = vcf_file if isinstance(vcf_file, str) else getattr(vcf_file, "name", None)
        if path and os.path.isfile(path):
            return path
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
):
    try:
        logs: list[str] = []
        genotype = {}
        meta = {}
        data_source = "manual"

        vcf_path = _resolve_vcf_path(vcf_file, demo_name)
        if vcf_path:
            genotype, meta, logs = parse_vcf_file(vcf_path)
            data_source = "vcf"
            logs.insert(0, f"Lab VCF parsed: {os.path.basename(vcf_path)}")

        if not genotype:
            genotype = _genotype_from_dropdowns(cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9)

        if not genotype:
            return (
                scanner_idle_html(),
                "<div style='color:#f87171;padding:16px;'>⚠️ Upload a VCF or select a demo case, then SCAN.</div>",
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
        }

        result = run_analysis(patient_data)
        result["data_source"] = data_source
        lang = LANG_MAP.get(report_language, "English")
        narrative = generate_narrative_safe(result, lang)
        result["narrative"] = narrative
        result["report_language"] = lang

        scanner = scanner_active_html(
            patient_data["patient_name"], result["fingerprint_id"], biometric, fp_b64
        )
        fp_html = render_fingerprint_card(result, narrative)
        rec_html = render_recommendations(result["recommendations"])
        pop_html = render_population_notes(result.get("population_notes", []))

        pdf_path = None
        try:
            pdf_bytes = build_report_pdf(result, narrative)
            fd, pdf_path = tempfile.mkstemp(suffix=".pdf", prefix=f"genofingerprint_{result['fingerprint_id']}_")
            os.close(fd)
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
        except Exception:
            pdf_path = None

        return scanner, fp_html, rec_html, pop_html, DISCLAIMER, render_vcf_log(logs), result, pdf_path

    except Exception as e:
        return (
            scanner_idle_html(),
            f"<div style='color:#f87171;padding:16px;'>Error: {e}</div>",
            "", "", DISCLAIMER, "", None, None,
        )


def chat_ask(message, history, analysis_state, report_language):
    if not message.strip():
        return history, ""
    lang = LANG_MAP.get(report_language, "English")
    answer = ask_clinical_question(message, analysis_state, lang)
    history = history + [[message, answer]]
    return history, ""


def warmup_rag():
    from agents.rag_store import get_rag_collection
    get_rag_collection()


with gr.Blocks(title="GenoFingerprint AI", css=CSS, theme=gr.themes.Base(primary_hue="cyan")) as app:
    analysis_state = gr.State(None)

    gr.HTML("""
    <div style="text-align:center;padding:28px 0 12px;">
        <div style="font-size:10px;letter-spacing:5px;color:#00d4ff;font-weight:600;">GLOBAL CPIC · MULTI-LANGUAGE · CLINICIAN-FIRST</div>
        <div style="font-size:40px;font-weight:900;background:linear-gradient(90deg,#22d3ee,#818cf8);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;">🧬 GenoFingerprint AI</div>
        <div style="font-size:14px;color:#94a3b8;max-width:780px;margin:8px auto 0;">
            Bedside pharmacogenomics · Any lab VCF · CPIC rules · Doctor + patient reports in 8 languages</div>
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

                    gr.Markdown("### Step 1 — Lab VCF")
                    demo_dd = gr.Dropdown(
                        choices=["Select demo case..."] + list(DEMO_PATIENTS.keys()),
                        label="Demo cases (auto-loads anonymized VCF)",
                        value="Select demo case...",
                    )
                    vcf_upload = gr.File(
                        label="Or upload VCF from sequencing lab",
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

                    gr.Markdown("### Step 3 — Patient (auto-filled from VCF)")
                    pname = gr.Textbox(label="Patient Name")
                    with gr.Row():
                        pid = gr.Textbox(label="Patient ID")
                        page = gr.Number(label="Age", value=0)
                    pgender = gr.Radio(["Male", "Female", "Other"], label="Gender", value="Male")
                    pind = gr.Textbox(label="Clinical Indication", lines=2)

                    with gr.Accordion("Manual gene override", open=False):
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
            chatbot = gr.Chatbot(label="Clinical Assistant", height=440, value=CHAT_WELCOME)
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
                    "Explain CYP2C19 poor metabolizer prevalence globally vs South Asia.",
                    "Is this tool CDSCO approved?",
                    "Summarize risks in Spanish for the patient.",
                ],
                inputs=chat_in,
            )

    jipmer_btn.click(
        run_jipmer_demo,
        outputs=[demo_dd, pname, pid, page, pgender, pind, cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9, vcf_upload],
    ).then(
        run_bedside_scan,
        inputs=[fingerprint_in, vcf_upload, demo_dd, pname, pid, page, pgender, pind, cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9, report_lang],
        outputs=[scanner_status, fingerprint_out, recs_out, pop_out, disc_out, vcf_log_out, analysis_state, pdf_out],
    )

    demo_dd.change(
        load_demo,
        inputs=[demo_dd],
        outputs=[pname, pid, page, pgender, pind, cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9, vcf_upload],
    )

    scan_btn.click(
        run_bedside_scan,
        inputs=[
            fingerprint_in, vcf_upload, demo_dd, pname, pid, page, pgender, pind,
            cyp2c19, cyp2d6, slco1b1, tpmt, cyp2c9, report_lang,
        ],
        outputs=[scanner_status, fingerprint_out, recs_out, pop_out, disc_out, vcf_log_out, analysis_state, pdf_out],
    )

    chat_btn.click(chat_ask, inputs=[chat_in, chatbot, analysis_state, report_lang], outputs=[chatbot, chat_in])
    chat_in.submit(chat_ask, inputs=[chat_in, chatbot, analysis_state, report_lang], outputs=[chatbot, chat_in])

    app.load(warmup_rag)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("GRADIO_SERVER_PORT", "7860")))
    app.launch(server_name="0.0.0.0", server_port=port)
