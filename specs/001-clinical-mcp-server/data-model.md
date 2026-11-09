# Data Model: clinical-mcp

**Feature**: specs/001-clinical-mcp-server  
**Date**: 2026-11-07  
**Source**: Feature spec (FR-002, FR-003–FR-016), Constitution Principles III–VI

---

## Entity Definitions

### 1. ComprehensivePatientInput

**Purpose**: Composite input for `run_comprehensive_patient_audit`. An engine executes if and only
if its corresponding sub-model is non-null. All fields are optional and default to `None`.

| Field | Type | Default |
|-------|------|---------|
| `ckd_epi` | `CKDEPIInput \| None` | `None` |
| `cockcroft_gault` | `CockcroftGaultInput \| None` | `None` |
| `aki_urinary` | `AKIIndicesInput \| None` | `None` |
| `acid_base` | `AcidBaseInput \| None` | `None` |
| `osmolality` | `OsmolalityInput \| None` | `None` |
| `calcium` | `CalciumInput \| None` | `None` |
| `qtc` | `QTcInput \| None` | `None` |
| `hemodynamics` | `HemodynamicsInput \| None` | `None` |
| `meld` | `MELDInput \| None` | `None` |
| `fib4` | `FIB4Input \| None` | `None` |
| `oxygenation` | `OxygenationInput \| None` | `None` |
| `qsofa_sirs` | `QSOFASIRSInput \| None` | `None` |
| `pe_ddimer` | `PEDDimerInput \| None` | `None` |

Model config: `extra="forbid"`.

---

### 2. EngineInput (Per-Domain Base Pattern)

**Purpose**: Strict Pydantic input model for each calculator with physiological boundary guards.

**Common Pattern**:
```python
class EngineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Each field uses Field(ge=, le=, gt=) with clinical bounds.
```

**Domain-Specific Input Models**:

#### Renal Domain (`schemas/renal.py`)
| Model | Fields |
|-------|--------|
| `CKDEPIInput` | `scr_mg_dl` (`0.1–30.0`), `age_years` (`18–120`), `sex: Literal["male","female"]` |
| `CockcroftGaultInput` | `age_years` (`18–120`), `sex`, `weight_kg` (`20–350`), `height_cm` (`100–250`), `scr_mg_dl` (`0.1–30.0`) |
| `AKIIndicesInput` | `urine_sodium_meq_l` (`0–300`), `serum_sodium_meq_l` (`100–180`), `urine_creatinine_mg_dl` (`>0–500`), `serum_creatinine_mg_dl` (`0.1–30`), `on_diuretics=False`, `serum_bun_mg_dl?` (`1–200`), `urine_urea_mg_dl?` (`1–5000`) |

#### Acid-Base Domain (`schemas/acid_base.py`)
| Model | Fields |
|-------|--------|
| `AcidBaseInput` | `na_meq_l` (`100–180`), `cl_meq_l` (`50–150`), `hco3_meq_l` (`1–60`), `albumin_g_dl=4.0` (`0.5–6.0`), `glucose_mg_dl=100.0` (`0–2000`), `paco2_mmhg?` (`10–100`), `ph?` (`6.5–7.8`), `lactate_mmol_l?` (`0–30`), `prior_known_disorder?` |
| `OsmolalityInput` | `na_meq_l`, `glucose_mg_dl`, `bun_mg_dl` (`1–200`), `measured_osmolality_mosm_kg?`, `ethanol_mg_dl?`, `weight_kg?`, `sex?`, `age_years?` |
| `CalciumInput` | `total_ca_mg_dl` (`4.0–15.0`), `albumin_g_dl` (`0.5–6.0`) |

#### Cardiology Domain (`schemas/cardiology.py`)
| Model | Fields |
|-------|--------|
| `QTcInput` | `qt_ms` (`150–800`), `hr_bpm` (`20–300`), `sex="male"`, `qrs_ms=90.0` (`40–200`) |
| `HemodynamicsInput` | `sbp_mmhg` (`30–300`), `dbp_mmhg` (`20–200`), `hr_bpm` (`20–300`) |

#### Hepatology Domain (`schemas/hepatology.py`)
| Model | Fields |
|-------|--------|
| `MELDInput` | `bilirubin_mg_dl` (`0.1–60`), `inr` (`0.5–10`), `creatinine_mg_dl` (`0.1–15`), `sodium_meq_l` (`100–180`), `albumin_g_dl` (`0.5–6.0`), `sex="male"`, `dialysis=False` |
| `FIB4Input` | `age_years` (`18–120`), `ast_u_l` (`1–10000`), `alt_u_l` (`1–10000`), `platelets_10e9_l` (`10–1000`) |

