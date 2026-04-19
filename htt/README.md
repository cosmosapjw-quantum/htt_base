# bass-py — BASS (Python side)

**BASS = Bianchi Anisotropy System Solver** — low-ℓ (ℓ ≤ 30) special-purpose CMB solver, inverse of the MES kinematic bound hierarchy.

## Current status (v0.8.2-w8-02, 2026-04-18)

- **22 bass/ modules**, **35 test files**, **1,637 tests passing**
- **0 P0/P1 findings** outstanding
- Full regression: ~40 s
- Phases complete: W3, W4, W5, W6, W7; W8 in progress (2/3 prompts done)
- Next prompt: **W8-03 (visibility source g·Π)** — Document 12 ceiling item 2/3

See `HANDOFF_PACKET.md` for comprehensive state summary.

## Key recent results

| Result | Value | Reference | Agreement |
|--------|-------|-----------|-----------|
| τ_reion (Planck 2018 default) | 0.054108 | 0.054 ± 0.007 | Δ = 0.0001 |
| z_* (last scattering, κ=1) | 1089.89 | 1089.95 ± 0.27 | Δ = 0.06 |
| x_e(z=1075) | 0.11335 | 0.1137 (memory) | 0.3% |
| W6-04 ↔ W7-01/02 cross-check | rel 1e-16 | machine precision | ✓ |
| Polarization amplification factor | 4/3 exact | analytical | ✓ |

## Running tests

```bash
# Full regression
PYTHONPATH=. pytest bass/ tsc/ -q

# This session's recombination layer only
PYTHONPATH=. pytest bass/recombination/ -v
```

## Directory layout

```
bass/
├── background/      bianchi_types, einstein_bianchi            [pre-session]
├── perturbation/    baryon_fluid (W6-01), cdm_fluid (W6-03)
├── transport/       multipole_hierarchy (W5-A)
│                    dipole_driven_hierarchy (W6-02)
│                    emode_hierarchy (W7-01, spin-2)
│                    bianchi_i_hierarchy, implicit_hierarchy, shear_sources
│                    ray_transport
├── closure/         quadrupole_tca (W6-04, sign-fixed v1.2)
│                    polter_recoupling (W7-02)
├── collision/       thomson_tensor
├── recombination/   recombination_ingest (W8-01, HyRec-2 ingest)
│                    reionization (W8-02, tanh τ≈0.054)
│                    fixtures/ — real Planck 2018 reference CSV (520 KB)
├── runtime/         canonical_decision (W3), sigma_floor, validation_labels
├── tilt/            baryon_only_policy, beta_policy_gate
├── observational/   beta_threshold, planck_mes_bounds
└── validation/      channel_routing, comparator_policy

tsc/                 Trace Semantics Controller (admissibility, charts, diagnostics)
```

## v1.2 mandatory patterns (every new module)

1. **Physical sign assertions** — `assert q > 0` vs externally-known sign
2. **Cross-module cross-check** at machine precision
3. **Analytic derivation BEFORE code** (zero first-attempt failures)
4. **Non-invasive wrapping** with `is_trivial → W5-A bit-exact` test
5. **Scope declaration** with explicit "deferred" list

## Ownership rules (v4.1)

- BASS owns the only final allow/block path (`bass.runtime.canonical_decision`)
- TSC cannot emit final validation labels — only chart-level suggestions
- MIO/HTT are out-of-scope for this package (observatory/local-patch, W6+)

## References

- `HANDOFF_PACKET.md` — 11-section research handoff (primary context)
- `CHANGELOG.md` — version history
- `BASS_PY_INTEGRATION_v4_1_MERGED.md` — architecture baseline
- `MASTER_PROMPT_LIST_bass_py_v1_2.md` — W3–W15 roadmap
- Session packets: `WEEK{3-8}_*_PACKET.md`
