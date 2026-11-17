"""Read the single-sample GRCh38 research panel. VCF headers cannot assert diplotypes."""

from __future__ import annotations

import re
from pathlib import Path

from data.snp_reference import DEMO_SCENARIOS, DEMO_VCF_PROFILES, MARKERS, REVIEW_WINDOWS

_HEADER = "#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT".split()
_LOCI = {(chrom, pos): rsid for rsid, (_, chrom, pos, _, _) in MARKERS.items()}
_CALL = re.compile(r"([01.])([/|])([01.])")
_MAX_BYTES = 10 * 1024 * 1024
_SAMPLE_DIR = Path(__file__).resolve().with_name("samples")
_DEMO_FILES = {
    "PT001": "rajesh_post_stent.vcf",
    "PT002": "priya_tamoxifen.vcf",
    "PT003": "arjun_statin.vcf",
}


class VCFValidationError(ValueError):
    """An uploaded file cannot be safely interpreted."""


def _panel_diplotype(gene: str, calls: dict[str, tuple[str, str]]) -> str:
    if gene == "CYP2D6":
        return "Indeterminate: SNPs cannot establish CYP2D6 copy number or structural haplotypes"

    copies = {rsid: gt.count("1") for rsid, (gt, _) in calls.items()}
    total = sum(copies.values())
    if total == 0:
        return "Variant not detected at panel markers; gene function indeterminate"
    if gene == "SLCO1B1":
        if total == 2:
            return "c.521CC"
        return "Indeterminate: c.521T/C detected; second haplotype unresolved"

    heterozygotes = [(gt, ps) for gt, ps in calls.values() if gt.count("1") == 1]
    if len(heterozygotes) > 1:
        phase_sets = {ps for _, ps in heterozygotes}
        if any("|" not in gt for gt, _ in heterozygotes) or len(phase_sets) != 1 or "" in phase_sets:
            return "Indeterminate: phase unresolved"

    haplotypes = [
        frozenset(rsid for rsid, (gt, _) in calls.items() if gt[i] == "1")
        for i in (0, 2)
    ]
    supported = {
        "CYP2C19": {("rs4244285",): "*2", ("rs4986893",): "*3", ("rs12248560",): "*17"},
        "CYP2C9": {("rs1799853",): "*2", ("rs1057910",): "*3"},
        "TPMT": {
            ("rs1800460", "rs1142345"): "*3A",
            ("rs1800460",): "*3B",
            ("rs1142345",): "*3C",
        },
    }
    mapping = {frozenset(markers): allele for markers, allele in supported[gene].items()}
    if any(hap and hap not in mapping for hap in haplotypes):
        return "Indeterminate: unsupported marker combination on one haplotype"
    if not all(haplotypes):
        markers = "/".join(mapping[hap] for hap in haplotypes if hap)
        return f"Indeterminate: {markers} marker pattern detected; reference haplotype unconfirmed"
    alleles = [mapping[hap] for hap in haplotypes]
    if gene == "CYP2C19" and "*17" in alleles:
        return "Indeterminate: increased-function haplotype requires broader testing"
    return "/".join(sorted(alleles))


