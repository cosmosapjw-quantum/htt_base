# LB-0 — Conventions, Notation, Units, SSOT

**Session LB-0**. No code is produced. All subsequent sessions must conform to this document.

**Reading prerequisite**: none. Every symbol is defined here.

---

## Table of contents

1. Metric signature and index convention
2. 1+3 decomposition and projection tensor
3. Kinematic variables (Θ, σ_ab, ω_ab, A_a)
4. Observer congruence and frame split rule
5. PSTF tensor convention and packing
6. Species label set and canonical ordering
7. Unit system
8. Constants SSOT
9. Cross-reference table: Ellis equation ↔ bass_py module
10. Numerical precision targets
11. External-code policy
12. Glossary
13. Observer-frame layering (FB-8 placeholder)

---

## 1. Metric signature and index convention

**Signature**: `(−, +, +, +)` — Ellis convention (matches the entire Ellis/Maartens/MacCallum 2012 text and the lowell reference).

**Indices**:
- Greek `μ, ν, ρ, σ, …` — spacetime indices in {0, 1, 2, 3}
- Latin early `a, b, c, …` — abstract 4-indices
- Latin late `i, j, k, …` — spatial 3-indices in {1, 2, 3}
- `A_ℓ` shorthand for an ordered set of ℓ spatial indices `a₁ a₂ … a_ℓ` used on PSTF tensors

**Tensor operations** (in code):

| Symbol | Meaning | NumPy idiom |
|---|---|---|
| `T_ab` | general 2-tensor | `T[a, b]` |
| `T_{ab}` | symmetric: `T_{ab} = (T_ab + T_ba)/2` | `0.5 * (T + T.T)` |
| `T_{⟨ab⟩}` | symmetric trace-free: `T_{(ab)} − (1/3) T^c_c h_{ab}` | `sym_trace_free(T)` utility |
| `∇_a` | covariant derivative (4D) | abstract — manifested per context |
| `D_a` or `∇̃_a` | spatial covariant derivative projected by h_a^b | abstract |
| `T^c_c` | trace (contracted) | `np.trace(T)` |

Convention: the PSTF projection `⟨·⟩` is **always** symmetric-trace-free in 3-space unless explicitly noted as 4D.

---

## 2. 1+3 decomposition (Ellis §4.2)

Given an observer 4-velocity `u^a` normalised to `u^a u_a = −1`, spacetime decomposes as

```
g_ab = -u_a u_b + h_ab
h_ab = g_ab + u_a u_b
```

`h_ab` is the **projection tensor orthogonal to u^a**, satisfying:

- `h_ab u^b = 0`
- `h_a^b h_b^c = h_a^c` (idempotent)
- `h^a_a = 3` (projects onto 3-space)

In bass_py the canonical observer congruence is `n^a` (normal to the Bianchi hypersurface). For orthogonal Bianchi backgrounds, `u_γ^a = u_ν^a = u_c^a = u_b^a = n^a`. For tilted Bianchi, species 4-velocities differ:

```
u_(s)^a = γ_s (n^a + v_(s)^a)     where v_(s)^a n_a = 0, γ_s = (1 − v_s²)^{−1/2}
```

(This is already implemented in `bass.tilt.species_tilt.TiltedSpeciesParams`; see Y-Block.)

**`v̂_e` default — SSOT (FB02-F1 resolved, FB-3.1)**:

The tilt direction `v̂_e` is a spatial unit vector in the `n^a`-frame
tetrad basis (`e_1, e_2, e_3`). The **canonical default is the first
tetrad axis**:

```
v̂_e = (1, 0, 0)   # aligned with e_1 — the Σ_+ eigenvector (§5.4)
```

This choice is fixed by three mutually-consistent considerations:

1. **Principal-shear alignment** (§5.4): `e_1` is the axis the
   axisymmetric Bianchi shear `Σ_+` compresses/expands; aligning the
   tilt with this axis keeps the `(β, v̂_e)` + `(Σ_+, Σ_−)` problem
   axisymmetric whenever the cosmology is axisymmetric.
2. **Pontzen-Challinor frame** (bianchi_types.py): the Class-B twist
   lives in `e_2` (`a_α = (0, a_twist, 0)`), so `e_1` is the
   twist-free axis — the cleanest choice for an orthogonal `(v̂_e,
   a_α)` split.
