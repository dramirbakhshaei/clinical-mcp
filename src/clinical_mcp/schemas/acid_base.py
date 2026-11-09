"""Acid-base, osmolality, and corrected calcium schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from clinical_mcp.schemas.common import (
    AcidBaseDisorder,
    EngineInput,
    EngineOutput,
    UCUMUnit,
)


class AcidBaseInput(EngineInput):
    na_meq_l: float = Field(..., ge=100.0, le=180.0)
    cl_meq_l: float = Field(..., ge=50.0, le=150.0)
    hco3_meq_l: float = Field(..., ge=1.0, le=60.0)
    albumin_g_dl: float = Field(4.0, ge=0.5, le=6.0)
    glucose_mg_dl: float = Field(100.0, ge=0.0, le=2000.0)
    paco2_mmhg: float | None = Field(None, ge=10.0, le=100.0)
    ph: float | None = Field(None, ge=6.5, le=7.8)
    lactate_mmol_l: float | None = Field(None, ge=0.0, le=30.0)
    prior_known_disorder: AcidBaseDisorder | None = None


class AcidBaseOutput(EngineOutput):
    raw_anion_gap: float
    albumin_corrected_anion_gap: float
    delta_ratio: float | None
    winters_expected_paco2_min: float | None
    winters_expected_paco2_max: float | None
    disorders: list[AcidBaseDisorder]
    corrected_na_katz: float
    corrected_na_hillier: float
    active_na_correction_method: Literal["katz", "hillier"]
    unit: UCUMUnit = UCUMUnit.MEQ_L


class OsmolalityInput(EngineInput):
    na_meq_l: float = Field(..., ge=100.0, le=180.0)
    glucose_mg_dl: float = Field(..., ge=0.0, le=2000.0)
    bun_mg_dl: float = Field(..., ge=1.0, le=200.0)
    measured_osmolality_mosm_kg: float | None = Field(None, ge=100.0, le=1000.0)
    ethanol_mg_dl: float | None = Field(None, ge=0.0, le=1000.0)
    weight_kg: float | None = Field(None, ge=20.0, le=350.0)
    sex: Literal["male", "female"] | None = None
    age_years: float | None = Field(None, ge=18.0, le=120.0)


class OsmolalityOutput(EngineOutput):
    calculated_osmolality_mosm_kg: float
    osmolar_gap_mosm_kg: float | None
    free_water_deficit_l: float | None
    toxic_alcohol_flag: bool
    unit: UCUMUnit = UCUMUnit.MOSM_KG


class CalciumInput(EngineInput):
    total_ca_mg_dl: float = Field(..., ge=4.0, le=15.0)
    albumin_g_dl: float = Field(..., ge=0.5, le=6.0)


class CalciumOutput(EngineOutput):
    corrected_ca_mg_dl: float
    unit: UCUMUnit = UCUMUnit.MG_DL
