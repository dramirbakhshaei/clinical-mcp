"""Pure critical care oxygenation and sepsis functions."""

from __future__ import annotations

from typing import Literal

from clinical_mcp.schemas.critical_care import (
    OxygenationInput,
    OxygenationOutput,
    QSOFASIRSInput,
    QSOFASIRSOutput,
)


def calculate_oxygenation(data: OxygenationInput) -> OxygenationOutput:
    """Alveolar gas equation, A-a gradient, and Berlin P/F staging.

    Propagation: FiO2, barometric pressure, PaCO2, RQ -> alveolar PAO2 ->
    A-a gradient; PaO2/FiO2 -> Berlin ARDS stage.
    """
    pao2_alveolar = data.fio2 * (data.barometric_pressure_mmhg - 47.0) - (
        data.paco2_mmhg / data.respiratory_quotient
    )
    aa_gradient = pao2_alveolar - data.pao2_mmhg
    expected = data.age_years / 4.0 + 4.0
    pf_ratio = data.pao2_mmhg / data.fio2

    stage: Literal["none", "mild", "moderate", "severe"]
    if pf_ratio <= 100.0:
        stage = "severe"
    elif pf_ratio <= 200.0:
        stage = "moderate"
    elif pf_ratio <= 300.0:
        stage = "mild"
    else:
        stage = "none"

    return OxygenationOutput(
        pao2_alveolar_mmhg=round(pao2_alveolar, 1),
        aa_gradient_mmhg=round(aa_gradient, 1),
        expected_aa_gradient_mmhg=round(expected, 1),
        pf_ratio=round(pf_ratio, 1),
        ards_stage=stage,
        clinical_pearls_and_actions=[
            f"P/F {pf_ratio:.1f} corresponds to Berlin {stage} ARDS.",
            "The alveolar gas equation subtracts 47 mmHg of water vapor pressure.",
        ],
        llm_trap_prevented=[
            "Omitting the 47 mmHg water-vapor term overestimates alveolar oxygen.",
            "Berlin staging uses the P/F ratio, not PaO2 alone.",
        ],
    )


def calculate_qsofa(data: QSOFASIRSInput) -> QSOFASIRSOutput:
    """qSOFA always, SIRS only with at least two available parameters.

    Propagation: RR/SBP/GCS -> qSOFA; temperature, HR, RR, WBC -> SIRS ->
    lactate integration -> sepsis screen.
    """
    qsofa = 0
    if data.rr_bpm >= 22.0:
        qsofa += 1
    if data.sbp_mmhg <= 100.0:
        qsofa += 1
    if data.gcs_score < 15:
        qsofa += 1

    parameters = [
        data.temp_celsius is not None,
        data.hr_bpm is not None,
        True,  # RR is required
        data.wbc_10e9_l is not None,
    ]
    sirs: int | None = None
    if sum(parameters) >= 2:
        sirs = 0
        if data.temp_celsius is not None and (
            data.temp_celsius > 38.0 or data.temp_celsius < 36.0
        ):
            sirs += 1
        if data.hr_bpm is not None and data.hr_bpm > 90.0:
            sirs += 1
        if data.rr_bpm > 20.0:
            sirs += 1
        if data.wbc_10e9_l is not None and (
            data.wbc_10e9_l > 12.0 or data.wbc_10e9_l < 4.0
        ):
            sirs += 1

    lactate = data.lactate_mmol_l
    screen: Literal["low", "moderate", "high"]
    if qsofa >= 2 or (sirs is not None and sirs >= 2) or (lactate is not None and lactate >= 4.0):
        screen = "high"
    elif qsofa == 1 or (lactate is not None and lactate >= 2.0):
        screen = "moderate"
    else:
        screen = "low"

    return QSOFASIRSOutput(
        qsofa_score=qsofa,
        sirs_score=sirs,
        sepsis_screen=screen,
        clinical_pearls_and_actions=[
            f"qSOFA {qsofa}; SIRS {sirs if sirs is not None else 'not computable'}; screen {screen}.",
            "qSOFA >=2 is a prompt for urgent reassessment, not a diagnosis.",
        ],
        llm_trap_prevented=[
            "SIRS cannot be scored from a single parameter; require at least two available criteria."
        ],
    )


__all__ = ["calculate_oxygenation", "calculate_qsofa"]
