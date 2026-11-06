"""
Regression tests for the star-allele caller and CPIC phenotype mapping.

These cover the genotype-calling bugs that the golden cases did not exercise:
a lone TPMT *3C allele, CYP2D6 *10/*41 decreased-function alleles, and the
ambiguous CYP2C19 *2/*17 diplotype. Run with: pytest -q
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from data.vcf_parser import parse_vcf_text  # noqa: E402
from agents.pipeline import run_analysis  # noqa: E402
from data.cpic_knowledge import CPIC_DATA  # noqa: E402

_HEADER = (
    "##fileformat=VCFv4.2\n"
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
)


def _vcf(rows: list[tuple[str, str]]) -> str:
    body = "\n".join(
        f"1\t1\t{rsid}\tA\tG\t99\tPASS\t.\tGT\t{gt}" for rsid, gt in rows
    )
    return _HEADER + body


def _genotype(rows: list[tuple[str, str]]) -> dict:
    genotype, _, _ = parse_vcf_text(_vcf(rows))
    return genotype


# ── TPMT *3C (the dangerous false-negative) ──────────────────────────

def test_tpmt_3c_heterozygous_is_not_called_normal():
    # rs1142345 = *3C defining SNP, heterozygous, rs1800460 absent.
    g = _genotype([("rs1142345", "0/1")])
    assert g["TPMT"] == "*1/*3C"
    assert CPIC_DATA["TPMT"]["variants"][g["TPMT"]] == "Intermediate Activity"


def test_tpmt_3c_homozygous_is_low_activity():
    g = _genotype([("rs1142345", "1/1")])
    assert g["TPMT"] == "*3C/*3C"
    assert CPIC_DATA["TPMT"]["variants"][g["TPMT"]] == "Low Activity"


def test_tpmt_both_variants_het_assumed_cis_3a():
    g = _genotype([("rs1800460", "0/1"), ("rs1142345", "0/1")])
    assert g["TPMT"] == "*1/*3A"


# ── CYP2D6 *10 / *41 decreased-function alleles ──────────────────────

def test_cyp2d6_10_homozygous_is_intermediate_not_normal():
    g = _genotype([("rs1065852", "1/1")])
    assert g["CYP2D6"] == "*10/*10"
    assert CPIC_DATA["CYP2D6"]["variants"][g["CYP2D6"]] == "Intermediate Metabolizer"


def test_cyp2d6_4_and_10_compound_is_intermediate():
    g = _genotype([("rs3892097", "0/1"), ("rs1065852", "0/1")])
    assert g["CYP2D6"] == "*4/*10"
    assert CPIC_DATA["CYP2D6"]["variants"][g["CYP2D6"]] == "Intermediate Metabolizer"


def test_cyp2d6_single_10_stays_normal():
    # One *10 with one *1 is still Normal (activity score 1.25) — must not over-call.
    g = _genotype([("rs1065852", "0/1")])
    assert g["CYP2D6"] == "*1/*10"
    assert CPIC_DATA["CYP2D6"]["variants"][g["CYP2D6"]] == "Normal Metabolizer"


# ── CYP2C19 *2/*17 ambiguous diplotype ───────────────────────────────

def test_cyp2c19_2_17_is_not_collapsed_to_1_2():
    g = _genotype([("rs4244285", "0/1"), ("rs12248560", "0/1")])
    assert g["CYP2C19"] == "*2/*17"
    assert CPIC_DATA["CYP2C19"]["variants"][g["CYP2C19"]] == "Intermediate Metabolizer"


# ── Every diplotype the caller can emit maps to a known phenotype ────

def test_all_emitted_cyp2d6_diplotypes_are_in_knowledge_base():
    # Guards against a future allele addition that silently yields "Indeterminate".
    seen = set()
    for a in ("rs3892097", "rs1065852", "rs28371725"):
        for b in ("rs3892097", "rs1065852", "rs28371725"):
            g = _genotype([(a, "0/1"), (b, "0/1")])
            if "CYP2D6" in g:
                seen.add(g["CYP2D6"])
    for dip in seen:
        assert dip in CPIC_DATA["CYP2D6"]["variants"], f"{dip} missing from knowledge base"


# ── An Intermediate CYP2D6 result actually produces a recommendation ──

def test_cyp2d6_intermediate_produces_codeine_recommendation():
    patient = {
        "patient_id": "T-IM",
        "indication": "pain requiring codeine",
        "genotype": {"CYP2D6": "*10/*10"},
    }
    result = run_analysis(patient)
    drugs = {r["drug"] for r in result["recommendations"]}
    assert "CODEINE" in drugs  # IM entry exists, so the drug is not silently dropped
