"""Exercise the callbacks wired to the Gradio bedside and Q&A pages."""

from pathlib import Path

import pytest


@pytest.fixture
def app_module(monkeypatch):
    # Test the local app without requiring a workstation proxy or a live API.
    for scheme in ("all", "http", "https"):
        for name in (f"{scheme}_proxy", f"{scheme.upper()}_PROXY"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GRADIO_ANALYTICS_ENABLED", "False")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import app

    return app


@pytest.mark.parametrize("patient,drug,source,actions", [
    ("Rajesh", "CLOPIDOGREL", "synthetic_vcf", ["AVOID"]),
    ("Priya", "TAMOXIFEN", "synthetic_vcf_plus_lab", ["AVOID"]),
    ("Arjun", "SIMVASTATIN", "synthetic_vcf", ["AVOID", "CAUTION"]),
])
def test_bundled_demo_callbacks_generate_report_and_pdf(app_module, patient, drug, source, actions):
    name = next(name for name in app_module.DEMO_PATIENTS if name.startswith(patient))
    *fields, vcf, medications, context = app_module.load_demo(name)
    _, card, recs, _, _, logs, report, pdf = app_module.run_bedside_scan(
        None, vcf, name, *fields, "தமிழ் Tamil", medications, context,
    )
    try:
        assert report["data_source"] == source
        assert report["recommendations"][0]["drug"] == drug
        assert [r["action"] for r in report["recommendations"]] == actions
        assert drug in recs
        assert report["narrative"]["local_explanation"].splitlines()[0] in card
        assert Path(pdf).read_bytes().startswith(b"%PDF-")
        if patient == "Priya":
            assert "synthetic lab result with confirmed copy number" in logs
        history, text = app_module.chat_ask(f"Why {drug}?", None, report, "தமிழ் Tamil")
        assert [entry["role"] for entry in history] == ["user", "assistant"]
        assert f"**{drug}** [AVOID]" in history[-1]["content"]
        assert text == ""
    finally:
        if pdf:
            Path(pdf).unlink(missing_ok=True)


def test_malformed_upload_clears_result_and_cannot_fall_back_to_manual(app_module, tmp_path):
    bad = tmp_path / "malformed.vcf"
    bad.write_text("bad VCF")
    scan = app_module.run_bedside_scan(
        None, str(bad), app_module.JIPMER_DEMO, "Synthetic", "TEST", 50, "Other", "test",
        "*2/*2", "Not tested", "Not tested", "Not tested", "Not tested", "English",
        ["clopidogrel"], "acs_pci",
    )
    assert scan[-2:] == (None, None)
    assert "Malformed VCF" in scan[1]


def test_uploaded_priya_vcf_stays_indeterminate_without_demo_selection(app_module):
    vcf = str(Path("data/samples/priya_tamoxifen.vcf").resolve())
    scan = app_module.run_bedside_scan(
        None, vcf, "Select demo case...", "Synthetic", "TEST", 50, "Other", "test",
        "Not tested", "*4/*4", "Not tested", "Not tested", "Not tested", "English",
        ["tamoxifen"], "early_stage_er_positive",
    )
    report, pdf = scan[-2:]
    try:
        assert report["data_source"] == "vcf"
        assert report["phenotypes"]["CYP2D6"] == "Indeterminate"
        assert report["recommendations"] == []
    finally:
        if pdf:
            Path(pdf).unlink(missing_ok=True)
