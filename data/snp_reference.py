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
        "rs3892097": "*4",    # 1846G>A, no function
        "rs1065852": "*10",   # 100C>T, decreased function (NB: also tags *4 — see README panel scope)
        "rs28371725": "*41",  # 2988G>A, decreased function (*5 is a gene deletion, not a SNP, so not called)
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
    # *2 (no function) + *17 (increased function): CPIC classifies as Intermediate.
    # Must be checked before the lone *2 / *17 branches, or the *17 is silently lost.
    if n2 == 1 and n17 == 1:
        return "*2/*17"
    if n2 == 1:
        return "*1/*2"
    if n3 == 1:
        return "*1/*3"
    if n17 >= 2:
        return "*17/*17"
    if n17 == 1:
        return "*1/*17"
    return "*1/*1"


# CYP2D6 allele activity values (CPIC / Caudle et al. 2020 activity-score standard).
_CYP2D6_ACTIVITY = {"*1": 1.0, "*2": 1.0, "*4": 0.0, "*10": 0.25, "*41": 0.5}


def infer_cyp2d6(star_counts: dict[str, int]) -> str:
    """
    Build a CYP2D6 diplotype from the panel's reduced/no-function alleles
    (*4, *10, *41), filling the remaining copies with *1.

    Covers *10 and *41 (common decreased-function alleles, frequent in South/East
    Asian patients), not only *4 — a *10/*10 or *10/*41 patient is an Intermediate
    Metaboliser, not Normal. See the knowledge base for the diplotype-to-phenotype
    map and the README panel-scope note for limits (e.g. rs1065852 also tags *4).
    """
    variant_alleles: list[str] = []
    for star in ("*4", "*10", "*41"):
        variant_alleles.extend([star] * star_counts.get(star, 0))
    variant_alleles = variant_alleles[:2]
    alleles = variant_alleles + ["*1"] * (2 - len(variant_alleles))

    def _num(a: str) -> int:
        s = a.lstrip("*")
        return int(s) if s.isdigit() else 999

    alleles.sort(key=lambda a: (0 if a == "*1" else 1, _num(a)))
    return "/".join(alleles)


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
    """
    TPMT diplotype from rs1800460 (*3A/*3B-defining) and rs1142345 (*3C-defining).

    A lone rs1142345 variant (*3C) must NOT be called *1/*1 — that is the dangerous
    false-negative: a TPMT Intermediate Metaboliser told azathioprine is standard-dose
    safe. Simplification (see README panel scope): when both SNPs carry equal variant
    counts they are assumed in cis as the *3A haplotype; an rs1800460-only variant is
    labelled *3A here (true *3B is not separately reported). Any one no-function allele
    is Intermediate; two is Low activity.
    """
    n3a = star_counts.get("*3A", 0)   # rs1800460
    n3c = star_counts.get("*3C", 0)   # rs1142345

    if n3a == 0 and n3c == 0:
        return "*1/*1"
    # Both variants present at equal count → assumed cis (*3A haplotype).
    if n3a >= 1 and n3c >= 1 and n3a == n3c:
        return "*1/*3A" if n3a == 1 else "*3A/*3A"
    # rs1142345 (*3C) alone — the branch the original caller was missing.
    if n3c >= 1 and n3a == 0:
        return "*1/*3C" if n3c == 1 else "*3C/*3C"
    # rs1800460 alone.
    if n3a >= 1 and n3c == 0:
        return "*1/*3A" if n3a == 1 else "*3A/*3A"
    # Unequal counts of the two variants → compound no-function, Low activity.
    return "*3A/*3C"


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
