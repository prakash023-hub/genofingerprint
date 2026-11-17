"""Versioned CPIC excerpts encoded as research demonstration rules."""

VARIANTS = {'CYP2C19': {'*1/*1': 'Normal Metabolizer',
             '*1/*2': 'Intermediate Metabolizer',
             '*1/*3': 'Intermediate Metabolizer',
             '*2/*2': 'Poor Metabolizer',
             '*2/*3': 'Poor Metabolizer',
             '*3/*3': 'Poor Metabolizer',
             '*2/*17': 'Intermediate Metabolizer',
             '*1/*17': 'Rapid Metabolizer',
             '*17/*17': 'Ultrarapid Metabolizer',
             '*3/*17': 'Intermediate Metabolizer'},
 'CYP2D6': {'*1/*1': 'Normal Metabolizer',
            '*1/*2': 'Normal Metabolizer',
            '*1/*10': 'Normal Metabolizer',
            '*1/*41': 'Normal Metabolizer',
            '*4/*4': 'Poor Metabolizer',
            '*4/*5': 'Poor Metabolizer',
            '*1/*4': 'Intermediate Metabolizer',
            '*4/*10': 'Intermediate Metabolizer',
            '*4/*41': 'Intermediate Metabolizer',
            '*10/*10': 'Intermediate Metabolizer',
            '*10/*41': 'Intermediate Metabolizer',
            '*41/*41': 'Intermediate Metabolizer'},
 'SLCO1B1': {'c.521TT': 'Normal Function',
             'c.521TC': 'Decreased Function',
             'c.521CC': 'Poor Function'},
 'TPMT': {'*1/*1': 'Normal Activity',
          '*1/*3A': 'Intermediate Activity',
          '*1/*3C': 'Intermediate Activity',
          '*3A/*3A': 'Low Activity',
          '*3C/*3C': 'Low Activity',
          '*3A/*3C': 'Low Activity',
          '*1/*3B': 'Intermediate Activity',
          '*3A/*3B': 'Low Activity',
          '*3B/*3B': 'Low Activity',
          '*3B/*3C': 'Low Activity'},
 'CYP2C9': {'*1/*1': 'Normal Metabolizer',
            '*1/*2': 'Intermediate Metabolizer',
            '*1/*3': 'Intermediate Metabolizer',
            '*2/*3': 'Poor Metabolizer',
            '*3/*3': 'Poor Metabolizer',
            '*2/*2': 'Intermediate Metabolizer'}}

CYP2D6_ACTIVITY = {"*1": 1, "*2": 1, "*4": 0, "*5": 0, "*10": 0.25, "*41": 0.5}

