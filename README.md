# 🧬 GenoFingerprint AI

GenoFingerprint is a pharmacogenomics research and education prototype. Use synthetic inputs. The Gradio app shows panel findings, versioned CPIC rule excerpts, eight patient-language views, a clinician PDF and clinical Q&A.

The [hosted demo](https://genofingerprint-105254876763.asia-south1.run.app/) is separate from a local checkout.

**30-second demo:** In Bedside Device, choose **Run Rajesh Post-Stent Case**. The synthetic CYP2C19 \*2/\*2 result triggers **CLOPIDOGREL [AVOID]** in the selected ACS/PCI scenario.

## Workflow

1. The VCF reader checks a single-sample GRCh38 file against panel markers. The manual workflow accepts a separately characterized lab diplotype.
2. LangGraph validates inputs, maps phenotypes, checks explicit medication selection and guideline context, then constructs stable recommendations.
3. The same rows drive the clinician summary, displayed actions, patient explanation, PDF and recorded findings in Q&A.
4. Clinical Q&A retrieves versioned sources as general education and shows recorded findings in a separate section. Optional Claude integration chooses the order of two prewritten report sections. The API receives the requested language only, and a short timeout falls back to the deterministic order.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt pytest pypdf
python -m pytest -q
python -m evals.run_evals
python app.py
```

The default local URL is http://127.0.0.1:7860. For optional presentation ordering, set `ANTHROPIC_API_KEY` in the environment. Synthetic demos and regression tests work without credentials.

## Deploy (Cloud Run)

```bash
gcloud run deploy genofingerprint --source . --region asia-south1 \
  --allow-unauthenticated --set-env-vars ANTHROPIC_API_KEY=<your-key>
```

## VCF coverage and limitations

The parser accepts a single-sample VCF up to 10 MiB with a GRCh38 or hg38 reference declaration. Each used marker needs a valid, PASS diploid genotype and the expected forward-strand coordinate and alleles. Explicit reference genotypes are recorded at site level. Missing sites, no-calls, conflicting records, unsupported alleles and ambiguous phase can prevent gene-level interpretation. Known structural calls and unmodeled variants in nearby regions can block interpretation. The review windows and marker count are limited. The caller has no independent validation of read depth, genotype quality, assay coverage or copy number.

| Gene | Markers | VCF interpretation |
| --- | --- | --- |
| CYP2C19 | rs4244285, rs4986893, rs12248560 | Two resolved no-function marker haplotypes can support a panel poor-metabolizer result. Other results remain indeterminate unless independently characterized. |
| CYP2D6 | rs3892097, rs1065852, rs28371725 | SNPs leave copy number, deletion, hybrid alleles and definitive diplotypes unresolved. The bundled Priya demo includes an explicit synthetic lab result. Uploading that VCF alone leaves CYP2D6 indeterminate. |
| CYP2C9 | rs1799853, rs1057910 | Biallelic supported marker calls can be classified. A partial panel cannot establish `*1` or support warfarin dosing. |
| SLCO1B1 | rs4149056 | Biallelic c.521C supports a panel poor-function result. c.521T/C or T/T alone leaves broader function unresolved. |
| TPMT | rs1800460, rs1142345 | Two heterozygous sites require a common phase set. Both changes on one chromosome are a `*3A` marker pattern. Split across chromosomes, they support `*3B/*3C`. NUDT15 is outside the panel. |

Manual inputs represent lab-characterized results or explicitly synthetic data. A reference call at a tested SNP does not establish a normal-function reference haplotype across the gene. Phenoconversion, uncommon alleles, interactions, contraindications, transplant and oncology regimen details, and full population coverage require independent review. The optional fingerprint image is a visual demo prop. Use a synthetic image.

## Guideline audit

The risk categories are report priorities assigned by the application. They are independent of the CPIC strength-of-recommendation scale. `USE` denotes no PGx-driven adjustment in the selected scope. The app does not generate prescriptions.

| Medication | Source | Implemented scope |
| --- | --- | --- |
| Clopidogrel | [CPIC 2022, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC9287492/) | Adult ACS/PCI only. Other cardiovascular and neurovascular contexts require separate review. |
| Warfarin | [CPIC 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5546947/) | Review-only. CYP2C9 alone does not supply VKORC1, the applicable additional variants or the clinical inputs of the dosing algorithm. |
| Metoprolol | [CPIC 2024, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11502236/) | PM review of starting dose and titration; IM and NM standard initiation guidance; UM withheld. |
| Simvastatin and atorvastatin | [CPIC 2022, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC9035072/) | SLCO1B1-directed review. Simvastatin poor function favors an alternative. Atorvastatin poor and decreased function have different starting-dose limits. |
| Codeine | [CPIC 2021, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC8249478/) | Adult CYP2D6 PGx findings. PM and UM have separate concerns; other label restrictions and comorbidities require review. |
| Tamoxifen | [CPIC 2018, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC5931215/) | Score-zero branch in adult adjuvant therapy for early-stage ER-positive disease. The historical activity-score and allele-specific rows need specialist review before implementation. |
| Azathioprine | [CPIC 2025 update](https://pmc.ncbi.nlm.nih.gov/articles/PMC12997511/) and [correction](https://pubmed.ncbi.nlm.nih.gov/42050374/) | Review-only. A qualified reviewer should verify the combined TPMT/NUDT15 branches and indication-specific starting regimens before any dosing implementation. |
| Omeprazole | Outside this audit | Historical dosing logic is disabled pending review of the CPIC PPI guideline. |

Spanish, French and Portuguese patient guidance fits the PDF font. Tamil, Hindi, Arabic and Chinese patient guidance is displayed in Gradio. The PDF provides English guidance and identifies where to read the local text.

## Author

**Prakash Raj K** — M.Pharm (Industrial Pharmacy), Executive PG in Data Science & AI (IIIT-Bangalore)
[GitHub](https://github.com/prakash023-hub)
