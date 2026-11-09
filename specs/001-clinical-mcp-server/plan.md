# Implementation Plan: clinical-mcp

**Branch**: `001-clinical-mcp-server` | **Date**: 2026-11-06 | **Spec**: specs/001-clinical-mcp-server/spec.md

**Input**: Feature specification from `specs/001-clinical-mcp-server/spec.md`

## Summary

Build `clinical-mcp` — the definitive open-source Model Context Protocol (MCP) server for deterministic clinical physiology, critical care, and pharmacokinetic calculations. The system implements 6 specialized domain modules plus 1 unified multi-system patient audit tool, exposing 14 clinical calculators through a clean hexagonal architecture. All mathematical computation executes in pure Python (Zero Token Arithmetic), with strict Pydantic v2 boundary guards, coupled physiological propagation, explainable output with trap telemetry, and ≥95% test coverage.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `mcp[cli]>=1.2.0` — Model Context Protocol server framework
- `pydantic>=2.9.0` — Strict data validation with Field constraints
- `rich>=13.9.0` — Terminal UI for CLI benchmark dashboard

**Dev Dependencies**:
- `pytest>=8.3.0` — Unit testing with coverage
- `ruff>=0.7.0` — Fast Python linting/formatting
- `mypy>=1.13.0` — Static type checking

**Storage**: N/A (stateless computation engine; no persistence layer)

**Testing**: `pytest` with coverage target ≥95% for engine modules; deterministic gold-standard reference fixtures

**Target Platform**: Linux/macOS/Windows (Python 3.11+); MCP stdio/HTTP transport

**Project Type**: Library + CLI + MCP Server (hybrid)

**Performance Goals**:
- Individual calculator latency < 5ms
- Comprehensive audit (13 calculators) < 500ms wall-clock time for 100 consecutive invocations of `run_comprehensive_patient_audit` (all 13 sub-models populated) on any modern 2+ vCPU / 4GB+ RAM Linux/WSL2 runner (or < 5ms average per full audit call)
- Test suite execution < 5 seconds

**Constraints**:
- Zero Token Arithmetic: No math in LLM tokens; all computation in pure Python
- Hexagonal Architecture: Engines 100% pure Python, zero MCP/transport dependencies
- Fail-Fast Guards: Pydantic Field constraints reject impossible biology pre-execution
- Coupled Propagation: Automatic confounder correction (glucose→Na⁺, albumin→AG, IBW→ABW)
- Explainable Output: Every response = results+units + staging + pearls + trap telemetry
- Test-Driven Verification: Every equation + boundary clamp has pytest fixture

**Scale/Scope**:
- 7 engine modules (6 domain + 1 poly-audit)
- 14 clinical calculators
- ~50 Pydantic models (input/output per calculator)
- ~200 pytest test cases (gold-standard + edge cases + trap vectors)
- 1 CLI demo with 5 notorious "LLM Trap" benchmarks
- 1 MCP server exposing all tools

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Approach |
|-----------|--------|------------------------|
| I. Zero Token Arithmetic | ✅ PASS | All math in `engines/` pure Python functions; MCP tools delegate to engines |
| II. Hexagonal Architecture | ✅ PASS | `engines/` = pure Python + Pydantic; `server.py` = MCP adapter; `schemas/` = contracts |
| III. Fail-Fast Boundary Guards | ✅ PASS | Every input model uses `Field(ge=..., le=...)` + custom `@field_validator` with clinical error messages |
| IV. Coupled Physiological Propagation | ✅ PASS | Each engine documents propagation chain in docstring; pre-computation steps mandatory |
| V. Explainable Output & Trap Telemetry | ✅ PASS | Output models include `results`, `staging`, `clinical_pearls_and_actions`, `llm_trap_prevented` |
| VI. Test-Driven Clinical Verification | ✅ PASS | pytest fixtures for gold-standard values, boundaries, traps; ≥95% coverage enforced |

