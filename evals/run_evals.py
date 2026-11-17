#!/usr/bin/env python3
"""Run synthetic cases against the parser, pipeline and deterministic report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.pipeline import run_analysis
from data.vcf_parser import VCFValidationError, parse_demo_file, parse_vcf_file, parse_vcf_text


def load_cases():
    return json.loads(Path(__file__).with_name("golden_cases.json").read_text(encoding="utf-8"))


def evaluate_case(case: dict) -> None:
    patient = case["patient"].copy()
    expect = case["expect"]
    try:
        if case.get("use_synthetic_lab_result"):
            genotype, _, _ = parse_demo_file(ROOT / case["vcf"], patient["patient_id"])
            patient.update(genotype=genotype, data_source="synthetic_vcf_plus_lab")
        elif "vcf" in case or "vcf_text" in case:
            parsed = parse_vcf_file(ROOT / case["vcf"]) if "vcf" in case else parse_vcf_text(case["vcf_text"])
            patient.update(genotype=parsed[0], data_source="vcf")
    except VCFValidationError:
        assert expect.get("invalid_vcf"), "Unexpected VCF validation error"
        return
    assert not expect.get("invalid_vcf"), "Invalid VCF was accepted"

    result = run_analysis(patient)
    assert result["report_ready"], result["error"]
    for gene, phenotype in expect.get("phenotypes", {}).items():
        actual = result["phenotypes"].get(gene)
        assert actual == phenotype, f"{gene}: expected {phenotype!r}, got {actual!r}"
    actual = {
        row["drug"]: [row["gene"], row["action"], row["risk"]]
        for row in result["recommendations"]
    }
    assert len(actual) == len(result["recommendations"]), "Duplicate drug rows"
    assert actual == expect["recommendations"], f"Expected {expect['recommendations']!r}, got {actual!r}"
    for row in result["recommendations"]:
        assert row["guideline"] and row["source"].startswith("https://")
    for drug in expect.get("unassessed", []):
        assert any(note.startswith(f"{drug}:") for note in result["assessment_notes"]), f"Missing note for {drug}"


def run_evals() -> int:
    passed = failed = 0
    for case in load_cases():
        try:
            evaluate_case(case)
        except (AssertionError, ValueError, KeyError) as error:
            print(f"FAIL {case['id']}: {error}")
            failed += 1
        else:
            print(f"PASS {case['id']}")
            passed += 1
    print(f"\n{passed} passed, {failed} failed.")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(run_evals())
