"""Pure comprehensive patient audit orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from clinical_mcp.engines.acid_base import (
    calculate_acid_base,
    calculate_corrected_calcium,
    calculate_osmolality,
)
from clinical_mcp.engines.cardiology import calculate_hemodynamics, calculate_qtc
from clinical_mcp.engines.critical_care import calculate_oxygenation, calculate_qsofa
from clinical_mcp.engines.hematology import calculate_peddimer
from clinical_mcp.engines.hepatology import calculate_fib4, calculate_meld
from clinical_mcp.engines.renal import (
    calculate_aki_indices,
    calculate_ckd_epi,
    calculate_cockcroft_gault,
)
from clinical_mcp.schemas.common import LLMTrapCategory
from clinical_mcp.schemas.poly_audit import (
    ComprehensiveAuditReport,
    ComprehensivePatientInput,
)

_ENGINES: list[tuple[str, Callable[[Any], Any]]] = [
    ("ckd_epi", calculate_ckd_epi),
    ("cockcroft_gault", calculate_cockcroft_gault),
    ("aki_urinary", calculate_aki_indices),
    ("acid_base", calculate_acid_base),
    ("osmolality", calculate_osmolality),
    ("calcium", calculate_corrected_calcium),
    ("qtc", calculate_qtc),
    ("hemodynamics", calculate_hemodynamics),
    ("meld", calculate_meld),
    ("fib4", calculate_fib4),
    ("oxygenation", calculate_oxygenation),
    ("qsofa_sirs", calculate_qsofa),
    ("pe_ddimer", calculate_peddimer),
]


def run_comprehensive_patient_audit(data: ComprehensivePatientInput) -> ComprehensiveAuditReport:
    """Execute every applicable domain engine and aggregate trap telemetry.

    Propagation: each non-null sub-model -> its pure domain engine; results feed
    cross-domain discordance flags, trap categories, and the unified risk summary.
    """
    executed: list[str] = []
    skipped: list[str] = []
    failed: dict[str, str] = {}
    results: dict[str, Any] = {}
    descriptions: list[str] = []
    categories: list[LLMTrapCategory] = []

    for name, engine in _ENGINES:
        sub_model = getattr(data, name)
        if sub_model is None:
            skipped.append(name)
            continue
        try:
            result = engine(sub_model)
        except Exception as exc:  # noqa: BLE001 - one bad engine must not stop the audit
            failed[name] = str(exc)
            descriptions.append(f"{name}: {exc}")
            continue
        results[name] = result
        executed.append(name)
        for text in result.llm_trap_prevented:
            if text not in descriptions:
                descriptions.append(text)

        if name == "acid_base":
            ab = result
            if (
                ab.albumin_corrected_anion_gap > 12.0
                and ab.raw_anion_gap <= 12.0
            ):
                categories.append(LLMTrapCategory.HYPOALBUMINEMIA_MASKED_HAGMA)
        elif name == "cockcroft_gault":
            if result.weight_selection_rule == "adjbw":
                categories.append(LLMTrapCategory.OBESITY_COCKCROFT_GAULT_OVERDOSE)
        elif name == "aki_urinary":
            if sub_model.on_diuretics:
                categories.append(LLMTrapCategory.DIURETIC_FENA_MISINTERPRETATION)
        elif name == "qtc":
            if result.qrs_widened or sub_model.hr_bpm > 100.0:
                categories.append(LLMTrapCategory.TACHYCARDIA_OR_WIDE_QRS_QTC_ARTIFACT)
        elif name == "meld":
            if result.clamps_applied:
                categories.append(LLMTrapCategory.UNOS_MELD_LOGARITHMIC_BOUNDARY_VIOLATION)
        elif name == "pe_ddimer":
            if sub_model.age_years > 50.0:
                categories.append(LLMTrapCategory.AGE_UNADJUSTED_DDIMER_FALSE_POSITIVE)

    unique_categories: list[LLMTrapCategory] = []
    for category in categories:
        if category not in unique_categories:
            unique_categories.append(category)

    flags: list[str] = []
    ckd = results.get("ckd_epi")
    cg = results.get("cockcroft_gault")
    if ckd is not None and cg is not None:
        egfr = ckd.egfr_ml_min_per_173m2
        crcl = cg.crcl_ml_min
        if egfr > 0 and abs(crcl - egfr) / egfr > 0.30:
            flags.append(
                f"CKD-EPI ({egfr:.1f}) and Cockcroft-Gault ({crcl:.1f}) differ by >30%; dose by CrCl."
            )
    meld = results.get("meld")
    if meld is not None and ckd is not None:
        if ckd.egfr_ml_min_per_173m2 < 30.0:
            flags.append("MELD with eGFR <30: renal replacement status affects both scores.")
    if meld is not None and results.get("aki_urinary") is not None:
        flags.append("Concurrent AKI and liver disease: interpret MELD creatinine with caution.")
    qtc = results.get("qtc")
    if qtc is not None and qtc.recommended_qtc_ms >= 500.0:
        flags.append("QTc >=500 ms: high Torsades risk; review QT-prolonging drugs and electrolytes.")
    oxy = results.get("oxygenation")
    if oxy is not None and oxy.pf_ratio <= 300.0:
        flags.append(f"P/F {oxy.pf_ratio:.1f}: Berlin ARDS criteria met.")

    if flags:
        summary = " | ".join(flags)
    elif failed:
        summary = "One or more engines failed; see failed_engines."
    elif executed:
        summary = f"{len(executed)} engines executed without cross-domain red flags."
    else:
        summary = "No sub-models supplied; no engines executed."

    return ComprehensiveAuditReport(
        executed_engines=executed,
        skipped_engines=skipped,
        failed_engines=failed,
        triggered_trap_categories=unique_categories,
        trap_descriptions="; ".join(descriptions),
        cross_domain_flags=flags,
        unified_risk_summary=summary,
        ckd_epi=results.get("ckd_epi"),
        cockcroft_gault=results.get("cockcroft_gault"),
        aki_urinary=results.get("aki_urinary"),
        acid_base=results.get("acid_base"),
        osmolality=results.get("osmolality"),
        calcium=results.get("calcium"),
        qtc=results.get("qtc"),
        hemodynamics=results.get("hemodynamics"),
        meld=results.get("meld"),
        fib4=results.get("fib4"),
        oxygenation=results.get("oxygenation"),
        qsofa_sirs=results.get("qsofa_sirs"),
        pe_ddimer=results.get("pe_ddimer"),
    )


__all__ = ["run_comprehensive_patient_audit"]
