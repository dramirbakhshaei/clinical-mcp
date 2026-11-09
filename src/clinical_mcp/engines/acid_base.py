"""Pure acid-base, osmolality, and calcium functions."""

from __future__ import annotations

from typing import Literal

from clinical_mcp.schemas.acid_base import (
    AcidBaseInput,
    AcidBaseOutput,
    CalciumInput,
    CalciumOutput,
    OsmolalityInput,
    OsmolalityOutput,
)
from clinical_mcp.schemas.common import AcidBaseDisorder


def _classify_disorders(
    data: AcidBaseInput,
    corrected_ag: float,
    delta_ratio: float | None,
) -> list[AcidBaseDisorder]:
    hco3 = data.hco3_meq_l
    paco2 = data.paco2_mmhg
    ph = data.ph
    hagna = corrected_ag > 12.0 and hco3 < 24.0
    nagma = corrected_ag <= 12.0 and hco3 < 22.0

    if hagna:
        if delta_ratio is not None and delta_ratio < 1.0:
            return [AcidBaseDisorder.MIXED_HAGMA_NAGMA]
        if (delta_ratio is not None and delta_ratio > 2.0) or hco3 > 26.0:
            return [AcidBaseDisorder.HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS]
        return [AcidBaseDisorder.PURE_HAGMA]
    if nagma:
        return [AcidBaseDisorder.PURE_NAGMA]
    if paco2 is not None and paco2 > 45.0 and (ph is None or ph < 7.35):
        return [AcidBaseDisorder.UNCOMPENSATED_RESPIRATORY_ACIDOSIS]
    if paco2 is not None and paco2 < 35.0 and (ph is None or ph > 7.45):
        return [AcidBaseDisorder.SUPERIMPOSED_RESPIRATORY_ALKALOSIS]
    return [AcidBaseDisorder.NORMAL]


def calculate_acid_base(data: AcidBaseInput) -> AcidBaseOutput:
    """Coupled acid-base analysis.

    Propagation: glucose -> Katz/Hillier corrected sodium -> Figge albumin-
    corrected anion gap -> delta ratio -> Winter's expected PaCO2 range;
    prior_known_disorder is preserved when supplied.
    """
    raw_ag = data.na_meq_l - data.cl_meq_l - data.hco3_meq_l
    corrected_ag = raw_ag + 2.5 * (4.0 - data.albumin_g_dl)

    glucose_delta = max(0.0, data.glucose_mg_dl - 100.0)
    katz = round(data.na_meq_l + 0.016 * glucose_delta, 1)
    hillier = round(data.na_meq_l + 0.024 * glucose_delta, 1)
    method: Literal["katz", "hillier"] = "hillier" if data.glucose_mg_dl > 400.0 else "katz"

    delta_ratio: float | None = None
    if corrected_ag > 12.0 and data.hco3_meq_l < 24.0:
        delta_ratio = round((corrected_ag - 12.0) / (24.0 - data.hco3_meq_l), 2)

    winters_min: float | None = None
    winters_max: float | None = None
    if data.paco2_mmhg is not None:
        winters_min = round(1.5 * data.hco3_meq_l + 6.0, 1)
        winters_max = round(1.5 * data.hco3_meq_l + 10.0, 1)

    disorders = _classify_disorders(data, corrected_ag, delta_ratio)
    if data.prior_known_disorder is not None:
        disorders = [data.prior_known_disorder] + [
            d for d in disorders if d != data.prior_known_disorder
        ]

    pearls = [
        f"Active sodium correction method: {method} (Hillier above glucose 400 mg/dL).",
        f"Albumin-corrected anion gap is {corrected_ag:.1f} mEq/L; Figge correction unmasked it."
        if corrected_ag > 12.0 >= raw_ag
        else f"Albumin-corrected anion gap is {corrected_ag:.1f} mEq/L.",
    ]
    if delta_ratio is not None:
        pearls.append(f"Delta ratio {delta_ratio}: >2 favors concurrent metabolic alkalosis.")
    if (
        winters_min is not None
        and winters_max is not None
        and data.paco2_mmhg is not None
    ):
        if data.paco2_mmhg < winters_min:
            pearls.append("Measured PaCO2 is below Winter's expected range: additional respiratory alkalosis.")
        elif data.paco2_mmhg > winters_max:
            pearls.append("Measured PaCO2 is above Winter's expected range: additional respiratory acidosis.")

    traps = [
        "Uncorrected sodium underestimates the true sodium in hyperglycemia.",
        "The raw anion gap misses HAGMA when albumin is low; always apply Figge correction.",
    ]
    return AcidBaseOutput(
        raw_anion_gap=round(raw_ag, 1),
        albumin_corrected_anion_gap=round(corrected_ag, 1),
        delta_ratio=delta_ratio,
        winters_expected_paco2_min=winters_min,
        winters_expected_paco2_max=winters_max,
        disorders=disorders,
        corrected_na_katz=katz,
        corrected_na_hillier=hillier,
        active_na_correction_method=method,
        clinical_pearls_and_actions=pearls,
        llm_trap_prevented=traps,
    )


