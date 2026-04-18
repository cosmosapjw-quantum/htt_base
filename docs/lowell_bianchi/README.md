# Phase LB — Low-ℓ Tetrad-Based Bianchi Solver Foundation

**Purpose**: Build the *rigorous* species-by-species background evolution plus the 1+3 covariant PSTF multipole hierarchy (lowell reference §6) that any later perturbation / line-of-sight / inference work must stand on. Nothing here is phenomenological.

**Status**: Design-complete, implementation pending. Y-Block (`bass/background/tetrad_state.py`, `bass/tilt/species_tilt.py`, `bass/closure/quadrupole_tca.py`) is the bedrock this phase builds on.

---

## 1. Scope

**In scope (this phase)**:

1. Species-specific background evolution for **photon (γ), neutrino (ν), baryon (b), cold dark matter (c), cosmological constant (Λ)**
2. The exact Ellis/Maartens/MacCallum 1+3 covariant PSTF multipole hierarchy at all ℓ up to `L ∈ {4, 6, 8}`
3. Closure and truncation strategies (hard-cut + W6-04 TCA as the ℓ=2 quadrupole closure)
4. Thomson collision operator expressed natively in the PSTF hierarchy (not just a scalar damping rate)
5. A single `solve_ivp`-compatible integrator driving all of the above against one η-grid
6. Regression tests pinning z_eq, z_*, τ_reion, Σ²-decay, Kolb-Turner thermal-history table values

**Out of scope (later phases)**:

- Perturbation theory in any form (scalar/vector/tensor)
- Line-of-sight projection to C_ℓ
- Direction-dependent likelihood
- Anisotropic recombination, patchy reionization
- Massive-neutrino transition (m_ν → 0 here; massive is a later pass)
- Electroweak / strong-interaction thermal relics (BBN is out of scope)

**Non-goals — deliberately excluded**:

- CAMB / CLASS / AniCLASS / HyRec as physics engines. They are **oracles only**: used to *validate*, never to *produce* a quantity we depend on.
- Any shortcut that sacrifices the 1+3 covariant structure (e.g. synchronous-gauge or Newtonian-gauge perturbation equations).
- Phenomenological damping terms, anything that is "close enough" without a derivation from Ellis / Kolb-Turner / Baumann.

---

## 2. Reference materials

| Symbol | Full reference | Role |
|---|---|---|
| **Ellis** | Ellis, Maartens, MacCallum, *Relativistic Cosmology* (Cambridge, 2012). 638 pp. | Mathematical foundation — 1+3 covariant decomposition, PSTF formalism, tetrad evolution, exact Bianchi hierarchy |
| **Kolb** | Kolb & Turner, *The Early Universe* (Frontiers in Physics 69, 1990). 590 pp. | Physics content — thermal history, equilibrium thermodynamics, Boltzmann equation, recombination, neutrino cosmology |
| **Baumann** | "Lecture Notes in Cosmology" (377 pp PDF in repository root) | Physics supplement — modern Friedmann/FLRW treatment, Boltzmann equation derivation, cleaner notation |
| **lowell** | `/lowell_bianchi_solver_reference.md` | Project-specific spec note summarising the low-ℓ solver architecture — §2, §3.2, §6, §10 already partially implemented in Y-Block |
| **Y-Block** | commit `c3dc68c` | `tetrad_state.py`, `species_tilt.py`, `test_reference_cross_check.py` — the bedrock |

**Chapter-to-purpose mapping** (which chapter to consult for which LB-* session):

| Topic | Ellis | Kolb | Baumann |
|---|---|---|---|
| 1+3 decomposition, projection h_ab | §4.1–4.2 | — | §4.1 (background) |
| Kinematic variables Θ, σ_ab, ω_ab, A_a | §4.2–4.3 | — | — |
| Stress-energy decomposition per species | §5.1–5.2 | §3.3 (equilibrium) | §4.2 (energy-momentum pert) |
| Raychaudhuri + shear propagation | §6.2–6.5 | — | §2.3 (Friedmann) |
| Boltzmann equation (covariant) | §4.5 (moments) | §5.1, §6.4 | §3.7–3.8 |
| PSTF multipole hierarchy | §4.5–4.6 | — | §4.6 (linearised) |
| Thermal history, z_eq, z_*, τ_reion | — | §3.5, §5.4 | §3.2, §3.10 |
| Neutrino decoupling, (4/11)^{1/3} | — | §5.5 | §3.6 |
| Thomson kernel, recombination | §5.5 | §5.1, §5.4 | §3.10 |
| Bianchi classification, tetrad | §18.1–18.3 | — | — |
| Exact Bianchi hierarchy | §18.4 (or §4.6 adapted) | — | — |