**No violations** — architecture fully aligns with all six constitutional principles.

## Project Structure

### Documentation (this feature)

```text
specs/001-clinical-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── renal.json
│   ├── acid_base.json
│   ├── cardiology.json
│   ├── hepatology.json
│   ├── critical_care.json
│   ├── hematology.json
│   └── poly_audit.json
└── tasks.md             # Phase 2 output (not created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── clinical_mcp/
    ├── __init__.py
    ├── schemas/
    │   ├── __init__.py
    │   ├── renal.py
    │   ├── acid_base.py
    │   ├── cardiology.py
    │   ├── hepatology.py
    │   ├── critical_care.py
    │   ├── hematology.py
    │   └── poly_audit.py
    │   └── common.py
    ├── engines/
    │   ├── __init__.py
    │   ├── renal.py
    │   ├── acid_base.py
    │   ├── cardiology.py
    │   ├── hepatology.py
    │   ├── critical_care.py
    │   ├── hematology.py
    │   └── poly_audit.py
    ├── server.py              # FastMCP server exposing all tools
    ├── cli_demo.py            # Rich terminal benchmark dashboard
    └── __main__.py            # Entry point: python -m clinical_mcp

tests/
├── __init__.py
├── conftest.py                # Shared fixtures
├── test_renal.py
├── test_acid_base.py
├── test_cardiology.py
├── test_hepatology.py
├── test_critical_care.py
├── test_hematology.py
├── test_poly_audit.py
└── test_boundary_guards.py    # Cross-cutting validation tests

pyproject.toml                 # uv project config with entrypoint
README.md                      # Flagship documentation
```

**Structure Decision**: Single-project layout with clear hexagonal separation (`schemas/` = contracts, `engines/` = pure domain logic, `server.py` = transport adapter, `cli_demo.py` = presentation layer). This matches the user's explicit directory structure requirement and satisfies Constitutional Principle II.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — all constitutional principles are satisfied by the chosen architecture. No complexity justification needed.

---

## Phase 0: Research

*All technical decisions resolved from user requirements and constitution. No NEEDS CLARIFICATION items remain.*

### Research Findings

| Topic | Decision | Rationale | Alternatives Considered |
|-------|----------|-----------|------------------------|
| Package manager | `uv` (pyproject.toml) | User requirement; fast, modern, PEP 621 compliant | Poetry, pip-tools — slower, less standard |
| MCP framework | `mcp[cli]>=1.2.0` | Official MCP Python SDK; stdio + HTTP transport | Custom MCP impl — reinvents wheel, higher maintenance |
| Validation | Pydantic v2 `Field` + `@field_validator` | Constitution Principle III; best-in-class performance | dataclasses + manual validation — verbose, error-prone |
| Testing | pytest + coverage | Constitution Principle VI; industry standard | unittest — less expressive fixtures |
| Linting | ruff + mypy | Fast, comprehensive, integrates with CI | flake8 + black + mypy — slower, fragmented |
| CLI UI | Rich | User requirement; beautiful terminal output | textual — overkill for demo dashboard |
| Entry point | `clinical-mcp = "clinical_mcp.server:main"` | User requirement; stdio MCP server | HTTP-only — less flexible for Claude Desktop |

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

**Key Entities** (from spec FR-002, FR-016):

1. **ComprehensivePatientInput** — Composite model for poly-audit; all 13 sub-models optional and default to `None`
   - `ckd_epi`, `cockcroft_gault`, `aki_urinary`, `acid_base`, `osmolality`, `calcium`, `qtc`, `hemodynamics`, `meld`, `fib4`, `oxygenation`, `qsofa_sirs`, `pe_ddimer`
   - An engine executes if and only if its corresponding sub-model is non-null