3. **Literature convention**: King-Ellis 1973 §3 takes the tilt along
   the `x` axis; EMM 2012 §5.4 eqs (5.12)-(5.14) are written in the
   same convention.

**Cross-reference surface** — every callable / dataclass that exposes
`v̂_e` as a field or argument MUST reuse the same default constant so
that the SSOT stays single-sourced:

| Location | Field / constant | SSOT anchor |
|---|---|---|
| `bass.species.tilted.TiltedSpeciesBackground.v_hat_e` | default = `V_HAT_E_DEFAULT` | FB-3.1 wrapper (this doc) |
| `bass.species.tilted.V_HAT_E_DEFAULT` | module constant `(1, 0, 0)` | FB-3.1 SSOT |
| `bass.background.einstein_bianchi.BianchiCosmology.v_hat_e` | default = `_V_HAT_E_DEFAULT = (1, 0, 0)` | FB-0.2 |
| `bass.collision.tilted_visibility.TiltedVisibility` | stores `v_e: Callable[[η], (3,)]`; default caller supplies `(1, 0, 0)` × `v_magnitude(η)` | LB-4 Layer A |
| `bass.hierarchy.tilt_kinematics.accel_from_tilt` | reads `tilted.v_vector(η)` → inherits `V_HAT_E_DEFAULT` | FB-3.2 (shipped) |
| `bass.hierarchy.tilt_kinematics.vorticity_from_tilt` | reads `tilted.v_vector(η)` → inherits `V_HAT_E_DEFAULT`; Class B uses `StructureConstants.a_twist` | FB-3.2 (shipped) |
| FB-4 Thomson kernel Layer B | same `v̂_e` SSOT — no separate default | FB-4 (planned) |

The regression test that pins this SSOT is
`bass/species/test_tilted.py::test_T13_v_hat_default_matches_bianchi_cosmology_fb02_f1` —
it fails the instant any of the above defaults drifts from
`(1, 0, 0)`.

Non-unit `v̂_e` is explicitly invalid. `BianchiCosmology` and
`TiltedSpeciesBackground` both raise `ValueError` when
`|v̂_e|² − 1` exceeds `1e-10`, so a caller who passes a noisy
direction sees the error immediately rather than discovering a silent
renormalisation downstream.

**Frame split rule** — universal for the entire LB phase and beyond:

> **Transport is evaluated in the n^a frame. Collision and visibility are evaluated in the u_e^a frame (electron rest frame).**

This is lowell reference §1.2 and is **non-negotiable**. Transposing a collision source into the n^a frame without the proper Lorentz boost produces subtle O(v_e) errors that are invisible at FLRW but dominate in tilted Bianchi.

---

## 3. Kinematic variables (Ellis §4.2–4.3)

Decomposing the covariant gradient of u^a:

```
∇_a u_b = -u_a A_b + (1/3) Θ h_ab + σ_ab + ω_ab
```

- **Expansion** Θ = ∇_a u^a — scalar; in Bianchi cosmology Θ = 3 a'/a when u^a = n^a on FLRW slices
- **Shear** σ_ab — symmetric trace-free, orthogonal to u^a:
  - `σ_ab = D_{⟨a} u_{b⟩}` = `(1/2)(D_a u_b + D_b u_a) − (1/3) D_c u^c h_ab`
  - σ² ≡ (1/2) σ_ab σ^ab is the **scalar shear invariant** (some authors use σ² = σ_ab σ^ab without the 1/2; bass_py follows Ellis and uses the factor 1/2 convention; see §5 below)
- **Vorticity** ω_ab — antisymmetric, orthogonal to u^a; dual 3-vector ω^a = (1/2) ε^{abcd} u_b ∇_c u_d
- **4-acceleration** A^a = u^b ∇_b u^a — orthogonal to u^a by construction

**bass_py mapping**:

| Kinematic | Stored where | Convention |
|---|---|---|
| Θ | `BianchiBackgroundState.calH × 3 / a` (derived) | Θ = 3𝓗/a = 3H |
| σ_ab | `TetradBackgroundState.sigma_tensor` (3×3 STF) | Axisymmetric: (Σ_+, Σ_-) → tensor via `axisymmetric_sigma_tensor` |
| σ² invariant | `TetradBackgroundState.shear_magnitude_sq` | **Σ² = σ_ab σ^ab / 6** — matches `htt.core.bounds` |
| ω_ab | not yet stored (zero for Types I/V/VII_0 at background level) | To be added in LB-2 when Types VII_h/VIII/IX come online |
| A_a | zero at background in all current bass_py types | LB-2 will expose a hook |