#### Critical Care Domain (`schemas/critical_care.py`)
| Model | Fields |
|-------|--------|
| `OxygenationInput` | `pao2_mmhg` (`20–600`), `paco2_mmhg` (`10–100`), `fio2` (`0.21–1.0`), `age_years` (`18–120`), `barometric_pressure_mmhg=760.0` (`500–800`), `respiratory_quotient=0.8` (`0.7–1.0`) |
| `QSOFASIRSInput` | `rr_bpm` (`5–60`), `sbp_mmhg` (`30–300`), `gcs_score` (`3–15`), `temp_celsius?` (`20–45`), `hr_bpm?` (`20–300`), `wbc_10e9_l?` (`0–200`), `paco2_mmhg?` (`10–100`), `lactate_mmol_l?` (`0–30`) |

#### Hematology Domain (`schemas/hematology.py`)
| Model | Fields |
|-------|--------|
| `PEDDimerInput` | `age_years` (`18–120`), `d_dimer_ng_ml_feu` (`0–50000`), `wells_score` (`0–12.5`) |

---

### 3. EngineOutput (Per-Domain Base Pattern)

**Purpose**: Structured response with the four constitutionally mandated components.

**Common Pattern**:
```python
class EngineOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unit: UCUMUnit                        # (a) one top-level UCUM unit
    clinical_pearls_and_actions: list[str] # (b) interpretation and next actions
    llm_trap_prevented: list[str]          # (c) explicit trap descriptions
    # (d) flat domain-specific float/int result and staging fields
```

There is **no** nested `Quantity` wrapper, `results` dict, or generic `staging` dict. Every numeric
result is a flat `float`/`int` field declared on its domain output model.

**Domain-Specific Output Models**:

#### Renal Domain
| Model | Flat Fields | Unit |
|-------|-------------|------|
| `CKDEPIOutput` | `egfr_ml_min_per_173m2`, `kdigo_stage` (G1/G2/G3a/G3b/G4/G5) | `mL/min/1.73m2` |
| `CockcroftGaultOutput` | `bmi`, `ibw_kg`, `adjbw_kg`, `selected_weight_kg`, `weight_selection_rule` (actual/ibw/adjbw), `crcl_ml_min` | `mL/min` |
| `AKIIndicesOutput` | `fena_percent`, `feurea_percent?`, `aki_etiology` (prerenal/atn/indeterminate/diuretic_confounded) | `%` |

#### Acid-Base Domain
| Model | Flat Fields | Unit |
|-------|-------------|------|
| `AcidBaseOutput` | `raw_anion_gap`, `albumin_corrected_anion_gap`, `delta_ratio?`, `winters_expected_paco2_min?`, `winters_expected_paco2_max?`, `disorders: list[AcidBaseDisorder]`, `corrected_na_katz`, `corrected_na_hillier`, `active_na_correction_method` (katz/hillier) | `mEq/L` |
| `OsmolalityOutput` | `calculated_osmolality_mosm_kg`, `osmolar_gap_mosm_kg?`, `free_water_deficit_l?`, `toxic_alcohol_flag` | `mOsm/kg` |
| `CalciumOutput` | `corrected_ca_mg_dl` | `mg/dL` |

#### Cardiology Domain
| Model | Flat Fields | Unit |
|-------|-------------|------|
| `QTcOutput` | `qrs_widened`, `bogossian_modified_qt_ms?`, `qtc_bazett_ms`, `qtc_fridericia_ms`, `qtc_framingham_ms`, `recommended_primary_metric`, `recommended_qtc_ms`, `torsades_risk` | `ms` |
| `HemodynamicsOutput` | `map_mmhg`, `pulse_pressure_mmhg`, `shock_index`, `modified_shock_index`, `occult_shock`, `high_risk` | `mmHg` |

#### Hepatology Domain
| Model | Flat Fields | Unit |
|-------|-------------|------|
| `MELDOutput` | `meld_na`, `meld_3`, `mortality_bracket_meld_na`, `mortality_bracket_meld_3`, `clamps_applied: list[ClampAuditTrail]` | `score` |
| `FIB4Output` | `fib4_index`, `fibrosis_risk` (low/indeterminate/high) | `score` |

#### Critical Care Domain
| Model | Flat Fields | Unit |
|-------|-------------|------|
| `OxygenationOutput` | `pao2_alveolar_mmhg`, `aa_gradient_mmhg`, `expected_aa_gradient_mmhg`, `pf_ratio`, `ards_stage` (none/mild/moderate/severe) | `mmHg` |
| `QSOFASIRSOutput` | `qsofa_score`, `sirs_score?`, `sepsis_screen` (low/moderate/high) | `score` |

