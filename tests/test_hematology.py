"""Hematology (Wells / D-dimer) tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from clinical_mcp.engines.hematology import calculate_peddimer
from clinical_mcp.schemas.hematology import PEDDimerInput


class TestPEDDimerSchemas:
    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PEDDimerInput(age_years=17, d_dimer_ng_ml_feu=100, wells_score=1)


class TestPEDDimer:
    def test_age_adjusted_threshold(self) -> None:
        result = calculate_peddimer(
            PEDDimerInput(age_years=65, d_dimer_ng_ml_feu=600, wells_score=2)
        )
        assert result.age_adjusted_threshold_ng_ml == 650.0
        assert result.ddimer_positive is False
        assert result.ctpa_indicated is False
        assert result.wells_probability == "moderate"

    def test_standard_threshold_under_50(self) -> None:
        result = calculate_peddimer(
            PEDDimerInput(age_years=40, d_dimer_ng_ml_feu=501, wells_score=1)
        )
        assert result.age_adjusted_threshold_ng_ml == 500.0
        assert result.ddimer_positive is True
        assert result.wells_probability == "low"

    def test_high_wells_forces_ctpa(self) -> None:
        result = calculate_peddimer(
            PEDDimerInput(age_years=45, d_dimer_ng_ml_feu=100, wells_score=7)
        )
        assert result.wells_probability == "high"
        assert result.ctpa_indicated is True
