"""Pure pulmonary embolism risk functions."""

from __future__ import annotations

from typing import Literal

from clinical_mcp.schemas.hematology import PEDDimerInput, PEDDimerOutput


def calculate_peddimer(data: PEDDimerInput) -> PEDDimerOutput:
    """Wells score plus age-adjusted D-dimer threshold.

    Propagation: age -> age-adjusted D-dimer threshold -> D-dimer positivity ->
    Wells probability -> CTPA indication.
    """
    threshold = data.age_years * 10.0 if data.age_years > 50.0 else 500.0
    positive = data.d_dimer_ng_ml_feu > threshold

    probability: Literal["low", "moderate", "high"]
    if data.wells_score < 2.0:
        probability = "low"
    elif data.wells_score <= 6.0:
        probability = "moderate"
    else:
        probability = "high"

    ctpa = positive or data.wells_score > 6.0
    return PEDDimerOutput(
        age_adjusted_threshold_ng_ml=threshold,
        ddimer_positive=positive,
        ctpa_indicated=ctpa,
        wells_probability=probability,
        clinical_pearls_and_actions=[
            f"Age-adjusted threshold is {threshold:.0f} ng/mL FEU; Wells probability {probability}.",
            "A negative age-adjusted D-dimer in a low/moderate Wells patient can exclude PE.",
        ],
        llm_trap_prevented=[
            "A fixed 500 ng/mL threshold over-calls PE in older adults; multiply age by 10 after 50."
        ],
    )


__all__ = ["calculate_peddimer"]
