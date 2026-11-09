# Quickstart Guide: clinical-mcp

**Feature**: specs/001-clinical-mcp-server  
**Date**: 2026-11-07  
**Purpose**: Runnable validation scenarios proving the feature works end-to-end

---

## Prerequisites

- Python 3.11+
- `uv` package manager (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Git (for cloning)

---

## Installation

```bash
# Clone and enter project
git clone <repo-url> clinical-mcp
cd clinical-mcp

# Install all dependencies (core + dev)
uv sync --all-extras

# Verify installation
uv run python -m clinical_mcp.cli_demo --help
uv run pytest --version
uv run ruff --version
uv run mypy --version
```

---

## Running the MCP Server

### stdio Transport (Claude Desktop, Cursor, OpenCode)

```bash
# Direct stdio (for MCP clients)
uv run clinical-mcp
```

The server speaks MCP over stdio and exposes 14 tools (one per calculator plus
`comprehensive_audit`).

**Claude Desktop Config** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "clinical-mcp": {
      "command": "uv",
      "args": ["run", "clinical-mcp"],
      "cwd": "/path/to/clinical-mcp"
    }
  }
}
```

**Cursor Config** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "clinical-mcp": {
      "command": "uv",
      "args": ["run", "clinical-mcp"],
      "cwd": "/path/to/clinical-mcp"
    }
  }
}
```

**OpenCode Config** (`.opencode/mcp.json`):
```json
{
  "mcpServers": {
    "clinical-mcp": {
      "command": "uv",
      "args": ["run", "clinical-mcp"],
      "cwd": "/path/to/clinical-mcp"
    }
  }
}
```

---

## CLI Benchmark Dashboard

Runs 5 notorious "LLM Trap" scenarios comparing naive token arithmetic vs. deterministic engines:

```bash
# Run full dashboard
uv run python -m clinical_mcp.cli_demo

# Run a specific trap (1-5)
uv run python -m clinical_mcp.cli_demo --trap 1   # occult hypoalbuminemic HAGMA
uv run python -m clinical_mcp.cli_demo --trap 2   # obese Cockcroft-Gault overdose
uv run python -m clinical_mcp.cli_demo --trap 3   # tachycardic wide-QRS QTc artifact
uv run python -m clinical_mcp.cli_demo --trap 4   # UNOS MELD clamping
uv run python -m clinical_mcp.cli_demo --trap 5   # age-adjusted D-dimer
```

**Expected Output**: Rich terminal tables showing side-by-side comparison:
- Naive LLM Token Guess (incorrect)
- clinical-mcp Deterministic Engine (correct)
- Trap prevented explanation

---

## Running Tests

```bash
# Full test suite with coverage
uv run pytest --cov=src/clinical_mcp/engines --cov-report=term-missing

# Target: ≥95% engine coverage (current: 100%)
# Expected: 109 tests passing

# Run specific domain tests
uv run pytest tests/test_renal.py -v
uv run pytest tests/test_acid_base.py -v
uv run pytest tests/test_cardiology.py -v
uv run pytest tests/test_hepatology.py -v
uv run pytest tests/test_critical_care.py -v
uv run pytest tests/test_hematology.py -v
uv run pytest tests/test_poly_audit.py -v
uv run pytest tests/test_boundary_guards.py -v
```

---

## Type Checking & Linting

```bash
# Static type checking
uv run mypy src/clinical_mcp

# Linting (ruff replaces flake8, black, isort)
uv run ruff check src/clinical_mcp tests
```

---

## Validation Scenarios

Each scenario below can be tested via MCP tool calls or direct Python imports.

### 1. Renal: CKD-EPI eGFR
```python
from clinical_mcp.schemas.renal import CKDEPIInput
from clinical_mcp.engines.renal import calculate_ckd_epi

input = CKDEPIInput(scr_mg_dl=1.4, age_years=65, sex="male")
output = calculate_ckd_epi(input)
# Expected: eGFR ~55.8 mL/min/1.73m², KDIGO G3a
assert round(output.egfr_ml_min_per_173m2, 1) == 55.8
assert output.kdigo_stage == "G3a"
```

### 2. Renal: Cockcroft-Gault with ABW Selection
```python
from clinical_mcp.schemas.renal import CockcroftGaultInput
from clinical_mcp.engines.renal import calculate_cockcroft_gault

# Obese patient: 120 kg, 170 cm male, SCr 1.2
input = CockcroftGaultInput(
    scr_mg_dl=1.2, age_years=60, sex="male",
    weight_kg=120, height_cm=170
)
output = calculate_cockcroft_gault(input)
# Expected: IBW=65.8, AdjBW=87.5, CrCl uses AdjBW ~81 mL/min
assert output.weight_selection_rule == "adjbw"
assert round(output.ibw_kg, 1) == 65.8
assert round(output.adjbw_kg, 1) == 87.5
assert round(output.crcl_ml_min, 1) == 81.0
```

