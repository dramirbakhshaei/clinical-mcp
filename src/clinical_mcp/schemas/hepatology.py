"""Hepatic severity and fibrosis schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from clinical_mcp.schemas.common import ClampAuditTrail, EngineInput, EngineOutput, UCUMUnit


class MELDInput(EngineInput):
    bilirubin_mg_dl: float = Field(..., ge=0.1, le=60.0)
    inr: float = Field(..., ge=0.5, le=10.0)
    creatinine_mg_dl: float = Field(..., ge=0.1, le=15.0)
    sodium_meq_l: float = Field(..., ge=100.0, le=180.0)
    albumin_g_dl: float = Field(..., ge=0.5, le=6.0)
    sex: Literal["male", "female"] = "male"
    dialysis: bool = False


class MELDOutput(EngineOutput):
    meld_na: float
    meld_3: float
    mortality_bracket_meld_na: str
    mortality_bracket_meld_3: str
    clamps_applied: list[ClampAuditTrail]
    unit: UCUMUnit = UCUMUnit.SCORE


class FIB4Input(EngineInput):
    age_years: float = Field(..., ge=18.0, le=120.0)
    ast_u_l: float = Field(..., ge=1.0, le=10000.0)
    alt_u_l: float = Field(..., ge=1.0, le=10000.0)
    platelets_10e9_l: float = Field(..., ge=10.0, le=1000.0)


class FIB4Output(EngineOutput):
    fib4_index: float
    fibrosis_risk: Literal["low", "indeterminate", "high"]
    unit: UCUMUnit = UCUMUnit.SCORE
