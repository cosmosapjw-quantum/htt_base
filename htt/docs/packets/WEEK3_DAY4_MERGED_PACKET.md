# WEEK 3 DAY 4 PACKET — merged v4.1

**Date**: 2026-04-17
**Scope**: Species-resolved batch tangency diagnostic over {γ, ν_e, ν_μ, ν_τ}
**New module**: `species_tangency.py` (~270 LoC)
**Tests**: 40 across 9 classes
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings
**Cumulative**: 743 tests, 32.23 s runtime

---

## §1 — Scope and Paper I role

Paper I §III defines the tangency diagnostic $D_{s, \geq 2}$ per species $s$. The single-species
engine was built in W2D3 (`tangency.compute_D_diagnostic`, `TangencyResult`, Gram-based
regression-exact projection). D4 layers a batch computation over the four cosmological species:

- **Photon γ** — Bose-Einstein (ξ = +1), default chart `ONE_FIELD` (Θ-only ansatz)
- **Neutrinos ν_e, ν_μ, ν_τ** — Fermi-Dirac (ξ = −1), default chart `TWO_FIELD` (Θ + η fugacity)

The batch diagnostic preserves per-species results (`per_species` mapping) while exposing
aggregate statistics the runtime consumes: `worst_species` (argmax over relative residual),
`total_D_sq`, `all_tangent`, and `weighted_fraction_on_manifold` (source-magnitude-weighted
average).

Scope boundaries:

- **No G_field construction**: collision sources are the caller's responsibility. The first
  wiring of real sources lands at W4D3–D4 (`bass/collision/thomson_tensor.py` and
  `bass/transport/ray_transport.py` skeletons).
- **No runtime allow/block**: this module is a pure TSC-layer diagnostic. The canonical decision
  consumer (`source_Dge2_gate`) chooses its aggregation policy independently.
- **No TSC → BASS direct coupling**: the ownership boundary is respected — the module's
  only imports are `tangency` (future `tsc.diagnostics.tangency`) and stdlib/numpy.

---

## §2 — Architectural construction

### 2.1 Data flow

```
  caller supplies G_fields : {species -> G_s(x)}
          │
          ├── compute_species_tangency(G_fields, charts, alpha)
          │         │
          │         ├── for each SpeciesChart c in charts:
          │         │     compute_D_diagnostic(G_fields[c.species],
          │         │                         c.kind, c.xi, c.eta, alpha)
          │         │     => TangencyResult_s
          │         │
          │         └── _aggregate(per_species, species_order)
          │                 │
          │                 └── SpeciesTangencyResult
```

### 2.2 Deterministic species order

`species_order` is fixed by the caller's `charts` sequence. `compute_species_tangency` iterates
in that order and preserves it in the result. This guarantees `worst_species` and selector
outputs (`tangent_species`, `off_manifold_species`) are reproducible across runs and process
restarts.

### 2.3 Aggregation semantics (mathematical definitions)

For $N$ species in the chart set:

$$\mathrm{total\_D\_sq} \;=\; \sum_{s} D_s^2, \qquad \mathrm{total\_norm\_sq} \;=\; \sum_s \|G_s\|_{*,s}^2$$

$$\mathrm{max\_relative\_residual} \;=\; \max_s \frac{D_s}{\|G_s\|_{*,s}}, \qquad \mathrm{worst\_species} \;=\; \arg\max_s \frac{D_s}{\|G_s\|_{*,s}}$$

$$\mathrm{weighted\_fraction\_on\_manifold} \;=\; \frac{\sum_s \|\Pi_{V_s} G_s\|_{*,s}^2}{\sum_s \|G_s\|_{*,s}^2}$$

These aggregates are additive in the Paper I weighted inner product, so the batch result is the
natural physical summary — contribution is by source magnitude, not by nominal species count.

### 2.4 Chart override helpers

Two pre-built override sets live in the module:

- `override_neutrino_chart_one_field(eta=0.0)` — forces ν into ONE_FIELD (sensitivity probe for
  Paper I §IV when chemistry closure demands a one-field ν)
- `photon_only_chart()` — single-species chart (unit tests, γ-only studies)

Both return `tuple[SpeciesChart, ...]` and feed straight into `compute_species_tangency` via
the `charts` kwarg.

---

## §3 — Implementation ledger

| Component | Function / class | Role |
|-----------|-----------------|------|
| `CosmologicalSpecies` enum | §1 | 4-member enum: PHOTON + 3 ν flavors |
| `NEUTRINO_FLAVORS` | §1 | Frozen tuple of 3 ν species |
| `SpeciesChart` frozen dataclass | §2 | Per-species (species, ξ, kind, η) |
| `DEFAULT_SPECIES_CHARTS` tuple | §2 | Standard cosmological assignment |
| `SpeciesTangencyResult` frozen dataclass | §3 | Batch result container with aggregates |
| `compute_species_tangency` | §4 | Main entry: batch diagnostic |
| `_aggregate` | §5 | Internal helper combining per-species into aggregate |
| `tangent_species`, `off_manifold_species` | §6 | Species selectors in stable order |
| `per_species_relative_residuals` | §6 | Flat {species: D/‖G‖} mapping |
| `override_neutrino_chart_one_field` | §7 | Force ν → ONE_FIELD chart set |
| `photon_only_chart` | §7 | γ-only chart set |

### 3.1 Import graph (clean for TSC move)

```
species_tangency  ──→  tangency  (current) / tsc.diagnostics.tangency (post-freeze)
                  ──→  stdlib + numpy
```

No imports from `bass/runtime/` or `bass/validation/`. No import of `canonical_decision`,
`validation_labels`, `sigma_floor`, `baryon_only_policy`. Ready for the W3D5b directory move
with the rest of `tsc/diagnostics/`.

---

## §4 — Verified behaviour

### 4.1 All-on-manifold baseline

Pure-$x$ G fields across all species → every species has $D_s / \|G_s\| = 0$ to machine zero;
`all_tangent = True`, `weighted_fraction = 1.0000`. Verified in
`TestBatchComputation::test_all_on_manifold_is_all_tangent`.

### 4.2 Mixed-species off-manifold localization

Smoke-test scenario: γ + ν_μ + ν_τ use pure-x; ν_e uses x³ (heavily off-manifold).

| Quantity | Observed |
|----------|----------|
| `all_tangent` | False |
| `worst_species` | `nu_e` |
| `tangent_species(result)` | (photon, nu_mu, nu_tau) |
| `off_manifold_species(result)` | (nu_e,) |
| `weighted_fraction_on_manifold` | 0.729 |

The 27% drop in `weighted_fraction` accurately reflects ν_e's source magnitude contribution,
and `worst_species` picks the correct offender. Verified in
`TestWorstSpeciesIdentification::test_nu_e_worst_when_heavily_off_manifold`.

### 4.3 Additivity of `total_D_sq`

Direct summation over `per_species[s].D_sq` for $s \in$ species_order matches
`result.total_D_sq` to relative precision $10^{-12}$. Verified in
`TestAggregation::test_total_D_sq_equals_sum_over_species`.

### 4.4 `worst_species` tie-breaking

When two species have identical D_s / ‖G_s‖ values (e.g., ν_e = ν_μ both x³), the argmax
consistently returns the first in `species_order`. This matches numpy's `argmax` convention.
Verified in `TestWorstSpeciesIdentification::test_worst_species_stable_on_tie`.

### 4.5 Chart override sensitivity

The `override_neutrino_chart_one_field()` probe correctly forces all ν into ONE_FIELD. A G-field
of pure-$x$ then registers as on-manifold for both γ and ν (all four species), confirming the
override-path exercises the same `compute_D_diagnostic` underlying engine.

### 4.6 Input validation

