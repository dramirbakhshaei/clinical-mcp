"""Cardiology tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from clinical_mcp.engines.cardiology import calculate_hemodynamics, calculate_qtc
from clinical_mcp.schemas.cardiology import HemodynamicsInput, QTcInput


class TestQTcSchemas:
    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            QTcInput(qt_ms=100, hr_bpm=70)
        with pytest.raises(ValidationError):
            QTcInput(qt_ms=400, hr_bpm=310)


class TestHemodynamicsSchemas:
    def test_bounds(self) -> None:
        with pytest.raises(ValidationError):
            HemodynamicsInput(sbp_mmhg=10, dbp_mmhg=80, hr_bpm=70)


class TestQTc:
    def test_normal_hr_uses_bazett(self) -> None:
        result = calculate_qtc(QTcInput(qt_ms=380, hr_bpm=70))
        assert result.qtc_bazett_ms == pytest.approx(410.5, abs=0.2)
        assert result.qtc_fridericia_ms == pytest.approx(400.0, abs=0.2)
        assert result.qtc_framingham_ms == pytest.approx(402.0, abs=0.2)
        assert result.recommended_primary_metric == "bazett"
        assert result.qrs_widened is False
        assert result.bogossian_modified_qt_ms is None

    def test_tachycardia_uses_framingham(self) -> None:
        result = calculate_qtc(QTcInput(qt_ms=400, hr_bpm=110, qrs_ms=140))
        assert result.qrs_widened is True
        assert result.bogossian_modified_qt_ms == pytest.approx(332.1, abs=0.1)
        assert result.recommended_primary_metric == "framingham"
        assert result.recommended_qtc_ms < result.qtc_bazett_ms

    def test_bradycardia_uses_fridericia(self) -> None:
        result = calculate_qtc(QTcInput(qt_ms=400, hr_bpm=50))
        assert result.recommended_primary_metric == "fridericia"

    def test_torsades_threshold(self) -> None:
        result = calculate_qtc(QTcInput(qt_ms=520, hr_bpm=60))
        assert result.recommended_qtc_ms >= 500
        assert result.torsades_risk is True

    def test_bogossian_factor_is_0485(self) -> None:
        result = calculate_qtc(QTcInput(qt_ms=400, hr_bpm=70, qrs_ms=120))
        assert result.bogossian_modified_qt_ms == pytest.approx(400 - 0.485 * 120)


class TestHemodynamics:
    def test_normal(self) -> None:
        result = calculate_hemodynamics(
            HemodynamicsInput(sbp_mmhg=120, dbp_mmhg=80, hr_bpm=100)
        )
        assert result.map_mmhg == pytest.approx(93.3, abs=0.1)
        assert result.pulse_pressure_mmhg == 40.0
        assert result.shock_index == pytest.approx(0.83, abs=0.01)
        assert result.occult_shock is False
        assert result.high_risk is False

    def test_occult_shock_and_high_risk(self) -> None:
        result = calculate_hemodynamics(
            HemodynamicsInput(sbp_mmhg=100, dbp_mmhg=80, hr_bpm=130)
        )
        assert result.shock_index == pytest.approx(1.3)
        assert result.occult_shock is True
        assert result.modified_shock_index > 1.3
        assert result.high_risk is True
