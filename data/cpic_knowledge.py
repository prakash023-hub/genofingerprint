CPIC_DATA = {
    "CYP2C19": {
        "variants": {
            "*1/*1": "Normal Metabolizer",
            "*1/*2": "Intermediate Metabolizer",
            "*1/*3": "Intermediate Metabolizer",
            "*2/*2": "Poor Metabolizer",
            "*2/*3": "Poor Metabolizer",
            "*3/*3": "Poor Metabolizer",
            "*1/*17": "Rapid Metabolizer",
            "*17/*17": "Ultrarapid Metabolizer",
        },
        "drugs": {
            "clopidogrel": {
                "Poor Metabolizer": {"risk": "HIGH", "recommendation": "Avoid clopidogrel. Use prasugrel or ticagrelor instead.", "rationale": "Reduced conversion to active metabolite. Increased risk of stent thrombosis."},
                "Intermediate Metabolizer": {"risk": "MODERATE", "recommendation": "Consider alternative antiplatelet therapy. Monitor closely.", "rationale": "Reduced but not absent CYP2C19 activity."},
                "Normal Metabolizer": {"risk": "LOW", "recommendation": "Use standard dose clopidogrel 75mg/day.", "rationale": "Normal CYP2C19 activity."},
                "Rapid Metabolizer": {"risk": "LOW", "recommendation": "Use standard dose clopidogrel 75mg/day.", "rationale": "Normal to increased CYP2C19 activity."},
                "Ultrarapid Metabolizer": {"risk": "LOW", "recommendation": "Use standard dose clopidogrel 75mg/day.", "rationale": "Increased CYP2C19 activity."}
            },
            "omeprazole": {
                "Poor Metabolizer": {"risk": "MODERATE", "recommendation": "Reduce dose by 50%. Monitor for adverse effects.", "rationale": "Increased drug exposure."},
                "Normal Metabolizer": {"risk": "LOW", "recommendation": "Use standard dose.", "rationale": "Normal metabolism."},
                "Ultrarapid Metabolizer": {"risk": "MODERATE", "recommendation": "Increase dose or switch to rabeprazole.", "rationale": "Rapid metabolism may reduce efficacy."}
            }
        }
    },
    "CYP2D6": {
        "variants": {
            "*1/*1": "Normal Metabolizer",
            "*1/*2": "Normal Metabolizer",
            "*4/*4": "Poor Metabolizer",
            "*4/*5": "Poor Metabolizer",
            "*1/*4": "Intermediate Metabolizer",
            "*1xN/*1": "Ultrarapid Metabolizer",
        },
        "drugs": {
            "codeine": {
                "Poor Metabolizer": {"risk": "MODERATE", "recommendation": "Avoid codeine. Use non-opioid analgesics.", "rationale": "Reduced conversion to morphine."},
                "Normal Metabolizer": {"risk": "LOW", "recommendation": "Use standard dose codeine.", "rationale": "Normal conversion to morphine."},
                "Ultrarapid Metabolizer": {"risk": "HIGH", "recommendation": "CONTRAINDICATED. Avoid codeine entirely.", "rationale": "Rapid conversion. Risk of respiratory depression."}
            },
            "tamoxifen": {
                "Poor Metabolizer": {"risk": "HIGH", "recommendation": "Avoid tamoxifen. Consider aromatase inhibitor.", "rationale": "Reduced conversion to active endoxifen."},
                "Normal Metabolizer": {"risk": "LOW", "recommendation": "Use standard dose tamoxifen 20mg/day.", "rationale": "Normal conversion to endoxifen."}
            },
            "metoprolol": {
                "Poor Metabolizer": {"risk": "MODERATE", "recommendation": "Reduce dose by 50-75%. Monitor heart rate.", "rationale": "Increased drug exposure."},
                "Normal Metabolizer": {"risk": "LOW", "recommendation": "Use standard dose.", "rationale": "Normal metabolism."}
            }
        }
    },
    "SLCO1B1": {
        "variants": {
            "c.521TT": "Normal Function",
            "c.521TC": "Decreased Function",
            "c.521CC": "Poor Function",
        },
        "drugs": {
            "simvastatin": {
                "Poor Function": {"risk": "HIGH", "recommendation": "Avoid simvastatin >20mg. Switch to pravastatin or rosuvastatin.", "rationale": "High risk of myopathy and rhabdomyolysis."},
                "Decreased Function": {"risk": "MODERATE", "recommendation": "Use simvastatin ≤20mg or switch to pravastatin.", "rationale": "Moderately increased simvastatin exposure."},
                "Normal Function": {"risk": "LOW", "recommendation": "Use standard dose simvastatin.", "rationale": "Normal hepatic uptake."}
            },
            "atorvastatin": {
                "Poor Function": {"risk": "MODERATE", "recommendation": "Use lowest effective dose. Monitor CK levels.", "rationale": "Moderately increased atorvastatin exposure."},
                "Normal Function": {"risk": "LOW", "recommendation": "Use standard dose.", "rationale": "Normal hepatic uptake."}
            }
        }
    },
    "TPMT": {
        "variants": {
            "*1/*1": "Normal Activity",
            "*1/*3A": "Intermediate Activity",
            "*3A/*3A": "Low Activity",
            "*3C/*3C": "Low Activity",
        },
        "drugs": {
            "azathioprine": {
                "Low Activity": {"risk": "HIGH", "recommendation": "Reduce dose by 90% or switch. Risk of fatal myelosuppression.", "rationale": "Accumulation of toxic thioguanine nucleotides."},
                "Intermediate Activity": {"risk": "MODERATE", "recommendation": "Reduce dose by 30-70%. Monitor CBC weekly.", "rationale": "Moderately increased thioguanine exposure."},
                "Normal Activity": {"risk": "LOW", "recommendation": "Use standard dose with routine monitoring.", "rationale": "Normal thiopurine metabolism."}
            }
        }
    },
    "CYP2C9": {
        "variants": {
            "*1/*1": "Normal Metabolizer",
            "*1/*2": "Intermediate Metabolizer",
            "*1/*3": "Intermediate Metabolizer",
            "*2/*3": "Poor Metabolizer",
            "*3/*3": "Poor Metabolizer",
        },
        "drugs": {
            "warfarin": {
                "Poor Metabolizer": {"risk": "HIGH", "recommendation": "Reduce starting dose by 50-75%. Intensive INR monitoring.", "rationale": "Severely reduced warfarin clearance. High bleeding risk."},
                "Intermediate Metabolizer": {"risk": "MODERATE", "recommendation": "Reduce starting dose by 25-50%. Monitor INR closely.", "rationale": "Reduced warfarin clearance."},
                "Normal Metabolizer": {"risk": "LOW", "recommendation": "Use standard dosing algorithm.", "rationale": "Normal warfarin metabolism."}
            }
        }
    }
}