Three error paths verified (`TestInputValidation`):
- Missing G_field entry → `ValueError` listing missing species by name
- Duplicate chart species → `ValueError("duplicate")`
- Partial coverage (2 of 4 species) → `ValueError` identifying the missing ones

---

## §5 — Three-tier claim taxonomy

### 5.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| Per-species `TangencyResult` populated deterministically for all default species | `TestBatchComputation` |
| `all_tangent == AND over is_tangent flags` | Tested on-manifold + mixed scenarios |
| `worst_species` = argmax over relative residual | `TestWorstSpeciesIdentification` (4 tests) |
| `total_D_sq` additive across species | `test_total_D_sq_equals_sum_over_species` (rel err < 1e-12) |
| `weighted_fraction_on_manifold ∈ [0, 1]` | Range-invariant check |
| Default chart set matches cosmological convention (γ BE one-field, ν FD two-field) | `TestDefaultChartSet` (4 tests) |
| Selector order matches `species_order` | `test_selector_order_matches_species_order` |
| Import graph TSC-clean | `TestRetrofitReadiness` (W3D3) + this module's import scan |

### 5.2 CONDITIONAL

| Claim | Condition |
|-------|-----------|
| `weighted_fraction` as a meaningful "on-manifold" scalar | Physically reasonable under equal source normalization. When species are normalized differently (e.g., per-species weights from `SpeciesRegistry.beta_bar`), the interpretation tightens or loosens. W4 wiring will revisit. |
| Default `DEFAULT_SPECIES_CHARTS` | Matches standard cosmology; deviations (e.g., sterile ν, extra degrees of freedom) require a separate chart set |
| `eta = 0` for ν by default | Reflects chemistry-baseline assumption; production runs with finite chemical potentials supply different `eta` values per flavor |

### 5.3 NOT ESTABLISHED (deferred)

- Integration with real collision sources (Thomson tensor, neutrino free-streaming) — W4D3–D4
- Coupling to `canonical_decision.source_Dge2_gate` with an aggregation policy (worst-species
  vs. weighted fraction) — W3D5 or later wiring
- Sterile neutrino / BSM species extension — out of scope

---

## §6 — Self-audit (PHYS-MATH-CODE)

### 6.1 Findings

| Check | Status |
|-------|--------|
| ASCII section banners | ✅ |
| Banned vocabulary scan | ✅ clean |
| Frozen dataclasses for `SpeciesChart` and `SpeciesTangencyResult` | ✅ |
| Type hints on all public functions | ✅ |
| Informative error messages on all validation paths | ✅ (3 distinct paths) |
| No circular imports | ✅ (imports tangency + stdlib + numpy only) |
| TSC layer does not import bass runtime | ✅ |
| No regression in 703 prior tests | ✅ 743/743 green |
| Species enum stable (exactly 4 members with pinned strings) | ✅ `test_pinned_values` |

**P0 / P1 findings: 0 / 0**.

### 6.2 Design-spec alignment

No new design-spec items surfaced in D4. The `SpeciesTangencyResult` shape was designed
consistent with D1's `CanonicalDecision` conventions (frozen, aggregate-from-parts, deterministic
ordering). The aggregation policy for `source_Dge2_gate` at the canonical-decision level
(whether to feed `max_relative_residual` or `weighted_fraction_on_manifold` or both) will be
decided at W3D5b wiring; the raw fields are all available on `SpeciesTangencyResult`.

---

## §7 — API surface