def parse_vcf_text(content: str) -> tuple[dict[str, str], dict, list[str]]:
    """Return panel calls, an empty metadata dict and sample-free audit messages."""
    if len(content.encode("utf-8")) > _MAX_BYTES:
        raise VCFValidationError("VCF exceeds the research panel size limit.")
    logs = []
    calls = {}
    blocked = {}
    seen = set()
    references = []
    header = False
    version = False
    for number, line in enumerate(content.splitlines(), 1):
        if not line.strip():
            continue
        if line.startswith("##") and not header:
            if line.startswith("##fileformat="):
                if version or not re.fullmatch(r"##fileformat=VCFv4\.[0-5]", line):
                    raise VCFValidationError("Expected one supported VCF 4.x fileformat declaration.")
                version = True
            if line.startswith("##reference="):
                references.append(line.partition("=")[2].strip())
            if line.startswith("##genotype="):
                logs.append("Uploaded diplotype header ignored.")
            continue
        fields = line.split("\t")
        if fields[0] == "#CHROM":
            if header or fields[:9] != _HEADER or len(fields) != 10 or not fields[9].strip():
                raise VCFValidationError("Expected one VCF column header and exactly one sample.")
            header = True
            continue
        if not header or not version or len(fields) != 10 or line.startswith("#"):
            raise VCFValidationError(f"Malformed VCF at line {number}.")

        chrom, position, identifiers, ref, alt, _, filt, info, fmt, sample = fields
        chrom = chrom.removeprefix("chr")
        if not re.fullmatch(r"[1-9][0-9]{0,8}", position) or not re.fullmatch(r"[ACGTNacgtn]+", ref):
            raise VCFValidationError(f"Invalid position or reference allele at line {number}.")
        pos = int(position)
        keys, values = fmt.split(":"), sample.split(":")
        if len(keys) != len(set(keys)) or len(values) > len(keys):
            raise VCFValidationError(f"Invalid FORMAT or sample fields at line {number}.")
        sample_data = dict(zip(keys, values))
        gt = sample_data.get("GT", ".")
        ids = set(identifiers.split(";")) & MARKERS.keys()
        locus_id = _LOCI.get((chrom, pos))
        if locus_id:
            ids.add(locus_id)
        if not ids:
            end_match = re.search(r"(?:^|;)END=([0-9]{1,9})(?:;|$)", info)
            end = int(end_match[1]) if end_match else pos + len(ref) - 1
            structural = any(symbol in alt for symbol in "<>[]*") or "SVTYPE=" in info
            if structural or gt not in {"0/0", "0|0"}:
                for gene, (contig, start, stop) in REVIEW_WINDOWS.items():
                    if chrom == contig and pos <= stop and end >= start:
                        blocked[gene] = "unsupported record in panel region"
            continue

        for rsid in sorted(ids):
            gene, expected_chrom, expected_pos, expected_ref, expected_alt = MARKERS[rsid]
            if rsid in seen:
                blocked[gene] = "duplicate marker"
            seen.add(rsid)
            if len(ids) > 1 or (chrom, pos, ref.upper()) != (expected_chrom, expected_pos, expected_ref):
                blocked[gene] = "marker chromosome, position or reference mismatch"
                continue
            if alt.upper() not in {expected_alt, "."} or (alt == "." and "1" in gt):
                blocked[gene] = "unsupported alternate or structural allele"
                continue
            if filt != "PASS":
                blocked[gene] = "marker did not pass VCF filtering"
                continue
            if not _CALL.fullmatch(gt) or "." in gt:
                blocked[gene] = "missing or unsupported diploid genotype"
                continue
            if "CN" in sample_data or "SVTYPE=" in info:
                blocked[gene] = "unsupported copy-number or structural record"
                continue
            ps = sample_data.get("PS", "")
            calls[rsid] = gt, ps if re.fullmatch(r"[0-9]+", ps) else ""
            status = "reference genotype at this site" if "1" not in gt else "alternate allele detected"
            logs.append(f"{rsid}: {status} (GT {gt}).")

    if not header or not version:
        raise VCFValidationError("Missing VCF fileformat or sample header.")
    supported_reference = len(references) == 1 and re.fullmatch(r"(?:GRCh38(?:\.p[0-9]+)?|hg38)", references[0])
    genotype = {}
    for gene in REVIEW_WINDOWS:
        required = {rsid for rsid, marker in MARKERS.items() if marker[0] == gene}
        available = {rsid: calls[rsid] for rsid in sorted(required & calls.keys())}
        if not supported_reference:
            result = "Indeterminate: missing or unsupported GRCh38 reference declaration"
        elif gene in blocked:
            result = f"Indeterminate: {blocked[gene]}"
        elif not required & seen:
            result = "Not tested: panel markers absent"
        elif required - calls.keys():
            result = "Indeterminate: incomplete marker coverage"
        else:
            result = _panel_diplotype(gene, available)
        genotype[gene] = result
        logs.append(f"{gene}: {result}.")
    return genotype, {}, logs


def parse_vcf_file(path: str | Path) -> tuple[dict[str, str], dict, list[str]]:
    try:
        with Path(path).open("rb") as stream:
            content = stream.read(_MAX_BYTES + 1)
        if len(content) > _MAX_BYTES:
            raise VCFValidationError("VCF exceeds the research panel size limit.")
        return parse_vcf_text(content.decode("utf-8"))
    except (OSError, UnicodeError) as exc:
        raise VCFValidationError("The VCF could not be read as a UTF-8 text file.") from exc


def parse_demo_file(path: str | Path, patient_id: str) -> tuple[dict, dict, list[str]]:
    """Attach supplementary evidence only when the caller selects a bundled demo."""
    if patient_id not in _DEMO_FILES or Path(path).resolve() != _SAMPLE_DIR / _DEMO_FILES[patient_id]:
        raise VCFValidationError("Synthetic lab evidence is available only for its bundled case.")
    genotype, _, logs = parse_vcf_file(path)
    patient = next(p for p in DEMO_VCF_PROFILES.values() if p["patient_id"] == patient_id)
    scenario = DEMO_SCENARIOS[patient_id]
    for gene, diplotype in scenario.get("confirmed_genotype", {}).items():
        genotype[gene] = diplotype
        logs.append(f"{gene}: {diplotype} supplied by a synthetic lab result with confirmed copy number.")
    return genotype, {**patient, **scenario}, logs
