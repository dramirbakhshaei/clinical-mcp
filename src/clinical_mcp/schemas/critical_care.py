"""Critical care oxygenation and sepsis schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from clinical_mcp.schemas.common import EngineInput, EngineOutput, UCUMUnit


class OxygenationInput(EngineInput):
    pao2_mmhg: float = Field(..., ge=20.0, le=600.0)
    paco2_mmhg: float = Field(..., ge=10.0, le=100.0)
    fio2: float = Field(..., ge=0.21, le=1.0)
    age_years: float = Field(..., ge=18.0, le=120.0)
    barometric_pressure_mmhg: float = Field(760.0, ge=500.0, le=800.0)
    respiratory_quotient: float = Field(0.8, ge=0.7, le=1.0)


class OxygenationOutput(EngineOutput):
    pao2_alveolar_mmhg: float
    aa_gradient_mmhg: float
    expected_aa_gradient_mmhg: float
    pf_ratio: float
    ards_stage: Literal["none", "mild", "moderate", "severe"]
    unit: UCUMUnit = UCUMUnit.MMHG


class QSOFASIRSInput(EngineInput):
    rr_bpm: float = Field(..., ge=5.0, le=60.0)
    sbp_mmhg: float = Field(..., ge=30.0, le=300.0)
    gcs_score: int = Field(..., ge=3, le=15)
    temp_celsius: float | None = Field(None, ge=20.0, le=45.0)
    hr_bpm: float | None = Field(None, ge=20.0, le=300.0)
    wbc_10e9_l: float | None = Field(None, ge=0.0, le=200.0)
    paco2_mmhg: float | None = Field(None, ge=10.0, le=100.0)
    lactate_mmol_l: float | None = Field(None, ge=0.0, le=30.0)


class QSOFASIRSOutput(EngineOutput):
    qsofa_score: int
    sirs_score: int | None
    sepsis_screen: Literal["low", "moderate", "high"]
    unit: UCUMUnit = UCUMUnit.SCORE
