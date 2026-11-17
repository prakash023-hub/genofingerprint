"""Supported GRCh38 forward-strand panel markers and synthetic profiles."""

# rsID: (gene, chromosome, position, reference, supported alternate)
MARKERS = {
    "rs4244285": ("CYP2C19", "10", 94781859, "G", "A"),
    "rs4986893": ("CYP2C19", "10", 94780653, "G", "A"),
    "rs12248560": ("CYP2C19", "10", 94761900, "C", "T"),
    "rs3892097": ("CYP2D6", "22", 42128945, "C", "T"),
    "rs1065852": ("CYP2D6", "22", 42130692, "G", "A"),
    "rs28371725": ("CYP2D6", "22", 42127803, "C", "T"),
    "rs4149056": ("SLCO1B1", "12", 21178615, "T", "C"),
    "rs1799853": ("CYP2C9", "10", 94942290, "C", "T"),
    "rs1057910": ("CYP2C9", "10", 94981296, "A", "C"),
    "rs1800460": ("TPMT", "6", 18138997, "C", "T"),
    "rs1142345": ("TPMT", "6", 18130687, "T", "C"),
}

# Conservative review windows for unmodelled records near panel loci.
# These are screening intervals, not validated assay coverage boundaries.
REVIEW_WINDOWS = {
    "CYP2C19": ("10", 94760000, 94856000),
    "CYP2C9": ("10", 94930000, 94995000),
    "SLCO1B1": ("12", 21120000, 21250000),
    "TPMT": ("6", 18110000, 18160000),
    "CYP2D6": ("22", 42110000, 42150000),
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


# Explicit synthetic clinical inputs, deliberately separate from file metadata.
DEMO_SCENARIOS = {
    "PT001": {"medications": ["clopidogrel"], "clinical_context": "acs_pci"},
    "PT002": {
        "medications": ["tamoxifen"],
        "clinical_context": "early_stage_er_positive",
        "confirmed_genotype": {"CYP2D6": "*4/*4"},
    },
    "PT003": {"medications": ["simvastatin", "atorvastatin"]},
}