# drug: (gene, guideline version and URL, required clinical context)
GUIDELINES = {
    "clopidogrel": ("CYP2C19", "CPIC 2022, Table 2", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9287492/", "acs_pci"),
    "warfarin": ("CYP2C9", "CPIC 2017", "https://pmc.ncbi.nlm.nih.gov/articles/PMC5546947/", None),
    "metoprolol": ("CYP2D6", "CPIC 2024, Table 2", "https://pmc.ncbi.nlm.nih.gov/articles/PMC11502236/", None),
    "simvastatin": ("SLCO1B1", "CPIC 2022, Table 2", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9035072/", None),
    "atorvastatin": ("SLCO1B1", "CPIC 2022, Table 2", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9035072/", None),
    "codeine": ("CYP2D6", "CPIC 2021, Table 2", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8249478/", None),
    "tamoxifen": ("CYP2D6", "CPIC 2018, Table 2", "https://pmc.ncbi.nlm.nih.gov/articles/PMC5931215/", "early_stage_er_positive"),
    "azathioprine": ("TPMT", "CPIC 2025 update and correction", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12997511/", None),
}

# Application action and risk are independent. USE indicates no PGx-driven
# change in the covered scenario, subject to the clinician's usual checks.
_STANDARD = ("USE", "LOW", "No genotype-based adjustment in this guideline scenario.")
_RULES = {
    "clopidogrel": {
        "Poor Metabolizer": ("AVOID", "HIGH", "In ACS/PCI, CYP2C19 activity limits clopidogrel activation. Avoid if possible. The prescriber can evaluate ticagrelor or prasugrel if appropriate and without contraindications."),
        "Intermediate Metabolizer": ("AVOID", "MODERATE", "In ACS/PCI, avoid standard-dose clopidogrel if possible. The prescriber can evaluate ticagrelor or prasugrel if appropriate and without contraindications."),
        "Normal Metabolizer": _STANDARD,
        "Rapid Metabolizer": _STANDARD,
        "Ultrarapid Metabolizer": _STANDARD,
    },
    "codeine": {
        "Poor Metabolizer": ("AVOID", "MODERATE", "Reduced morphine formation can cause inadequate analgesia. The prescriber should evaluate an analgesic other than codeine or tramadol."),
        "Intermediate Metabolizer": ("CAUTION", "MODERATE", "The guideline starts with label dosing and advises considering another analgesic if response is inadequate."),
        "Normal Metabolizer": _STANDARD,
        "Ultrarapid Metabolizer": ("AVOID", "HIGH", "Increased morphine formation raises toxicity risk. The prescriber should evaluate an analgesic other than codeine or tramadol."),
    },
    "metoprolol": {
        "Poor Metabolizer": ("CAUTION", "MODERATE", "Higher exposure can increase bradycardia risk. CPIC advises the lowest recommended starting dose, careful titration and closer monitoring, or consideration of another beta blocker."),
        "Intermediate Metabolizer": _STANDARD,
        "Normal Metabolizer": _STANDARD,
    },
    "tamoxifen": {
        # The 2018 intermediate rules are score- and allele-specific, using
        # earlier CYP2D6 activity values. Only the score-zero branch is enabled.
        "Poor Metabolizer": ("AVOID", "HIGH", "For adjuvant therapy of early-stage ER-positive breast cancer, discuss alternative endocrine therapy with oncology. Menopausal status and suitability for ovarian suppression affect the options."),
    },
    "simvastatin": {
        "Poor Function": ("AVOID", "HIGH", "Higher simvastatin exposure substantially increases myopathy risk. CPIC recommends an alternative statin selected for the required potency."),
        "Decreased Function": ("CAUTION", "MODERATE", "CPIC favors an alternative statin. If simvastatin is warranted, the guideline limits it to less than 20 mg/day."),
        "Normal Function": _STANDARD,
    },
    "atorvastatin": {
        "Poor Function": ("CAUTION", "MODERATE", "Increased exposure raises myopathy risk. CPIC recommends a starting dose no higher than 20 mg, with specialist review of alternatives or combination therapy if more potency is needed."),
        "Decreased Function": ("CAUTION", "MODERATE", "Increased exposure may raise myopathy risk. CPIC recommends a starting dose no higher than 40 mg and review of combination therapy when more potency is needed."),
        "Normal Function": _STANDARD,
    },
}

REVIEW_REASONS = {
    "warfarin": "CYP2C9 alone is insufficient for a dose. A validated algorithm needs clinical inputs and VKORC1, with additional variants considered as specified by CPIC.",
    "azathioprine": "TPMT alone does not characterize thiopurine risk. Review NUDT15, the indication and intended starting regimen against the corrected guideline (https://pubmed.ncbi.nlm.nih.gov/42050374/).",
    "tamoxifen": "This prototype implements the score-zero rule only. Specialist review of the published activity-score and allele-specific rows is needed.",
    "omeprazole": "Outside this safety audit. The historical dosing rule is disabled pending review of the CPIC PPI guideline.",
}

# Existing consumers can enumerate supported diplotypes with this structure.
CPIC_DATA = {gene: {"variants": diplotypes} for gene, diplotypes in VARIANTS.items()}
