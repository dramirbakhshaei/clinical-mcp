"""Hepatology tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from clinical_mcp.engines.hepatology import _bracket, calculate_fib4, calculate_meld
from clinical_mcp.schemas.hepatology import FIB4Input, MELDInput


class TestMELDSchemas:
    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            MELDInput(
                bilirubin_mg_dl=0.0,
                inr=1.0,
                creatinine_mg_dl=1.0,
                sodium_meq_l=135,
                albumin_g_dl=3.0,
            )


class TestFIB4Schemas:
    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            FIB4Input(age_years=17, ast_u_l=40, alt_u_l=30, platelets_10e9_l=200)


class TestMELD:
    def test_clamps_are_recorded(self) -> None:
        result = calculate_meld(
            MELDInput(
                bilirubin_mg_dl=0.8,
                inr=0.9,
                creatinine_mg_dl=0.7,
                sodium_meq_l=140,
                albumin_g_dl=4.0,
            )
        )
        assert len(result.clamps_applied) == 5
        assert result.meld_na == pytest.approx(6.4)
        assert result.meld_3 == pytest.approx(8.7)
        assert result.clamps_applied[0].rule == "UNOS floor 1.0"

    def test_no_clamps(self) -> None:
        result = calculate_meld(
            MELDInput(
                bilirubin_mg_dl=2.0,
                inr=1.5,
                creatinine_mg_dl=1.2,
                sodium_meq_l=135,
                albumin_g_dl=3.0,
            )
        )
        assert result.clamps_applied == []
        assert result.meld_na > 0
        assert result.meld_3 > 0

    def test_creatinine_caps_differ(self) -> None:
        result = calculate_meld(
            MELDInput(
                bilirubin_mg_dl=2.0,
                inr=1.5,
                creatinine_mg_dl=5.0,
                sodium_meq_l=135,
                albumin_g_dl=3.0,
            )
        )
        rules = [c.rule for c in result.clamps_applied]
        assert "MELD-Na cap 4.0" in rules
        assert "MELD 3.0 cap 3.0" in rules

    def test_dialysis_uses_caps(self) -> None:
        result = calculate_meld(
            MELDInput(
                bilirubin_mg_dl=2.0,
                inr=1.5,
                creatinine_mg_dl=1.2,
                sodium_meq_l=135,
                albumin_g_dl=3.0,
                dialysis=True,
            )
        )
        rules = [c.rule for c in result.clamps_applied]
        assert "dialysis -> 4.0" in rules
        assert "dialysis -> 3.0" in rules

    def test_mortality_brackets(self) -> None:
        assert _bracket(40) == "71.3%"
        assert _bracket(30) == "52.6%"
        assert _bracket(20) == "19.6%"
        assert _bracket(10) == "6.0%"
        assert _bracket(5) == "1.9%"


class TestFIB4:
    def test_low(self) -> None:
        result = calculate_fib4(
            FIB4Input(age_years=30, ast_u_l=20, alt_u_l=40, platelets_10e9_l=300)
        )
        assert result.fibrosis_risk == "low"

    def test_indeterminate(self) -> None:
        result = calculate_fib4(
            FIB4Input(age_years=50, ast_u_l=40, alt_u_l=30, platelets_10e9_l=200)
        )
        assert result.fibrosis_risk == "indeterminate"

    def test_high(self) -> None:
        result = calculate_fib4(
            FIB4Input(age_years=60, ast_u_l=100, alt_u_l=40, platelets_10e9_l=100)
        )
        assert result.fibrosis_risk == "high"
