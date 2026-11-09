"""Composite patient input and unified audit report."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from clinical_mcp.schemas.acid_base import (
    AcidBaseInput,
    AcidBaseOutput,
    CalciumInput,
    CalciumOutput,
    OsmolalityInput,
    OsmolalityOutput,
)
from clinical_mcp.schemas.cardiology import (
    HemodynamicsInput,
    HemodynamicsOutput,
    QTcInput,
    QTcOutput,
)
from clinical_mcp.schemas.common import LLMTrapCategory
from clinical_mcp.schemas.critical_care import (
    OxygenationInput,
    OxygenationOutput,
    QSOFASIRSInput,
    QSOFASIRSOutput,
)
from clinical_mcp.schemas.hematology import PEDDimerInput, PEDDimerOutput
from clinical_mcp.schemas.hepatology import FIB4Input, FIB4Output, MELDInput, MELDOutput
from clinical_mcp.schemas.renal import (
    AKIIndicesInput,
    AKIIndicesOutput,
    CKDEPIInput,
    CKDEPIOutput,
    CockcroftGaultInput,
    CockcroftGaultOutput,
)


class ComprehensivePatientInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ckd_epi: CKDEPIInput | None = None
    cockcroft_gault: CockcroftGaultInput | None = None
    aki_urinary: AKIIndicesInput | None = None
    acid_base: AcidBaseInput | None = None
    osmolality: OsmolalityInput | None = None
    calcium: CalciumInput | None = None
    qtc: QTcInput | None = None
    hemodynamics: HemodynamicsInput | None = None
    meld: MELDInput | None = None
    fib4: FIB4Input | None = None
    oxygenation: OxygenationInput | None = None
    qsofa_sirs: QSOFASIRSInput | None = None
    pe_ddimer: PEDDimerInput | None = None


class ComprehensiveAuditReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executed_engines: list[str]
    skipped_engines: list[str]
    failed_engines: dict[str, str]
    triggered_trap_categories: list[LLMTrapCategory]
    trap_descriptions: str
    cross_domain_flags: list[str]
    unified_risk_summary: str

    ckd_epi: CKDEPIOutput | None = None
    cockcroft_gault: CockcroftGaultOutput | None = None
    aki_urinary: AKIIndicesOutput | None = None
    acid_base: AcidBaseOutput | None = None
    osmolality: OsmolalityOutput | None = None
    calcium: CalciumOutput | None = None
    qtc: QTcOutput | None = None
    hemodynamics: HemodynamicsOutput | None = None
    meld: MELDOutput | None = None
    fib4: FIB4Output | None = None
    oxygenation: OxygenationOutput | None = None
    qsofa_sirs: QSOFASIRSOutput | None = None
    pe_ddimer: PEDDimerOutput | None = None
