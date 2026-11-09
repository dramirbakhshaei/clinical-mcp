"""Comprehensive audit integration tests."""

from __future__ import annotations

import time

import pytest

import clinical_mcp.engines.poly_audit as poly_audit
from clinical_mcp.engines.acid_base import calculate_acid_base
from clinical_mcp.engines.cardiology import calculate_qtc
from clinical_mcp.engines.critical_care import calculate_oxygenation, calculate_qsofa
from clinical_mcp.engines.hematology import calculate_peddimer
from clinical_mcp.engines.hepatology import calculate_fib4, calculate_meld
from clinical_mcp.engines.poly_audit import run_comprehensive_patient_audit
from clinical_mcp.engines.renal import (
    calculate_aki_indices,
    calculate_ckd_epi,
    calculate_cockcroft_gault,
)
from clinical_mcp.schemas.acid_base import AcidBaseInput, CalciumInput, OsmolalityInput
from clinical_mcp.schemas.cardiology import HemodynamicsInput, QTcInput
from clinical_mcp.schemas.common import LLMTrapCategory, UCUMUnit
from clinical_mcp.schemas.critical_care import OxygenationInput, QSOFASIRSInput
from clinical_mcp.schemas.hematology import PEDDimerInput
from clinical_mcp.schemas.hepatology import FIB4Input, MELDInput
from clinical_mcp.schemas.poly_audit import ComprehensivePatientInput
from clinical_mcp.schemas.renal import (
    AKIIndicesInput,
    CKDEPIInput,
    CockcroftGaultInput,
)


def _full_case() -> ComprehensivePatientInput:
    return ComprehensivePatientInput(
        ckd_epi=CKDEPIInput(scr_mg_dl=2.5, age_years=60, sex="male"),
        cockcroft_gault=CockcroftGaultInput(
            age_years=60, sex="male", weight_kg=120.0, height_cm=165.0, scr_mg_dl=2.5
        ),
        aki_urinary=AKIIndicesInput(
            urine_sodium_meq_l=40,
            serum_sodium_meq_l=140,
            urine_creatinine_mg_dl=100,
            serum_creatinine_mg_dl=2.5,
            on_diuretics=True,
        ),
        acid_base=AcidBaseInput(
            na_meq_l=140,
            cl_meq_l=109,
            hco3_meq_l=23,
            albumin_g_dl=2.0,
            glucose_mg_dl=500,
            paco2_mmhg=30,
            ph=7.30,
        ),
        osmolality=OsmolalityInput(
            na_meq_l=140, glucose_mg_dl=180, bun_mg_dl=28, measured_osmolality_mosm_kg=320
        ),
        calcium=CalciumInput(total_ca_mg_dl=8.0, albumin_g_dl=2.0),
        qtc=QTcInput(qt_ms=400, hr_bpm=110, qrs_ms=140),
        hemodynamics=HemodynamicsInput(sbp_mmhg=120, dbp_mmhg=80, hr_bpm=100),
        meld=MELDInput(
            bilirubin_mg_dl=0.8,
            inr=0.9,
            creatinine_mg_dl=0.7,
            sodium_meq_l=140,
            albumin_g_dl=4.0,
        ),
        fib4=FIB4Input(age_years=60, ast_u_l=100, alt_u_l=40, platelets_10e9_l=100),
        oxygenation=OxygenationInput(pao2_mmhg=100, paco2_mmhg=40, fio2=0.4, age_years=40),
        qsofa_sirs=QSOFASIRSInput(
            rr_bpm=24,
            sbp_mmhg=90,
            gcs_score=14,
            temp_celsius=38.5,
            hr_bpm=110,
            wbc_10e9_l=14.0,
            lactate_mmol_l=4.2,
        ),
        pe_ddimer=PEDDimerInput(age_years=65, d_dimer_ng_ml_feu=600, wells_score=2),
    )


class TestPolyAuditSchemas:
    def test_empty_input(self) -> None:
        model = ComprehensivePatientInput()
        assert model.ckd_epi is None

    def test_report_flat_fields(self) -> None:
        report = run_comprehensive_patient_audit(_full_case())
        assert report.ckd_epi is not None
        assert not hasattr(report, "all_domain_results")


class TestComprehensiveAudit:
    def test_all_engines_execute(self) -> None:
        report = run_comprehensive_patient_audit(_full_case())
        assert len(report.executed_engines) == 13
        assert report.skipped_engines == []
        assert report.failed_engines == {}
        assert report.trap_descriptions

    def test_all_trap_categories(self) -> None:
        report = run_comprehensive_patient_audit(_full_case())
        assert set(report.triggered_trap_categories) == set(LLMTrapCategory)

    def test_cross_domain_flags(self) -> None:
        report = run_comprehensive_patient_audit(_full_case())
        assert any("CKD-EPI" in f for f in report.cross_domain_flags)
        assert any("MELD with eGFR" in f for f in report.cross_domain_flags)
        assert any("ARDS" in f for f in report.cross_domain_flags)
        assert report.unified_risk_summary

    def test_empty_patient(self) -> None:
        report = run_comprehensive_patient_audit(ComprehensivePatientInput())
        assert report.executed_engines == []
        assert len(report.skipped_engines) == 13
        assert "No sub-models" in report.unified_risk_summary


