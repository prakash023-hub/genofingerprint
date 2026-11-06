# 🧬 GenoFingerprint AI

**CPIC pharmacogenomics clinical decision support** — lab VCF → star alleles → phenotypes → CPIC drug actions (AVOID / CAUTION / USE) → clinician PDF + patient explanation in 8 languages (incl. Tamil) → clinical Q&A.

🔗 **Live demo:** https://genofingerprint-105254876763.asia-south1.run.app/

**30-second demo:** Bedside Device → **▶ Run Rajesh Post-Stent Case** → result: **CLOPIDOGREL — AVOID** (CYP2C19 \*2/\*2 poor metabolizer).

---

## Why it matters

The same drug dose can be safe for one patient and ineffective or toxic for another, depending on genes such as CYP2C19, CYP2D6, CYP2C9, SLCO1B1 and TPMT. CPIC publishes evidence-based guidelines for this, but they are rarely applied at the bedside. CYP2C19 poor metabolizers are more common in South Asian populations than in many others, so clopidogrel after a stent is a real risk in Indian hospitals.

## Architecture

```
VCF / manual genotype
        │
        ▼
┌──────────────── LangGraph pipeline (deterministic, CPIC rules) ────────────────┐
│ parser → phenotype_mapper → risk_scorer → recommendation                       │
│ (validate genes) (allele→phenotype) (indication-aware drug risk) (actions + ID) │
└────────────────────────────────────────────────────────────────────────────────┘
        │
        ├─► Narrator: CPIC rule narrative (always) + Claude narrative (if API key set)
        ├─► PDF report for the clinician
        └─► Clinical Q&A agent: keyword RAG over CPIC knowledge + patient context → Claude
```

**Design choice:** drug recommendations come only from the deterministic CPIC rules engine. The LLM only *explains* results and answers questions — it is told never to invent recommendations. Without an API key, the app still works fully using rule-based narratives.

## Tech stack

| Layer | Tools |
|---|---|
| Orchestration | LangGraph (4-node StateGraph) |
| LLM | Anthropic Claude (narration + Q&A), optional |
| Retrieval | Lightweight keyword RAG over CPIC knowledge base |
| UI | Gradio |
| Reports | ReportLab PDF |
| Deploy | Docker → Google Cloud Run (asia-south1) |

**Genes:** CYP2C19 · CYP2D6 · CYP2C9 · SLCO1B1 · TPMT
**Drugs:** clopidogrel, warfarin, metoprolol, simvastatin, atorvastatin, codeine, tamoxifen, azathioprine

## Run locally

```bash
git clone https://github.com/prakash023-hub/genofingerprint.git
cd genofingerprint
pip install -r requirements.txt
cp .env.example .env          # optional: add ANTHROPIC_API_KEY
python evals/run_evals.py     # golden-case evals, must pass 3/3
python app.py                 # http://127.0.0.1:7860
```

## Deploy (Cloud Run)

```bash
gcloud run deploy genofingerprint --source . --region asia-south1 \
  --allow-unauthenticated --set-env-vars ANTHROPIC_API_KEY=<your-key>
```

## Scope & limitations

- Clinical decision **support** only — not CDSCO / FDA approved. A clinician must confirm all prescribing.
- Demo VCFs are anonymized / synthetic — no real patient data.
- The fingerprint image is a demo of the bedside workflow; no biometric matching is performed.
- 5-gene panel; hospital EHR integration is future work.

### Panel scope — which alleles are called

The caller is transparent about exactly what it genotypes. Alleles outside this list are not detected and default to the reference (`*1`); document this limit before any real use.

| Gene | SNPs used | Alleles called | Notes |
|---|---|---|---|
| CYP2C19 | rs4244285, rs4986893, rs12248560 | `*2`, `*3`, `*17` | `*2/*17` is reported as Intermediate (ambiguous diplotype, not collapsed to `*1/*2`) |
| CYP2D6 | rs3892097, rs1065852, rs28371725 | `*4`, `*10`, `*41` | Phenotype via the CPIC/Caudle 2020 activity-score standard. `*5` (gene deletion) and copy-number are not detected. rs1065852 also tags `*4`, so a `*10` call co-occurring with `*4` is approximate |
| CYP2C9 | rs1799853, rs1057910 | `*2`, `*3` | — |
| SLCO1B1 | rs4149056 | `c.521T>C` | — |
| TPMT | rs1800460, rs1142345 | `*3A`, `*3B`/`*3C` | Unphased: equal variant counts are assumed in cis as `*3A`; an rs1800460-only variant is labelled `*3A` (true `*3B` is not separately reported) |

Phasing is not resolved from unphased VCF genotypes; compound-heterozygous calls are a documented simplification. This is a research/education demo, not a validated diagnostic.

## Author

**Prakash Raj K** — M.Pharm (Industrial Pharmacy), Executive PG in Data Science & AI (IIIT-Bangalore)
[GitHub](https://github.com/prakash023-hub)
