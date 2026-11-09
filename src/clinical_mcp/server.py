"""FastMCP server exposing 14 deterministic clinical calculators."""

from __future__ import annotations

from typing import Any, Literal, cast

from mcp.server.mcpserver import MCPServer

from clinical_mcp.engines.acid_base import (
    calculate_acid_base,
    calculate_corrected_calcium,
    calculate_osmolality,
)
from clinical_mcp.engines.cardiology import calculate_hemodynamics, calculate_qtc
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
from clinical_mcp.schemas.critical_care import OxygenationInput, QSOFASIRSInput
from clinical_mcp.schemas.hematology import PEDDimerInput
from clinical_mcp.schemas.hepatology import FIB4Input, MELDInput
from clinical_mcp.schemas.poly_audit import ComprehensivePatientInput
from clinical_mcp.schemas.renal import AKIIndicesInput, CKDEPIInput, CockcroftGaultInput

mcp = MCPServer("Open Clinical AI Lab - Deterministic Physiology Server")


def _dump(model: Any) -> dict[str, Any]:
    return cast(dict[str, Any], model.model_dump(mode="json"))


@mcp.tool()
def ckd_epi(
    scr_mg_dl: float, age_years: float, sex: Literal["male", "female"]
) -> dict[str, Any]:
    """2021 race-free CKD-EPI eGFR with KDIGO staging. Uses constant 142, no race coefficient."""
    return _dump(calculate_ckd_epi(CKDEPIInput(scr_mg_dl=scr_mg_dl, age_years=age_years, sex=sex)))


@mcp.tool()
def cockcroft_gault(
    age_years: float,
    sex: Literal["male", "female"],
    weight_kg: float,
    height_cm: float,
    scr_mg_dl: float,
) -> dict[str, Any]:
    """Cockcroft-Gault CrCl with Devine IBW and obesity-adjusted body weight."""
    return _dump(
        calculate_cockcroft_gault(
            CockcroftGaultInput(
                age_years=age_years,
                sex=sex,
                weight_kg=weight_kg,
                height_cm=height_cm,
                scr_mg_dl=scr_mg_dl,
            )
        )
    )


@mcp.tool()
def aki_indices(
    urine_sodium_meq_l: float,
    serum_sodium_meq_l: float,
    urine_creatinine_mg_dl: float,
    serum_creatinine_mg_dl: float,
    on_diuretics: bool = False,
    serum_bun_mg_dl: float | None = None,
    urine_urea_mg_dl: float | None = None,
) -> dict[str, Any]:
    """FENa and FEUrea with diuretic-aware AKI interpretation."""
    return _dump(
        calculate_aki_indices(
            AKIIndicesInput(
                urine_sodium_meq_l=urine_sodium_meq_l,
                serum_sodium_meq_l=serum_sodium_meq_l,
                urine_creatinine_mg_dl=urine_creatinine_mg_dl,
                serum_creatinine_mg_dl=serum_creatinine_mg_dl,
                on_diuretics=on_diuretics,
                serum_bun_mg_dl=serum_bun_mg_dl,
                urine_urea_mg_dl=urine_urea_mg_dl,
            )
        )
    )


@mcp.tool()
def acid_base(
    na_meq_l: float,
    cl_meq_l: float,
    hco3_meq_l: float,
    albumin_g_dl: float = 4.0,
    glucose_mg_dl: float = 100.0,
    paco2_mmhg: float | None = None,
    ph: float | None = None,
    lactate_mmol_l: float | None = None,
) -> dict[str, Any]:
    """Katz/Hillier sodium correction, Figge anion gap, delta ratio, and Winter's formula."""
    return _dump(
        calculate_acid_base(
            AcidBaseInput(
                na_meq_l=na_meq_l,
                cl_meq_l=cl_meq_l,
                hco3_meq_l=hco3_meq_l,
                albumin_g_dl=albumin_g_dl,
                glucose_mg_dl=glucose_mg_dl,
                paco2_mmhg=paco2_mmhg,
                ph=ph,
                lactate_mmol_l=lactate_mmol_l,
            )
        )
    )


@mcp.tool()
def osmolality(
    na_meq_l: float,
    glucose_mg_dl: float,
    bun_mg_dl: float,
    measured_osmolality_mosm_kg: float | None = None,
    ethanol_mg_dl: float | None = None,
    weight_kg: float | None = None,
    sex: Literal["male", "female"] | None = None,
    age_years: float | None = None,
) -> dict[str, Any]:
    """Calculated osmolality, osmolar gap with toxic-alcohol flag, and free water deficit."""
    return _dump(
        calculate_osmolality(
            OsmolalityInput(
                na_meq_l=na_meq_l,
                glucose_mg_dl=glucose_mg_dl,
                bun_mg_dl=bun_mg_dl,
                measured_osmolality_mosm_kg=measured_osmolality_mosm_kg,
                ethanol_mg_dl=ethanol_mg_dl,
                weight_kg=weight_kg,
                sex=sex,
                age_years=age_years,
            )
        )
    )


