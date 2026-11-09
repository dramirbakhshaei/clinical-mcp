"""Rich terminal dashboard: naive token guess vs deterministic engine."""

from __future__ import annotations

import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from clinical_mcp.engines.poly_audit import run_comprehensive_patient_audit
from clinical_mcp.schemas.acid_base import AcidBaseInput
from clinical_mcp.schemas.cardiology import QTcInput
from clinical_mcp.schemas.hematology import PEDDimerInput
from clinical_mcp.schemas.hepatology import MELDInput
from clinical_mcp.schemas.poly_audit import ComprehensiveAuditReport, ComprehensivePatientInput
from clinical_mcp.schemas.renal import CockcroftGaultInput

DEMO_TRAP_CASES: list[ComprehensivePatientInput] = [
    ComprehensivePatientInput(
        acid_base=AcidBaseInput(
            na_meq_l=140.0,
            cl_meq_l=109.0,
            hco3_meq_l=23.0,
            albumin_g_dl=2.0,
            glucose_mg_dl=500.0,
            paco2_mmhg=30.0,
            ph=7.30,
            lactate_mmol_l=6.0,
        )
    ),
    ComprehensivePatientInput(
        cockcroft_gault=CockcroftGaultInput(
            age_years=60.0, sex="male", weight_kg=120.0, height_cm=165.0, scr_mg_dl=1.0
        )
    ),
    ComprehensivePatientInput(
        qtc=QTcInput(qt_ms=400.0, hr_bpm=110.0, sex="male", qrs_ms=140.0)
    ),
    ComprehensivePatientInput(
        meld=MELDInput(
            bilirubin_mg_dl=0.8,
            inr=0.9,
            creatinine_mg_dl=0.7,
            sodium_meq_l=140.0,
            albumin_g_dl=4.0,
            sex="male",
        )
    ),
    ComprehensivePatientInput(
        pe_ddimer=PEDDimerInput(age_years=65.0, d_dimer_ng_ml_feu=600.0, wells_score=2.0)
    ),
]

_TITLES = [
    "1. Occult Hypoalbuminemic Lactic Acidosis",
    "2. Obese Cockcroft-Gault DOAC Overdose",
    "3. Tachycardic Wide-QRS Bazett False Positive",
    "4. UNOS MELD Logarithmic Floor Clamping",
    "5. Age-Adjusted D-Dimer PE Exclusion",
]

_NAIVE = [
    "Raw AG 8 mEq/L -> 'no HAGMA'; reports Na 140 mEq/L.",
    "CrCl ~140 mL/min from total body weight -> full DOAC dose.",
    "Bazett 450 ms -> false Torsades alarm; ignores wide QRS.",
    "MELD ~6 without UNOS floors or caps.",
    "D-dimer 600 > fixed 500 -> CTPA indicated.",
]


def _deterministic(report: ComprehensiveAuditReport) -> str:
    if report.acid_base is not None:
        ab = report.acid_base
        return (
            f"Corrected AG {ab.albumin_corrected_anion_gap} mEq/L -> "
            f"{ab.disorders[0]}; active Na correction {ab.active_na_correction_method}."
        )
    if report.cockcroft_gault is not None:
        cg = report.cockcroft_gault
        return (
            f"IBW {cg.ibw_kg} kg, AdjBW {cg.adjbw_kg} kg, selects {cg.weight_selection_rule} "
            f"-> CrCl {cg.crcl_ml_min} mL/min."
        )
    if report.qtc is not None:
        q = report.qtc
        return (
            f"Bogossian QT {q.bogossian_modified_qt_ms} ms; uses {q.recommended_primary_metric} "
            f"-> QTc {q.recommended_qtc_ms} ms (Torsades risk: {q.torsades_risk})."
        )
    if report.meld is not None:
        m = report.meld
        return (
            f"MELD-Na {m.meld_na} ({m.mortality_bracket_meld_na}), "
            f"MELD 3.0 {m.meld_3} ({m.mortality_bracket_meld_3}); "
            f"{len(m.clamps_applied)} UNOS clamps applied."
        )
    if report.pe_ddimer is not None:
        p = report.pe_ddimer
        return (
            f"Age-adjusted threshold {p.age_adjusted_threshold_ng_ml:.0f} ng/mL FEU -> "
            f"positive={p.ddimer_positive}, CTPA={p.ctpa_indicated}."
        )
    return "No engine executed."


def build_dashboard(console: Console, selected: list[int] | None = None) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Open Clinical AI Lab[/bold cyan] — Deterministic Physiology vs Token Guess",
            border_style="cyan",
        )
    )
    indexes = selected if selected is not None else list(range(len(DEMO_TRAP_CASES)))
    for index in indexes:
        case = DEMO_TRAP_CASES[index]
        report = run_comprehensive_patient_audit(case)
        table = Table(
            title=_TITLES[index],
            show_header=True,
            header_style="bold magenta",
            expand=True,
        )
        table.add_column("Naive LLM token guess", style="red", ratio=1)
        table.add_column("clinical-mcp deterministic engine", style="green", ratio=1)
        table.add_row(_NAIVE[index], _deterministic(report))
        console.print(table)
        categories = ", ".join(c.value for c in report.triggered_trap_categories) or "none"
        console.print(f"[dim]Trap categories:[/dim] [yellow]{categories}[/yellow]")
        console.print(f"[dim]Engine summary:[/dim] {report.unified_risk_summary}\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="clinical-mcp trap dashboard")
    parser.add_argument("--trap", type=int, choices=range(1, 6), help="render one trap (1-5)")
    parser.add_argument("--all", action="store_true", help="render all traps (default)")
    args = parser.parse_args(argv)
    _ = args.all
    selected = [args.trap - 1] if args.trap else None
    build_dashboard(Console(), selected)


if __name__ == "__main__":
    main()