2. **EngineInput (per domain)** — Strict Pydantic models with `Field` constraints
   - Example: `CKDEPIInput(scr_mg_dl: float = Field(ge=0.1, le=30.0), age_years: float = Field(ge=18, le=120), sex: Literal["male", "female"])`
   - Custom `@field_validator` messages: "pH 6.4 is incompatible with life (valid range: 6.50–7.80)"

3. **EngineOutput (per domain)** — Structured response with 4 required components
   - Flat numeric `float`/`int` result fields paired with a top-level `unit: UCUMUnit` (e.g., `egfr_ml_min_per_173m2: float`, `unit: UCUMUnit = UCUMUnit.ML_MIN_1_73M2`); no nested `Quantity` wrapper
   - Explicit domain staging fields (e.g., `kdigo_stage: Literal["G1", "G2", "G3a", "G3b", "G4", "G5"]`)
   - `clinical_pearls_and_actions: List[str]` — evidence-based interpretation
   - `llm_trap_prevented: List[str]` — explicit trap descriptions

4. **ComprehensiveAuditReport** — Aggregated poly-audit output
   - `executed_engines: list[str]` — engines that ran
   - `skipped_engines: list[str]` — engines not executed per deterministic rule
   - `failed_engines: dict[str, str]` — engine name → error message
   - `triggered_trap_categories: list[LLMTrapCategory]` — deduplicated, first-occurrence order
   - `trap_descriptions: str` — unique human-readable trap strings joined with `"; "`
   - Flat optional domain result fields — `ckd_epi: Optional[CKDEPIOutput]`, `cockcroft_gault: Optional[CockcroftGaultOutput]`, `aki_urinary: Optional[AKIIndicesOutput]`, `acid_base: Optional[AcidBaseOutput]`, `osmolality: Optional[OsmolalityOutput]`, `calcium: Optional[CalciumOutput]`, `qtc: Optional[QTcOutput]`, `hemodynamics: Optional[HemodynamicsOutput]`, `meld: Optional[MELDOutput]`, `fib4: Optional[FIB4Output]`, `oxygenation: Optional[OxygenationOutput]`, `qsofa_sirs: Optional[QSOFASIRSOutput]`, `pe_ddimer: Optional[PEDDimerOutput]` (None when the engine did not execute)
   - `cross_domain_flags: List[str]` — discordance alerts (e.g., "CKD-EPI 52 vs CG 78 mL/min: DOAC dosing discrepancy")
   - `unified_risk_summary: str` — executive summary

5. **ClampAuditTrail** — UNOS/physiological boundary clamps
   - `parameter: str`, `original_value: float`, `clamped_value: float`, `rule: str`

6. **ComprehensivePatientInput** — Composite input model for `run_comprehensive_patient_audit` containing optional sub-models mapped directly to domain `EngineInput` Pydantic classes:
   - `ckd_epi: Optional[CKDEPIInput] = None`
   - `cockcroft_gault: Optional[CockcroftGaultInput] = None`
   - `aki_urinary: Optional[AKIIndicesInput] = None`
   - `acid_base: Optional[AcidBaseInput] = None`
   - `osmolality: Optional[OsmolalityInput] = None`
   - `calcium: Optional[CalciumInput] = None`
   - `qtc: Optional[QTcInput] = None`
   - `hemodynamics: Optional[HemodynamicsInput] = None`
   - `meld: Optional[MELDInput] = None`
   - `fib4: Optional[FIB4Input] = None`
   - `oxygenation: Optional[OxygenationInput] = None`
   - `qsofa_sirs: Optional[QSOFASIRSInput] = None`
   - `pe_ddimer: Optional[PEDDimerInput] = None`
   Deterministic Rule: An engine executes iff its corresponding sub-model is non-null (`is not None`). Each skipped sub-model is listed in `skipped_engines` in the output.

