# Feature Specification: Clinical MCP Server

**Feature Branch**: `001-clinical-mcp-server`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "Build `clinical-mcp`, the definitive open-source Model Context Protocol (MCP) server for deterministic clinical physiology, critical care, and pharmacokinetic calculations. The system must provide 6 specialized domain modules plus 1 unified multi-system patient audit tool..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Renal & Pharmacokinetic Clearance Calculations (Priority: P1)

**As a** clinician or pharmacist **I want to** calculate kidney function and drug dosing adjustments using validated formulas **so that** I can make safe prescribing decisions for patients with renal impairment.

**Why this priority**: Renal dosing errors cause preventable adverse drug events. This domain provides the foundational calculations used daily in clinical practice (CKD-EPI for staging, Cockcroft-Gault for FDA-labeled drug dosing, AKI indices for etiology differentiation).

**Independent Test**: Can be fully tested by providing lab values (SCr, age, sex, weight, height, urinary electrolytes) and verifying outputs match published reference values for each formula. Each calculator (CKD-EPI, Cockcroft-Gault, FENa/FEUrea) produces deterministic results with KDIGO staging and dosing guidance.

**Acceptance Scenarios**:
1. **Given** a 65-year-old male with SCr 1.4 mg/dL, **When** CKD-EPI is calculated, **Then** eGFR returns ~52 mL/min/1.73m² with KDIGO Stage G3a
2. **Given** an 80 kg, 175 cm male with SCr 1.2 mg/dL, **When** Cockcroft-Gault runs, **Then** CrCl returns ~78 mL/min using Devine IBW with ABW selection logic
3. **Given** FENa inputs with on_diuretics=true, **When** AKI indices run, **Then** FENa interpretation is suppressed and FEUrea becomes primary with prerenal/ATN thresholds applied

---

### User Story 2 - Acid-Base, Electrolyte & Osmolality Analysis (Priority: P1)

**As a** critical care physician **I want to** automatically compute corrected electrolytes, anion gap with albumin correction, delta ratio, and osmolality **so that** I can rapidly diagnose complex acid-base disorders and toxic ingestions without manual calculation errors.

**Why this priority**: Acid-base disorders are time-critical in ICU. Coupled propagation (glucose→Na⁺ correction→osmolality; albumin→AG correction→delta ratio) prevents cascade errors that occur when calculators are used in isolation.

