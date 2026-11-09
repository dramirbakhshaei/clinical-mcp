"""Critical care tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from clinical_mcp.engines.critical_care import calculate_oxygenation, calculate_qsofa
from clinical_mcp.schemas.critical_care import OxygenationInput, QSOFASIRSInput


class TestOxygenationSchemas:
    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            OxygenationInput(pao2_mmhg=100, paco2_mmhg=40, fio2=0.1, age_years=40)


class TestQSOFASIRSchemas:
    def test_temp_lower_bound_is_20(self) -> None:
        model = QSOFASIRSInput(
            rr_bpm=20, sbp_mmhg=120, gcs_score=15, temp_celsius=20.0
        )
        assert model.temp_celsius == 20.0
        with pytest.raises(ValidationError):
            QSOFASIRSInput(rr_bpm=20, sbp_mmhg=120, gcs_score=15, temp_celsius=19.9)


class TestOxygenation:
    def test_alveolar_gas(self) -> None:
        result = calculate_oxygenation(
            OxygenationInput(pao2_mmhg=80, paco2_mmhg=40, fio2=0.21, age_years=40)
        )
        assert result.pao2_alveolar_mmhg == pytest.approx(99.7, abs=0.1)
        assert result.aa_gradient_mmhg == pytest.approx(19.7, abs=0.1)
        assert result.expected_aa_gradient_mmhg == 14.0
        assert result.pf_ratio == pytest.approx(381.0, abs=0.1)
        assert result.ards_stage == "none"

    @pytest.mark.parametrize(
        ("fio2", "pao2", "stage"),
        [(0.4, 100.0, "mild"), (0.5, 75.0, "moderate"), (0.8, 64.0, "severe")],
    )
    def test_berlin_staging(self, fio2: float, pao2: float, stage: str) -> None:
        result = calculate_oxygenation(
            OxygenationInput(pao2_mmhg=pao2, paco2_mmhg=40, fio2=fio2, age_years=40)
        )
        assert result.ards_stage == stage


class TestQSOFASIRS:
    def test_septic_patient(self, septic_vitals: QSOFASIRSInput) -> None:
        result = calculate_qsofa(septic_vitals)
        assert result.qsofa_score == 3
        assert result.sirs_score == 4
        assert result.sepsis_screen == "high"

    def test_sirs_none_with_one_parameter(self) -> None:
        result = calculate_qsofa(QSOFASIRSInput(rr_bpm=18, sbp_mmhg=120, gcs_score=15))
        assert result.sirs_score is None
        assert result.qsofa_score == 0
        assert result.sepsis_screen == "low"

    def test_temp_and_wbc_criteria(self) -> None:
        result = calculate_qsofa(
            QSOFASIRSInput(
                rr_bpm=18,
                sbp_mmhg=120,
                gcs_score=15,
                temp_celsius=35.5,
                wbc_10e9_l=3.0,
            )
        )
        assert result.sirs_score == 2
        assert result.sepsis_screen == "high"

    def test_moderate_lactate(self) -> None:
        result = calculate_qsofa(
            QSOFASIRSInput(rr_bpm=18, sbp_mmhg=120, gcs_score=15, lactate_mmol_l=2.5)
        )
        assert result.sepsis_screen == "moderate"

    def test_high_lactate(self) -> None:
        result = calculate_qsofa(
            QSOFASIRSInput(rr_bpm=18, sbp_mmhg=120, gcs_score=15, lactate_mmol_l=4.0)
        )
        assert result.sepsis_screen == "high"
