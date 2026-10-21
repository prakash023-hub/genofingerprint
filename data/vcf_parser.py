"""Parse pharmacogenomics VCF files into CPIC star-allele genotypes."""

from __future__ import annotations

import re
from pathlib import Path

from data.snp_reference import (
    DEMO_VCF_PROFILES,
    PGX_SNPS,
    genotype_from_parsed_snps,
)

ALL_RSIDS = {rsid for gene in PGX_SNPS.values() for rsid in gene}


def parse_vcf_text(content: str) -> tuple[dict[str, str], dict, list[str]]:
    """
    Returns (genotype dict, patient profile dict, parse log lines).
    """
    logs: list[str] = []
    snps: dict[str, tuple[str, str, str]] = {}
    sample_id = "SAMPLE"
    embedded_genotype: dict[str, str] = {}
    patient_meta: dict = {}

    for line in content.splitlines():
        if line.startswith("##patient="):
            # ##patient=PT001_RAJESH
            key = line.split("=", 1)[1].strip()
            patient_meta = DEMO_VCF_PROFILES.get(key, {})
            logs.append(f"Matched demo profile: {key}")
        if line.startswith("##genotype="):
            # ##genotype=CYP2C19:*2/*2,CYP2D6:*1/*1
            for part in line.split("=", 1)[1].split(","):
                if ":" in part:
                    gene, var = part.strip().split(":", 1)
                    embedded_genotype[gene.strip()] = var.strip()
            logs.append(f"Embedded genotype header: {embedded_genotype}")
        if line.startswith("#CHROM"):
            cols = line.strip().split("\t")
            if len(cols) >= 10:
                sample_id = cols[9]
            continue
        if line.startswith("#"):
            continue
        fields = line.strip().split("\t")
        if len(fields) < 10:
            continue
        rsid = fields[2] if fields[2] != "." else ""
        if not rsid.startswith("rs") and fields[2] == ".":
            # try ID from INFO or match by known positions — skip
            continue
        if rsid not in ALL_RSIDS and not rsid.startswith("rs"):
            continue
        ref, alt = fields[3], fields[4]
        format_keys = fields[8].split(":")
        sample_vals = fields[9].split(":")
        gt_idx = format_keys.index("GT") if "GT" in format_keys else 0
        gt = sample_vals[gt_idx] if gt_idx < len(sample_vals) else "./."
        if rsid in ALL_RSIDS:
            snps[rsid] = (ref, alt, gt)
            logs.append(f"Found {rsid} GT={gt}")

    genotype = genotype_from_parsed_snps(snps)
    if embedded_genotype:
        genotype.update(embedded_genotype)

    if not patient_meta and sample_id in DEMO_VCF_PROFILES:
        patient_meta = DEMO_VCF_PROFILES[sample_id]

    logs.append(f"Inferred genotype: {genotype}")
    return genotype, patient_meta, logs


def parse_vcf_file(path: str | Path) -> tuple[dict[str, str], dict, list[str]]:
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_vcf_text(content)