### 3. Acid-Base: Coupled Propagation (Hypoalbuminemic Lactic Acidosis)
```python
from clinical_mcp.schemas.acid_base import AcidBaseInput
from clinical_mcp.engines.acid_base import calculate_acid_base

# Na 140, Cl 104, HCO3 12, Albumin 2.0, Glucose 500
input = AcidBaseInput(
    na_meq_l=140, cl_meq_l=104, hco3_meq_l=12,
    albumin_g_dl=2.0, glucose_mg_dl=500,
    paco2_mmhg=28, ph=7.25
)
output = calculate_acid_base(input)
# Expected: Hillier Na+ correction, Figge AG, delta ratio, Winter's
assert output.active_na_correction_method == "hillier"
assert output.corrected_na_hillier > 140  # Glucose correction
assert output.albumin_corrected_anion_gap > output.raw_anion_gap  # Albumin correction
assert output.delta_ratio is not None
```

### 4. Acid-Base: Osmolar Gap Toxic Alcohol Screen
```python
from clinical_mcp.schemas.acid_base import OsmolalityInput
from clinical_mcp.engines.acid_base import calculate_osmolality

input = OsmolalityInput(
    na_meq_l=140, glucose_mg_dl=100, bun_mg_dl=14,
    measured_osmolality_mosm_kg=320, ethanol_mg_dl=0
)
output = calculate_osmolality(input)
# Expected: Calculated ~290.6, Gap=29.4 → toxic alcohol flag
assert output.osmolar_gap_mosm_kg is not None
assert output.osmolar_gap_mosm_kg > 10
assert output.toxic_alcohol_flag is True
```

### 5. Cardiology: QTc Auto-Selection at Tachycardia
```python
from clinical_mcp.schemas.cardiology import QTcInput
from clinical_mcp.engines.cardiology import calculate_qtc

# HR 110, QT 420, QRS 90
input = QTcInput(qt_ms=420, hr_bpm=110, sex="male", qrs_ms=90)
output = calculate_qtc(input)
# Expected: Bazett over-corrects, Framingham selected
assert output.recommended_primary_metric == "framingham"
assert output.recommended_qtc_ms < 500
```

### 6. Cardiology: Wide-QRS Bogossian Adjustment
```python
input = QTcInput(qt_ms=400, hr_bpm=50, sex="male", qrs_ms=140)
output = calculate_qtc(input)
# Expected: Wide-QRS adjustment applied, warning in traps
assert output.qrs_widened is True
assert output.bogossian_modified_qt_ms is not None
assert any("Bogossian" in trap for trap in output.llm_trap_prevented)
```

### 7. Hepatology: MELD-Na with UNOS Clamping
```python
from clinical_mcp.schemas.hepatology import MELDInput
from clinical_mcp.engines.hepatology import calculate_meld

# Low labs requiring clamping
input = MELDInput(
    bilirubin_mg_dl=0.8, inr=0.9, creatinine_mg_dl=0.7,
    sodium_meq_l=137, albumin_g_dl=3.5, sex="male", dialysis=False
)
output = calculate_meld(input)
# Expected: 3 clamps (bilirubin, INR, Cr all floored to 1.0)
assert len(output.clamps_applied) == 3
assert output.meld_na < output.meld_3
```

### 8. Critical Care: ARDS Staging
```python
from clinical_mcp.schemas.critical_care import OxygenationInput
from clinical_mcp.engines.critical_care import calculate_oxygenation

input = OxygenationInput(
    pao2_mmhg=80, paco2_mmhg=40, fio2=0.5, age_years=60
)
output = calculate_oxygenation(input)
# Expected: P/F=160 → Moderate ARDS
assert output.pf_ratio == 160.0
assert output.ards_stage == "moderate"
```

### 9. Hematology: Age-Adjusted D-Dimer
```python
from clinical_mcp.schemas.hematology import PEDDimerInput
from clinical_mcp.engines.hematology import calculate_peddimer

# Age 65, D-dimer 600, Wells 3.0
input = PEDDimerInput(
    age_years=65, d_dimer_ng_ml_feu=600, wells_score=3.0
)
output = calculate_peddimer(input)
# Expected: Age-adjusted threshold = 650, D-dimer below → CTPA not indicated
assert output.age_adjusted_threshold_ng_ml == 650.0
assert output.ctpa_indicated is False
```