#### Hematology Domain
| Model | Flat Fields | Unit |
|-------|-------------|------|
| `PEDDimerOutput` | `age_adjusted_threshold_ng_ml`, `ddimer_positive`, `ctpa_indicated`, `wells_probability` (low/moderate/high) | `ng/mL FEU` |

---

### 4. ComprehensiveAuditReport

**Purpose**: Aggregated output from `run_comprehensive_patient_audit`.

| Field | Type | Description |
|-------|------|-------------|
| `executed_engines` | `list[str]` | Engines that ran |
| `skipped_engines` | `list[str]` | Sub-models that were `None` |
| `failed_engines` | `dict[str, str]` | Engine name → error message |
| `triggered_trap_categories` | `list[LLMTrapCategory]` | Deduplicated, first-occurrence order |
| `trap_descriptions` | `str` | Unique trap strings joined with `"; "` |
| `cross_domain_flags` | `list[str]` | Discordance alerts |
| `unified_risk_summary` | `str` | Executive clinical summary |
| `ckd_epi` … `pe_ddimer` | Optional domain outputs | Flat per-domain results; `None` when the engine did not execute |

The report contains **no** `all_domain_results`, `domain_results`, `results`, or
`all_traps_prevented` wrapper.

**Cross-Domain Flag Rules** (implemented):
- If `|CKD-EPI_eGFR - CG_CrCl| / CKD-EPI_eGFR > 0.3` → CKD-EPI vs Cockcroft-Gault discrepancy.
- If `MELD` computed AND `CKD-EPI eGFR < 30` → MELD with severe renal impairment.
- If `MELD` computed AND `AKI` computed → concurrent AKI and liver disease.
- If `recommended_qtc_ms >= 500` → high Torsades risk.
- If `P/F ratio <= 300` → Berlin ARDS criteria met.

---

### 5. ClampAuditTrail

**Purpose**: Record of every UNOS/physiological boundary clamp applied.

| Field | Type | Description |
|-------|------|-------------|
| `parameter` | `str` | Parameter name (e.g., `"bilirubin_mg_dl"`) |
| `original_value` | `float` | Value before clamping |
| `clamped_value` | `float` | Value after clamping |
| `rule` | `str` | Rule description (e.g., `"UNOS floor 1.0"`, `"MELD 3.0 cap 3.0"`) |

---

### 6. Enums

- **`UCUMUnit`** (`StrEnum`): `mL/min/1.73m2`, `mL/min`, `%`, `mEq/L`, `mg/dL`, `mOsm/kg`, `L`,
  `ms`, `mmHg`, `L/min/m2`, `score`, `ng/mL FEU`.
- **`LLMTrapCategory`** (`StrEnum`): `HYPOALBUMINEMIA_MASKED_HAGMA`,
  `OBESITY_COCKCROFT_GAULT_OVERDOSE`, `DIURETIC_FENA_MISINTERPRETATION`,
  `TACHYCARDIA_OR_WIDE_QRS_QTC_ARTIFACT`, `UNOS_MELD_LOGARITHMIC_BOUNDARY_VIOLATION`,
  `AGE_UNADJUSTED_DDIMER_FALSE_POSITIVE`.
- **`AcidBaseDisorder`** (`StrEnum`): `NORMAL`, `PURE_HAGMA`, `PURE_NAGMA`, `MIXED_HAGMA_NAGMA`,
  `HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS`, `UNCOMPENSATED_RESPIRATORY_ACIDOSIS`,
  `SUPERIMPOSED_RESPIRATORY_ALKALOSIS`.

---

## Validation Rules Summary

| Entity | Rule Type | Example |
|--------|-----------|---------|
| All inputs | `Field(ge=, le=, gt=)` | `hco3_meq_l: Field(ge=1.0, le=60.0)` |
| All inputs | `extra="forbid"` | Unknown keys raise a validation error |
| All outputs | Flat numeric fields | `crcl_ml_min: float` |
| All outputs | One top-level UCUM unit | `unit: UCUMUnit = UCUMUnit.ML_MIN` |
| All outputs | 4 components mandatory | numeric fields, staging field, `clinical_pearls_and_actions`, `llm_trap_prevented` |
| Engine functions | Pure Python, no I/O | `def calculate_xyz(input: XYZInput) -> XYZOutput:` |
| Engine functions | Docstring documents propagation | `"""Propagation: glucose → corrected Na⁺ → osmolality"""` |

---

## State Transitions

None — all engines are pure functions (stateless). `ComprehensivePatientInput` →
`ComprehensiveAuditReport` is a single transformation pipeline.