@mcp.tool()
def corrected_calcium(total_ca_mg_dl: float, albumin_g_dl: float) -> dict[str, Any]:
    """Payne albumin-corrected total calcium."""
    return _dump(
        calculate_corrected_calcium(
            CalciumInput(total_ca_mg_dl=total_ca_mg_dl, albumin_g_dl=albumin_g_dl)
        )
    )


@mcp.tool()
def qtc(
    qt_ms: float,
    hr_bpm: float,
    sex: Literal["male", "female"] = "male",
    qrs_ms: float = 90.0,
) -> dict[str, Any]:
    """Bazett/Fridericia/Framingham QTc with Bogossian wide-QRS adjustment."""
    return _dump(
        calculate_qtc(QTcInput(qt_ms=qt_ms, hr_bpm=hr_bpm, sex=sex, qrs_ms=qrs_ms))
    )


@mcp.tool()
def hemodynamics(sbp_mmhg: float, dbp_mmhg: float, hr_bpm: float) -> dict[str, Any]:
    """MAP, pulse pressure, shock index, and modified shock index."""
    return _dump(
        calculate_hemodynamics(
            HemodynamicsInput(sbp_mmhg=sbp_mmhg, dbp_mmhg=dbp_mmhg, hr_bpm=hr_bpm)
        )
    )


@mcp.tool()
def meld(
    bilirubin_mg_dl: float,
    inr: float,
    creatinine_mg_dl: float,
    sodium_meq_l: float,
    albumin_g_dl: float,
    sex: Literal["male", "female"] = "male",
    dialysis: bool = False,
) -> dict[str, Any]:
    """MELD-Na and MELD 3.0 with UNOS clamp audit trail and mortality brackets."""
    return _dump(
        calculate_meld(
            MELDInput(
                bilirubin_mg_dl=bilirubin_mg_dl,
                inr=inr,
                creatinine_mg_dl=creatinine_mg_dl,
                sodium_meq_l=sodium_meq_l,
                albumin_g_dl=albumin_g_dl,
                sex=sex,
                dialysis=dialysis,
            )
        )
    )


@mcp.tool()
def fib4(age_years: float, ast_u_l: float, alt_u_l: float, platelets_10e9_l: float) -> dict[str, Any]:
    """FIB-4 fibrosis index with low/indeterminate/high staging."""
    return _dump(
        calculate_fib4(
            FIB4Input(
                age_years=age_years,
                ast_u_l=ast_u_l,
                alt_u_l=alt_u_l,
                platelets_10e9_l=platelets_10e9_l,
            )
        )
    )


@mcp.tool()
def oxygenation(
    pao2_mmhg: float,
    paco2_mmhg: float,
    fio2: float,
    age_years: float,
    barometric_pressure_mmhg: float = 760.0,
    respiratory_quotient: float = 0.8,
) -> dict[str, Any]:
    """Alveolar gas equation, A-a gradient, P/F ratio, and Berlin ARDS staging."""
    return _dump(
        calculate_oxygenation(
            OxygenationInput(
                pao2_mmhg=pao2_mmhg,
                paco2_mmhg=paco2_mmhg,
                fio2=fio2,
                age_years=age_years,
                barometric_pressure_mmhg=barometric_pressure_mmhg,
                respiratory_quotient=respiratory_quotient,
            )
        )
    )


@mcp.tool()
def qsofa_sirs(
    rr_bpm: float,
    sbp_mmhg: float,
    gcs_score: int,
    temp_celsius: float | None = None,
    hr_bpm: float | None = None,
    wbc_10e9_l: float | None = None,
    paco2_mmhg: float | None = None,
    lactate_mmol_l: float | None = None,
) -> dict[str, Any]:
    """qSOFA always, SIRS only with two or more available parameters, plus sepsis screen."""
    return _dump(
        calculate_qsofa(
            QSOFASIRSInput(
                rr_bpm=rr_bpm,
                sbp_mmhg=sbp_mmhg,
                gcs_score=gcs_score,
                temp_celsius=temp_celsius,
                hr_bpm=hr_bpm,
                wbc_10e9_l=wbc_10e9_l,
                paco2_mmhg=paco2_mmhg,
                lactate_mmol_l=lactate_mmol_l,
            )
        )
    )


@mcp.tool()
def pe_ddimer(age_years: float, d_dimer_ng_ml_feu: float, wells_score: float) -> dict[str, Any]:
    """Wells score with age-adjusted D-dimer threshold and CTPA indication."""
    return _dump(
        calculate_peddimer(
            PEDDimerInput(
                age_years=age_years,
                d_dimer_ng_ml_feu=d_dimer_ng_ml_feu,
                wells_score=wells_score,
            )
        )
    )


@mcp.tool()
def comprehensive_audit(payload: ComprehensivePatientInput) -> dict[str, Any]:
    """Run all applicable domain engines and return flat results plus trap telemetry."""
    return _dump(run_comprehensive_patient_audit(payload))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
