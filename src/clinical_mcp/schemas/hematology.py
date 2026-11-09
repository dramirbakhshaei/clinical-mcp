"""Pulmonary embolism risk schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from clinical_mcp.schemas.common import EngineInput, EngineOutput, UCUMUnit


class PEDDimerInput(EngineInput):
    age_years: float = Field(..., ge=18.0, le=120.0)
    d_dimer_ng_ml_feu: float = Field(..., ge=0.0, le=50000.0)
    wells_score: float = Field(..., ge=0.0, le=12.5)


class PEDDimerOutput(EngineOutput):
    age_adjusted_threshold_ng_ml: float
    ddimer_positive: bool
    ctpa_indicated: bool
    wells_probability: Literal["low", "moderate", "high"]
    unit: UCUMUnit = UCUMUnit.NG_ML_FEU
