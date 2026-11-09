"""Shared Pydantic primitives for every clinical output."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class UCUMUnit(StrEnum):
    """Allowed UCUM-style units for v1 output models."""

    ML_MIN_1_73M2 = "mL/min/1.73m2"
    ML_MIN = "mL/min"
    PERCENT = "%"
    MEQ_L = "mEq/L"
    MG_DL = "mg/dL"
    MOSM_KG = "mOsm/kg"
    L = "L"
    MS = "ms"
    MMHG = "mmHg"
    L_MIN_M2 = "L/min/m2"
    SCORE = "score"
    NG_ML_FEU = "ng/mL FEU"


class LLMTrapCategory(StrEnum):
    HYPOALBUMINEMIA_MASKED_HAGMA = "HYPOALBUMINEMIA_MASKED_HAGMA"
    OBESITY_COCKCROFT_GAULT_OVERDOSE = "OBESITY_COCKCROFT_GAULT_OVERDOSE"
    DIURETIC_FENA_MISINTERPRETATION = "DIURETIC_FENA_MISINTERPRETATION"
    TACHYCARDIA_OR_WIDE_QRS_QTC_ARTIFACT = "TACHYCARDIA_OR_WIDE_QRS_QTC_ARTIFACT"
    UNOS_MELD_LOGARITHMIC_BOUNDARY_VIOLATION = "UNOS_MELD_LOGARITHMIC_BOUNDARY_VIOLATION"
    AGE_UNADJUSTED_DDIMER_FALSE_POSITIVE = "AGE_UNADJUSTED_DDIMER_FALSE_POSITIVE"


class AcidBaseDisorder(StrEnum):
    NORMAL = "NORMAL"
    PURE_HAGMA = "PURE_HAGMA"
    PURE_NAGMA = "PURE_NAGMA"
    MIXED_HAGMA_NAGMA = "MIXED_HAGMA_NAGMA"
    HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS = (
        "HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS"
    )
    UNCOMPENSATED_RESPIRATORY_ACIDOSIS = "UNCOMPENSATED_RESPIRATORY_ACIDOSIS"
    SUPERIMPOSED_RESPIRATORY_ALKALOSIS = "SUPERIMPOSED_RESPIRATORY_ALKALOSIS"


class EngineInput(BaseModel):
    """Base input: reject unknown keys so typos never silently change a dose."""

    model_config = ConfigDict(extra="forbid")


class EngineOutput(BaseModel):
    """Base output: flat numeric fields plus one top-level UCUM unit."""

    model_config = ConfigDict(extra="forbid")

    unit: UCUMUnit
    clinical_pearls_and_actions: list[str] = []
    llm_trap_prevented: list[str] = []


class ClampAuditTrail(BaseModel):
    parameter: str
    original_value: float
    clamped_value: float
    rule: str
