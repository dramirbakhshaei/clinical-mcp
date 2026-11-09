"""Renal engine and schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from clinical_mcp.engines.renal import (
    calculate_aki_indices,
    calculate_ckd_epi,
    calculate_cockcroft_gault,
)
from clinical_mcp.schemas.renal import (
    AKIIndicesInput,
    CKDEPIInput,
    CockcroftGaultInput,
)


class TestCKDEPISchemas:
    def test_valid(self) -> None:
        model = CKDEPIInput(scr_mg_dl=1.0, age_years=40, sex="male")
        assert model.sex == "male"

    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CKDEPIInput(scr_mg_dl=0.05, age_years=40, sex="male")
        with pytest.raises(ValidationError):
            CKDEPIInput(scr_mg_dl=1.0, age_years=17, sex="male")


class TestCockcroftGaultSchemas:
    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CockcroftGaultInput(
                age_years=60, sex="male", weight_kg=10, height_cm=165, scr_mg_dl=1.0
            )
        with pytest.raises(ValidationError):
            CockcroftGaultInput(
                age_years=60, sex="male", weight_kg=80, height_cm=90, scr_mg_dl=1.0
            )


class TestAKIIndicesSchemas:
    def test_optional_fields(self) -> None:
        model = AKIIndicesInput(
            urine_sodium_meq_l=20,
            serum_sodium_meq_l=140,
            urine_creatinine_mg_dl=100,
            serum_creatinine_mg_dl=1.0,
        )
        assert model.serum_bun_mg_dl is None
        assert model.urine_urea_mg_dl is None


class TestCKDEPI:
    def test_gold_standard(self) -> None:
        result = calculate_ckd_epi(CKDEPIInput(scr_mg_dl=1.0, age_years=40, sex="male"))
        assert result.egfr_ml_min_per_173m2 == pytest.approx(97.6, abs=0.3)
        assert result.kdigo_stage == "G1"
        assert result.unit.value == "mL/min/1.73m2"

    @pytest.mark.parametrize(
        ("scr", "stage"),
        [(1.4, "G2"), (1.8, "G3a"), (2.4, "G3b"), (4.5, "G4"), (8.0, "G5")],
    )
    def test_kdigo_stages(self, scr: float, stage: str) -> None:
        result = calculate_ckd_epi(CKDEPIInput(scr_mg_dl=scr, age_years=40, sex="male"))
        assert result.kdigo_stage == stage

    def test_female_coefficient(self) -> None:
        male = calculate_ckd_epi(CKDEPIInput(scr_mg_dl=1.0, age_years=50, sex="male"))
        female = calculate_ckd_epi(CKDEPIInput(scr_mg_dl=1.0, age_years=50, sex="female"))
        assert female.egfr_ml_min_per_173m2 < male.egfr_ml_min_per_173m2

    def test_2021_constant_142(self) -> None:
        result = calculate_ckd_epi(CKDEPIInput(scr_mg_dl=1.0, age_years=40, sex="male"))
        assert 97.0 < result.egfr_ml_min_per_173m2 < 98.5


class TestCockcroftGault:
    def test_obese_switches_to_adjbw(self, obese_dosing: CockcroftGaultInput) -> None:
        result = calculate_cockcroft_gault(obese_dosing)
        assert result.bmi > 40
        assert result.weight_selection_rule == "adjbw"
        assert result.selected_weight_kg == result.adjbw_kg
        assert result.crcl_ml_min == pytest.approx(94.2, abs=0.3)

    def test_underweight_uses_actual(self) -> None:
        result = calculate_cockcroft_gault(
            CockcroftGaultInput(
                age_years=40, sex="male", weight_kg=50.0, height_cm=180.0, scr_mg_dl=1.0
            )
        )
        assert result.weight_selection_rule == "actual"
        assert result.selected_weight_kg == 50.0

    def test_normal_uses_ibw(self) -> None:
        result = calculate_cockcroft_gault(
            CockcroftGaultInput(
                age_years=40, sex="male", weight_kg=80.0, height_cm=180.0, scr_mg_dl=1.0
            )
        )
        assert result.weight_selection_rule == "ibw"
        assert result.selected_weight_kg == result.ibw_kg

    def test_female_factor(self) -> None:
        male = calculate_cockcroft_gault(
            CockcroftGaultInput(
                age_years=40, sex="male", weight_kg=70.0, height_cm=170.0, scr_mg_dl=1.0
            )
        )
        female = calculate_cockcroft_gault(
            CockcroftGaultInput(
                age_years=40, sex="female", weight_kg=70.0, height_cm=170.0, scr_mg_dl=1.0
            )
        )
        assert female.crcl_ml_min < male.crcl_ml_min


class TestAKIIndices:
    def test_fena_prerenal(self) -> None:
        result = calculate_aki_indices(
            AKIIndicesInput(
                urine_sodium_meq_l=40,
                serum_sodium_meq_l=140,
                urine_creatinine_mg_dl=100,
                serum_creatinine_mg_dl=1.0,
            )
        )
        assert result.fena_percent == pytest.approx(0.29, abs=0.01)
        assert result.aki_etiology == "prerenal"
        assert result.feurea_percent is None

    def test_fena_atn(self) -> None:
        result = calculate_aki_indices(
            AKIIndicesInput(
                urine_sodium_meq_l=80,
                serum_sodium_meq_l=140,
                urine_creatinine_mg_dl=50,
                serum_creatinine_mg_dl=2.0,
            )
        )
        assert result.aki_etiology == "atn"

    def test_indeterminate_fena(self) -> None:
        result = calculate_aki_indices(
            AKIIndicesInput(
                urine_sodium_meq_l=175,
                serum_sodium_meq_l=140,
                urine_creatinine_mg_dl=100,
                serum_creatinine_mg_dl=1.0,
            )
        )
        assert result.aki_etiology == "indeterminate"

    def test_feuera_prerenal(self) -> None:
        result = calculate_aki_indices(
            AKIIndicesInput(
                urine_sodium_meq_l=40,
                serum_sodium_meq_l=140,
                urine_creatinine_mg_dl=100,
                serum_creatinine_mg_dl=1.0,
                serum_bun_mg_dl=20,
                urine_urea_mg_dl=400,
            )
        )
        assert result.feurea_percent == pytest.approx(20.0)
        assert result.aki_etiology == "prerenal"

    def test_feuera_atn(self) -> None:
        result = calculate_aki_indices(
            AKIIndicesInput(
                urine_sodium_meq_l=40,
                serum_sodium_meq_l=140,
                urine_creatinine_mg_dl=100,
                serum_creatinine_mg_dl=1.0,
                serum_bun_mg_dl=20,
                urine_urea_mg_dl=1200,
            )
        )
        assert result.aki_etiology == "atn"

    def test_feuera_indeterminate(self) -> None:
        result = calculate_aki_indices(
            AKIIndicesInput(
                urine_sodium_meq_l=40,
                serum_sodium_meq_l=140,
                urine_creatinine_mg_dl=100,
                serum_creatinine_mg_dl=1.0,
                serum_bun_mg_dl=20,
                urine_urea_mg_dl=800,
            )
        )
        assert result.aki_etiology == "indeterminate"

    def test_diuretic_confounded(self) -> None:
        result = calculate_aki_indices(
            AKIIndicesInput(
                urine_sodium_meq_l=40,
                serum_sodium_meq_l=140,
                urine_creatinine_mg_dl=100,
                serum_creatinine_mg_dl=1.0,
                on_diuretics=True,
            )
        )
        assert result.aki_etiology == "diuretic_confounded"