```python
from species_tangency import (
    # Enum + frozen tuple
    CosmologicalSpecies,
    NEUTRINO_FLAVORS,

    # Chart spec
    SpeciesChart,
    DEFAULT_SPECIES_CHARTS,

    # Result
    SpeciesTangencyResult,

    # Main entry
    compute_species_tangency,

    # Convenience selectors
    tangent_species,
    off_manifold_species,
    per_species_relative_residuals,

    # Chart overrides
    override_neutrino_chart_one_field,
    photon_only_chart,
)

# Typical usage
result = compute_species_tangency(
    G_fields={
        CosmologicalSpecies.PHOTON: G_photon,
        CosmologicalSpecies.NU_E:   G_nu_e,
        CosmologicalSpecies.NU_MU:  G_nu_mu,
        CosmologicalSpecies.NU_TAU: G_nu_tau,
    },
)

if not result.all_tangent:
    print(f"off-manifold species: {off_manifold_species(result)}")
    print(f"worst: {result.worst_species.value} at "
          f"D/||G|| = {result.max_relative_residual:.2e}")
```

---

## §8 — Numerical ledger

| Quantity | Value |
|----------|-------|
| New tests | 40 (9 classes) |
| Cumulative tests | 743 |
| Full-suite runtime | 32.23 s |
| New module LoC | ~270 |
| P0 / P1 findings | 0 / 0 |
| Banned vocabulary hits | 0 |
| Species covered | 4 (γ + ν_e + ν_μ + ν_τ) |
| Default chart configuration | γ one-field BE, ν_{e,μ,τ} two-field FD |
| `total_D_sq` additivity precision | < 10⁻¹² relative error |
| `weighted_fraction_on_manifold` range | [0, 1] (inclusive both ends) |

---

## §9 — Next action (W3D5 split)

D5 is the closing day of Week 3 and splits per v4.1 MERGED §4.1:

### §9.1 D5a — L0 precision dashboard

Oracle: analytic Paper I closed-form moment values + ch05 cross-reference table (no CAMB).

Comparisons to lock in (per `BASS_PY_INTEGRATION_MERGED.md` §3.1 Table):

| Quantity | Oracle | Target tolerance |
|----------|--------|------------------|
| $I_3, I_4$ (BE, η=0) | $\Gamma(n+1)\zeta(n+1)$ | $<10^{-10}$ rel err |
| $I_4/I_3$ ratios (BE/MB/FD) | 3.8322 / 4.0000 / 4.1060 | $<10^{-10}$ |
| $\Sigma_2 = (8/15) I_4/I_3$ | ch05 Eq. (shear-source) | $<10^{-10}$ |
| $F^{-1} \circ F$ closure | identity | $<10^{-8}$ at amp ≤ 0.2 |
| MB Laguerre Gram orthogonality | $(s+2)(s+1)\delta_{ss'}$ | $<10^{-13}$ (W2D1 bound stands) |
| MB TWO_FIELD Gram κ | 54.3 at η=0 | reproducibility only |

Deliverable: `precision_dashboard.py` (~200 LoC, ~20 tests) emitting JSON + Markdown table.
L0 gate passes iff all rows green.

### §9.2 D5b — ownership freeze commit

Deliverables:
- Directory migration per v4.1 MERGED §2.2:
  - `bianchi_types`, `einstein_bianchi` → `bass/background/`
  - `shear_sources` → `bass/transport/`
  - `baryon_only_policy` → `bass/tilt/`
  - `comparator_policy`, `channel_routing` → `bass/validation/`
  - `canonical_decision`, `validation_labels`, `sigma_floor` → `bass/runtime/`
  - `laguerre_basis`, `forward_F_to_T`, `inverse_T_to_F`, `inverse_T_to_F_mc`, `boost_perturbative` → `tsc/charts/`
  - `tangency`, `species_tangency` → `tsc/diagnostics/`
  - `realizability` → `tsc/admissibility/`
- `__init__.py` scaffolding for all new directories
- Import-path updates across all test files (bulk `sed`-like edit)
- `test_ownership_freeze.py` (~12 tests) — import-graph AST check enforcing:
  - BASS is sole allow/block owner
  - TSC never emits final labels
  - No TSC → MIO direct path
  - No HTT → TSC direct path
  - spec_version pin consistent across modules

Expected ~32 new tests across D5a + D5b.

**W3 end target**: 775 tests (743 + ~32).

---

**End of W3D4 packet. Awaiting approval for D5.**
