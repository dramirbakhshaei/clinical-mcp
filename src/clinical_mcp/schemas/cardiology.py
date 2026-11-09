"""Cardiac repolarization and hemodynamic schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from clinical_mcp.schemas.common import EngineInput, EngineOutput, UCUMUnit


class QTcInput(EngineInput):
    qt_ms: float = Field(..., ge=150.0, le=800.0)
    hr_bpm: float = Field(..., ge=20.0, le=300.0)
    sex: Literal["male", "female"] = "male"
    qrs_ms: float = Field(90.0, ge=40.0, le=200.0)


class QTcOutput(EngineOutput):
    qrs_widened: bool
    bogossian_modified_qt_ms: float | None
    qtc_bazett_ms: float
    qtc_fridericia_ms: float
    qtc_framingham_ms: float
    recommended_primary_metric: str
    recommended_qtc_ms: float
    torsades_risk: bool
    unit: UCUMUnit = UCUMUnit.MS


class HemodynamicsInput(EngineInput):
    sbp_mmhg: float = Field(..., ge=30.0, le=300.0)
    dbp_mmhg: float = Field(..., ge=20.0, le=200.0)
    hr_bpm: float = Field(..., ge=20.0, le=300.0)


class HemodynamicsOutput(EngineOutput):
    map_mmhg: float
    pulse_pressure_mmhg: float
    shock_index: float
    modified_shock_index: float
    occult_shock: bool
    high_risk: bool
    unit: UCUMUnit = UCUMUnit.MMHG