class TestPolyAuditLiverTransplant:
    def test_dialysis_and_abw(self) -> None:
        report = run_comprehensive_patient_audit(
            ComprehensivePatientInput(
                ckd_epi=CKDEPIInput(scr_mg_dl=3.0, age_years=55, sex="female"),
                cockcroft_gault=CockcroftGaultInput(
                    age_years=55, sex="female", weight_kg=110, height_cm=160, scr_mg_dl=3.0
                ),
                meld=MELDInput(
                    bilirubin_mg_dl=5.0,
                    inr=2.5,
                    creatinine_mg_dl=2.0,
                    sodium_meq_l=130,
                    albumin_g_dl=2.5,
                    dialysis=True,
                ),
            )
        )
        assert report.meld is not None
        assert report.cockcroft_gault is not None
        assert report.cockcroft_gault.weight_selection_rule == "adjbw"
        assert any("eGFR <30" in f for f in report.cross_domain_flags)


class TestCrossDomainFlags:
    def test_qtc_flag(self) -> None:
        report = run_comprehensive_patient_audit(
            ComprehensivePatientInput(
                qtc=QTcInput(qt_ms=520, hr_bpm=60),
                meld=MELDInput(
                    bilirubin_mg_dl=2.0,
                    inr=1.5,
                    creatinine_mg_dl=1.2,
                    sodium_meq_l=135,
                    albumin_g_dl=3.0,
                ),
                aki_urinary=AKIIndicesInput(
                    urine_sodium_meq_l=40,
                    serum_sodium_meq_l=140,
                    urine_creatinine_mg_dl=100,
                    serum_creatinine_mg_dl=1.0,
                ),
            )
        )
        assert any("Torsades" in f for f in report.cross_domain_flags)
        assert any("AKI and liver" in f for f in report.cross_domain_flags)


class TestPolyAuditPerformance:
    def test_100_invocations_under_500ms(self) -> None:
        case = _full_case()
        run_comprehensive_patient_audit(case)
        start = time.perf_counter()
        for _ in range(100):
            run_comprehensive_patient_audit(case)
        assert time.perf_counter() - start < 0.5


class TestTrapCategoryCoverage:
    def test_demo_cases_trigger_five_categories(self) -> None:
        from clinical_mcp.cli_demo import DEMO_TRAP_CASES

        triggered = set()
        for case in DEMO_TRAP_CASES:
            report = run_comprehensive_patient_audit(case)
            triggered.update(report.triggered_trap_categories)
        assert len(triggered) >= 5


class TestPropagationVerification:
    def test_intermediate_values_present(self) -> None:
        report = run_comprehensive_patient_audit(_full_case())
        assert report.cockcroft_gault is not None
        assert report.cockcroft_gault.selected_weight_kg > 0
        assert report.acid_base is not None
        assert report.acid_base.raw_anion_gap != report.acid_base.albumin_corrected_anion_gap
        assert report.qtc is not None
        assert report.qtc.bogossian_modified_qt_ms is not None


class TestDocstringPropagation:
    def test_every_engine_documents_propagation(self) -> None:
        functions = [
            calculate_ckd_epi,
            calculate_cockcroft_gault,
            calculate_aki_indices,
            calculate_acid_base,
            poly_audit.calculate_osmolality,
            poly_audit.calculate_corrected_calcium,
            calculate_qtc,
            poly_audit.calculate_hemodynamics,
            calculate_meld,
            calculate_fib4,
            calculate_oxygenation,
            calculate_qsofa,
            calculate_peddimer,
        ]
        for function in functions:
            assert "Propagation:" in (function.__doc__ or "")


class TestUCUMUnits:
    def test_report_units_are_ucum(self) -> None:
        report = run_comprehensive_patient_audit(_full_case())
        fields = [
            report.ckd_epi,
            report.cockcroft_gault,
            report.aki_urinary,
            report.acid_base,
            report.osmolality,
            report.calcium,
            report.qtc,
            report.hemodynamics,
            report.meld,
            report.fib4,
            report.oxygenation,
            report.qsofa_sirs,
            report.pe_ddimer,
        ]
        for field in fields:
            assert field is not None
            assert isinstance(field.unit, UCUMUnit)


class TestGracefulDegradation:
    def test_optional_dependencies_return_none(self) -> None:
        report = run_comprehensive_patient_audit(
            ComprehensivePatientInput(
                acid_base=AcidBaseInput(na_meq_l=140, cl_meq_l=100, hco3_meq_l=20),
                osmolality=OsmolalityInput(na_meq_l=140, glucose_mg_dl=100, bun_mg_dl=14),
                aki_urinary=AKIIndicesInput(
                    urine_sodium_meq_l=40,
                    serum_sodium_meq_l=140,
                    urine_creatinine_mg_dl=100,
                    serum_creatinine_mg_dl=1.0,
                ),
            )
        )
        assert report.acid_base is not None
        assert report.acid_base.winters_expected_paco2_min is None
        assert report.osmolality is not None
        assert report.osmolality.osmolar_gap_mosm_kg is None
        assert report.aki_urinary is not None
        assert report.aki_urinary.feurea_percent is None


class TestFailedEngineRecovery:
    def test_failure_is_captured_and_audit_continues(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(_: object) -> object:
            raise RuntimeError("boom")

        monkeypatch.setattr(poly_audit, "_ENGINES", [("ckd_epi", boom)])
        report = run_comprehensive_patient_audit(
            ComprehensivePatientInput(
                ckd_epi=CKDEPIInput(scr_mg_dl=1.0, age_years=40, sex="male")
            )
        )
        assert report.executed_engines == []
        assert report.failed_engines == {"ckd_epi": "boom"}
        assert "ckd_epi: boom" in report.trap_descriptions
        assert "failed" in report.unified_risk_summary
