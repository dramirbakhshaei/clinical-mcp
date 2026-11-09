"""Fail-fast biological boundary guards."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from clinical_mcp.schemas.acid_base import AcidBaseInput, CalciumInput, OsmolalityInput
from clinical_mcp.schemas.cardiology import HemodynamicsInput, QTcInput
from clinical_mcp.schemas.critical_care import OxygenationInput, QSOFASIRSInput
from clinical_mcp.schemas.hematology import PEDDimerInput
from clinical_mcp.schemas.hepatology import FIB4Input, MELDInput
from clinical_mcp.schemas.renal import AKIIndicesInput, CKDEPIInput, CockcroftGaultInput
from clinical_mcp.schemas.validators import check_range


class TestRenalBoundaries:
    def test_creatinine(self) -> None:
        with pytest.raises(ValidationError):
            CKDEPIInput(scr_mg_dl=0.05, age_years=40, sex="male")
        with pytest.raises(ValidationError):
            CKDEPIInput(scr_mg_dl=31, age_years=40, sex="male")

    def test_age_and_weight(self) -> None:
        with pytest.raises(ValidationError):
            CKDEPIInput(scr_mg_dl=1, age_years=121, sex="male")
        with pytest.raises(ValidationError):
            CockcroftGaultInput(
                age_years=60, sex="male", weight_kg=351, height_cm=170, scr_mg_dl=1
            )

    def test_aki_zero_urine_creatinine(self) -> None:
        with pytest.raises(ValidationError):
            AKIIndicesInput(
                urine_sodium_meq_l=20,
                serum_sodium_meq_l=140,
                urine_creatinine_mg_dl=0,
                serum_creatinine_mg_dl=1.0,
            )


class TestAcidBaseBoundaries:
    def test_ph(self) -> None:
        for ph in (6.4, 7.9):
            with pytest.raises(ValidationError):
                AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=24, ph=ph)

    def test_sodium_and_glucose(self) -> None:
        with pytest.raises(ValidationError):
            AcidBaseInput(na_meq_l=99, cl_meq_l=100, hco3_meq_l=24)
        with pytest.raises(ValidationError):
            OsmolalityInput(na_meq_l=140, glucose_mg_dl=-1, bun_mg_dl=14)

    def test_albumin(self) -> None:
        with pytest.raises(ValidationError):
            CalciumInput(total_ca_mg_dl=8.0, albumin_g_dl=0.1)


class TestCardiologyBoundaries:
    def test_qt_hr_qrs(self) -> None:
        with pytest.raises(ValidationError):
            QTcInput(qt_ms=149, hr_bpm=70)
        with pytest.raises(ValidationError):
            QTcInput(qt_ms=801, hr_bpm=70)
        with pytest.raises(ValidationError):
            QTcInput(qt_ms=400, hr_bpm=19)
        with pytest.raises(ValidationError):
            QTcInput(qt_ms=400, hr_bpm=70, qrs_ms=201)

    def test_hemodynamics(self) -> None:
        with pytest.raises(ValidationError):
            HemodynamicsInput(sbp_mmhg=301, dbp_mmhg=80, hr_bpm=70)


class TestHepatologyBoundaries:
    def test_meld(self) -> None:
        with pytest.raises(ValidationError):
            MELDInput(
                bilirubin_mg_dl=0.0,
                inr=1.0,
                creatinine_mg_dl=1.0,
                sodium_meq_l=135,
                albumin_g_dl=3.0,
            )
        with pytest.raises(ValidationError):
            MELDInput(
                bilirubin_mg_dl=2.0,
                inr=0.4,
                creatinine_mg_dl=1.0,
                sodium_meq_l=135,
                albumin_g_dl=3.0,
            )

    def test_fib4(self) -> None:
        with pytest.raises(ValidationError):
            FIB4Input(age_years=120, ast_u_l=40, alt_u_l=30, platelets_10e9_l=5)


class TestCriticalCareBoundaries:
    def test_fio2_and_gcs(self) -> None:
        with pytest.raises(ValidationError):
            OxygenationInput(pao2_mmhg=100, paco2_mmhg=40, fio2=0.2, age_years=40)
        with pytest.raises(ValidationError):
            OxygenationInput(pao2_mmhg=601, paco2_mmhg=40, fio2=0.5, age_years=40)
        with pytest.raises(ValidationError):
            QSOFASIRSInput(rr_bpm=20, sbp_mmhg=120, gcs_score=16)


class TestPEDDimerBoundaries:
    def test_age_and_ddimer(self) -> None:
        with pytest.raises(ValidationError):
            PEDDimerInput(age_years=121, d_dimer_ng_ml_feu=100, wells_score=1)
        with pytest.raises(ValidationError):
            PEDDimerInput(age_years=60, d_dimer_ng_ml_feu=50001, wells_score=1)


class TestPediatricRejection:
    def test_pediatric_out_of_scope(self) -> None:
        with pytest.raises(ValidationError):
            CKDEPIInput(scr_mg_dl=0.5, age_years=10, sex="male")


class TestClinicalMessageHelper:
    def test_check_range_message(self) -> None:
        with pytest.raises(ValueError, match="incompatible with life"):
            check_range("pH", 6.4, 6.5, 7.8)
        assert check_range("pH", 7.4, 6.5, 7.8) == 7.4
