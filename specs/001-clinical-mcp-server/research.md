# Research Findings: clinical-mcp

**Feature**: specs/001-clinical-mcp-server  
**Date**: 2026-11-06  
**Status**: All technical decisions resolved — no NEEDS CLARIFICATION items remain.

---

## Decisions Summary

| # | Topic | Decision | Source |
|---|-------|----------|--------|
| 1 | Package manager | `uv` with `pyproject.toml` | User requirement |
| 2 | MCP framework | `mcp[cli]>=1.2.0` | Official SDK; stdio + HTTP |
| 3 | Validation | Pydantic v2 `Field` + `@field_validator` | Constitution Principle III |
| 4 | Testing | `pytest>=8.3.0` + coverage | Constitution Principle VI |
| 5 | Linting/Type-check | `ruff>=0.7.0` + `mypy>=1.13.0` | Modern, fast, CI-friendly |
| 6 | CLI UI | `rich>=13.9.0` | User requirement; terminal dashboard |
| 7 | Entry point | `clinical-mcp = "clinical_mcp.server:main"` | User requirement |
| 8 | Architecture | Hexagonal (schemas/engines/server/cli) | Constitution Principle II |
| 9 | Math execution | Pure Python in `engines/` | Constitution Principle I |
| 10 | Boundary guards | Pydantic `Field(ge=, le=)` + custom validators | Constitution Principle III |
| 11 | Coupled propagation | Mandatory pre-computation in each engine | Constitution Principle IV |
| 12 | Output structure | 4-component Pydantic model | Constitution Principle V |
| 11 | Test coverage | ≥95% for engine modules | Constitution Principle VI |

---

## Detailed Research

### 1. Package Manager: `uv`

**Decision**: Use `uv` for dependency management and virtual environments.

**Rationale**: 
- User explicitly requested `uv` with `pyproject.toml`
- 10-100x faster than pip/poetry
- PEP 621 compliant (standard `pyproject.toml`)
- Built-in lockfile (`uv.lock`) for reproducible builds
- Native support for `[project.optional-dependencies]` for dev/prod separation

**Alternatives Considered**:
- **Poetry**: Mature but slower; lockfile format not standard
- **pip-tools**: Requires manual `requirements.txt` management; no built-in venv
- **PDM**: Good but less adoption; `uv` is emerging standard

### 2. MCP Framework: `mcp[cli]>=1.2.0`

**Decision**: Use official Model Context Protocol Python SDK.

**Rationale**:
- Official reference implementation from Anthropic
- Supports both stdio (Claude Desktop) and HTTP transports
- `[cli]` extra includes CLI utilities for development
- Version 1.2.0+ has stable API for tool registration
- Handles JSON-RPC framing, schema generation, error handling

**Alternatives Considered**:
- **Custom MCP implementation**: Reinvents protocol handling; high maintenance burden
- **FastMCP (community)**: Wrapper around official SDK; adds abstraction layer without benefit

### 3. Validation: Pydantic v2

**Decision**: Pydantic v2 with `Field` constraints and `@field_validator` for custom error messages.

**Rationale**:
- Constitution Principle III requires "strict Pydantic v2 `Field` constraints"
- v2 is 5-50x faster than v1 (Rust core)
- `Field(ge=, le=, description=)` expresses physiological bounds declaratively
- `@field_validator(mode="before")` enables custom clinical error messages (e.g., "pH 6.4 is incompatible with life")
- Automatic JSON Schema generation for MCP tool schemas

**Alternatives Considered**:
- **dataclasses + manual validation**: Verbose, error-prone, no schema generation
- **attrs + cattrs**: Less ecosystem support; no built-in constraints
- **msgspec**: Fast but less mature validation API

### 4. Testing: pytest

**Decision**: pytest with deterministic gold-standard fixtures.

**Rationale**:
- Constitution Principle VI: "deterministic `pytest` unit tests"
- Industry standard for Python; rich fixture system
- `pytest-cov` for coverage reporting (≥95% gate)
- Parametrized tests ideal for equation verification matrices
- `conftest.py` for shared clinical reference fixtures

**Alternatives Considered**:
- **unittest**: Built-in but verbose; poor parametrization
- **hypothesis**: Property-based testing; overkill for fixed clinical formulas

### 5. Linting & Type Checking: ruff + mypy

**Decision**: `ruff>=0.7.0` for linting/formatting, `mypy>=1.13.0` for static types.

**Rationale**:
- `ruff` replaces flake8, black, isort, pyupgrade — single tool, 100x faster
- `mypy` catches type errors in Pydantic models and engine signatures
- Both integrate with pre-commit and CI
- User requirement in dev dependencies

**Alternatives Considered**:
- **flake8 + black + isort**: Fragmented config; slower
- **pyright**: Fast but less configurable for Pydantic v2 internals

### 6. CLI UI: Rich

**Decision**: `rich>=13.9.0` for terminal benchmark dashboard.

**Rationale**:
- User requirement: "visually striking `Rich` terminal benchmark dashboard"
- Tables, panels, progress bars, syntax highlighting built-in
- No TUI framework overhead (unlike `textual`)
- Perfect for side-by-side "Naive LLM" vs "clinical-mcp" comparison tables

**Alternatives Considered**:
- **textual**: Full TUI framework; overkill for static dashboard
- **blessed**: Lower-level; more boilerplate
- **plain print**: Not "visually striking"

### 7. Entry Point: `clinical-mcp = "clinical_mcp.server:main"`

**Decision**: Single stdio MCP server entry point.

**Rationale**:
- User requirement
- `stdio` transport works natively with Claude Desktop, Cursor, OpenCode
- `server.py` contains `FastMCP` instantiation and tool registration
- `main()` function serves as CLI entry when run as module