---

## 4. Shear convention & normalisation — critical

### 4.1 Conformal-shear identification (Ellis SSOT, locked FB-0.1)

The **stored Bianchi shear tensor `Σ_ab` is the Ellis conformal
shear**:

```
Σ_ab  ≡  a × σ_ab
```

where `σ_ab` is the **proper-time physical shear** (Ellis §4.2.3 /
§18.3). The proper-time evolution ``σ̇_ab + Θ σ_ab = S_proper``
translates in conformal time (``prime = d/dη``, ``𝓗 = a'/a = a H``) to

```
dΣ_ab/dη  =  -2 𝓗 Σ_ab  +  𝓗² · S^{WE}(type)
```

which is the form implemented by `bass/background/einstein_bianchi.py`
and its per-type dispatch in `bass/transport/shear_sources.py`. The
dimensionless Wainwright-Ellis source ``S^{WE}`` is defined so that in
Hubble-normalised time ``τ = H t`` and with ``Σ̂ = σ/H``,
``dΣ̂/dτ = (q - 2) Σ̂ + S^{WE}(N_i, A)``.

Consequences (Type I Kasner limit):

- ``σ × a³ = const`` (Kasner invariant, physical)
- ``Σ × a² = const`` (conformal; LB-5 I-11 / LB-6-15 post-FB-0.1)
- ``Σ² × a⁴ = const`` (LB-5 I-12 / LB-6-16 post-FB-0.1)

### 4.2 Dimensionless shear scalar (Pontzen-Challinor)

For observable comparisons we use the dimensionless shear scalar:

```
Σ²  ≡  σ_ab σ^ab / (6 H²)    [dimensionless]
```

which is what `htt.core.bounds`, `comparator_policy`,
`spectrum.cl_assembly` (Route B sentinel), and
`tetrad_state.shear_magnitude_sq` use. Note this ``Σ²`` is a scalar
and is distinct from the tensor ``Σ_ab`` defined in §4.1; the symbol
clash is historical (both appear in the literature) and we resolve it
contextually — ``Σ_ab`` always means the Ellis conformal shear, ``Σ²``
(lowercase 2) always means the Pontzen-Challinor dimensionless scalar.

For an axisymmetric shear ``σ_ab σ^ab = 2 σ_+² + 2 σ_−²`` and at late
time (``H ≈ H_0 ≈ 67.36 km/s/Mpc = 2.25e-4 Mpc⁻¹`` in natural units —
see §7) the route-B sentinel ``Σ² = 10⁻⁸`` corresponds to
``σ / H ≈ 2.45 × 10⁻⁴``.

### 4.3 Conventions to avoid

- **Do not** use the alternative "Σ × a = const" convention (shipped
  pre-FB-0.1). It corresponds to tracking ``Σ_alt = a² σ`` rather
  than ``Σ = a σ``, breaking consistency with `proper_shear_at_eta`
  and downstream hierarchy T-terms.
- **Do not** use the Ellis factor-of-(1/2) ``σ² = (1/2) σ_ab σ^ab``
  scalar without converting to the Pontzen-Challinor normalisation in
  §4.2.

### 4.4 FB roadmap impact (D2 locked)

FB plan §6 D2 (Σ-convention) is locked to the Ellis choice documented
here. Any future perturbation / tilted-sector work (FB-3, FB-5) must
inherit this convention — no re-derivation required.

---

## 5. PSTF tensor convention and packing (Ellis §4.5)

### 5.1 Definition

A rank-ℓ **PSTF tensor** (Projected, Symmetric, Trace-Free) is a tensor `Π_{A_ℓ} ≡ Π_{a_1 a_2 … a_ℓ}` satisfying:

1. **Projected**: `Π_{A_ℓ} u^{a_k} = 0` for all k ∈ {1, …, ℓ}
2. **Symmetric**: invariant under any permutation of the ℓ indices
3. **Trace-free**: `h^{a_k a_m} Π_{A_ℓ} = 0` for any pair (a_k, a_m)

The number of **independent components** of a rank-ℓ PSTF 3-tensor is `2ℓ + 1` (same as spin-weighted ℓ spherical harmonics).

### 5.2 Storage — canonical packing

In bass_py LB-2, a `PSTFTensor` stores its independent components as a **NumPy array of shape (2ℓ+1,)** indexed by `m ∈ {−ℓ, …, +ℓ}` (integer offset).

```
class PSTFTensor:
    ell: int
    # components[i] corresponds to m = i - ell, for i ∈ {0, 1, …, 2ℓ}
    components: np.ndarray  # shape (2ℓ+1,), dtype float64
```

Rationale: axisymmetric Bianchi reduces to m ∈ {0, ±2} in the cl_assembly pipeline already. The (2ℓ+1,) packing matches the `bass.los.bianchi_propagator` convention and the standard spin-weighted spherical harmonic basis.

### 5.3 Alternative: full 3-tensor form

For tensor-algebra operations (products, traces, contractions) the `PSTFTensor` also exposes a `.full_tensor()` method returning the (3, 3, …, 3) — ℓ axes — symmetric trace-free NumPy array. The (2ℓ+1,) packing is the **storage** form; the full-tensor is the **algebra** form.

Conversion is handled by a **Clebsch-Gordan basis transformation** detailed in LB-2 `02_multipole_hierarchy_spec.md §3`.

### 5.4 Basis alignment

The m-basis used by PSTFTensor must align with the principal shear axis: **m=0 is aligned with the Σ_+ eigenvector** (the axis where the diagonal shear is maximally compressive/expansive). The ±2 modes are the off-axis components. This matches bass_py's `bianchi_propagator` m∈{0,±2} output.

For Bianchi IX where no distinguished axis exists, the basis is fixed by the initial shear eigenvectors and rotates adiabatically with them; LB-2 will expose a utility to track the basis rotation angle ψ(η).

---

## 6. Species label set and canonical ordering

Five species in LB-1:

| Index | Label | Symbol | w_rest | Notes |
|---|---|---|---|---|
| 0 | photon | γ | 1/3 | Blackbody, T_γ,0 = 2.7255 K |
| 1 | neutrino | ν | 1/3 (massless) | Collisionless after z_dec ≈ 10¹⁰ |
| 2 | baryon | b | 0 (c_s² → 0 at late time) | Thomson-coupled to γ via electrons |
| 3 | cold dark matter | c | 0 | Pressureless dust |
| 4 | cosmological constant | Λ | −1 | ρ_Λ constant |

**Canonical registry ordering** (γ, ν, b, c, Λ) is fixed for all LB-1+ code. Iteration order in Python dicts must preserve this.

Future extensions (out of LB scope):
- `γ_polarized` — distinguish E/B polarisation states — added at the multipole-hierarchy level, not the background level
- `ν_massive` — massive-neutrino fluid transition — triggered around z_mν ~ 200 for Σ m_ν = 0.06 eV
- `dark_radiation` — N_eff surplus — absorbed into ν as N_eff = 3.044

---

## 7. Unit system

**Natural geometric units** throughout bass_py. Specifically:

| Quantity | Unit | Symbol in code | Example |
|---|---|---|---|
| length | Mpc | `_mpc` suffix | `eta_mpc` |
| time | Mpc (conformal) | — | `η = ∫ dt / a` |
| Hubble rate | Mpc⁻¹ | `_mpc` suffix | `H_mpc = H_km_s_mpc / c_km_s` |
| energy density | ρ_crit,0 (today's critical density) | dimensionless | `rho_gamma` |
| temperature | Kelvin | `_K` suffix | `T_gamma_K` |
| mass | eV/c² | `_eV` | `m_nu_eV` |
| cross-section | Mpc² | `_mpc2` | `sigma_T_mpc2` |

**Why ρ_crit,0 normalisation**: it makes Ω_X(a) ↔ ρ_X(a) transparent, `ρ_γ(a) = Ω_γ,0 / a⁴`, `ρ_m(a) = Ω_m,0 / a³`, with today-values from `ssot.C`.

**Speed of light**: `c_km_s = 299792.458 km/s` — SSOT in `bass.spectrum.flrw_boltzmann.C_KMS` (and will be aliased into `bass.species.constants` in LB-1).

**Conformal Hubble**: `𝓗 = a H = a' / a` where prime = d/dη. In code, `calH_mpc`.

---

## 8. Constants SSOT

The single source of truth for physical constants is **`bass/htt/htt/core/ssot.py` class `C`**. LB-1 adds a thin wrapper `bass/species/constants.py` that re-exports the subset relevant to species evolution, with an invariant test verifying the re-export matches `C` to bit identity.

| Constant | Symbol | Value | Source |
|---|---|---|---|
| CMB temperature today | T_γ,0 | 2.7255 K | Fixsen 2009; `C.T0_K` |
| Neutrino-to-photon ratio | T_ν / T_γ | (4/11)^(1/3) ≈ 0.71377 | Kolb §5.5 eq (5.14) |
| Effective neutrino number | N_eff | 3.044 | Planck 2018 |
| Baryon density today | ω_b ≡ Ω_b h² | 0.02237 | Planck 2018; `ssot.C` |
| CDM density today | ω_c ≡ Ω_c h² | 0.12 | Planck 2018 |
| Matter density today | Ω_m,0 | 0.3153 | Planck 2018 |
| Dark energy today | Ω_Λ,0 | 1 − Ω_m,0 − Ω_r,0 (flat) | derived |
| Hubble today | H_0 | 67.36 km/s/Mpc | Planck 2018 |
| Radiation density today | Ω_r,0 | 9.22e-5 (incl. 3.044 massless ν) | Planck 2018 |
| Helium mass fraction | Y_He | 0.245 | BBN, Kolb Ch 4 |
| Thomson cross-section | σ_T | 6.6524587321e-29 m² | CODATA |
| Newton constant | G | 6.67430e-11 m³/(kg·s²) | CODATA |

**Derivation rules**:
- Ω_γ,0 = (π²/15) × a_rad T_γ,0⁴ / ρ_crit,0 — numerically ≈ 5.39e-5
- Ω_ν,0 (massless) = (7/8) × (4/11)^{4/3} × N_eff × Ω_γ,0 ≈ (7/8) × 0.6816 × 3.044 × Ω_γ,0 ≈ 3.83e-5
- Ω_r,0 = Ω_γ,0 + Ω_ν,0 ≈ 9.22e-5 ✓ consistent with bass_py `flrw_cosmology`

---

## 9. Cross-reference table: Ellis equation ↔ bass_py module

| Ellis § | Equation / concept | Implemented in |
|---|---|---|
| §4.2 | 1+3 decomposition, Θ, σ_ab, ω_ab | `bass.background.einstein_bianchi` (FLRW limit + 10-type) |
| §4.5 | Moment expansion of distribution function | LB-2 `bass.hierarchy.pstf_tensor` (new) |
| §4.6 | Multipole hierarchy equations | LB-2 `bass.hierarchy.hierarchy_rhs` (new) |
| §5.1 | Perfect fluid T_ab | `bass.tilt.species_tilt.decompose_tilted_species` (Y-Block) |
| §5.2 | Non-perfect T_ab = ρuu + ph + 2q(_a u_b) + π_ab | `bass.tilt.species_tilt` (Y-Block) |
| §5.3 | Continuity + momentum equations | LB-1 `bass.species.*` (new) |
| §5.5 | Thomson scattering tensor | LB-4 `bass.collision.thomson_pstf` (extend existing) |
| §6.2 | Raychaudhuri | `bass.background.einstein_bianchi` (implicit in ODE) |
| §6.3 | Shear propagation | `bass.background.einstein_bianchi._hubble_squared` + `shear_sources` |
| §6.4 | Vorticity propagation | `bass.background.nonperturbative_tilt.rhs_bianchi` (orthogonal) |
| §6.5 | Raychaudhuri + constraints | implicit |
| §18.1 | Bianchi classification | `bass.background.bianchi_types` |
| §18.2 | Tetrad formalism, structure constants | `bass.background.bianchi_types.StructureConstants` |
| §18.3 | Class A / Class B evolution | dispatch in `bass.background.einstein_bianchi` |
| §18.4 | Exact Bianchi hierarchy (adapted) | LB-2 (new) |
| lowell §10 | Quadrupole TCA | `bass.closure.quadrupole_tca` (W6-04) + Y-Block cross-check |

---

## 10. Numerical precision targets

| Quantity | Tolerance | Rationale |
|---|---|---|
| η grid spacing | Δη / η ≲ 10⁻³ at recombination | captures g(η) width ~80 Mpc / η_* ~ 14000 Mpc |
| Background integration (a, H) | rtol=1e-10, atol=1e-14 | sufficient for FLRW BI shear decay test |
| Species continuity residual | < 10⁻¹² | |ρ̇_s + Θ(ρ_s+p_s)| / Θ ρ_s |
| Total Friedmann constraint | < 10⁻⁸ | Σ Ω_s + Σ² − W² + Ω_k − 1 |
| Hierarchy truncation at L=6 | Π_{ℓ=7} / Π_{ℓ=2} < 10⁻³ (FLRW) | truncation cost |
| TCA residual at Γ_T ≫ H | < 10⁻⁴ of source | Y-Block TCA test already pins this |
| Kolb thermal history table match | < 5 % on z_eq, < 0.03 % on z_*, < 2 % on τ_reion | matching to standard values |

---

## 11. External-code policy

**Hard rule**: external cosmology codes (CAMB, CLASS, AniCLASS, HyRec, RECFAST, class_sz, camb_ini_ext, …) may appear only in:

1. `scripts/generate_*_reference.py` producing oracle files under `data/`
2. `*_test.py` files that *compare* bass_py output to an oracle
3. `bass/recombination/fixtures/` (HyRec-generated recombination table — pre-computed, read-only)

They may NOT appear in:

- `bass/**/*.py` (production code)
- `tsc/**/*.py` (diagnostics)
- `htt/htt/**/*.py` (inference) — even via stubbed imports

**Enforcement**: a regression test `bass.validation.test_external_code_policy` greps imports and raises if any forbidden import is found in production code. This test must be added in LB-0 as a no-code deliverable (it's a *guarding* test, not a physics test).

---

## 12. Glossary

## 13. Observer-frame layering (FB-8 placeholder)

FB-8 introduces an **observer-frame** layer on top of the already
audited FB-7 cosmological-frame likelihood stack. The following rules
are SSOT for that layer:

- **Type distinction is load-bearing**:
  `(beta_cosmo, v_hat_cosmo)` and `(beta_obs, v_hat_obs)` are separate
  surfaces with separate ownership. They must not inherit from each
  other and must not be silently coerced into a shared runtime carrier.
- **Rapidity convention is shared, not the type**:
  the future `GlobalTilt` and the FB-8 `ObserverBoost` both use
  non-negative rapidity as the decision-level scalar, with the sign of
  the motion living in the direction vector. This inherits the FB-3.5
  rapidity/admissibility SSOT.
- **Composition order is pinned**:
  cosmological-frame tilt is applied first, then observer-frame boost:

  ```text
  cosmological tilt -> observer boost
  ```

- **Production path**:
  observer-frame likelihood composition happens in
  `bass.likelihood.observer_frame_adapter`, which wraps the FB-7
  cosmological-frame likelihood. The diagnostic helper
  `bass.observer.compose_tilts` is not a production surface.

This section is a documentation placeholder only during FB-META-8. The
rendered observer-frame gallery outputs are deferred until the phase
ships physics rather than skeletons.

| Term | Definition |
|---|---|
| PSTF | Projected Symmetric Trace-Free tensor (Ellis §4.5) |
| 1+3 split | Decomposition of spacetime into time (u^a) + space (h_ab) |
| Covariant / GIC | Gauge-Invariant Covariant — no coordinate system is invoked |
| Tetrad | Orthonormal basis {e_0, e_1, e_2, e_3} adapted to u^a |
| `A_ℓ` | Ordered set of ℓ spatial tetrad indices (shorthand notation) |
| TCA | Tight Coupling Approximation — algebraic closure in the Γ_T ≫ H regime |
| Route B | Michaelis-Menten lookup D_2(Σ²) sentinel used for regression (W10-01) |
| SSOT | Single Source of Truth — `ssot.C` class |
| oracle | external code used for validation only, never for science |
| Σ² | dimensionless shear, σ_ab σ^ab / (6 H²) |
| 𝓗 | conformal Hubble, a'/a where prime = d/dη |
| Θ | expansion scalar, ∇_a u^a = 3 a'/a at FLRW |
| T_ν | neutrino temperature, (4/11)^{1/3} T_γ after e⁺e⁻ annihilation |
| z_eq | matter-radiation equality redshift, ~3400 |
| z_* | last-scattering redshift, 1089.94 |
| τ_reion | optical depth through reionization, 0.0544 |

---

## 13. Implementation checklist for LB-0

- [x] Write `docs/lowell_bianchi/README.md`
- [x] Write `docs/lowell_bianchi/00_conventions.md` (this file)
- [ ] Add `bass/validation/test_external_code_policy.py` enforcing §11 — one small test, guards all future sessions
- [ ] Commit as `LB-0: conventions and reading guide` — no physics code

When LB-0 is committed, LB-1 can begin.
