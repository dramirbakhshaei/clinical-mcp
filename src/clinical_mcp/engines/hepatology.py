"""Pure hepatic severity and fibrosis functions."""

from __future__ import annotations

import math
from typing import Literal

from clinical_mcp.schemas.common import ClampAuditTrail
from clinical_mcp.schemas.hepatology import (
    FIB4Input,
    FIB4Output,
    MELDInput,
    MELDOutput,
)


def _bracket(score: float) -> str:
    if score >= 40.0:
        return "71.3%"
    if score >= 30.0:
        return "52.6%"
    if score >= 20.0:
        return "19.6%"
    if score >= 10.0:
        return "6.0%"
    return "1.9%"


def calculate_meld(data: MELDInput) -> MELDOutput:
    """MELD-Na and MELD 3.0 with UNOS clamp audit.

    Propagation: raw bilirubin, INR, creatinine, sodium, albumin -> UNOS floor
    and cap clamps (creatinine cap 4.0 for MELD-Na, 3.0 for MELD 3.0) ->
    logarithmic scores -> 90-day mortality bracket.
    """
    clamps: list[ClampAuditTrail] = []

    bilirubin = max(1.0, data.bilirubin_mg_dl)
    if bilirubin != data.bilirubin_mg_dl:
        clamps.append(
            ClampAuditTrail(
                parameter="bilirubin_mg_dl",
                original_value=data.bilirubin_mg_dl,
                clamped_value=bilirubin,
                rule="UNOS floor 1.0",
            )
        )
    inr = max(1.0, data.inr)
    if inr != data.inr:
        clamps.append(
            ClampAuditTrail(
                parameter="inr", original_value=data.inr, clamped_value=inr, rule="UNOS floor 1.0"
            )
        )

    cr_na = max(1.0, data.creatinine_mg_dl)
    if cr_na != data.creatinine_mg_dl:
        clamps.append(
            ClampAuditTrail(
                parameter="creatinine_mg_dl",
                original_value=data.creatinine_mg_dl,
                clamped_value=cr_na,
                rule="UNOS floor 1.0",
            )
        )
    if data.dialysis:
        cr_na = 4.0
        clamps.append(
            ClampAuditTrail(
                parameter="creatinine_mg_dl (MELD-Na)",
                original_value=data.creatinine_mg_dl,
                clamped_value=cr_na,
                rule="dialysis -> 4.0",
            )
        )
    elif cr_na > 4.0:
        cr_na = 4.0
        clamps.append(
            ClampAuditTrail(
                parameter="creatinine_mg_dl (MELD-Na)",
                original_value=data.creatinine_mg_dl,
                clamped_value=cr_na,
                rule="MELD-Na cap 4.0",
            )
        )

    cr_3 = max(1.0, data.creatinine_mg_dl)
    if data.dialysis:
        cr_3 = 3.0
        clamps.append(
            ClampAuditTrail(
                parameter="creatinine_mg_dl (MELD 3.0)",
                original_value=data.creatinine_mg_dl,
                clamped_value=cr_3,
                rule="dialysis -> 3.0",
            )
        )
    elif cr_3 > 3.0:
        cr_3 = 3.0
        clamps.append(
            ClampAuditTrail(
                parameter="creatinine_mg_dl (MELD 3.0)",
                original_value=data.creatinine_mg_dl,
                clamped_value=cr_3,
                rule="MELD 3.0 cap 3.0",
            )
        )

    sodium = min(137.0, max(125.0, data.sodium_meq_l))
    if sodium != data.sodium_meq_l:
        clamps.append(
            ClampAuditTrail(
                parameter="sodium_meq_l",
                original_value=data.sodium_meq_l,
                clamped_value=sodium,
                rule="UNOS clamp 125-137",
            )
        )

    albumin = min(3.5, max(1.5, data.albumin_g_dl))
    if albumin != data.albumin_g_dl:
        clamps.append(
            ClampAuditTrail(
                parameter="albumin_g_dl",
                original_value=data.albumin_g_dl,
                clamped_value=albumin,
                rule="UNOS clamp 1.5-3.5",
            )
        )

    meld_base = (
        3.78 * math.log(bilirubin)
        + 11.2 * math.log(inr)
        + 9.57 * math.log(cr_na)
        + 6.43
    )
    meld_na = meld_base + 1.32 * (137.0 - sodium) - 0.033 * meld_base * (137.0 - sodium)
    meld_na = round(max(6.0, meld_na), 1)

    meld_3 = (
        1.33 * (1.0 if data.sex == "female" else 0.0)
        + 4.56 * math.log(bilirubin)
        + 0.82 * (137.0 - sodium)
        - 0.24 * (137.0 - sodium) * math.log(bilirubin)
        + 9.53 * math.log(inr)
        + 11.14 * math.log(cr_3)
        + 1.85 * math.log(albumin)
        - 1.53 * math.log(cr_3) * math.log(albumin)
        + 6.43
    )
    meld_3 = round(max(6.0, meld_3), 1)

    return MELDOutput(
        meld_na=meld_na,
        meld_3=meld_3,
        mortality_bracket_meld_na=_bracket(meld_na),
        mortality_bracket_meld_3=_bracket(meld_3),
        clamps_applied=clamps,
        clinical_pearls_and_actions=[
            "Use MELD 3.0 for allocation; MELD-Na remains useful for trending.",
            f"90-day mortality bracket: {_bracket(meld_3)}.",
        ],
        llm_trap_prevented=[
            "UNOS floors every component at 1.0 and caps creatinine; skipping clamps changes the score.",
            "MELD 3.0 caps creatinine at 3.0, unlike MELD-Na at 4.0.",
        ],
    )


def calculate_fib4(data: FIB4Input) -> FIB4Output:
    """FIB-4 fibrosis index.

    Propagation: age, AST, ALT, platelets -> FIB-4 index -> fibrosis risk stage.
    """
    fib4 = (data.age_years * data.ast_u_l) / (
        data.platelets_10e9_l * math.sqrt(data.alt_u_l)
    )
    fib4 = round(fib4, 2)
    risk: Literal["low", "indeterminate", "high"]
    if fib4 < 1.45:
        risk = "low"
    elif fib4 <= 3.25:
        risk = "indeterminate"
    else:
        risk = "high"
    return FIB4Output(
        fib4_index=fib4,
        fibrosis_risk=risk,
        clinical_pearls_and_actions=[f"FIB-4 {fib4} is {risk} risk for advanced fibrosis."],
        llm_trap_prevented=["FIB-4 uses platelets and the square root of ALT, not ALT alone."],
    )


__all__ = ["calculate_meld", "calculate_fib4"]
