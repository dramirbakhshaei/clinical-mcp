"""Acid-base, osmolality, and calcium tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from clinical_mcp.engines.acid_base import (
    calculate_acid_base,
    calculate_corrected_calcium,
    calculate_osmolality,
)
from clinical_mcp.schemas.acid_base import (
    AcidBaseInput,
    CalciumInput,
    OsmolalityInput,
)
from clinical_mcp.schemas.common import AcidBaseDisorder


class TestAcidBaseSchemas:
    def test_defaults(self) -> None:
        model = AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=24)
        assert model.albumin_g_dl == 4.0
        assert model.glucose_mg_dl == 100.0

    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            AcidBaseInput(na_meq_l=90, cl_meq_l=100, hco3_meq_l=24)
        with pytest.raises(ValidationError):
            AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=24, ph=6.4)


class TestOsmolalitySchemas:
    def test_optional_fields(self) -> None:
        model = OsmolalityInput(na_meq_l=140, glucose_mg_dl=100, bun_mg_dl=14)
        assert model.measured_osmolality_mosm_kg is None


class TestCalciumSchemas:
    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CalciumInput(total_ca_mg_dl=8.0, albumin_g_dl=0.1)


class TestCoupledAcidBase:
    def test_hillier_above_400(self, hyperglycemia: AcidBaseInput) -> None:
        result = calculate_acid_base(hyperglycemia)
        assert result.corrected_na_katz == 146.4
        assert result.corrected_na_hillier == 149.6
        assert result.active_na_correction_method == "hillier"

    def test_katz_at_or_below_400(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(
                na_meq_l=140, cl_meq_l=100, hco3_meq_l=24, glucose_mg_dl=400
            )
        )
        assert result.corrected_na_hillier == 147.2
        assert result.active_na_correction_method == "katz"

    def test_no_glucose_delta(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=24, glucose_mg_dl=80)
        )
        assert result.corrected_na_katz == 140.0
        assert result.corrected_na_hillier == 140.0
        assert result.active_na_correction_method == "katz"

    def test_figge_and_delta_ratio(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(na_meq_l=140, cl_meq_l=90, hco3_meq_l=20, albumin_g_dl=2.0)
        )
        assert result.raw_anion_gap == 30.0
        assert result.albumin_corrected_anion_gap == 35.0
        assert result.delta_ratio == pytest.approx(5.75)
        assert (
            AcidBaseDisorder.HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS
            in result.disorders
        )

    def test_winters_range(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=20, paco2_mmhg=30)
        )
        assert result.winters_expected_paco2_min == 36.0
        assert result.winters_expected_paco2_max == 40.0

    def test_winters_none_without_paco2(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=20)
        )
        assert result.winters_expected_paco2_min is None
        assert result.winters_expected_paco2_max is None

    def test_normal(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(
                na_meq_l=140, cl_meq_l=102, hco3_meq_l=24, paco2_mmhg=40, ph=7.40
            )
        )
        assert result.disorders == [AcidBaseDisorder.NORMAL]

    def test_pure_hagma(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=20)
        )
        assert result.disorders == [AcidBaseDisorder.PURE_HAGMA]

    def test_pure_nagma(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(na_meq_l=140, cl_meq_l=112, hco3_meq_l=20)
        )
        assert result.disorders == [AcidBaseDisorder.PURE_NAGMA]

    def test_mixed_hagma_nagma(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(na_meq_l=140, cl_meq_l=112, hco3_meq_l=20, albumin_g_dl=2.0)
        )
        assert result.disorders == [AcidBaseDisorder.MIXED_HAGMA_NAGMA]

    def test_uncompensated_respiratory_acidosis(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(
                na_meq_l=140, cl_meq_l=102, hco3_meq_l=24, paco2_mmhg=50, ph=7.30
            )
        )
        assert result.disorders == [AcidBaseDisorder.UNCOMPENSATED_RESPIRATORY_ACIDOSIS]

    def test_superimposed_respiratory_alkalosis(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(
                na_meq_l=140, cl_meq_l=102, hco3_meq_l=24, paco2_mmhg=30, ph=7.50
            )
        )
        assert result.disorders == [AcidBaseDisorder.SUPERIMPOSED_RESPIRATORY_ALKALOSIS]

    def test_prior_disorder_respected(self) -> None:
        result = calculate_acid_base(
            AcidBaseInput(
                na_meq_l=140,
                cl_meq_l=102,
                hco3_meq_l=24,
                prior_known_disorder=AcidBaseDisorder.PURE_NAGMA,
            )
        )
        assert result.disorders[0] == AcidBaseDisorder.PURE_NAGMA

    def test_acidosis_pearls_branches(self) -> None:
        low = calculate_acid_base(
            AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=20, paco2_mmhg=25)
        )
        high = calculate_acid_base(
            AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=20, paco2_mmhg=50)
        )
        assert any("below Winter" in p for p in low.clinical_pearls_and_actions)
        assert any("above Winter" in p for p in high.clinical_pearls_and_actions)


class TestOsmolality:
    def test_calculated_and_gap(self) -> None:
        result = calculate_osmolality(
            OsmolalityInput(
                na_meq_l=140,
                glucose_mg_dl=180,
                bun_mg_dl=28,
                measured_osmolality_mosm_kg=320,
            )
        )
        assert result.calculated_osmolality_mosm_kg == pytest.approx(300.0)
        assert result.osmolar_gap_mosm_kg == pytest.approx(20.0)
        assert result.toxic_alcohol_flag is True
        assert result.free_water_deficit_l is None

    def test_ethanol_and_free_water(self) -> None:
        result = calculate_osmolality(
            OsmolalityInput(
                na_meq_l=150,
                glucose_mg_dl=100,
                bun_mg_dl=14,
                ethanol_mg_dl=37,
                weight_kg=70,
                sex="male",
                age_years=40,
            )
        )
        assert result.calculated_osmolality_mosm_kg == pytest.approx(320.6)
        assert result.free_water_deficit_l == pytest.approx(3.0)

    def test_elderly_female_factor(self) -> None:
        result = calculate_osmolality(
            OsmolalityInput(
                na_meq_l=150,
                glucose_mg_dl=100,
                bun_mg_dl=14,
                weight_kg=60,
                sex="female",
                age_years=70,
            )
        )
        assert result.free_water_deficit_l == pytest.approx(1.93, abs=0.01)

    def test_no_measured_osmolality(self) -> None:
        result = calculate_osmolality(
            OsmolalityInput(na_meq_l=140, glucose_mg_dl=100, bun_mg_dl=14)
        )
        assert result.osmolar_gap_mosm_kg is None
        assert result.toxic_alcohol_flag is False


class TestCalcium:
    def test_payne(self) -> None:
        result = calculate_corrected_calcium(CalciumInput(total_ca_mg_dl=8.0, albumin_g_dl=2.0))
        assert result.corrected_ca_mg_dl == 9.6
        assert result.unit.value == "mg/dL"
