---

description: "Task list for clinical-mcp implementation"
---

# Tasks: clinical-mcp

**Input**: Design documents from `/specs/001-clinical-mcp-server/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED per Constitution Principle VI (Test-Driven Clinical Verification) - every equation and boundary clamp must have deterministic pytest unit tests with ≥95% coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per implementation plan (src/clinical_mcp/{schemas,engines}, tests/, contracts/)
- [ ] T002 Initialize uv project with pyproject.toml (Python 3.11+, dependencies: mcp[cli]>=1.2.0, pydantic>=2.9.0, rich>=13.9.0; dev: pytest>=8.3.0, ruff>=0.7.0, mypy>=1.13.0)
- [ ] T003 [P] Configure ruff.toml for linting/formatting (target-version=py311, line-length=100)
- [ ] T004 [P] Configure mypy.ini for strict type checking (strict=true, warn_return_any=true)
- [ ] T005 [P] Create pytest.ini with coverage config (--cov=src/clinical_mcp/engines --cov-fail-under=95)
- [ ] T006 [P] Create .gitignore for Python/uv projects
- [ ] T007 [P] Create README.md stub with project description

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Create shared base models in src/clinical_mcp/schemas/__init__.py (EngineInput base, EngineOutput base with top-level `unit: UCUMUnit`, ConfigDict with extra="forbid", strict=True; `UCUMUnit` StrEnum with allowed units "mL/min/1.73m2", "mL/min", "%", "mEq/L", "mg/dL", "mOsm/kg", "L", "ms", "mmHg", "L/min/m2", "score", "ng/mL FEU")
- [ ] T009 Create shared validators in src/clinical_mcp/schemas/validators.py (custom @field_validator for pH, Na, glucose, albumin, etc. with clinical error messages like "pH 6.4 is incompatible with life (valid range: 6.50–7.80)")
- [ ] T010 Create conftest.py in tests/ with shared fixtures (gold-standard reference values, boundary limit fixtures, trap case fixtures for hyperglycemia >400, hypoalbuminemia <1.5, obesity ABW switching)
- [ ] T011 Create base engine interface in src/clinical_mcp/engines/__init__.py (type hints for all calculate_* functions returning EngineOutput)
- [ ] T012 [P] Create LLMTrapCategory StrEnum in src/clinical_mcp/schemas/common.py (6 categories: HYPOALBUMINEMIA_MASKED_HAGMA, OBESITY_COCKCROFT_GAULT_OVERDOSE, DIURETIC_FENA_MISINTERPRETATION, TACHYCARDIA_OR_WIDE_QRS_QTC_ARTIFACT, UNOS_MELD_LOGARITHMIC_BOUNDARY_VIOLATION, AGE_UNADJUSTED_DDIMER_FALSE_POSITIVE)
- [ ] T013 [P] Create AcidBaseDisorder StrEnum in src/clinical_mcp/schemas/common.py (7 categories: NORMAL, PURE_HAGMA, PURE_NAGMA, MIXED_HAGMA_NAGMA, HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS, UNCOMPENSATED_RESPIRATORY_ACIDOSIS, SUPERIMPOSED_RESPIRATORY_ALKALOSIS)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Renal & Pharmacokinetic Clearance Calculations (Priority: P1) 🎯 MVP

**Goal**: Implement CKD-EPI eGFR, Cockcroft-Gault CrCl with IBW/ABW selection, and AKI urinary indices (FENa/FEUrea) with diuretic-aware interpretation

**Independent Test**: Provide lab values (SCr, age, sex, weight, height, urinary electrolytes) and verify outputs match published reference values for each formula. Each calculator produces deterministic results with KDIGO staging and dosing guidance.

### Tests for User Story 1 (REQUIRED - Constitution Principle VI)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US1] Contract tests for renal input/output schemas in tests/test_renal.py::TestCKDEPISchemas (validate Field constraints: scr_mg_dl ge=0.1 le=30.0, age_years ge=18 le=120, sex enum)
- [ ] T015 [P] [US1] Contract tests for CockcroftGault schemas in tests/test_renal.py::TestCockcroftGaultSchemas (validate weight_kg ge=20 le=350, height_cm ge=100 le=250)
- [ ] T016 [P] [US1] Contract tests for AKIIndices schemas in tests/test_renal.py::TestAKIIndicesSchemas (validate on_diuretics bool, optional serum_bun/urine_urea)
- [ ] T017 [P] [US1] Gold-standard unit tests for CKD-EPI in tests/test_renal.py::TestCKD_EPI (textbook case: SCr 1.0, age 40, male = 97.5 mL/min/1.73m²; boundary: SCr 0.1, 30.0; race-free coefficients kappa 0.7/0.9, alpha -0.241/-0.302, mult 1.012/1.0)
- [ ] T018 [P] [US1] Gold-standard unit tests for Cockcroft-Gault in tests/test_renal.py::TestCockcroftGault (Devine IBW: male 50+0.9*(height-152.4), female 45.5+0.9*(height-152.4); AdjBW = IBW + 0.4*(actual-IBW); weight selection rule: actual<IBW→actual, actual>=1.2*IBW or BMI>=30→AdjBW, otherwise IBW; CKD-EPI vs CG discordance flag >30%)
- [ ] T019 [P] [US1] Gold-standard unit tests for AKI Indices in tests/test_renal.py::TestAKIIndices (FENa = (U_Na*S_Cr)/(S_Na*U_Cr)*100; FEUrea = (U_Urea*S_Cr)/(S_BUN*U_Cr)*100; on_diuretics=true suppresses FENa, FEUrea ≤35% prerenal >50% ATN)
- [ ] T020 [P] [US1] Boundary guard tests in tests/test_boundary_guards.py::TestRenalBoundaries (reject SCr<0.1, SCr>30, age<18, age>120, weight<20, weight>350 with clinical error messages)
- [ ] T021 [P] [US1] Trap case tests in tests/test_renal.py::TestRenalTraps (obesity ABW switching at 1.2×IBW, BMI≥30; diuretic-confounded FENa)
- [ ] T022 [P] [US1] **Pediatric rejection test** in tests/test_boundary_guards.py::TestPediatricRejection (assert age_years < 18 raises Pydantic ValidationError explaining pediatric formulas out of scope for v1)

### Implementation for User Story 1

- [ ] T023 [P] [US1] Create renal input schemas in src/clinical_mcp/schemas/renal.py (CKDEPIInput, CockcroftGaultInput, AKIIndicesInput with all Field constraints and custom validators)
- [ ] T024 [P] [US1] Create renal output schemas in src/clinical_mcp/schemas/renal.py (CKDEPIOutput with `egfr_ml_min_per_173m2: float`, `kdigo_stage: Literal["G1","G2","G3a","G3b","G4","G5"]`; CockcroftGaultOutput with exact fields in declaration order: `bmi: float`, `ibw_kg: float`, `adjbw_kg: float`, `selected_weight_kg: float`, `weight_selection_rule: Literal["actual","ibw","adjbw"]`, `crcl_ml_min: float`; AKIIndicesOutput with `fena_percent: float`, `feurea_percent: float`, `aki_etiology: Literal["prerenal","atn","indeterminate","diuretic_confounded"]`; all with top-level `unit: UCUMUnit`, `clinical_pearls_and_actions: list[str]`, `llm_trap_prevented: list[str]`)
- [ ] T025 [US1] Implement CKD-EPI engine in src/clinical_mcp/engines/renal.py::calculate_ckd_epi (pure Python, 2021 race-free equation, KDIGO G1-G5 staging, docstring documenting propagation chain)
- [ ] T026 [US1] Implement Cockcroft-Gault engine in src/clinical_mcp/engines/renal.py::calculate_cockcroft_gault (pure Python, Devine IBW, AdjBW, weight selection rule: actual<IBW→actual, actual>=1.2*IBW or BMI>=30→AdjBW, otherwise IBW; CKD-EPI vs CG discordance flag, docstring). MUST return exact fields in declaration order: bmi, ibw_kg, adjbw_kg, selected_weight_kg, weight_selection_rule, crcl_ml_min.
- [ ] T027 [US1] Implement AKI Indices engine in src/clinical_mcp/engines/renal.py::calculate_aki_indices (pure Python, FENa/FEUrea, diuretic-aware interpretation, docstring)
- [ ] T028 [US1] Create renal engine __init__.py exports in src/clinical_mcp/engines/renal.py (public API: calculate_ckd_epi, calculate_cockcroft_gault, calculate_aki_indices)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Run `uv run pytest tests/test_renal.py -v` to verify.

---

## Phase 4: User Story 2 - Acid-Base, Electrolyte & Osmolality Analysis (Priority: P1)

**Goal**: Implement coupled acid-base engine (Hillier Na⁺ correction, Figge AG correction, delta ratio, Winter's formula), osmolality/osmolar gap/free water deficit, and Payne corrected calcium

**Independent Test**: Provide comprehensive metabolic panel plus blood gas values and verify each coupled output matches gold-standard reference calculations (Figge AG, Hillier Na⁺, Winter's formula, osmolar gap >10 flagging).

### Tests for User Story 2 (REQUIRED - Constitution Principle VI)

- [ ] T029 [P] [US2] Contract tests for acid-base schemas in tests/test_acid_base.py::TestAcidBaseSchemas (validate na/cl/hco3 bounds, albumin default 4.0, glucose default 100.0, optional paco2/ph/lactate)
- [ ] T030 [P] [US2] Contract tests for osmolality schemas in tests/test_acid_base.py::TestOsmolalitySchemas (validate na/glucose/bun required, optional measured_osmolality/ethanol/weight/sex/age)
- [ ] T031 [P] [US2] Contract tests for corrected calcium schemas in tests/test_acid_base.py::TestCalciumSchemas
- [ ] T032 [P] [US2] Gold-standard unit tests for coupled acid-base in tests/test_acid_base.py::TestCoupledAcidBase (Katz: corrected_na_katz = round(na + 0.016 * max(0, glucose-100), 1); Hillier: corrected_na_hillier = round(na + 0.024 * max(0, glucose-100), 1); active method = "hillier" if glucose>400 else "katz"; Figge: albumin_corrected_anion_gap = raw_anion_gap + 2.5*(4.0-albumin); delta_ratio = (albumin_corrected_anion_gap - 12) / (24 - hco3) when AG>12 and HCO3<24; Winter's: expected_min = 1.5*hco3 + 6, expected_max = 1.5*hco3 + 10)
- [ ] T033 [P] [US2] Gold-standard unit tests for osmolality in tests/test_acid_base.py::TestOsmolality (2*Na + Glucose/18 + BUN/2.8 + Ethanol/3.7; osmolar gap >10 toxic alcohol flag; free water deficit TBW factors: 0.6 male, 0.5 female/elderly male, 0.45 elderly female)
- [ ] T034 [P] [US2] Gold-standard unit tests for corrected calcium in tests/test_acid_base.py::TestCalcium (Payne: total_Ca + 0.8*(4.0-albumin))
- [ ] T035 [P] [US2] Boundary guard tests in tests/test_boundary_guards.py::TestAcidBaseBoundaries (reject pH<6.5, pH>7.8, Na<100, Na>180, albumin<0, glucose<0 with clinical messages)
- [ ] T036 [P] [US2] Trap case tests in tests/test_acid_base.py::TestAcidBaseTraps (hyperglycemia >400 uses Hillier 0.024 factor; hypoalbuminemia <1.5 Figge correction; delta_ratio > 2.0 triggers HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS)

### Implementation for User Story 2

- [ ] T037 [P] [US2] Create acid-base input schemas in src/clinical_mcp/schemas/acid_base.py (`AcidBaseInput` including `prior_known_disorder: Optional[AcidBaseDisorder] = None`, `AcidBaseOutput`, `OsmolalityInput`, `OsmolalityOutput`, `CalciumInput`, and `CalciumOutput` with Field constraints and validators)
- [ ] T038 [P] [US2] Create acid-base output schemas in src/clinical_mcp/schemas/acid_base.py (AcidBaseOutput with exact fields: `raw_anion_gap: float`, `albumin_corrected_anion_gap: float`, `delta_ratio: Optional[float]`, `winters_expected_paco2_min: Optional[float]`, `winters_expected_paco2_max: Optional[float]`, `disorders: list[AcidBaseDisorder]`, `corrected_na_katz: float`, `corrected_na_hillier: float`, `active_na_correction_method: Literal["katz","hillier"]`; OsmolalityOutput with `calculated_osmolality_mosm_kg: float`, `osmolar_gap_mosm_kg: float`, `free_water_deficit_l: float`, `toxic_alcohol_flag: bool`; CalciumOutput with `corrected_ca_mg_dl: float`; all with top-level `unit: UCUMUnit`, `clinical_pearls_and_actions: list[str]`, `llm_trap_prevented: list[str]`)
- [ ] T039 [US2] Implement coupled acid-base engine in src/clinical_mcp/engines/acid_base.py::calculate_acid_base (pure Python, mandatory propagation: Katz/Hillier Na⁺ correction → Figge AG → delta ratio → Winter's expected PaCO2 range; docstring with "Propagation:" prefix). MUST return exact fields with both Katz and Hillier corrected Na⁺, active method selection, Figge AG, delta ratio, Winter's min/max, AcidBaseDisorder list.
- [ ] T040 [US2] Implement osmolality engine in src/clinical_mcp/engines/acid_base.py::calculate_osmolality (pure Python, calculated osmolality, osmolar gap, free water deficit with TBW factors, docstring)
- [ ] T041 [US2] Implement corrected calcium engine in src/clinical_mcp/engines/acid_base.py::calculate_corrected_calcium (pure Python, Payne formula, docstring)
- [ ] T042 [US2] Create acid-base engine __init__.py exports in src/clinical_mcp/engines/acid_base.py (public API: calculate_acid_base, calculate_osmolality, calculate_corrected_calcium)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Run `uv run pytest tests/test_acid_base.py -v` to verify.

---

## Phase 5: User Story 3 - Cardiac Repolarization & Hemodynamic Assessment (Priority: P1)

**Goal**: Implement multi-formula QTc correction (Bazett, Fridericia, Framingham) with auto-selection and Bogossian wide-QRS adjustment, plus hemodynamic indices (MAP, shock index, modified shock index)

**Independent Test**: Provide QT, HR, sex, QRS duration and verify all three formulas compute, auto-selection logic triggers correctly, Torsades threshold (500ms) flagged, and wide-QRS adjustment warning appears when QRS >120ms.

### Tests for User Story 3 (REQUIRED - Constitution Principle VI)

- [ ] T043 [P] [US3] Contract tests for QTc schemas in tests/test_cardiology.py::TestQTcSchemas (validate qt_ms 150-800, hr_bpm 20-300, sex enum, qrs_ms 40-200 default 90)
- [ ] T044 [P] [US3] Contract tests for hemodynamics schemas in tests/test_cardiology.py::TestHemodynamicsSchemas (validate sbp 30-300, dbp 20-200, hr 20-300)
- [ ] T045 [P] [US3] Gold-standard unit tests for QTc in tests/test_cardiology.py::TestQTc (Bazett: QT/sqrt(RR); Fridericia: QT/RR^(1/3); Framingham: QT+154*(1-RR); auto-select Fridericia/Framingham when HR<60 or HR>100; published Bogossian formula (Bogossian et al., Heart Rhythm 2014; PMID: 25149024): bogossian_modified_qt_ms = qt_ms - (0.485 * qrs_ms) when QRS≥120ms; Torsades ≥500ms; verify exact output fields)
- [ ] T046 [P] [US3] Gold-standard unit tests for hemodynamics in tests/test_cardiology.py::TestHemodynamics (MAP=(SBP+2*DBP)/3; Pulse Pressure=SBP-DBP; Shock Index=HR/SBP occult>0.9; Modified Shock Index=HR/MAP high risk>1.3)
- [ ] T047 [P] [US3] Boundary guard tests in tests/test_boundary_guards.py::TestCardiologyBoundaries (reject QT<150, QT>800, HR<20, HR>300, QRS<40, QRS>200)
- [ ] T048 [P] [US3] Trap case tests in tests/test_cardiology.py::TestCardiologyTraps (tachycardia Bazett over-correction at HR>100; bradycardia Bazett under-correction at HR<60; wide-QRS false positive QTc prolongation)

### Implementation for User Story 3

- [ ] T049 [P] [US3] Create cardiology input schemas in src/clinical_mcp/schemas/cardiology.py (QTcInput, HemodynamicsInput with Field constraints and validators)
- [ ] T050 [P] [US3] Create cardiology output schemas in src/clinical_mcp/schemas/cardiology.py (QTcOutput, HemodynamicsOutput with 4-component structure plus top-level `unit: UCUMUnit`). QTcOutput MUST expose `qrs_widened: bool` and `bogossian_modified_qt_ms: Optional[float]` before `qtc_bazett_ms`, `qtc_fridericia_ms`, and `qtc_framingham_ms`.
- [ ] T051 [US3] Implement QTc engine in src/clinical_mcp/engines/cardiology.py::calculate_qtc (pure Python, 3 formulas, auto-selection, published Bogossian formula (Bogossian et al., Heart Rhythm 2014; PMID: 25149024) when QRS≥120ms: `bogossian_modified_qt_ms = qt_ms - (0.485 * qrs_ms)`, use modified QT as numerator in all three rate-correction equations, Torsades flag, docstring). MUST return qrs_widened and bogossian_modified_qt_ms.
- [ ] T052 [US3] Implement hemodynamics engine in src/clinical_mcp/engines/cardiology.py::calculate_hemodynamics (pure Python, MAP, pulse pressure, shock indices, classification, docstring)
- [ ] T053 [US3] Create cardiology engine __init__.py exports in src/clinical_mcp/engines/cardiology.py (public API: calculate_qtc, calculate_hemodynamics)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently. Run `uv run pytest tests/test_cardiology.py -v` to verify.

---

## Phase 6: User Story 4 - Hepatic Disease Severity & Fibrosis Staging (Priority: P2)

**Goal**: Implement MELD-Na and MELD 3.0 with strict UNOS clamping (floors at 1.0, Cr caps at 4.0/3.0, Na 125-137, albumin 1.5-3.5), plus FIB-4 index

**Independent Test**: Provide lab values at boundary conditions and verify both MELD-Na and MELD 3.0 match UNOS calculator outputs with clamp audit trail.

### Tests for User Story 4 (REQUIRED - Constitution Principle VI)

- [ ] T054 [P] [US4] Contract tests for MELD schemas in tests/test_hepatology.py::TestMELDSchemas (validate bilirubin/INR/Cr/Na/albumin bounds, sex enum, dialysis bool)
- [ ] T055 [P] [US4] Contract tests for FIB-4 schemas in tests/test_hepatology.py::TestFIB4Schemas (validate age, AST, ALT, platelets bounds)
- [ ] T056 [P] [US4] Gold-standard unit tests for MELD-Na in tests/test_hepatology.py::TestMELD_Na (UNOS clamping: floor bilirubin/INR/Cr at 1.0; cap Cr at 4.0; Na clamp 125-137; albumin clamp 1.5-3.5; assert exact UNOS OPTN 90-day mortality bracket lookup (effective 2024-01-01): `>=40: "71.3%"`, `30-39: "52.6%"`, `20-29: "19.6%"`, `10-19: "6.0%"`, `<10: "1.9%"`)
- [ ] T057 [P] [US4] Gold-standard unit tests for MELD 3.0 in tests/test_hepatology.py::TestMELD_3_0 (MELD 3.0 specific: Cr cap at 3.0, sex coefficient, albumin coefficient, dialysis adjustment; assert exact UNOS OPTN 90-day mortality bracket lookup (effective 2024-01-01): `>=40: "71.3%"`, `30-39: "52.6%"`, `20-29: "19.6%"`, `10-19: "6.0%"`, `<10: "1.9%"`)
- [ ] T058 [P] [US4] Gold-standard unit tests for FIB-4 in tests/test_hepatology.py::TestFIB4 ((Age*AST)/(Platelets*sqrt(ALT)); fibrosis risk: <1.45 low, 1.45-3.25 indeterminate, >3.25 high)
- [ ] T059 [P] [US4] Boundary guard tests in tests/test_boundary_guards.py::TestHepatologyBoundaries (reject bilirubin<0, INR<0.5, Cr<0.1, Na<100, albumin<0)
- [ ] T060 [P] [US4] Trap case tests in tests/test_hepatology.py::TestHepatologyTraps (UNOS clamp omissions: naive LLM misses floor at 1.0, Na clamp 125-137, MELD 3.0 Cr cap 3.0 vs 4.0)

### Implementation for User Story 4

- [ ] T061 [P] [US4] Create hepatology input schemas in src/clinical_mcp/schemas/hepatology.py (MELDInput, FIB4Input with Field constraints and validators)
- [ ] T062 [P] [US4] Create hepatology output schemas in src/clinical_mcp/schemas/hepatology.py (MELDOutput, FIB4Output with 4-component structure plus top-level `unit: UCUMUnit`, including clamps_applied)
- [ ] T063 [US4] Implement MELD engine in src/clinical_mcp/engines/hepatology.py::calculate_meld (pure Python, MELD-Na + MELD 3.0, UNOS clamping with audit trail, 90-day mortality brackets, docstring)
- [ ] T064 [US4] Implement FIB-4 engine in src/clinical_mcp/engines/hepatology.py::calculate_fib4 (pure Python, fibrosis risk staging, docstring)
- [ ] T065 [US4] Create hepatology engine __init__.py exports in src/clinical_mcp/engines/hepatology.py (public API: calculate_meld, calculate_fib4)

**Checkpoint**: At this point, User Stories 1-4 should all work independently. Run `uv run pytest tests/test_hepatology.py -v` to verify.

---

## Phase 7: User Story 5 - Critical Care Oxygenation & Sepsis Triage (Priority: P1)

**Goal**: Implement oxygenation engine (alveolar gas equation, A-a gradient, P/F ratio with Berlin ARDS staging) and qSOFA/SIRS/sepsis screening

**Independent Test**: Provide ABG values and vital signs and verify PAO2 alveolar gas equation, A-a gradient with age-expected, P/F ratio with Berlin staging, qSOFA ≥2 and SIRS ≥2 criteria.

### Tests for User Story 5 (REQUIRED - Constitution Principle VI)

- [ ] T066 [P] [US5] Contract tests for oxygenation schemas in tests/test_critical_care.py::TestOxygenationSchemas (validate pao2 20-600, paco2 10-100, fio2 0.21-1.0, age 18-120, barometric pressure default 760, RQ default 0.8)
- [ ] T067 [P] [US5] Contract tests for qSOFA/SIRS schemas in tests/test_critical_care.py::TestQSOFASIRSSchemas (validate required rr 5-60, sbp 30-300, gcs 3-15 and optional temp_celsius 20-45, hr_bpm, wbc_10e9_l, paco2_mmhg, lactate_mmol_l)
- [ ] T068 [P] [US5] Gold-standard unit tests for oxygenation in tests/test_critical_care.py::TestOxygenation (PAO2 = fio2*(P_atm-47) - PaCO2/RQ; A-a = PAO2-PaO2; expected A-a = age/4+4; P/F = PaO2/fio2; Berlin: Mild 201-300, Moderate 101-200, Severe ≤100)
- [ ] T069 [P] [US5] Gold-standard unit tests for qSOFA/SIRS in tests/test_critical_care.py::TestQSOFASIRS (qSOFA: RR≥22, SBP≤100, GCS<15; SIRS: temp>38/<36, HR>90, RR>20, WBC>12/<4; lactate≥4 for sepsis screening)
- [ ] T070 [P] [US5] Boundary guard tests in tests/test_boundary_guards.py::TestCriticalCareBoundaries (reject fio2<0.21, fio2>1.0, pao2<20, pao2>600, gcs<3, gcs>15)
- [ ] T071 [P] [US5] Trap case tests in tests/test_critical_care.py::TestCriticalCareTraps (naive LLM misses alveolar gas equation water vapor pressure 47mmHg; RQ default 0.8; Berlin staging thresholds)

### Implementation for User Story 5

- [ ] T072 [P] [US5] Create critical care input schemas in src/clinical_mcp/schemas/critical_care.py (`OxygenationInput`; `QSOFASIRSInput` with required qSOFA fields `rr_bpm: float`, `sbp_mmhg: float`, `gcs_score: int` and optional SIRS/sepsis fields `temp_celsius: Optional[float] = Field(None, ge=20.0, le=45.0)`, `hr_bpm: Optional[float] = None`, `wbc_10e9_l: Optional[float] = None`, `paco2_mmhg: Optional[float] = None`, `lactate_mmol_l: Optional[float] = None`, all with Field constraints and validators)
- [ ] T073 [P] [US5] Create critical care output schemas in src/clinical_mcp/schemas/critical_care.py (OxygenationOutput, QSOFASIRSOutput with 4-component structure plus top-level `unit: UCUMUnit`)
- [ ] T074 [US5] Implement oxygenation engine in src/clinical_mcp/engines/critical_care.py::calculate_oxygenation (pure Python, alveolar gas equation, A-a gradient, P/F ratio, Berlin ARDS staging, docstring)
- [ ] T075 [US5] Implement qSOFA/SIRS engine in src/clinical_mcp/engines/critical_care.py::calculate_qsofa (pure Python, qSOFA score from `rr_bpm`/`sbp_mmhg`/`gcs_score`, all 4 SIRS criteria from `temp_celsius`/`hr_bpm`/`rr_bpm`/`paco2_mmhg`/`wbc_10e9_l`, `lactate_mmol_l` integration, sepsis screening, docstring). MUST return exact fields: qsofa_score, sirs_score (Optional[int] - None if <2 SIRS params provided), sepsis_screen.
- [ ] T076 [US5] Create critical care engine __init__.py exports in src/clinical_mcp/engines/critical_care.py (public API: calculate_oxygenation, calculate_qsofa)

**Checkpoint**: At this point, User Stories 1-5 should all work independently. Run `uv run pytest tests/test_critical_care.py -v` to verify.

---

## Phase 8: User Story 6 - Pulmonary Embolism Risk Stratification (Priority: P2)

**Goal**: Implement Wells PE/DVT score with age-adjusted D-dimer threshold (age×10 ng/mL FEU for age>50) and CTPA indication decision

**Independent Test**: Provide age, D-dimer, Wells score and verify age-adjusted threshold calculation, imaging recommendation, and Wells probability stratification.

### Tests for User Story 6 (REQUIRED - Constitution Principle VI)

- [ ] T077 [P] [US6] Contract tests for PEDDimer schemas in tests/test_hematology.py::TestPEDDimerSchemas (validate `PEDDimerInput`/`PEDDimerOutput`: age 18-120, d_dimer 0-50000, wells_score 0-12.5)
- [ ] T078 [P] [US6] Gold-standard unit tests for PEDDimer in tests/test_hematology.py::TestPEDDimer (age-adjusted threshold: age>50 → age*10 ng/mL FEU; standard 500 for ≤50; CTPA indication logic; Wells probability: low/moderate/high)
- [ ] T079 [P] [US6] Boundary guard tests in tests/test_boundary_guards.py::TestPEDDimerBoundaries (reject age<18, age>120, d_dimer<0, d_dimer>50000)
- [ ] T080 [P] [US6] Trap case tests in tests/test_hematology.py::TestPEDDimerTraps (age-adjusted D-dimer: naive LLM uses fixed 500 threshold for 65yo missing age*10=650; Wells score integration)

### Implementation for User Story 6

- [ ] T081 [P] [US6] Create hematology input schemas in src/clinical_mcp/schemas/hematology.py (PEDDimerInput with Field constraints and validators)
- [ ] T082 [P] [US6] Create hematology output schemas in src/clinical_mcp/schemas/hematology.py (PEDDimerOutput with 4-component structure plus top-level `unit: UCUMUnit`)
- [ ] T083 [US6] Implement PEDDimer engine in src/clinical_mcp/engines/hematology.py::calculate_peddimer (pure Python, age-adjusted threshold, CTPA decision, Wells probability, docstring)
- [ ] T084 [US6] Create hematology engine __init__.py exports in src/clinical_mcp/engines/hematology.py (public API: calculate_peddimer)

**Checkpoint**: At this point, User Stories 1-6 should all work independently. Run `uv run pytest tests/test_hematology.py -v` to verify.

---

## Phase 9: User Story 7 - Comprehensive Multi-System Patient Audit (Priority: P1)

**Goal**: Implement unified `run_comprehensive_patient_audit` that executes all 6 domain engines against a `ComprehensivePatientInput` composite model, aggregates results, generates cross-domain flags, compiles complete trap telemetry with `LLMTrapCategory` enums, and lists skipped engines per deterministic rule

**Independent Test**: Provide a complete patient panel and verify all 13 individual calculators execute, results aggregate into unified report, cross-domain flags surface, trap telemetry list is comprehensive with ≥5 distinct `LLMTrapCategory` values, and execution time < 500ms.

### Tests for User Story 7 (REQUIRED - Constitution Principle VI)

- [ ] T085 [P] [US7] Contract tests for poly-audit schemas in tests/test_poly_audit.py::TestPolyAuditSchemas (validate ComprehensivePatientInput all required/optional sub-models with constraints; ComprehensiveAuditReport structure with skipped_engines)
- [ ] T086 [P] [US7] Integration tests for comprehensive audit in tests/test_poly_audit.py::TestComprehensiveAudit (septic shock patient: all 6 domains produce results; cross-domain flags: CKD-EPI vs CG discordance, MELD with AKI, QTc with electrolytes; `triggered_trap_categories` ≥5 categories)
- [ ] T087 [P] [US7] Integration test for liver transplant candidate in tests/test_poly_audit.py::TestPolyAuditLiverTransplant (MELD 3.0 with dialysis clamp, CKD-EPI flagged not applicable on CRRT, CG with ABW)
- [ ] T088 [P] [US7] Cross-domain flag tests in tests/test_poly_audit.py::TestCrossDomainFlags (CKD-EPI vs CG >30% discrepancy; MELD with eGFR<30; QTc≥500 with low K/Mg; A-a gradient elevated with P/F≤300)
- [ ] T089 [P] [US7] **Performance benchmark test** in tests/test_poly_audit.py::TestPolyAuditPerformance (assert run_comprehensive_patient_audit with all 13 sub-models populated executes 100 consecutive invocations in < 500ms wall-clock time on 2+ vCPU / 4GB+ RAM Linux/WSL2 runner using time.perf_counter())
- [ ] T090 [P] [US7] **Trap category coverage test** in tests/test_poly_audit.py::TestTrapCategoryCoverage (assert at least 5 distinct LLMTrapCategory values triggered across benchmark suite (the 5 canonical clinical trap fixtures in src/clinical_mcp/cli_demo.py DEMO_TRAP_CASES), verified by tests/test_poly_audit.py::test_trap_category_coverage)
- [ ] T091 [P] [US7] **Propagation verification tests** in tests/test_poly_audit.py::TestPropagationVerification (assert intermediate coupled values present in outputs: renal selected_weight_kg/weight_selection_rule, acid-base raw_anion_gap/albumin_corrected_anion_gap/delta_ratio/winters_expected_paco2_min/max, cardiology qrs_widened/bogossian_modified_qt_ms)
- [ ] T092 [P] [US7] **Docstring propagation verification test** in tests/test_poly_audit.py::TestDocstringPropagation (assert every engine function __doc__ contains "Propagation:" documenting the coupled computation chain)
- [ ] T093 [P] [US7] **UCUM unit validation test** in tests/test_poly_audit.py::TestUCUMUnits (assert all output `unit` fields conform to standard clinical UCUM-style strings: "mL/min/1.73m2", "mL/min", "mEq/L", "ms", "mmHg", "%", "ng/mL FEU")
- [ ] T094 [P] [US7] **Graceful degradation test** in tests/test_poly_audit.py::TestGracefulDegradation (assert optional inputs paco2_mmhg=None in Acid-Base, measured_osmolality=None in Osmolality, serum_bun=None in AKI return None for dependent sub-calculations without raising exceptions)
- [ ] T095 [P] [US7] **Delta ratio > 2.0 test** in tests/test_acid_base.py::TestDeltaRatioFlag (assert delta_ratio > 2.0 triggers AcidBaseDisorder.HAGMA_PLUS_METABOLIC_ALKALOSIS_OR_CHRONIC_RESP_ACIDOSIS)
- [ ] T096 [P] [US7] **Pediatric age rejection test** in tests/test_boundary_guards.py::TestPediatricRejection (assert age_years < 18 raises Pydantic ValidationError explaining pediatric formulas out of scope for v1)
- [ ] T097 [P] [US7] **Literature errata regression test** in tests/test_poly_audit.py::TestLiteratureErrata (verify 2021 Race-Free CKD-EPI uses 142 constant (not legacy 2009 141 race-coefficient formula); verify Bogossian 2014 wide-QRS uses 0.485 factor (not 0.5))
- [ ] T098 [P] [US7] **Prior known disorder field test** in tests/test_acid_base.py::TestPriorKnownDisorder (add `prior_known_disorder: Optional[AcidBaseDisorder] = None` to AcidBaseInput; verify engine respects prior diagnosis when provided)

### Implementation for User Story 7

- [ ] T099 [P] [US7] Create poly-audit input schemas in src/clinical_mcp/schemas/poly_audit.py (ComprehensivePatientInput with all sub-models: ckd_epi, cockcroft_gault, aki_urinary, acid_base, osmolality, calcium, qtc, hemodynamics, meld, fib4, oxygenation, qsofa_sirs, pe_ddimer)
- [ ] T100 [P] [US7] Create poly-audit output schemas in src/clinical_mcp/schemas/poly_audit.py (`ComprehensiveAuditReport` with exact fields: `executed_engines: list[str]`, `skipped_engines: list[str]`, `failed_engines: dict[str, str]`, `triggered_trap_categories: list[LLMTrapCategory]` (deduplicated, preserving first-occurrence order), `trap_descriptions: str` (unique human-readable trap strings joined by `"; "` preserving declaration order), `cross_domain_flags: list[str]`, `unified_risk_summary: str`, and flat optional per-domain output fields `ckd_epi`, `cockcroft_gault`, `aki_urinary`, `acid_base`, `osmolality`, `calcium`, `qtc`, `hemodynamics`, `meld`, `fib4`, `oxygenation`, `qsofa_sirs`, `pe_ddimer`; `ClampAuditTrail` with `parameter`, `original_value`, `clamped_value`, `rule`)
- [ ] T101 [US7] Implement poly-audit engine in src/clinical_mcp/engines/poly_audit.py::run_comprehensive_patient_audit (pure Python, orchestrates all 6 domain engines per deterministic rule: execute iff sub-model non-null, aggregates flat domain result fields, computes cross_domain_flags per rules, unified_risk_summary, triggered_trap_categories with LLMTrapCategory enums, trap_descriptions, executed_engines, skipped_engines, failed_engines, docstring)
- [ ] T102 [US7] Create poly-audit engine __init__.py exports in src/clinical_mcp/engines/poly_audit.py (public API: run_comprehensive_patient_audit)

**Checkpoint**: At this point, ALL 7 User Stories should work independently AND together. Run `uv run pytest tests/test_poly_audit.py -v` to verify.

---

## Phase 10: MCP Server (Cross-Cutting - Required for All Stories)

**Goal**: Expose all 14 calculators as MCP tools via FastMCP server with rich docstrings for LLM agent discovery

**Independent Test**: Start server with `uv run clinical-mcp`, connect via MCP client, call each tool and verify correct delegation to engines

### Implementation for MCP Server

- [ ] T103 Create MCP server in src/clinical_mcp/server.py (FastMCP("Open Clinical AI Lab - Deterministic Physiology Server"), register all 14 tools with rich docstrings explaining parameter units and clinical indications)
- [ ] T104 Create __main__.py entry point in src/clinical_mcp/__main__.py (calls server.main() for `uv run clinical-mcp` and `python -m clinical_mcp`)
- [ ] T105 [P] Add tool for CKD-EPI in server.py (delegates to engines.renal.calculate_ckd_epi)
- [ ] T106 [P] Add tool for Cockcroft-Gault in server.py (delegates to engines.renal.calculate_cockcroft_gault)
- [ ] T107 [P] Add tool for AKI Indices in server.py (delegates to engines.renal.calculate_aki_indices)
- [ ] T108 [P] Add tool for Acid-Base in server.py (delegates to engines.acid_base.calculate_acid_base)
- [ ] T109 [P] Add tool for Osmolality in server.py (delegates to engines.acid_base.calculate_osmolality)
- [ ] T110 [P] Add tool for Calcium in server.py (delegates to engines.acid_base.calculate_corrected_calcium)
- [ ] T111 [P] Add tool for QTc in server.py (delegates to engines.cardiology.calculate_qtc)
- [ ] T112 [P] Add tool for Hemodynamics in server.py (delegates to engines.cardiology.calculate_hemodynamics)
- [ ] T113 [P] Add tool for MELD in server.py (delegates to engines.hepatology.calculate_meld)
- [ ] T114 [P] Add tool for FIB-4 in server.py (delegates to engines.hepatology.calculate_fib4)
- [ ] T115 [P] Add tool for Oxygenation in server.py (delegates to engines.critical_care.calculate_oxygenation)
- [ ] T116 [P] Add tool for qSOFA/SIRS in server.py (delegates to engines.critical_care.calculate_qsofa)
- [ ] T117 [P] Add tool for PEDDimer in server.py (delegates to engines.hematology.calculate_peddimer)
- [ ] T118 [P] Add tool for Comprehensive Audit in server.py (delegates to engines.poly_audit.run_comprehensive_patient_audit)

**Checkpoint**: Run `uv run clinical-mcp` and verify all 14 tools are listed. Test via MCP client.

---

## Phase 11: CLI Demo Dashboard (Cross-Cutting)

**Goal**: Build visually striking Rich terminal benchmark dashboard comparing "Naive LLM Token Guess" vs "clinical-mcp Deterministic Engine" for 5 notorious LLM Traps

**Independent Test**: Run `uv run python -m clinical_mcp.cli_demo` and verify all 5 trap scenarios display side-by-side comparison tables

### Implementation for CLI Demo

- [ ] T119 Create CLI demo in src/clinical_mcp/cli_demo.py (Rich Console, Table, Panel; 5 trap scenarios with predefined patient data). MUST define and export `DEMO_TRAP_CASES: list[ComprehensivePatientInput]` containing the 5 canonical trap fixtures, and render the Rich comparison table: 1) Occult Hypoalbuminemic Lactic Acidosis + Winter's Compensation Failure, 2) Obese Cockcroft-Gault vs CKD-EPI DOAC Overdose, 3) Tachycardic Wide-QRS Bazett False-Positive Torsades, 4) UNOS MELD-Na/MELD 3.0 Logarithmic Floor Clamping, 5) Age-Adjusted D-Dimer PE Exclusion.
- [ ] T120 [P] Implement Trap 1: Occult Hypoalbuminemic Lactic Acidosis + Winter's Compensation Failure (hypoalbuminemia masks AG elevation; uncorrected Na⁺ in hyperglycemia; trap: HYPOALBUMINEMIA_MASKED_HAGMA)
- [ ] T121 [P] Implement Trap 2: Obese Cockcroft-Gault vs CKD-EPI DOAC Overdose Trap (actual weight 120kg vs AdjBW 85kg → 40% vancomycin overdose)
- [ ] T122 [P] Implement Trap 3: Tachycardic Wide-QRS Bazett False-Positive Torsades Alarm (HR 110, QRS 140 → Bazett 520ms vs Fridericia 440ms)
- [ ] T123 [P] Implement Trap 4: UNOS MELD-Na/MELD 3.0 Logarithmic Floor Clamping (bilirubin 0.8→1.0, INR 0.9→1.0, Cr 0.7→1.0)
- [ ] T124 [P] Implement Trap 5: Age-Adjusted D-Dimer PE Exclusion (age 65, D-dimer 600 → threshold 650, CTPA not indicated vs fixed 500 would indicate)
- [ ] T125 [P] Add command-line argument parsing (--trap to run single trap, --all for full dashboard)

---

## Phase 12: Documentation & CI/CD (Polish & Cross-Cutting)

**Purpose**: Flagship GitHub documentation and CI pipeline

- [ ] T126 Create README.md with: badges (Python version, license, CI status), Mermaid.js hexagonal architecture diagram, Markdown comparison table of 18 clinical equations and LLM traps prevented, Claude Desktop/Cursor/OpenCode MCP JSON config snippets, quickstart commands
- [ ] T127 [P] Create GitHub Actions workflow in .github/workflows/ci.yml (jobs: test with coverage gate ≥95%, type-check mypy, lint ruff, build)
- [ ] T128 [P] Create AGENTS.md runtime guidance derived from constitution (development workflow, code style, testing requirements)
- [ ] T129 Run quickstart.md validation scenarios (all 10 Python snippets from quickstart.md must pass assertions)
- [ ] T130 [P] Run full test suite with coverage: `uv run pytest --cov=src/clinical_mcp/engines --cov-report=term-missing` (verify ≥95% engine coverage)
- [ ] T131 [P] Run type check: `uv run mypy src/clinical_mcp` (zero errors)
- [ ] T132 [P] Run lint: `uv run ruff check src/clinical_mcp` (zero errors)
- [ ] T133 [P] Run CLI demo: `uv run python -m clinical_mcp.cli_demo` (verify 5 trap tables render)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phases 3-9)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
  - **Recommended order**: US1 → US2 → US3 → US5 → US7 → US4 → US6 (P1s first, then P2s, US7 last as it integrates all)
- **MCP Server (Phase 10)**: Depends on at least US1-US3 engines being complete (to register tools)
- **CLI Demo (Phase 11)**: Depends on all engines complete (uses all 5 trap scenarios)
- **Documentation & CI/CD (Phase 12)**: Depends on all implementation complete

### User Story Dependencies

- **User Story 1 (P1 - Renal)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1 - Acid-Base)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P1 - Cardiology)**: Can start after Foundational (Phase 2) - Independent of US1/US2
- **User Story 4 (P2 - Hepatology)**: Can start after Foundational (Phase 2) - Independent
- **User Story 5 (P1 - Critical Care)**: Can start after Foundational (Phase 2) - Independent
- **User Story 6 (P2 - Hematology)**: Can start after Foundational (Phase 2) - Independent
- **User Story 7 (P1 - Poly-Audit)**: **Depends on US1-US6 engines being complete** (orchestrates all domains)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD per Constitution Principle VI)
- Schemas (input/output) before engines
- Engine implementation before MCP tool registration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003-T007)
- All Foundational tasks marked [P] can run in parallel (T008-T013)
- All contract tests for a user story marked [P] can run in parallel
- All gold-standard unit tests for a user story marked [P] can run in parallel
- All boundary guard tests marked [P] can run in parallel
- All trap case tests marked [P] can run in parallel
- All schema creation tasks within a story marked [P] can run in parallel (input + output schemas)
- Different user stories can be worked on in parallel by different team members **after Foundational phase**
- MCP Server tool registration tasks (T105-T118) all marked [P] - can run in parallel
- CLI Demo trap implementations (T120-T124) all marked [P] - can run in parallel
- Documentation/CI tasks (T127-T133) marked [P] can run in parallel

---

## Parallel Example: User Story 1 (Renal)

```bash
# Launch all contract tests for US1 together:
Task T014: "Contract tests for renal input/output schemas in tests/test_renal.py::TestCKDEPISchemas"
Task T015: "Contract tests for CockcroftGault schemas in tests/test_renal.py::TestCockcroftGaultSchemas"
Task T016: "Contract tests for AKIIndices schemas in tests/test_renal.py::TestAKIIndicesSchemas"