**Alternatives Considered**:
- **HTTP-only server**: Requires proxy for stdio clients; more complex deployment
- **Multiple entry points**: Unnecessary complexity; single server exposes all tools

### 8. Architecture: Hexagonal (Clean)

**Decision**: Explicit separation per user specification:
- `schemas/` — Pydantic contracts (input/output models)
- `engines/` — Pure Python domain functions (zero dependencies)
- `server.py` — MCP adapter (transport layer)
- `cli_demo.py` — Presentation layer (Rich dashboard)

**Rationale**:
- Constitution Principle II: "engines must be 100% pure Python functions... zero dependency on MCP or transport layers"
- Enables independent testing of engines without MCP runtime
- Allows swap of transport (stdio ↔ HTTP) without touching clinical logic
- Clear dependency direction: `server` → `engines` ← `schemas` (engines depend on schemas only)

**Alternatives Considered**:
- **Layered architecture**: Tight coupling between transport and domain
- **Monolithic**: Single file; violates Constitution Principle II

### 9. Zero Token Arithmetic

**Decision**: All mathematical operations in `engines/*.py` as pure Python functions.

**Rationale**:
- Constitution Principle I: "LLMs must never compute logarithms, exponents, or physiological corrections in tokens"
- MCP tools in `server.py` delegate to engine functions
- Engine functions accept validated Pydantic models, return validated Pydantic models
- No `eval()`, no string math, no LLM reasoning in computation path

**Implementation Pattern**:
```python
# engines/renal.py
def calculate_ckd_epi(input: CKDEPIInput) -> CKDEPIOutput:
    # Pure Python math only
    scr = input.scr_mg_dl
    # ... formula implementation
    return CKDEPIOutput(...)

# server.py
@mcp.tool()
def ckd_epi(input: CKDEPIInput) -> CKDEPIOutput:
    return calculate_ckd_epi(input)  # Delegation only
```

### 10. Fail-Fast Boundary Guards

**Decision**: Every input model uses `Field` constraints + custom validators.

**Rationale**:
- Constitution Principle III: "strict Pydantic v2 `Field` constraints for human-compatible biological limits"
- Validation occurs at model construction — before any engine function executes
- Custom `@field_validator` provides clinically meaningful error messages

**Examples**:
```python
class AcidBaseInput(BaseModel):
    ph: float = Field(ge=6.5, le=7.8, description="Arterial pH")
    na_meq_l: float = Field(ge=100, le=180, description="Serum sodium")
    
    @field_validator("ph", mode="before")
    @classmethod
    def validate_ph(cls, v):
        if v < 6.5 or v > 7.8:
            raise ValueError(f"pH {v} is incompatible with life (valid range: 6.50–7.80)")
        return v
```

### 11. Coupled Physiological Propagation

**Decision**: Each engine implements mandatory pre-computation propagation chain.

**Rationale**:
- Constitution Principle IV: "Calculators must account for physiological confounders automatically as a mandatory pre-computation step"
- Documented in engine docstrings per constitution
- Prevents cascade errors from sequential tool calls

**Propagation Chains**:
| Engine | Pre-computation Steps |
|--------|----------------------|
| Osmolality | Hillier glucose-corrected Na⁺ → osmolality calculation |
| Acid-Base | Hillier Na⁺ → Figge albumin-corrected AG → delta ratio → Winter's formula |
| Cockcroft-Gault | Devine IBW → Adjusted BW → weight selection rule → CrCl |
| MELD | UNOS clamping (floors/caps) → MELD-Na & MELD 3.0 |
| QTc | Wide-QRS adjustment (if QRS>120) → RR → 3 formulas → auto-selection |

### 12. Explainable Output & Trap Telemetry

**Decision**: Every output model contains 4 required components.

**Rationale**:
- Constitution Principle V: "Every tool response must return a structured Pydantic model containing: (a) numerical results with units, (b) guideline staging/risk strata, (c) clinical_pearls_and_actions, (d) llm_trap_prevented"

**Output Model Template**:
```python
class EngineOutput(BaseModel):
    unit: UCUMUnit                     # one top-level UCUM unit
    clinical_pearls_and_actions: List[str]
    llm_trap_prevented: List[str]
    # plus flat float/int result and staging fields on each domain output
```

**Trap Telemetry Examples**:
- "Uncorrected sodium would underestimate osmolarity by 12 mOsm/kg in this hyperglycemic patient"
- "Bazett formula over-corrects at HR 110 bpm; Fridericia selected automatically"
- "Using actual body weight (120 kg) instead of AdjBW (85 kg) would overdose vancomycin by 40%"

### 13. Test-Driven Clinical Verification

**Decision**: Comprehensive pytest suite with gold-standard fixtures.

**Rationale**:
- Constitution Principle VI: "Every equation and boundary clamp must have deterministic pytest unit tests"
- Fixtures cover: textbook references, boundary limits, trap cases, regression vectors
- Coverage threshold ≥95% for engine modules
- Tests run in CI on every commit

**Fixture Categories**:
1. **Gold-standard references**: Published textbook values (e.g., CKD-EPI at SCr=1.0, age=40, male = 97.5)
2. **Boundary limits**: pH 6.50/7.80, Na 100/180, glucose 0/1000
3. **Trap cases**: Glucose >400 (Hillier 0.024), albumin <1.5 (Figge), obesity ABW switching
4. **Regression vectors**: Known literature errata (e.g., MELD 3.0 creatinine cap 3.0 vs 4.0)

---

## Open Questions

None — all decisions resolved from user requirements and constitutional principles.