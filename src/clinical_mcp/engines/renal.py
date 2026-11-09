"""Pure renal physiology functions. No transport or MCP imports."""

from __future__ import annotations

from typing import Literal

from clinical_mcp.schemas.renal import (
    AKIIndicesInput,
    AKIIndicesOutput,
    CKDEPIInput,
    CKDEPIOutput,
    CockcroftGaultInput,
    CockcroftGaultOutput,
)


def calculate_ckd_epi(data: CKDEPIInput) -> CKDEPIOutput:
    """2021 race-free CKD-EPI.

    Propagation: serum creatinine -> race-free eGFR -> KDIGO G-stage. No other
    engine feeds this calculation.
    """
    female = data.sex == "female"
    kappa = 0.7 if female else 0.9
    alpha = -0.241 if female else -0.302
    ratio = data.scr_mg_dl / kappa
    egfr = 142.0 * (min(ratio, 1.0) ** alpha) * (max(ratio, 1.0) ** -1.200)
    egfr *= 0.9938 ** data.age_years
    if female:
        egfr *= 1.012
    egfr = round(egfr, 1)

    stage: Literal["G1", "G2", "G3a", "G3b", "G4", "G5"]
    if egfr >= 90.0:
        stage = "G1"
    elif egfr >= 60.0:
        stage = "G2"
    elif egfr >= 45.0:
        stage = "G3a"
    elif egfr >= 30.0:
        stage = "G3b"
    elif egfr >= 15.0:
        stage = "G4"
    else:
        stage = "G5"

    return CKDEPIOutput(
        egfr_ml_min_per_173m2=egfr,
        kdigo_stage=stage,
        clinical_pearls_and_actions=[
            f"KDIGO {stage}: confirm chronicity with a repeat eGFR after 3 months.",
            "Race is not a coefficient in the 2021 equation; do not apply a race multiplier.",
        ],
        llm_trap_prevented=[
            "Legacy 2009 CKD-EPI used constant 141 and a race coefficient; 2021 uses 142 race-free."
        ],
    )


def calculate_cockcroft_gault(data: CockcroftGaultInput) -> CockcroftGaultOutput:
    """Cockcroft-Gault with Devine IBW and 1.2x IBW / BMI 30 obesity switching.

    Propagation: height -> Devine IBW -> adjusted body weight -> weight selection
    -> Cockcroft-Gault CrCl used for drug dosing.
    """
    ibw = (50.0 if data.sex == "male" else 45.5) + 0.9 * (data.height_cm - 152.4)
    ibw = max(ibw, 20.0)
    adjbw = ibw + 0.4 * (data.weight_kg - ibw)
    bmi = data.weight_kg / ((data.height_cm / 100.0) ** 2)

    selected: float
    rule: Literal["actual", "ibw", "adjbw"]
    if data.weight_kg < ibw:
        selected, rule = data.weight_kg, "actual"
    elif data.weight_kg >= 1.2 * ibw or bmi >= 30.0:
        selected, rule = adjbw, "adjbw"
    else:
        selected, rule = ibw, "ibw"

    crcl = ((140.0 - data.age_years) * selected) / (72.0 * data.scr_mg_dl)
    if data.sex == "female":
        crcl *= 0.85
    crcl = round(crcl, 1)

    return CockcroftGaultOutput(
        bmi=round(bmi, 1),
        ibw_kg=round(ibw, 1),
        adjbw_kg=round(adjbw, 1),
        selected_weight_kg=round(selected, 1),
        weight_selection_rule=rule,
        crcl_ml_min=crcl,
        clinical_pearls_and_actions=[
            f"Dose renally cleared drugs with CrCl {crcl} mL/min, not eGFR.",
            "Cockcroft-Gault is an estimate; adjust for rapidly changing renal function.",
        ],
        llm_trap_prevented=[
            "Using total body weight in an obese patient overestimates CrCl and can cause drug overdose."
        ],
    )


def calculate_aki_indices(data: AKIIndicesInput) -> AKIIndicesOutput:
    """FENa and FEUrea with diuretic-aware interpretation.

    Propagation: paired urine/serum sodium and creatinine -> FENa; optional
    BUN/urea -> FEUrea; diuretic state suppresses FENa interpretation.
    """
    fena = (
        data.urine_sodium_meq_l
        * data.serum_creatinine_mg_dl
        / (data.serum_sodium_meq_l * data.urine_creatinine_mg_dl)
        * 100.0
    )
    fena = round(fena, 2)

    feurea: float | None = None
    if data.serum_bun_mg_dl is not None and data.urine_urea_mg_dl is not None:
        feurea = (
            data.urine_urea_mg_dl
            * data.serum_creatinine_mg_dl
            / (data.serum_bun_mg_dl * data.urine_creatinine_mg_dl)
            * 100.0
        )
        feurea = round(feurea, 2)

    etiology: Literal["prerenal", "atn", "indeterminate", "diuretic_confounded"]
    if data.on_diuretics:
        etiology = "diuretic_confounded"
        pearl = "FENa is unreliable on diuretics; interpret FEUrea instead."
        trap = "Diuretics raise FENa, so a low FENa does not exclude prerenal disease."
    elif feurea is not None:
        if feurea <= 35.0:
            etiology, pearl = "prerenal", "FEUrea <=35% favors prerenal azotemia."
        elif feurea > 50.0:
            etiology, pearl = "atn", "FEUrea >50% favors intrinsic (ATN) injury."
        else:
            etiology, pearl = "indeterminate", "FEUrea 35-50% is indeterminate."
        trap = "Using FENa alone misses the diuretic effect; FEUrea is the diuretic-resistant index."
    elif fena < 1.0:
        etiology, pearl = "prerenal", "FENa <1% favors prerenal azotemia."
        trap = "A single FENa without the diuretic history can misclassify AKI."
    elif fena > 2.0:
        etiology, pearl = "atn", "FENa >2% favors intrinsic (ATN) injury."
        trap = "A single FENa without the diuretic history can misclassify AKI."
    else:
        etiology, pearl = "indeterminate", "FENa 1-2% is indeterminate."
        trap = "A single FENa without the diuretic history can misclassify AKI."

    return AKIIndicesOutput(
        fena_percent=fena,
        feurea_percent=feurea,
        aki_etiology=etiology,
        clinical_pearls_and_actions=[pearl],
        llm_trap_prevented=[trap],
    )


__all__ = ["calculate_ckd_epi", "calculate_cockcroft_gault", "calculate_aki_indices"]