When in doubt, **Ellis drives the formalism, Kolb drives the physics, Baumann is a sanity check.**

---

## 3. Session sequence and dependency graph

```
                    ┌─────────────────────────┐
                    │   LB-0 conventions      │
                    │   docs/lowell_bianchi/  │
                    │   00_conventions.md     │
                    └──────────┬──────────────┘
                               │
                    ┌──────────┴──────────────┐
                    │   LB-1 species          │ 
                    │   bass/species/         │ depends on Y-Block §3.2
                    │   (5 species classes)   │   (species_tilt)
                    └──────────┬──────────────┘
                               │
                    ┌──────────┴──────────────┐
                    │   LB-2 hierarchy        │ depends on Y-Block §2
                    │   bass/hierarchy/       │   (tetrad_state)
                    │   pstf_tensor +         │
                    │   hierarchy_rhs         │
                    └──────────┬──────────────┘
                               │
         ┌─────────────────────┼──────────────────────┐
         │                     │                      │
    ┌────┴─────────┐   ┌───────┴────────┐   ┌────────┴────────┐
    │ LB-3 closure │   │ LB-4 collision │   │ (parallel-safe) │
    │ bass/hier-   │   │ bass/collision/│   │                 │
    │ archy/clos-  │   │ thomson_pstf   │   │                 │
    │ ure.py       │   │ (extend)       │   │                 │
    └────┬─────────┘   └───────┬────────┘   └────────┬────────┘
         │                     │                      │
         └─────────────────────┼──────────────────────┘
                               │
                    ┌──────────┴──────────────┐
                    │   LB-5 integrator       │
                    │   bass/hierarchy/       │
                    │   integrator.py         │
                    └──────────┬──────────────┘
                               │
                    ┌──────────┴──────────────┐
                    │   LB-6 integration      │
                    │   tests                 │
                    │   (Kolb table match)    │
                    └─────────────────────────┘
```

**Serial dependencies**:
- LB-1 can begin after LB-0 alone.
- LB-2 can begin after Y-Block; LB-0 docs provide the conventions LB-2 must respect.
- LB-3, LB-4 can proceed in parallel once LB-2 is in.
- LB-5 consumes LB-1 + LB-2 + LB-3 + LB-4.
- LB-6 is the final gate; cannot start until LB-5 passes its own unit tests.

---

## 4. Document catalogue

| File | Purpose | Audience | Depth |
|---|---|---|---|
| `README.md` (this file) | Meta-index, scope, reading order, session sequence | Anyone returning to the project | Overview |
| `00_conventions.md` | Signature, units, PSTF packing, kinematic variables, SSOT, cross-reference to bass_py | All LB sessions | Foundation — must read before LB-1+ |
| `01_species_background_spec.md` | Photon/neutrino/baryon/CDM/Λ background ODEs with exact equation citations | LB-1 implementer | Detailed spec |
| `02_multipole_hierarchy_spec.md` | PSTFTensor data structure + exact 1+3 covariant hierarchy RHS with all shear/vorticity/acceleration couplings | LB-2 implementer | Detailed spec |
| `03_closure_truncation_spec.md` | L=4/6/8 truncation strategies, integration with W6-04 TCA, error scaling | LB-3 implementer | Detailed spec |
| `04_thomson_collision_spec.md` | Ellis §5.5 Thomson tensor expressed as PSTF collision source K_{A_ℓ} | LB-4 implementer | Detailed spec |
| `05_integrator_spec.md` | Combined ODE state vector, step-size strategy, `solve_ivp` wiring | LB-5 implementer | Detailed spec |
| `06_integration_tests_spec.md` | Exact numerical targets, Kolb-Turner Table reproduction, Σ² decay, τ_reion pinning | LB-6 implementer | Test suite |

**All docs are self-contained**: an LLM agent can open any single spec and implement the corresponding session without cross-reading, *provided* the bass_py modules referenced in the Prerequisites section of that doc already exist.

---

## 5. Invariants that MUST hold at every session boundary

Before advancing from LB-N to LB-(N+1), verify:

