"""Renal and pharmacokinetic schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from clinical_mcp.schemas.common import EngineInput, EngineOutput, UCUMUnit


class CKDEPIInput(EngineInput):
    scr_mg_dl: float = Field(..., ge=0.1, le=30.0)
    age_years: float = Field(..., ge=18.0, le=120.0)
    sex: Literal["male", "female"]


class CKDEPIOutput(EngineOutput):
    egfr_ml_min_per_173m2: float
    kdigo_stage: Literal["G1", "G2", "G3a", "G3b", "G4", "G5"]
    unit: UCUMUnit = UCUMUnit.ML_MIN_1_73M2


class CockcroftGaultInput(EngineInput):
    age_years: float = Field(..., ge=18.0, le=120.0)
    sex: Literal["male", "female"]
    weight_kg: float = Field(..., ge=20.0, le=350.0)
    height_cm: float = Field(..., ge=100.0, le=250.0)
    scr_mg_dl: float = Field(..., ge=0.1, le=30.0)


class CockcroftGaultOutput(EngineOutput):
    bmi: float
    ibw_kg: float
    adjbw_kg: float
    selected_weight_kg: float
    weight_selection_rule: Literal["actual", "ibw", "adjbw"]
    crcl_ml_min: float
    unit: UCUMUnit = UCUMUnit.ML_MIN


class AKIIndicesInput(EngineInput):
    urine_sodium_meq_l: float = Field(..., ge=0.0, le=300.0)
    serum_sodium_meq_l: float = Field(..., ge=100.0, le=180.0)
    urine_creatinine_mg_dl: float = Field(..., gt=0.0, le=500.0)
    serum_creatinine_mg_dl: float = Field(..., ge=0.1, le=30.0)
    on_diuretics: bool = False
    serum_bun_mg_dl: float | None = Field(None, ge=1.0, le=200.0)
    urine_urea_mg_dl: float | None = Field(None, ge=1.0, le=5000.0)


class AKIIndicesOutput(EngineOutput):
    fena_percent: float
    feurea_percent: float | None
    aki_etiology: Literal["prerenal", "atn", "indeterminate", "diuretic_confounded"]
    unit: UCUMUnit = UCUMUnit.PERCENT