**Independent Test**: Can be tested by providing a comprehensive metabolic panel plus blood gas values and verifying each coupled output matches gold-standard reference calculations (Figge AG, Hillier Na⁺, Winter's formula, osmolar gap >10 flagging).

**Acceptance Scenarios**:
1. **Given** Na 140, Cl 104, HCO3 12, Albumin 2.0, Glucose 500, **When** acid-base engine runs, **Then** corrected Na⁺ (Hillier 0.024 factor), Figge-corrected AG, delta ratio, and Winter's expected PaCO2 all compute with appropriate flags
2. **Given** measured osmolality 320, calculated 305, **When** osmolar gap runs, **Then** gap = 15 mOsm/kg triggers toxic alcohol ingestion flag
3. **Given** Na 155, weight 70 kg male, **When** free water deficit runs, **Then** TBW factor 0.6 applied and deficit calculated in liters

---

### User Story 3 - Cardiac Repolarization & Hemodynamic Assessment (Priority: P1)

**As a** cardiologist or hospitalist **I want to** compute QTc using multiple correction formulas with automatic selection and wide-QRS adjustment **so that** I avoid Bazett over/under-correction artifacts and detect true Torsades risk.

**Why this priority**: QTc prolongation is a common drug safety concern. Automatic Fridericia/Framingham selection at heart rate extremes and Bogossian wide-QRS adjustment prevent false positives that lead to unnecessary drug holds.

**Independent Test**: Provide QT, HR, sex, QRS duration and verify all three formulas compute, auto-selection logic triggers correctly, Torsades threshold (500ms) flagged, and wide-QRS adjustment warning appears when QRS >120ms.

**Acceptance Scenarios**:
1. **Given** QT 420ms, HR 110 bpm, QRS 90ms, **When** QTc engine runs, **Then** Bazett over-corrects, Fridericia/Framingham auto-selected, result <500ms
2. **Given** QT 400ms, HR 50 bpm, QRS 140ms, **Then** Bogossian adjustment applied, wide-QRS warning emitted, corrected QTc computed
3. **Given** SBP 85, DBP 50, HR 115, **When** hemodynamics run, **Then** MAP=62, Shock Index=1.35 (occult shock), Modified Shock Index=1.85 (high risk)

---

### User Story 4 - Hepatic Disease Severity & Fibrosis Staging (Priority: P2)

**As a** hepatologist or transplant coordinator **I want to** calculate MELD-Na and MELD 3.0 with strict UNOS clamping **so that** liver transplant priority scoring is accurate and auditable.

**Why this priority**: MELD scores directly determine organ allocation. UNOS clamping rules (floors at 1.0, caps at 4.0/3.0, Na 125-137) must be enforced exactly to match official policy.

**Independent Test**: Provide lab values at boundary conditions (bilirubin 0.5→clamped to 1.0, creatinine 5.0→capped at 4.0/3.0, Na 120→clamped to 125) and verify both MELD-Na and MELD 3.0 match UNOS calculator outputs with clamp audit trail.

**Acceptance Scenarios**:
1. **Given** bilirubin 0.8, INR 0.9, Cr 0.7, Na 140, albumin 4.0, **When** MELD runs, **Then** all values floored to 1.0, clamp list shows 3 parameters clamped
2. **Given** dialysis=true, Cr 5.0, **When** MELD 3.0 runs, **Then** Cr capped at 3.0 per MELD 3.0 specification
3. **Given** age 60, AST 80, ALT 40, platelets 150, **When** FIB-4 runs, **Then** score = (60*80)/(150*sqrt(40)) ≈ 2.53 with fibrosis risk interpretation

---

### User Story 5 - Critical Care Oxygenation & Sepsis Triage (Priority: P1)

**As an** intensivist **I want to** compute A-a gradient, P/F ratio with Berlin ARDS staging, and qSOFA/SIRS **so that** I can rapidly classify respiratory failure severity and sepsis risk at the bedside.

**Why this priority**: ARDS staging drives ventilator management (low tidal volume, prone positioning). qSOFA triggers sepsis protocol activation. Both are time-sensitive clinical decisions.

**Independent Test**: Provide ABG values (PaO2, PaCO2, FiO2, age) and vital signs (RR, SBP, GCS, lactate) and verify PAO2 alveolar gas equation, A-a gradient with age-expected, P/F ratio with Berlin staging, qSOFA ≥2 and SIRS ≥2 criteria.

**Acceptance Scenarios**:
1. **Given** PaO2 80, PaCO2 40, FiO2 0.5, age 60, **When** oxygenation runs, **Then** PAO2≈99.7, A-a≈19.7, expected A-a≈19, P/F=160 (Moderate ARDS)
2. **Given** RR 24, SBP 95, GCS 13, lactate 3.5, **When** qSOFA/SIRS runs, **Then** qSOFA=2 (RR≥22, SBP≤100), SIRS=3 (RR, SBP, lactate), sepsis screening positive

---

### User Story 6 - Pulmonary Embolism Risk Stratification (Priority: P2)

**As an** emergency physician **I want to** apply age-adjusted D-dimer thresholds with Wells score **so that** I can safely rule out PE without unnecessary CTPA radiation in low-risk patients over 50.

**Why this priority**: Age-adjusted D-dimer (age×10 ng/mL FEU for >50yo) increases specificity while maintaining sensitivity, reducing false-positive imaging.

**Independent Test**: Provide age, D-dimer, Wells score and verify age-adjusted threshold calculation, imaging recommendation (exclude vs. indicate CTPA), and Wells probability stratification.

**Acceptance Scenarios**:
1. **Given** age 65, D-dimer 600 ng/mL FEU, Wells PE 3.0, **When** PE audit runs, **Then** age-adjusted threshold=650, D-dimer below threshold, CTPA not indicated despite elevated standard threshold
2. **Given** age 45, D-dimer 550, Wells 4.5, **Then** standard 500 threshold applies, CTPA indicated

---

### User Story 7 - Comprehensive Multi-System Patient Audit (Priority: P1)

**As a** clinical AI system **I want to** execute all domain engines against a unified patient snapshot **so that** I produce a single integrated risk report with cross-domain trap telemetry.

**Why this priority**: Real patients have multi-organ dysfunction. Running engines in isolation misses interactions (e.g., renal impairment affecting drug dosing, hepatic dysfunction affecting coagulation, acid-base affecting electrolytes). The unified audit aggregates all `llm_trap_prevented` entries for a complete safety audit trail.

**Independent Test**: Provide a complete patient panel (vitals, labs, blood gas, medications) and verify all 13 individual calculators execute, results aggregate into unified report, cross-domain flags surface (e.g., CKD-EPI vs CG discordance, MELD-Na with renal impairment), and trap telemetry list is comprehensive.

**Acceptance Scenarios**:
1. **Given** a septic shock patient with AKI, lactic acidosis, thrombocytopenia, **When** comprehensive audit runs, **Then** all 6 domains produce results, KDIGO stage + qSOFA + MELD + QTc + A-a gradient + Wells integrated, trap list includes glucose-corrected Na⁺, albumin-corrected AG, ABW selection, age-adjusted D-dimer, wide-QRS adjustment
2. **Given** a liver transplant candidate on CRRT, **When** audit runs, **Then** MELD 3.0 with dialysis clamp, CKD-EPI (not applicable on CRRT) flagged, Cockcroft-Gault with ABW, drug dosing adjustments aggregated

---

### Edge Cases

- **Boundary lab values**: pH 6.50/7.80, Na 100/180, glucose >1000, albumin <1.0 - all must validate or reject per constitutional boundary guards
- **Extreme anthropometrics**: weight 20 kg (cachexia), 350 kg (super-obesity), height 100/250 cm - IBW/ABW logic must handle gracefully
- **Missing optional inputs**: pCO2 not provided for Winter's formula, measured osmolality absent, ethanol level unknown - engines must degrade gracefully with clear "not calculated" outputs
- **Contradictory clinical picture**: metabolic alkalosis with respiratory acidosis - delta ratio >2.0 flag must trigger
- **Pediatric patients**: Age <18 - CKD-EPI not validated, Cockcroft-Gault not validated, MELD uses PELD - system MUST reject via a Pydantic `ValidationError` at input validation time.
- **Pregnancy**: In `CKDEPIOutput` and `CockcroftGaultOutput`, always include a standard clinical note in `clinical_pearls_and_actions` stating that serum creatinine equations underestimate GFR in pregnancy due to physiological hyperfiltration.
- **Interfering substances**: Lipemia, hemolysis, paraproteinemia causing pseudohyponatremia - Hillier correction does not address; flag in pearls

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide 6 domain modules (`renal.py`, `acid_base.py`, `cardiology.py`, `hepatology.py`, `critical_care.py`, `hematology.py`) each exposing pure Python engine functions
- **FR-002**: System MUST provide a unified `poly_audit.py` module defining the `ComprehensivePatientInput` composite model containing optional sub-models mapped directly to domain `EngineInput` Pydantic classes:
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
- **FR-003**: Per Constitution Principles I–VI: CKD-EPI engine MUST implement 2021 race-free equation with exact coefficients (kappa 0.7/0.9, alpha -0.241/-0.302, mult 1.012/1.0) and output KDIGO stage G1-G5. Uses constant 142 (2021 race-free) not legacy 141.
- **FR-004**: Per Constitution Principles I–VI: Cockcroft-Gault engine MUST compute Devine IBW and Adjusted BW, and select the dosing weight explicitly: use `weight_kg` if `weight_kg < ibw_kg`; use `adjbw_kg` if `weight_kg >= 1.2 * ibw_kg` or `bmi >= 30.0`; otherwise use `ibw_kg`. It MUST flag CKD-EPI vs CG discordance for drug dosing. Output schema MUST expose exact fields in declaration order: `bmi: float`, `ibw_kg: float`, `adjbw_kg: float`, `selected_weight_kg: float`, `weight_selection_rule: Literal["actual", "ibw", "adjbw"]`, `crcl_ml_min: float`, plus `unit: UCUMUnit`.
- **FR-005**: Per Constitution Principles I–VI: AKI urinary indices MUST compute FENa and FEUrea, automatically suppress FENa interpretation when on_diuretics=true, and apply FEUrea thresholds (≤35% prerenal, >50% ATN).
- **FR-006**: Per Constitution Principles I–VI: Acid-base engine MUST apply Katz/Hillier glucose-corrected Na⁺ with exact formulas:
  - `glucose_delta = max(0.0, glucose_mg_dl - 100.0)`
  - `corrected_na_katz = round(na_meq_l + 0.016 * glucose_delta, 1)`
  - `corrected_na_hillier = round(na_meq_l + 0.024 * glucose_delta, 1)`
  Rule: Always return both `corrected_na_katz` and `corrected_na_hillier` in `AcidBaseOutput`, and set `active_na_correction_method = "hillier"` when `glucose_mg_dl > 400.0`, else `"katz"`. When `glucose_mg_dl <= 100.0`, `glucose_delta = 0.0`, both corrected values equal `na_meq_l`, and `active_na_correction_method = "katz"`. Input `AcidBaseInput` MAY include `prior_known_disorder: Optional[AcidBaseDisorder] = None`; if provided, engine SHOULD respect prior diagnosis when computing `disorders`.
  Figge albumin-corrected AG: `albumin_corrected_anion_gap = raw_anion_gap + 2.5 * (4.0 - albumin_g_dl)`.
  Delta ratio with 4-tier interpretation. Winter's formula: `winters_expected_paco2_min = 1.5 * hco3 + 6`, `winters_expected_paco2_max = 1.5 * hco3 + 10` (±2 mmHg tolerance around 1.5×HCO₃ + 8).
  Output schema MUST expose exact fields: `raw_anion_gap: float`, `albumin_corrected_anion_gap: float`, `delta_ratio: Optional[float]`, `winters_expected_paco2_min: Optional[float]`, `winters_expected_paco2_max: Optional[float]`, `disorders: list[AcidBaseDisorder]`.
- **FR-007**: Per Constitution Principles I–VI: Osmolality engine MUST calculate osmolality (2×Na + Glucose/18 + BUN/2.8 + Ethanol/3.7), osmolar gap with >10 toxic alcohol flag, and free water deficit with sex/age-specific TBW factors.
- **FR-008**: Per Constitution Principles I–VI: Payne corrected calcium MUST compute: total Ca + 0.8×(4.0 - albumin). Input: `CalciumInput`; Output: `CalciumOutput`.
- **FR-009**: Per Constitution Principles I–VI: QTc engine MUST compute Bazett, Fridericia, Framingham, auto-select Fridericia/Framingham when HR<60 or HR>100, apply the published Bogossian formula (Bogossian et al., Heart Rhythm 2014; PMID: 25149024) when QRS≥120ms: `bogossian_modified_qt_ms = qt_ms - (0.485 * qrs_ms)`, using `bogossian_modified_qt_ms` as the QT numerator in all three rate-correction equations, and flag Torsades threshold ≥500ms. Output schema MUST expose exact fields: `qrs_widened: bool`, `bogossian_modified_qt_ms: Optional[float]`, `qtc_bazett_ms: float`, `qtc_fridericia_ms: float`, `qtc_framingham_ms: float`, `recommended_primary_metric: str` (which formula was auto-selected), `recommended_qtc_ms: float`. Uses 0.485 factor (Bogossian 2014) not 0.5.
- **FR-010**: Per Constitution Principles I–VI: Hemodynamic engine MUST compute MAP, pulse pressure, shock index (HR/SBP, occult >0.9), modified shock index (HR/MAP, high risk >1.3).
- **FR-011**: Per Constitution Principles I–VI: MELD-Na and MELD 3.0 engines MUST enforce UNOS clamping (floors at 1.0, Na 125-137, albumin 1.5-3.5), compute both scores, output 90-day mortality brackets, and list all clamps triggered. Per UNOS OPTN Policy (effective 2024-01-01): MELD-Na caps Creatinine at `4.0 mg/dL`; MELD 3.0 caps Creatinine at `3.0 mg/dL`. Mortality brackets: `>=40: "71.3%"`, `30-39: "52.6%"`, `20-29: "19.6%"`, `10-19: "6.0%"`, `<10: "1.9%"`.
- **FR-012**: Per Constitution Principles I–VI: FIB-4 engine MUST compute (Age × AST) / (Platelets × √ALT) with fibrosis risk staging.
- **FR-013**: Per Constitution Principles I–VI: Oxygenation engine MUST compute PAO2 (alveolar gas equation), A-a gradient with age-expected, P/F ratio with Berlin ARDS staging (Mild 201-300, Moderate 101-200, Severe ≤100).
- **FR-014**: Per Constitution Principles I–VI: qSOFA/SIRS engine MUST compute `qsofa_score` (0–3) always from required fields (`rr_bpm`, `sbp_mmhg`, `gcs_score`). `sirs_score` (`Optional[int]`) is computed only when `>= 2` of the 4 SIRS parameters (`temp_celsius`, `hr_bpm`, `rr_bpm`/`paco2_mmhg`, `wbc_10e9_l`) are non-null; when `sirs_score is None`, omit SIRS from risk staging and rely strictly on `qsofa_score` and `lactate_mmol_l`. Input model `QSOFASIRSInput` MUST include `temp_celsius: Optional[float] = Field(None, ge=20.0, le=45.0)`, `hr_bpm: Optional[float] = None`, `wbc_10e9_l: Optional[float] = None`, `paco2_mmhg: Optional[float] = None` alongside `rr_bpm`, `sbp_mmhg`, `gcs_score`.
- **FR-015**: Per Constitution Principles I–VI: PEDDimer (Wells PE/DVT) engine MUST compute age-adjusted D-dimer threshold (age×10 ng/mL FEU for age>50), integrate Wells score, and output CTPA indication decision. Input: `PEDDimerInput`; Output: `PEDDimerOutput`.
- **FR-016**: Per Constitution Principles I–VI: Comprehensive audit (`run_comprehensive_patient_audit`) MUST execute all applicable engines per the deterministic rule (an engine executes if and only if its corresponding sub-model is non-null). Execution order = exact field declaration order in `ComprehensivePatientInput` (`ckd_epi` -> `pe_ddimer`). Each engine runs inside a `try/except Exception` block; if an unexpected runtime error occurs, record `{engine_name: str(err)}` in `failed_engines`, append to `trap_descriptions`, and continue executing remaining engines. Aggregate results into unified `ComprehensiveAuditReport` with:
  - `executed_engines: list[str]`
  - `skipped_engines: list[str]` (sub-models that were null)
  - `failed_engines: dict[str, str]`
  - `triggered_trap_categories: list[LLMTrapCategory]` (deduplicated, preserving first-occurrence order)
  - `trap_descriptions: str` (all unique human-readable trap strings joined with `"; "`)
  - flat optional domain result fields: `ckd_epi: Optional[CKDEPIOutput]`, `cockcroft_gault: Optional[CockcroftGaultOutput]`, `aki_urinary: Optional[AKIIndicesOutput]`, `acid_base: Optional[AcidBaseOutput]`, `osmolality: Optional[OsmolalityOutput]`, `calcium: Optional[CalciumOutput]`, `qtc: Optional[QTcOutput]`, `hemodynamics: Optional[HemodynamicsOutput]`, `meld: Optional[MELDOutput]`, `fib4: Optional[FIB4Output]`, `oxygenation: Optional[OxygenationOutput]`, `qsofa_sirs: Optional[QSOFASIRSOutput]`, `pe_ddimer: Optional[PEDDimerOutput]` (None when the engine did not execute)
  - `cross_domain_flags: list[str]`
  - `unified_risk_summary: str`

### Architectural & Quality Invariants

*Governed strictly by `.specify/memory/constitution.md` Principles I–VI.*
- **Zero Token Arithmetic** (Principle I): All mathematical computations execute in pure Python with zero LLM token arithmetic.
- **Hexagonal Architecture** (Principle II): Core domain engines in `src/clinical_mcp/engines/` are 100% pure Python functions on strict Pydantic v2 models with zero MCP/transport dependencies.
- **Fail-Fast Physiological Boundary Guards** (Principle III): Every input schema enforces strict Pydantic v2 `Field` constraints for human-compatible biological limits; invalid inputs raise validation errors immediately.
- **Coupled Physiological Propagation** (Principle IV): Calculators account for physiological confounders automatically as mandatory pre-computation steps; each engine documents its propagation chain in its docstring.
- **Explainable Clinical Output & Trap Telemetry** (Principle V): Every tool response returns a structured Pydantic model with (a) flat numeric result fields plus a top-level `unit: UCUMUnit`, (b) guideline staging/risk strata, (c) `clinical_pearls_and_actions`, (d) `llm_trap_prevented`.
- **Test-Driven Clinical Verification** (Principle VI): Every equation and boundary clamp has deterministic `pytest` unit tests with ≥95% coverage for engine modules, using gold-standard reference values and edge-case trap fixtures.

### Key Entities

- **EngineInput**: Domain-specific Pydantic input model with strict Field constraints for each calculator (e.g., `CKDEPIInput`, `CockcroftGaultInput`, `AcidBaseInput`)
- **EngineOutput**: Domain-specific Pydantic output model containing numerical results with units, staging/stratification, clinical pearls, and trap telemetry
- **ComprehensiveAuditReport**: Aggregated output from `run_comprehensive_patient_audit` containing `executed_engines`, `skipped_engines`, `failed_engines`, `triggered_trap_categories`, `trap_descriptions`, flat optional domain result fields (`ckd_epi` … `pe_ddimer`), `cross_domain_flags`, and `unified_risk_summary`
- **ClampAuditTrail**: Record of every UNOS/physiological boundary clamp applied (parameter, original value, clamped value, rule triggered)
- **ComprehensivePatientInput**: Composite input model for `run_comprehensive_patient_audit` containing optional sub-models mapped directly to domain `EngineInput` Pydantic classes:
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
  An engine executes iff its sub-model is non-null.
- **LLMTrapCategory**: StrEnum with 6 distinct categories for structured trap telemetry:
  1. `HYPOALBUMINEMIA_MASKED_HAGMA`
  2. `OBESITY_COCKCROFT_GAULT_OVERDOSE`
  3. `DIURETIC_FENA_MISINTERPRETATION`
  4. `TACHYCARDIA_OR_WIDE_QRS_QTC_ARTIFACT`
  5. `UNOS_MELD_LOGARITHMIC_BOUNDARY_VIOLATION`
  6. `AGE_UNADJUSTED_DDIMER_FALSE_POSITIVE`
- **AcidBaseDisorder**: StrEnum for acid-base diagnosis classification:
  - `NORMAL`
  - `PURE_HAGMA`
  - `PURE_NAGMA`
  - `MIXED_HAGMA_NAGMA`
  - `HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS`
  - `UNCOMPENSATED_RESPIRATORY_ACIDOSIS`
  - `SUPERIMPOSED_RESPIRATORY_ALKALOSIS`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 13 individual calculators produce results matching published reference values within 0.1% tolerance for textbook cases (e.g., CKD-EPI at SCr 1.0, age 40, male = 97.5 mL/min/1.73m²)
- **SC-002**: Engine modules achieve ≥95% pytest coverage with deterministic tests running in <5 seconds total
- **SC-003**: Comprehensive audit completes execution for a full patient panel in <500ms wall-clock time for 100 consecutive invocations of `run_comprehensive_patient_audit` (all 13 sub-models populated) on any modern 2+ vCPU / 4GB+ RAM Linux/WSL2 runner (or < 5ms average per full audit call)
- **SC-004**: Zero tolerance for physiological boundary violations - any input outside human-compatible limits (pH<6.5, Na<100, etc.) raises validation error before computation
- **SC-005**: Coupled propagation verified: glucose correction applied before osmolality, albumin correction before AG/delta ratio, IBW/ABW selection before Cockcroft-Gault - zero missed propagations in test fixtures
- **SC-006**: Every tool response includes all 4 required output components (results+units, staging, pearls, trap telemetry) - 100% compliance in automated contract tests
- **SC-007**: LLM trap telemetry captures at least 5 distinct `LLMTrapCategory` values across domains (HYPOALBUMINEMIA_MASKED_HAGMA, OBESITY_COCKCROFT_GAULT_OVERDOSE, DIURETIC_FENA_MISINTERPRETATION, TACHYCARDIA_OR_WIDE_QRS_QTC_ARTIFACT, UNOS_MELD_LOGARITHMIC_BOUNDARY_VIOLATION, AGE_UNADJUSTED_DDIMER_FALSE_POSITIVE) - verified via automated test asserting ≥5 distinct categories triggered in the benchmark suite (the 5 canonical clinical trap fixtures in `src/clinical_mcp/cli_demo.py` `DEMO_TRAP_CASES`, verified by `tests/test_poly_audit.py::test_trap_category_coverage`)
- **SC-008**: Cross-domain discordance flags fire correctly: CKD-EPI vs Cockcroft-Gault discrepancy >30% for drug dosing, MELD-Na with concurrent AKI, QTc with electrolyte abnormalities

## Assumptions

- Target users: Clinicians (physicians, pharmacists, NPs/PAs), clinical informaticists, medical AI researchers, and MCP client developers
- Domain scope: Adult patients only (≥18 years). See Edge Cases section for pediatric rejection and pregnancy hyperfiltration rules.
- Transport layer: MCP server implementation (stdio, HTTP, WebSocket) is separate from engine library; engines are transport-agnostic per hexagonal architecture
- Regulatory: This is a clinical decision support tool, not a regulated medical device. Outputs include "clinical decision support" disclaimer in pearls
- Units: All inputs/outputs use standard clinical units (mg/dL, mmol/L, mEq/L, mmHg, bpm, kg, cm) with UCUM codes in structured output
- Reference standards: KDIGO 2024 for CKD/AKI, UNOS OPTN policy for MELD, ACC/AHA for QTc, Berlin Definition for ARDS, Surviving Sepsis Campaign for qSOFA/SIRS, Wells criteria for PE
- External dependencies: Python 3.11+, Pydantic v2, pytest. No runtime ML/LLM dependencies in engine layer

---