def calculate_osmolality(data: OsmolalityInput) -> OsmolalityOutput:
    """Serum osmolality, osmolar gap, and free water deficit.

    Propagation: sodium, glucose, BUN, ethanol -> calculated osmolality ->
    osmolar gap -> toxic alcohol flag; weight/sex/age -> TBW -> free water deficit.
    """
    ethanol = data.ethanol_mg_dl or 0.0
    calculated = (
        2.0 * data.na_meq_l
        + data.glucose_mg_dl / 18.0
        + data.bun_mg_dl / 2.8
        + ethanol / 3.7
    )
    calculated = round(calculated, 1)

    gap: float | None = None
    toxic = False
    if data.measured_osmolality_mosm_kg is not None:
        gap = round(data.measured_osmolality_mosm_kg - calculated, 1)
        toxic = gap > 10.0

    deficit: float | None = None
    if data.weight_kg is not None and data.sex is not None:
        if data.age_years is not None and data.age_years >= 65.0:
            factor = 0.5 if data.sex == "male" else 0.45
        else:
            factor = 0.6 if data.sex == "male" else 0.5
        deficit = round(factor * data.weight_kg * (data.na_meq_l / 140.0 - 1.0), 2)

    pearls = [f"Calculated osmolality {calculated} mOsm/kg."]
    if toxic:
        pearls.append("Osmolar gap >10: screen for methanol, ethylene glycol, or isopropanol.")
    if deficit is not None:
        pearls.append(f"Free water deficit {deficit} L; replace cautiously and recheck sodium.")

    return OsmolalityOutput(
        calculated_osmolality_mosm_kg=calculated,
        osmolar_gap_mosm_kg=gap,
        free_water_deficit_l=deficit,
        toxic_alcohol_flag=toxic,
        clinical_pearls_and_actions=pearls,
        llm_trap_prevented=[
            "Measured osmolality without a calculated osmolality cannot produce an osmolar gap."
        ],
    )


def calculate_corrected_calcium(data: CalciumInput) -> CalciumOutput:
    """Payne albumin-corrected calcium.

    Propagation: albumin -> Payne correction -> corrected total calcium.
    """
    corrected = data.total_ca_mg_dl + 0.8 * (4.0 - data.albumin_g_dl)
    return CalciumOutput(
        corrected_ca_mg_dl=round(corrected, 2),
        clinical_pearls_and_actions=[
            "Corrected calcium estimates ionized calcium; confirm with a direct ionized measurement."
        ],
        llm_trap_prevented=[
            "Total calcium is falsely low in hypoalbuminemia; report the albumin-corrected value."
        ],
    )


__all__ = ["calculate_acid_base", "calculate_osmolality", "calculate_corrected_calcium"]