1. **Full bass_py regression green** — no existing test broken
2. **New tests ≥ new LoC × 25 %** — roughly one test per 4 lines of physics code
3. **No external-code dependency introduced** — CAMB/CLASS/HyRec used only in tests (as oracles)
4. **No silent FLRW fallbacks** — if a Bianchi-type branch is not implemented, raise explicitly
5. **No gauge-fixed shortcuts** — every equation must be citeable back to an Ellis / Kolb / Baumann equation number in a comment
6. **PSTF tensors are always stored symmetric trace-free** — tested at construction and after every update
7. **No 0/0, NaN, or Inf in any integration output** — integrator must raise if it produces one

---

## 6. Success criteria for the phase as a whole

When LB-6 passes, we will have:

- A `solve_ivp` driver that takes **(Bianchi type, species set, initial conditions, η grid)** and produces the full background time-series + PSTF multipole tower up to L=8
- A regression suite that matches:
  - **z_eq = 3400 ± 50** (matter-radiation equality, from Kolb §3.5)
  - **z_* = 1089.94 ± 0.30** (last scattering, from HyRec)
  - **τ_reion = 0.0544 ± 0.0073** (Planck 2018)
  - **T_ν / T_γ = (4/11)^{1/3} ≈ 0.71377** (Kolb §5.5)
  - **Σ² ∝ a⁻⁴** for Bianchi I flat with vanishing tilt (Ellis §18.3)
  - **η_0 − η_* ≈ 14153 − 13873 Mpc** (conformal distance to CMB, CAMB reference match)
- A documentation trail where every equation in code traces back to a textbook citation

This is the **bedrock** on which §7 (matrix propagator), §9 (perturbation equations), §13 (CAMB-seed IC + tilted boost), and §14 (direction-dependent likelihood) of the lowell reference can later be built without buried ambiguities.

---

## 7. Post-LB — Full Bianchi coverage (FB) roadmap

**Status**: planning approved 2026-04-19 (user sign-off on §11 checklist of `FULL_BIANCHI_COVERAGE_PLAN.md`).

With LB-0..LB-6 bedrock green, the project pivots to **full coverage of all 11 Bianchi types × {orthogonal, tilted} = 22 configurations**. The roadmap is `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md`; the prior "post-LB A/B/C" option menu is **superseded** and absorbed as sub-phases inside FB:

| Old post-LB option | New FB home |
|---|---|
| A — Line-of-sight projection | FB-7.1 / FB-7.2 |
| B — Perturbation sector (k ≠ 0) | FB-5 (whole phase) |
| C — HTT / direction-dependent likelihood | FB-7.3 / FB-7.4 / FB-7.5 |

**FB phase summary** (35 sessions, ~7 weeks; parallelisable FB-3 ∥ FB-5):

| Phase | Sessions | Goal |
|---|---|---|
| FB-0 | 3 | Ellis convention flip + BianchiCosmology tilt fields + LB-5/6 carry-forwards |
| FB-1 | 4 | 11-type background PROVISIONAL → VALIDATED (Wainwright-Ellis match) |
| FB-2 | 4 | ∇̃ + ³R_{ab} + T4/T5/T6/T7 across all 11 types |
| FB-3 | 6 | Non-perturbative tilted sector (β, v̂_e, vorticity) |
| FB-4 | 3 | Thomson Layer B (full Lorentz kernel, E↔B mixing) |
| FB-5 | 7 | k ≠ 0 perturbation sector (CAMB seeds + tilted boost) |
| FB-6 | 3 | 22-configuration regression + P-C / CAMB literature match |
| FB-7 | 5 | C_ℓ extraction + HTT + likelihood |

Milestone gates M1..M6 sit at phase boundaries; see FB plan §8. Design decisions D1..D10 (§6 of the FB plan) have been locked at their recommended defaults:

- Frame: Pontzen-Challinor (a along axis 2, n₂=0 for Class B)
- Σ-convention: **Ellis** (`Σ² × a⁴ = const`); einstein_bianchi will flip in FB-0.1
- 11 types (not 9)
- Rapidity β (non-perturbative), no linearisation
- IX recollapse via `solve_ivp` event termination
- `k` as dimensionless eigenvalue; per-type harmonic mode dispatch (plane-wave / hyperbolic / Q-mode)
- Massive ν deferred (post-FB)
- External oracle = CAMB NPZ only (class guard preserved)
- HTT P0 triad resolved in FB-7.3 (not earlier)
- `tca_active_mask` kept compatible; tilted extension in FB-3

**Next concrete session**: FB-0.1 — Ellis convention flip. See `NEXT_SESSION_PROMPT.md §2`.