# Launch all gold-standard unit tests for US1 together:
Task T017: "Gold-standard unit tests for CKD-EPI in tests/test_renal.py::TestCKD_EPI"
Task T018: "Gold-standard unit tests for Cockcroft-Gault in tests/test_renal.py::TestCockcroftGault"
Task T019: "Gold-standard unit tests for AKI Indices in tests/test_renal.py::TestAKIIndices"

# Launch all boundary/trap tests for US1 together:
Task T020: "Boundary guard tests in tests/test_boundary_guards.py::TestRenalBoundaries"
Task T021: "Trap case tests in tests/test_renal.py::TestRenalTraps"
Task T022: "Pediatric rejection test in tests/test_boundary_guards.py::TestPediatricRejection"

# Launch schema creation for US1 together:
Task T023: "Create renal input schemas in src/clinical_mcp/schemas/renal.py"
Task T024: "Create renal output schemas in src/clinical_mcp/schemas/renal.py"
```

---

## Parallel Example: MCP Server Tool Registration

```bash
# All 14 tool registrations can run in parallel after engines are ready:
Task T105: "Add tool for CKD-EPI in server.py"
Task T106: "Add tool for Cockcroft-Gault in server.py"
Task T107: "Add tool for AKI Indices in server.py"
Task T108: "Add tool for Acid-Base in server.py"
Task T109: "Add tool for Osmolality in server.py"
Task T110: "Add tool for Calcium in server.py"
Task T111: "Add tool for QTc in server.py"
Task T112: "Add tool for Hemodynamics in server.py"
Task T113: "Add tool for MELD in server.py"
Task T114: "Add tool for FIB-4 in server.py"
Task T115: "Add tool for Oxygenation in server.py"
Task T116: "Add tool for qSOFA/SIRS in server.py"
Task T117: "Add tool for PEDDimer in server.py"
Task T118: "Add tool for Comprehensive Audit in server.py"
```

---

## Parallel Example: CLI Demo Traps

```bash
# All 5 trap implementations can run in parallel:
Task T120: "Implement Trap 1: Occult Hypoalbuminemic Lactic Acidosis"
Task T121: "Implement Trap 2: Obese Cockcroft-Gault DOAC Overdose"
Task T122: "Implement Trap 3: Tachycardic Wide-QRS Bazett False Positive"
Task T123: "Implement Trap 4: UNOS MELD Logarithmic Floor Clamping"
Task T124: "Implement Trap 5: Age-Adjusted D-Dimer PE Exclusion"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T013) **CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 (T014-T028) with TDD - tests first, fail, then implement
4. **STOP and VALIDATE**: Run `uv run pytest tests/test_renal.py -v` - all tests must pass
5. Run `uv run clinical-mcp` and verify CKD-EPI, Cockcroft-Gault, AKI tools work
6. Deploy/demo if ready

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Renal) → Test independently → **MVP!** Deploy/Demo
3. Add User Story 2 (Acid-Base) → Test independently → Deploy/Demo
4. Add User Story 3 (Cardiology) → Test independently → Deploy/Demo
5. Add User Story 5 (Critical Care) → Test independently → Deploy/Demo
6. Add User Story 7 (Poly-Audit) → Test independently → **Full P1 complete!** Deploy/Demo
7. Add User Story 4 (Hepatology) → Test independently → Deploy/Demo
8. Add User Story 6 (Hematology) → Test independently → Deploy/Demo
9. Add MCP Server (Phase 10) → All 14 tools exposed
10. Add CLI Demo (Phase 11) → 5 trap benchmarks
11. Add Documentation & CI/CD (Phase 12) → Production ready