INDIAN_ALLELE_FREQUENCIES = {
    "CYP2C19": {"Poor Metabolizer": "13-23%", "Intermediate Metabolizer": "35-40%", "Normal Metabolizer": "35-45%", "Rapid/Ultrarapid Metabolizer": "5-10%"},
    "CYP2D6": {"Poor Metabolizer": "1-3%", "Intermediate Metabolizer": "10-15%", "Normal Metabolizer": "75-85%", "Ultrarapid Metabolizer": "3-5%"},
    "SLCO1B1": {"Poor Function": "15-20%", "Decreased Function": "25-30%", "Normal Function": "50-60%"},
}

# Approximate global reference ranges (CPIC / PharmGKB / gnomAD literature)
GLOBAL_ALLELE_FREQUENCIES = {
    "CYP2C19": {"Poor Metabolizer": "2-5%", "Intermediate Metabolizer": "25-35%", "Normal Metabolizer": "35-45%", "Rapid/Ultrarapid Metabolizer": "15-30%"},
    "CYP2D6": {"Poor Metabolizer": "5-10%", "Intermediate Metabolizer": "10-15%", "Normal Metabolizer": "70-80%", "Ultrarapid Metabolizer": "1-5%"},
    "SLCO1B1": {"Poor Function": "1-2%", "Decreased Function": "15-20%", "Normal Function": "75-85%"},
}
