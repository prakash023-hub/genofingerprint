#!/usr/bin/env python3
"""Regression evals for CPIC PGx engine — run before deploy."""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agents.pipeline import run_analysis
from agents.rule_narrator import generate_rule_narrative
from data.vcf_parser import parse_vcf_file


def load_cases():
    path = os.path.join(os.path.dirname(__file__), "golden_cases.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_evals() -> int:
    cases = load_cases()
    failures = []

    for case in cases:
        cid = case["id"]
        vcf_path = os.path.join(ROOT, case["vcf"])
        genotype, meta, _ = parse_vcf_file(vcf_path)
        patient = {**case["patient"], "genotype": genotype, "data_source": "vcf"}
        result = run_analysis(patient)
        narrative = generate_rule_narrative(result, "English")
        exp = case["expect"]

        for key, val in exp.items():
            if key.startswith("phenotype_"):
                gene = key.replace("phenotype_", "")
                got = result["phenotypes"].get(gene)
                if got != val:
                    failures.append(f"{cid}: {gene} phenotype {got!r} != {val!r}")
            elif key == "must_avoid":
                avoid_drugs = {r["drug"] for r in result["recommendations"] if r["action"] == "AVOID"}
                for drug in val:
                    if drug not in avoid_drugs:
                        failures.append(f"{cid}: expected AVOID {drug}, got {avoid_drugs}")
            elif key == "doctor_summary_contains":
                summary = narrative.get("doctor_summary", "")
                for token in val:
                    if token not in summary.upper() and token.lower() not in summary.lower():
                        failures.append(f"{cid}: doctor_summary missing {token}")

        print(f"PASS {cid} · {result['fingerprint_id']} · HIGH={result['summary']['high_risk']}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(" ", f)
        return 1

    print(f"\nAll {len(cases)} golden cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_evals())