### 10. Poly-Audit: Comprehensive Multi-System
```python
from clinical_mcp.schemas.poly_audit import ComprehensivePatientInput
from clinical_mcp.engines.poly_audit import run_comprehensive_patient_audit
from clinical_mcp.schemas.renal import CKDEPIInput, CockcroftGaultInput, AKIIndicesInput
from clinical_mcp.schemas.acid_base import AcidBaseInput, OsmolalityInput, CalciumInput
from clinical_mcp.schemas.cardiology import QTcInput, HemodynamicsInput
from clinical_mcp.schemas.hepatology import MELDInput, FIB4Input
from clinical_mcp.schemas.critical_care import OxygenationInput, QSOFASIRSInput
from clinical_mcp.schemas.hematology import PEDDimerInput

# Septic shock with AKI, lactic acidosis, thrombocytopenia
patient = ComprehensivePatientInput(
    ckd_epi=CKDEPIInput(scr_mg_dl=2.8, age_years=65, sex="male"),
    cockcroft_gault=CockcroftGaultInput(
        age_years=65, sex="male", weight_kg=80, height_cm=175, scr_mg_dl=2.8
    ),
    aki_urinary=AKIIndicesInput(
        urine_sodium_meq_l=20, serum_sodium_meq_l=138,
        urine_creatinine_mg_dl=80, serum_creatinine_mg_dl=2.8,
        on_diuretics=False, serum_bun_mg_dl=45, urine_urea_mg_dl=200
    ),
    acid_base=AcidBaseInput(
        na_meq_l=138, cl_meq_l=102, hco3_meq_l=14, albumin_g_dl=2.5,
        glucose_mg_dl=180, paco2_mmhg=30, ph=7.22, lactate_mmol_l=4.5
    ),
    osmolality=OsmolalityInput(na_meq_l=138, glucose_mg_dl=180, bun_mg_dl=45),
    calcium=CalciumInput(total_ca_mg_dl=8.0, albumin_g_dl=2.5),
    qtc=QTcInput(qt_ms=440, hr_bpm=115, sex="male", qrs_ms=90),
    hemodynamics=HemodynamicsInput(sbp_mmhg=85, dbp_mmhg=50, hr_bpm=115),
    meld=MELDInput(
        bilirubin_mg_dl=1.2, inr=1.3, creatinine_mg_dl=2.8,
        sodium_meq_l=138, albumin_g_dl=2.5, sex="male"
    ),
    fib4=FIB4Input(age_years=65, ast_u_l=80, alt_u_l=60, platelets_10e9_l=90),
    oxygenation=OxygenationInput(pao2_mmhg=85, paco2_mmhg=30, fio2=0.5, age_years=65),
    qsofa_sirs=QSOFASIRSInput(
        rr_bpm=28, sbp_mmhg=85, gcs_score=13, temp_celsius=38.5,
        hr_bpm=115, wbc_10e9_l=18, paco2_mmhg=30, lactate_mmol_l=4.5
    ),
    pe_ddimer=PEDDimerInput(age_years=65, d_dimer_ng_ml_feu=600, wells_score=3.0)
)
report = run_comprehensive_patient_audit(patient)
# Expected: all 13 engines execute, cross-domain flags, unified trap telemetry
assert len(report.executed_engines) == 13
assert report.failed_engines == {}
assert len(report.triggered_trap_categories) >= 3
assert "Concurrent AKI and liver disease" in " ".join(report.cross_domain_flags)
assert report.pe_ddimer is not None and report.pe_ddimer.ctpa_indicated is False
```

---

## Expected Outcomes Checklist

| Scenario | Pass Criteria |
|----------|---------------|
| MCP server starts | `uv run clinical-mcp` exposes 14 tools over stdio |
| CLI dashboard runs | `uv run python -m clinical_mcp.cli_demo` shows 5 trap tables |
| All tests pass | `uv run pytest` → 109 tests, 0 failures |
| Coverage ≥95% | `uv run pytest --cov=src/clinical_mcp/engines` → engines ≥95% |
| Type check clean | `uv run mypy src/clinical_mcp` → 0 errors |
| Lint clean | `uv run ruff check src/clinical_mcp tests` → 0 errors |
| Validation scenarios | All 10 Python snippets produce expected assertions |

---

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| `uv` not found | Install: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Python version | Use `uv python install 3.11` then `uv python pin 3.11` |
| MCP client can't connect | Verify `cwd` in config matches project root |
| Import errors | Run `uv sync --all-extras` to ensure dev deps installed |
| Coverage <95% | Check `tests/` for missing edge-case fixtures |

---

## Next Steps

After validation, review the implementation task ledger:
```bash
sed -n '1,80p' specs/001-clinical-mcp-server/tasks.md
```
