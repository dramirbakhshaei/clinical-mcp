"""Pure cardiac repolarization and hemodynamic functions."""

from __future__ import annotations

import math

from clinical_mcp.schemas.cardiology import (
    HemodynamicsInput,
    HemodynamicsOutput,
    QTcInput,
    QTcOutput,
)


def calculate_qtc(data: QTcInput) -> QTcOutput:
    """Bazett, Fridericia, and Framingham QTc with Bogossian wide-QRS adjustment.

    Propagation: heart rate -> RR interval; QRS duration >=120 ms -> Bogossian
    modified QT -> all three rate-correction formulas -> auto-selected metric.
    """
    rr = 60.0 / data.hr_bpm
    qrs_widened = data.qrs_ms >= 120.0
    modified_qt: float | None = None
    numerator = data.qt_ms
    if qrs_widened:
        modified_qt = data.qt_ms - 0.485 * data.qrs_ms
        numerator = modified_qt

    bazett = numerator / math.sqrt(rr)
    fridericia = numerator / (rr ** (1.0 / 3.0))
    framingham = numerator + 154.0 * (1.0 - rr)

    if data.hr_bpm < 60.0:
        metric, recommended = "fridericia", fridericia
    elif data.hr_bpm > 100.0:
        metric, recommended = "framingham", framingham
    else:
        metric, recommended = "bazett", bazett

    recommended = round(recommended, 1)
    return QTcOutput(
        qrs_widened=qrs_widened,
        bogossian_modified_qt_ms=round(modified_qt, 1) if modified_qt is not None else None,
        qtc_bazett_ms=round(bazett, 1),
        qtc_fridericia_ms=round(fridericia, 1),
        qtc_framingham_ms=round(framingham, 1),
        recommended_primary_metric=metric,
        recommended_qtc_ms=recommended,
        torsades_risk=recommended >= 500.0,
        clinical_pearls_and_actions=[
            f"Use {metric} at this heart rate: QTc {recommended} ms.",
            "QTc >=500 ms or a >60 ms rise warrants stopping the offending drug.",
        ],
        llm_trap_prevented=[
            "Bazett over-corrects at tachycardia and under-corrects at bradycardia.",
            "A wide QRS inflates QTc; subtract the Bogossian 0.485 x QRS term before correcting.",
        ],
    )


def calculate_hemodynamics(data: HemodynamicsInput) -> HemodynamicsOutput:
    """MAP, pulse pressure, shock index, and modified shock index.

    Propagation: systolic and diastolic pressure -> MAP and pulse pressure;
    heart rate combined with SBP/MAP -> shock indices -> risk flags.
    """
    map_mmhg = (data.sbp_mmhg + 2.0 * data.dbp_mmhg) / 3.0
    pulse_pressure = data.sbp_mmhg - data.dbp_mmhg
    shock_index = data.hr_bpm / data.sbp_mmhg
    modified_shock_index = data.hr_bpm / map_mmhg

    return HemodynamicsOutput(
        map_mmhg=round(map_mmhg, 1),
        pulse_pressure_mmhg=round(pulse_pressure, 1),
        shock_index=round(shock_index, 2),
        modified_shock_index=round(modified_shock_index, 2),
        occult_shock=shock_index > 0.9,
        high_risk=modified_shock_index > 1.3,
        clinical_pearls_and_actions=[
            "Shock index >0.9 suggests occult shock even when blood pressure looks normal."
        ],
        llm_trap_prevented=[
            "A normal SBP does not exclude shock; the shock index exposes compensated states."
        ],
    )


__all__ = ["calculate_qtc", "calculate_hemodynamics"]