### Parallel Team Strategy (3+ Developers)

With multiple developers:

1. **Team completes Setup + Foundational together** (Phases 1-2)
2. **Once Foundational is done, parallel story implementation:**
   - Developer A: User Story 1 (Renal) + User Story 4 (Hepatology)
   - Developer B: User Story 2 (Acid-Base) + User Story 6 (Hematology)
   - Developer C: User Story 3 (Cardiology) + User Story 5 (Critical Care)
3. **All developers converge on User Story 7 (Poly-Audit)** - requires all engines
4. **Team splits cross-cutting work:**
   - Developer A: MCP Server (Phase 10)
   - Developer B: CLI Demo (Phase 11)
   - Developer C: Documentation & CI/CD (Phase 12)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability (US1-US7)
- Each user story should be independently completable and testable
- **Tests are REQUIRED per Constitution Principle VI** - verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constitutional Principles enforced in tasks:**
  - Zero Token Arithmetic: All math in `engines/` pure Python (T025-T027, T039-T041, T051-T052, T063-T064, T074-T075, T083, T101)
  - Hexagonal Architecture: `schemas/` → `engines/` ← `server.py` (no reverse deps)
  - Fail-Fast Guards: Every input model uses `Field(ge=, le=)` + custom `@field_validator` (T023, T037, T049, T061, T072, T081, T099)
  - Coupled Propagation: Mandatory pre-computation chains documented in engine docstrings (T025-T027, T039-T041, T051, T063, T074, T083, T101)
  - Explainable Output: All output models include 4 components plus top-level `unit: UCUMUnit` (T024, T038, T050, T062, T073, T082, T100)
  - Test-Driven Verification: ≥95% coverage, gold-standard fixtures, boundary/trap tests (T014-T022, T029-T036, T043-T048, T054-T060, T066-T071, T077-T080, T085-T098)
