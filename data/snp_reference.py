"""rsID → star allele inference for CPIC pharmacogenomics panel (GRCh38)."""

from __future__ import annotations

# Key SNPs per gene (CPIC / PharmGKB commonly used markers)
PGX_SNPS: dict[str, dict[str, str]] = {
    "CYP2C19": {
        "rs4244285": "*2",
        "rs4986893": "*3",
        "rs12248560": "*17",
    },
    "CYP2D6": {
        "rs3892097": "*4",
        "rs1065852": "*10",   # 100C>T (also present on *4); recorded, not used for calling
        "rs28371725": "*41",  # 2988G>A; recorded, not used for calling (*5 is a gene deletion, not a SNP)
    },
    "SLCO1B1": {
        "rs4149056": "c.521C",  # T=ref, C=variant (decreased function)
    },
    "CYP2C9": {
        "rs1799853": "*2",
        "rs1057910": "*3",
    },
    "TPMT": {
        "rs1800460": "*3A",
        "rs1142345": "*3C",
    },
}

# Demo patient metadata keyed by sample ID in VCF
DEMO_VCF_PROFILES: dict[str, dict] = {
    "PT001_RAJESH": {
        "patient_id": "PT001",
        "patient_name": "Rajesh Kumar",
        "age": 58,
        "gender": "Male",
        "indication": "ACS requiring clopidogrel after stent placement",
    },
    "PT002_PRIYA": {
        "patient_id": "PT002",
        "patient_name": "Priya Sharma",
        "age": 45,
        "gender": "Female",
        "indication": "Breast cancer requiring tamoxifen",
    },
    "PT003_ARJUN": {
        "patient_id": "PT003",
        "patient_name": "Arjun Patel",
        "age": 62,
        "gender": "Male",
        "indication": "Cardiac patient on statin therapy for hyperlipidemia",
    },
}


def _allele_count(gt: str, ref: str, alt: str, star: str) -> int:
    """Count alternate star alleles from GT field (0/0, 0/1, 1/1)."""
    if not gt or gt in (".", "./."):
        return 0
    parts = gt.replace("|", "/").split("/")
    if len(parts) != 2:
        return 0
    count = 0
    for p in parts:
        if p == "1":
            count += 1
    return count


def infer_cyp2c19(star_counts: dict[str, int]) -> str:
    n2 = star_counts.get("*2", 0)
    n3 = star_counts.get("*3", 0)
    n17 = star_counts.get("*17", 0)
    if n2 >= 2:
        return "*2/*2"
    if n3 >= 2:
        return "*3/*3"
    if n2 == 1 and n3 == 1:
        return "*2/*3"
    if n2 == 1:
        return "*1/*2"
    if n3 == 1:
        return "*1/*3"
    if n17 >= 2:
        return "*17/*17"
    if n17 == 1:
        return "*1/*17"
    return "*1/*1"


def infer_cyp2d6(star_counts: dict[str, int]) -> str:
    n4 = star_counts.get("*4", 0)
    if n4 >= 2:
        return "*4/*4"
    if n4 == 1:
        return "*1/*4"
    return "*1/*1"


def infer_slco1b1(variant_count: int) -> str:
    if variant_count >= 2:
        return "c.521CC"
    if variant_count == 1:
        return "c.521TC"
    return "c.521TT"


def infer_cyp2c9(star_counts: dict[str, int]) -> str:
    n2 = star_counts.get("*2", 0)
    n3 = star_counts.get("*3", 0)
    if n2 >= 2 or n3 >= 2 or (n2 == 1 and n3 == 1):
        if n2 >= 2:
            return "*2/*2" if n3 == 0 else "*2/*3"
        if n3 >= 2:
            return "*3/*3"
        return "*2/*3"
    if n2 == 1:
        return "*1/*2"
    if n3 == 1:
        return "*1/*3"
    return "*1/*1"


def infer_tpmt(star_counts: dict[str, int]) -> str:
    n3a = star_counts.get("*3A", 0)
    n3c = star_counts.get("*3C", 0)
    if n3a >= 2:
        return "*3A/*3A"
    if n3c >= 2:
        return "*3C/*3C"
    if n3a == 1:
        return "*1/*3A"
    return "*1/*1"


def genotype_from_parsed_snps(snps: dict[str, tuple[str, str, str]]) -> dict[str, str]:
    """Build gene diplotypes from {rsid: (ref, alt, gt)}."""
    genotype: dict[str, str] = {}

    cyp2c19: dict[str, int] = {"*2": 0, "*3": 0, "*17": 0}
    for rsid, star in PGX_SNPS["CYP2C19"].items():
        if rsid in snps:
            _, _, gt = snps[rsid]
            cyp2c19[star] = _allele_count(gt, "", "", star)
    if any(cyp2c19.values()) or "rs4244285" in snps:
        genotype["CYP2C19"] = infer_cyp2c19(cyp2c19)

    cyp2d6: dict[str, int] = {"*4": 0, "*10": 0, "*41": 0}
    for rsid, star in PGX_SNPS["CYP2D6"].items():
        if rsid in snps:
            _, _, gt = snps[rsid]
            cyp2d6[star] = _allele_count(gt, "", "", star)
    if any(cyp2d6.values()):
        genotype["CYP2D6"] = infer_cyp2d6(cyp2d6)

    if "rs4149056" in snps:
        _, _, gt = snps["rs4149056"]
        genotype["SLCO1B1"] = infer_slco1b1(_allele_count(gt, "", "", "c.521C"))

    cyp2c9: dict[str, int] = {"*2": 0, "*3": 0}
    for rsid, star in PGX_SNPS["CYP2C9"].items():
        if rsid in snps:
            _, _, gt = snps[rsid]
            cyp2c9[star] = _allele_count(gt, "", "", star)
    if any(cyp2c9.values()):
        genotype["CYP2C9"] = infer_cyp2c9(cyp2c9)

    tpm: dict[str, int] = {"*3A": 0, "*3C": 0}
    for rsid, star in PGX_SNPS["TPMT"].items():
        if rsid in snps:
            _, _, gt = snps[rsid]
            tpm[star] = _allele_count(gt, "", "", star)
    if any(tpm.values()):
        genotype["TPMT"] = infer_tpmt(tpm)

    return genotype
