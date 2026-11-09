"""Shared fixtures and canonical trap cases."""

from __future__ import annotations

import pytest

from clinical_mcp.schemas.acid_base import AcidBaseInput
from clinical_mcp.schemas.critical_care import QSOFASIRSInput
from clinical_mcp.schemas.renal import CKDEPIInput, CockcroftGaultInput


@pytest.fixture
def ckd_reference() -> CKDEPIInput:
    return CKDEPIInput(scr_mg_dl=1.0, age_years=40, sex="male")


@pytest.fixture
def obese_dosing() -> CockcroftGaultInput:
    return CockcroftGaultInput(
        age_years=60, sex="male", weight_kg=120.0, height_cm=165.0, scr_mg_dl=1.0
    )


@pytest.fixture
def hyperglycemia() -> AcidBaseInput:
    return AcidBaseInput(na_meq_l=140.0, cl_meq_l=100.0, hco3_meq_l=20.0, glucose_mg_dl=500.0)


@pytest.fixture
def septic_vitals() -> QSOFASIRSInput:
    return QSOFASIRSInput(
        rr_bpm=24.0,
        sbp_mmhg=90.0,
        gcs_score=14,
        temp_celsius=38.5,
        hr_bpm=110.0,
        wbc_10e9_l=14.0,
        lactate_mmol_l=4.2,
    )