7. **LLMTrapCategory** — StrEnum with 6 distinct categories for structured trap telemetry:
   - `HYPOALBUMINEMIA_MASKED_HAGMA`
   - `OBESITY_COCKCROFT_GAULT_OVERDOSE`
   - `DIURETIC_FENA_MISINTERPRETATION`
   - `TACHYCARDIA_OR_WIDE_QRS_QTC_ARTIFACT`
   - `UNOS_MELD_LOGARITHMIC_BOUNDARY_VIOLATION`
   - `AGE_UNADJUSTED_DDIMER_FALSE_POSITIVE`

8. **AcidBaseDisorder** — StrEnum for acid-base diagnosis classification:
   - `NORMAL`
   - `PURE_HAGMA`
   - `PURE_NAGMA`
   - `MIXED_HAGMA_NAGMA`
   - `HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS`
   - `UNCOMPENSATED_RESPIRATORY_ACIDOSIS`
   - `SUPERIMPOSED_RESPIRATORY_ALKALOSIS`

### Contracts (`contracts/`)

Each domain exposes a JSON Schema contract (auto-generated from Pydantic models) defining:
- Input schema with constraints and descriptions
- Output schema with all 4 components
- Example values for documentation

Files: `renal.json`, `acid_base.json`, `cardiology.json`, `hepatology.json`, `critical_care.json`, `hematology.json`, `poly_audit.json`

### Quickstart Guide (`quickstart.md`)

```bash
# Install
uv sync

# Run MCP server (stdio for Claude Desktop)
uv run clinical-mcp

# Run CLI benchmark dashboard
uv run python -m clinical_mcp.cli_demo

# Run tests with coverage
uv run pytest --cov=src/clinical_mcp/engines --cov-report=term-missing

# Type check
uv run mypy src/clinical_mcp

# Lint
uv run ruff check src/clinical_mcp
```

**Validation Scenarios**:
1. **Renal**: `CKDEPIInput(scr_mg_dl=1.4, age_years=65, sex="male")` → eGFR ~55.8, KDIGO G3a
2. **Acid-Base**: `AcidBaseInput(na_meq_l=140, cl_meq_l=104, hco3_meq_l=12, albumin_g_dl=2.0, glucose_mg_dl=500)` → Hillier Na⁺, Figge AG, delta ratio
3. **Cardiology**: `QTcInput(qt_ms=420, hr_bpm=110, sex="male", qrs_ms=90)` → Framingham auto-selected, <500ms
4. **Hepatology**: `MELDInput(bilirubin_mg_dl=0.8, inr=0.9, creatinine_mg_dl=0.7, sodium_meq_l=137, albumin_g_dl=3.5)` → 3 clamps logged
5. **Critical Care**: `OxygenationInput(pao2_mmhg=80, paco2_mmhg=40, fio2=0.5, age_years=60)` → P/F=160, Moderate ARDS
6. **Hematology**: `PEDDimerInput(age_years=65, d_dimer_ng_ml_feu=600, wells_score=3.0)` → age-adjusted threshold 650, CTPA not indicated
7. **Poly-Audit**: Full `ComprehensivePatientInput` → integrated report with cross-domain flags

---

## Phase 2: Tasks (Preview)

*Generated by `/speckit.tasks` after plan approval. High-level task groups:*

1. **Project Setup** — `pyproject.toml`, `uv.lock`, directory scaffolding
2. **Schemas Layer** — 7 schema modules with Pydantic models + validators
3. **Engines Layer** — 7 engine modules with pure Python functions + docstrings
4. **MCP Server** — `server.py` exposing all tools with rich docstrings
5. **CLI Demo** — `cli_demo.py` with 5 LLM Trap benchmarks + Rich UI
6. **Test Suite** — 7 test modules + boundary guards + conftest fixtures
7. **Documentation** — README.md with Mermaid diagram, comparison table, MCP configs
8. **CI/CD** — GitHub Actions workflow (test, type-check, lint, coverage gate)

---

*Plan complete. Ready for `/speckit.tasks` to generate detailed task breakdown.*