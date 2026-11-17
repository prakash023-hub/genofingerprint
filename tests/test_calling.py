"""Synthetic panel fixtures, including cases the old caller overinterpreted."""

import pytest

from agents.pipeline import run_analysis
from data.snp_reference import MARKERS
from data.vcf_parser import VCFValidationError, parse_vcf_text


HEADER = (
    "##fileformat=VCFv4.2\n"
    "##reference=GRCh38\n"
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
)


def row(rsid, sample, fmt="GT", *, alt=None, filt="PASS", contig_prefix=""):
    _, chromosome, pos, ref, expected_alt = MARKERS[rsid]
    return "\t".join([contig_prefix + chromosome, str(pos), rsid, ref, alt or expected_alt,
                      "99", filt, ".", fmt, sample])


def panel(*rows):
    return parse_vcf_text(HEADER + "\n".join(rows))[0]


@pytest.mark.parametrize("sample,fmt", [
    ("./.", "GT"), ("0/.", "GT"), ("0/0", "DP"), ("0/2", "GT"),
    ("1/1/1", "GT"), ("1", "GT"), ("0|.", "GT"),
])
def test_missing_invalid_or_unsupported_diploid_calls(sample, fmt):
    genotype = panel(row("rs4149056", sample, fmt))
    report = run_analysis({"age": 55, "data_source": "vcf", "genotype": genotype,
                           "medications": ["simvastatin"]})
    assert report["phenotypes"]["SLCO1B1"] == "Indeterminate"
    assert report["recommendations"] == []


def test_absence_no_call_and_reference_are_distinct():
    absent = panel()
    reference = panel(row("rs4149056", "0/0", alt="."))
    missing = panel(row("rs4149056", "./."))
    assert absent["SLCO1B1"].startswith("Not tested")
    assert reference["SLCO1B1"].startswith("Variant not detected at panel markers")
    assert missing["SLCO1B1"].startswith("Indeterminate: missing")


def test_missing_reference_blocks_all_calls():
    g, _, _ = parse_vcf_text(HEADER.replace("##reference=GRCh38\n", "") + row("rs4149056", "1/1"))
    assert "reference declaration" in g["SLCO1B1"]


@pytest.mark.parametrize("body,message", [
    (row("rs4149056", "1/1", alt="C,G"), "unsupported alternate"),
    (row("rs4149056", "1/1", filt="."), "did not pass"),
    (row("rs4149056", "1/1").replace("21178615", "21178616"), "mismatch"),
    (row("rs4149056", "1/1").replace("\tT\tC", "\tA\tC"), "mismatch"),
    (row("rs4149056", "1/1") + "\n" + row("rs4149056", "0/0"), "duplicate marker"),
    (row("rs4149056", "1/1") + "\n12\t21178000\t.\tT\t<DEL>\t.\tPASS\tEND=21179000\tGT\t0/1",
     "unsupported record"),
])
def test_blocked_marker_evidence(body, message):
    assert message in panel(body)["SLCO1B1"]


def test_chr_prefix_and_idless_record():
    assert panel(row("rs4149056", "1/1", contig_prefix="chr").replace("rs4149056", "."))["SLCO1B1"] == "c.521CC"


@pytest.mark.parametrize("content", [
    "malformed", HEADER + "12\t200", HEADER.replace("SAMPLE\n", "SAMPLE\tOTHER\n"),
    HEADER + row("rs4149056", "1/1").replace("21178615", "-1"),
])
def test_malformed_vcf(content):
    with pytest.raises(VCFValidationError):
        parse_vcf_text(content)


def test_fake_header_cannot_override_evidence_or_load_a_demo():
    content = HEADER.replace("#CHROM", "##genotype=SLCO1B1:c.521CC\n##patient=PT002_PRIYA\n#CHROM")
    g, metadata, logs = parse_vcf_text(content + row("rs4149056", "0/0"))
    assert not metadata
    assert g["SLCO1B1"].startswith("Variant not detected")
    assert "Uploaded diplotype header ignored." in logs


def test_tpmt_3c_marker_does_not_confirm_reference_haplotype():
    assert "*3C marker pattern" in panel(row("rs1800460", "0/0"), row("rs1142345", "0/1"))["TPMT"]


def test_tpmt_3c_homozygous():
    assert panel(row("rs1800460", "0/0"), row("rs1142345", "1/1"))["TPMT"] == "*3C/*3C"


@pytest.mark.parametrize("left,right", [("0/1", "0/1"), ("0|1:7", "0|1:8")])
def test_tpmt_unresolved_phase(left, right):
    a = row("rs1800460", left, "GT:PS" if ":" in left else "GT")
    b = row("rs1142345", right, "GT:PS" if ":" in right else "GT")
    assert panel(a, b)["TPMT"] == "Indeterminate: phase unresolved"


def test_tpmt_phased_trans_resolves_3b_3c_and_cis_leaves_reference_unconfirmed():
    a = row("rs1800460", "0|1:7", "GT:PS")
    assert panel(a, row("rs1142345", "1|0:7", "GT:PS"))["TPMT"] == "*3B/*3C"
    assert "*3A marker pattern" in panel(a, row("rs1142345", "0|1:7", "GT:PS"))["TPMT"]


@pytest.mark.parametrize("gt", ["1/1", "0/1", "0/0"])
def test_cyp2d6_defining_snps_cannot_resolve_deletion_or_duplication(gt):
    g = panel(row("rs3892097", gt), row("rs1065852", gt), row("rs28371725", "0/0"))
    assert "cannot establish CYP2D6 copy number" in g["CYP2D6"]


def test_cyp2d6_explicit_structural_variant_is_unsupported():
    g = panel("22\t42120000\t.\tA\t<DUP>\t.\tPASS\tEND=42140000\tGT\t0/1")
    assert g["CYP2D6"] == "Indeterminate: unsupported record in panel region"


def test_cyp2c19_2_17_unphased_is_indeterminate():
    g = panel(row("rs4244285", "0/1"), row("rs4986893", "0/0"), row("rs12248560", "0/1"))
    assert g["CYP2C19"] == "Indeterminate: phase unresolved"


@pytest.mark.parametrize("diplotype,score,phenotype", [
    ("*10/*10", 0.5, "Intermediate Metabolizer"), ("*10/*4", 0.25, "Intermediate Metabolizer"),
    ("*1/*10", 1.25, "Normal Metabolizer"), ("*4/*5", 0, "Poor Metabolizer"),
    ("*1x2/*1", 3, "Ultrarapid Metabolizer"), ("*1xN/*1", None, "Indeterminate"),
])
def test_lab_cyp2d6_activity(diplotype, score, phenotype):
    result = run_analysis({"genotype": {"CYP2D6": diplotype}})
    assert result["phenotypes"]["CYP2D6"] == phenotype
    assert result["activity_scores"].get("CYP2D6") == score
