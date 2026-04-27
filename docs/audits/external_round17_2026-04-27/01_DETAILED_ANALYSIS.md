# BASS Phase-1 Closure — Detailed Self-Contained Analysis
**Date:** 2026-04-27.   **Branch / commit:** `main` @ `02cb6c0`.   **Status:** Round-17 P2 (post-measurement).
**Audience:** External technical reader who has *no* prior context on this codebase.

---

## Abstract

BASS (Bianchi Anisotropy Solver) is a dual-implementation cosmology code that computes CMB temperature/E/B power spectra for FLRW and the eight non-trivial Bianchi homogeneous anisotropic backgrounds (types I, II, III, IV, V, VI₀, VI_h, VII₀, VII_h, VIII, IX). The codebase has two parallel computation paths: a 7363-line Rust path (`bass_rs/src/sync_gauge_camb.rs`) that follows Ma–Bertschinger 1995 in synchronous gauge and currently produces the production anchor `D_2 = 1002.086744 μK²` for FLRW Planck-2018; and a Python "PSTF primary" path that reformulates the same physics in 1+3 covariant tetrad / PSTF form so it can be naturally extended to anisotropic backgrounds. The Phase-1 goal is for the Python PSTF path to **bit-reproduce** the Rust anchor, at which point the Rust path is retired and the Python path becomes production. Phase 1 is currently **50.8% complete**. The Python PSTF canonical entry point produces `D_2 = 2.04 × 10¹⁰ μK²` (a 7-orders-of-magnitude gap), and the Python PSTF linear-probe entry point — which disables a spurious `max(|Σ_±|, 1e-6) = 1e-6` floor that boosts |α|² by ~10¹² — produces `D_2 = 6.4395 × 10³ μK²` (a 6.43× residual). Three audit cycles (10 external auditor verdicts, Rounds 12–14) plus 6 internal investigation rounds have triangulated the residual to a single architectural defect (**D-2**: the Lowell §13.2 leading-order adiabatic seed, valid only for `x = k·η_init ≪ 1`, is being applied at `η_init ≈ 261 Mpc` where over half the Planck-relevant k-grid sits in `x > 1` invalid territory). The closure path is to push the integrator's initial conformal time back to `z ≈ 10⁹` using the conditional inline DAE-relaxation already implemented at `htt/bass/hierarchy/integrator.py:434–498`. This is multi-month work. No simple multiplicative calibration factor closes the gap — Round-14 finding F1 measured per-(k, ℓ) std/|mean| 108–357% across all candidate factors.

---

## Part I — Project & Physics Context

### 1. Project: BASS / Bianchi Anisotropy Solver

BASS is the computational engine of a PhD thesis ("Tetrad-Based Departure Decomposition for FLRW Departure in Bianchi Anisotropic Cosmologies", Soongsil OMEG Institute) that proposes a master "departure identity"

```
x_C  =  Σ²_std  −  W²_std  +  Ω_tilt  +  Ω_{k,aniso}                        (1)
```

where each term has an exact 1+3-covariant operational definition. The thesis claim is that empirically `ln B(FLRW_tilt) = +26.40` and `β = 1.36 × 10⁻³` against Planck — i.e., a tilted FLRW background fits Planck better than untilted FLRW by ~26 e-folds of evidence. Production "anchors" the audit will encounter: Bayes-factor `F_Bayes = 0.093 ± 0.025`, gallery sentinel `D_2(Σ² = 10⁻⁸) = 0.174112 μK²`, and the FLRW reference `D_2 = 1002.086744 μK²` that this audit is about.

The project ships both a paper (`docs/manuscript/main.tex`, 12 chapters + appendices) and the BASS solver. The solver's job is to compute the second-rank object `C_ℓ^XY` for X, Y ∈ {T, E, B} given a Bianchi background and a Planck-2018 cosmology. The paper consumes `D_ℓ = ℓ(ℓ+1)/(2π) C_ℓ T_CMB²` from the solver; the solver in turn consumes a primordial curvature power spectrum `P_R(k)` and a kinematic / dynamic background description.

### 2. The physics being computed

The CMB anisotropy in linear perturbation theory is

```
Δ_T(n̂) / T_CMB  =  ∫ dη  e^{ik·n̂(η_0 − η)}  S_T(k, η)                     (2)
```

where `S_T(k, η)` is a "source" assembled from the photon distribution function's first three moments (Sachs–Wolfe term `Θ_0 + Ψ`, Doppler `(g v_b)′`, polarization quadrupole `polter = 2Θ_2/5 + 3E_2/5`) weighted by the recombination visibility `g(η)`. Decomposing onto spherical harmonics, integrating against `j_ℓ(k(η_0 − η))` (the line-of-sight kernel), and convolving with the primordial power gives

```
C_ℓ^TT  =  4π  ∫ d(ln k)  P_R(k)  |Δ_ℓ^T(k)|²,                              (3a)
P_R(k)  =  A_s · (k / k_pivot)^{n_s − 1}                                     (3b)
```

with Planck-2018 baseline `A_s = 2.1 × 10⁻⁹`, `n_s = 0.9649`, `k_pivot = 0.05 Mpc⁻¹`, `T_CMB = 2.72548 K` (Fixsen 2009). Eq. (3a) is encoded at `htt/bass/spectrum/cl_assembly.py:218` (`assemble_cl_TT_isotropic`). The transfer function `Δ_ℓ^T(k)` is produced by line-of-sight projection of `S_T(k, η)` onto `j_ℓ(k(η_0 − η))`; the source `S_T` is produced by extracting moments `(Θ_0, Θ_2, E_2, v_b)` from the IMEX integrator's evolved state at every η in the LoS quadrature grid.

For Bianchi backgrounds the perturbation theory uses the 1+3 covariant tetrad–PSTF framework (Maartens–Ellis–Stoeger; Ellis–van Elst; Lewis–Challinor) with hierarchy `I_{A_ℓ}` indexed by symmetric trace-free tensors. In FLRW this collapses to the standard m=0 sector of the spin-weighted decomposition. The Python PSTF code is the m=0 sector evolved as if it were the full tetrad-PSTF object, which reproduces FLRW exactly when `Σ_± = 0` and the Bianchi shear modes decouple from the m=0 channel.

### 3. Two computational paths

The codebase implements the same perturbation theory twice on purpose:

| Aspect | Rust path | Python "PSTF primary" path |
|---|---|---|
| File | `bass_rs/src/sync_gauge_camb.rs` (7363 lines) | `htt/bass/spectrum/flrw_pipeline.py` + ~20 modules |
| Gauge | Synchronous (CAMB convention) | Tetrad-PSTF (gauge-fixed at the tetrad level, which is operationally Newtonian-gauge-equivalent for ℓ ≥ 1) |
| ODE solver | Rodas5P (Rosenbrock 5th-order) | IMEX ARK4(3)6L[2]SA (Kennedy–Carpenter additive Runge–Kutta) |
| Background | Pre-tabulated η-grid with HYREC visibility | Pre-tabulated η-grid with HYREC visibility (shared `SpeciesBackgroundRegistry`) |
| LoS projection | Pre-tabulated `j_ℓ(x)` lookup table | `scipy.special.spherical_jn` per-call, k-adapted η-grid (Round-15 P0) |
| FLRW D_2 output | **1002.086744 μK²** (anchor) | 2.04 × 10¹⁰ μK² (canonical) / 6.44 × 10³ μK² (linear-probe) |
| Bianchi extension | Only Bianchi I, axisymmetric | All 11 backgrounds at primitive level (Round-16); axis-aligned only for off-Type-I families |

The Phase-1 goal is for the Python path to bit-reproduce the Rust path's `D_2 = 1002.086744 μK²` to within 1 × 10⁻⁹ fractional tolerance (≈ 1 × 10⁻⁶ μK² absolute). When this happens, `htt/bass/spectrum/test_d2_pstf_closure.py` (currently `xfail("PR-024c open")`) flips to `xpass`, the xfail marker is removed, and PR-026 retires the Rust path.

### 4. Why the dual-track architecture exists

Two independent reasons:

1. **Audit and oracle separation.** The Rust path was built first as a regression-armored production anchor. Having two completely independent implementations of the same physics gives a cross-check at every numerical decimal — if the two paths converge to the same `D_2` to 1 × 10⁻⁹, that is the strongest possible evidence that no implementation defect remains.
2. **Anisotropic extension.** The Python PSTF formulation generalizes naturally to all 11 Bianchi backgrounds; the Rust sync-gauge formulation does not. Round-16 (2026-04-26) landed 14 PRs of Bianchi primitives (PR-S1 through S14) that wire up the off-axis machinery for class-A and class-B families. These primitives evolve `m ∈ {-2, …, +2}` mode-mixing blocks rather than the FLRW-only `m = 0` slice. Off-axis modes for non-Type-I families are scope-limited (`OutOfScopeError` upstream of `make_nabla_tilde`) until the state-layout migration `m=0 → m∈{-2..+2}` is complete (3–5 days of work, blocked behind D-2 in current planning).

---

## Part II — Pipeline Anatomy

### 5. End-to-end pipeline (FLRW limit)

The Python pipeline produces `D_ℓ` in five sequential stages plus an optional bias-subtraction wrapper:

```
            (Planck-2018 species registry)
                       │
                       ▼
            ┌─────────────────────────┐
            │ build IMEX integrator    │   ⇐  cosmological_config.py
            │ η_initial = η(z_*) − 20  │      η_init ≈ 261 Mpc, η_today ≈ 14147 Mpc
            └─────────────────────────┘
                       │
                       ▼  (per-k, parallel via ProcessPoolExecutor)
            ┌─────────────────────────┐
            │ Lowell §13.2 seed at η_init │   ⇐  regular_adiabatic_ic.py::_seed_formulae
            │ Φ, Ψ, Θ_0, Θ_1, π_ν, …       │      ←★ THIS IS WHERE D-2 LIVES
            └─────────────────────────┘
                       │
                       ▼
            ┌─────────────────────────┐
            │ IMEX evolution η_init→η_today│  ⇐  imex_ark4.py + integrator.py
            │ (a, Σ_+, Σ_-, photon_T,     │      with conditional inline TCA at ℓ=2
            │  photon_E, ν_reduced)        │      (integrator.py:434-498)
            └─────────────────────────┘
                       │
                       ▼
            ┌─────────────────────────┐
            │ Source extraction        │   ⇐  tier_b_source_extraction.py
            │ Θ_0, Θ_2, E_2, v_b →     │      ←  D-3 lives here (gauge mismatch)
            │ S_T, S_E                 │
            └─────────────────────────┘
                       │
                       ▼
            ┌─────────────────────────┐
            │ Build per-k LoS η-grid   │   ⇐  los_grid_builder.py (Round-15 P0 closed D-1)
            │ Zone1 (Δη=2.4 Mpc) +     │
            │ Zone2 (Δη=2π/k/8)        │
            └─────────────────────────┘
                       │
                       ▼
            ┌─────────────────────────┐
            │ Project S × j_ℓ(k(η₀-η))→│   ⇐  flrw_bessel_projector.py
            │ Δ_ℓ^T(k), Δ_ℓ^E(k)       │
            └─────────────────────────┘
                       │
                       ▼  (collect over k)
            ┌─────────────────────────┐
            │ Assemble C_ℓ:            │   ⇐  cl_assembly.py
            │ C_ℓ = 4π ∫dlnk P_R(k)|α|²│
            └─────────────────────────┘
                       │
                       ▼
            ┌─────────────────────────┐
            │ D_ℓ = ℓ(ℓ+1)/(2π) C_ℓ ·  │   ⇐  cl_assembly.py::compute_dl
            │       T_CMB²              │
            └─────────────────────────┘
                       │
                       ▼
            D_2 ≈ 1002 μK² (target)  /  6.44 × 10³ μK² (current linear-probe)
                                      /  2.04 × 10¹⁰ μK² (current canonical)
```

Each block is described in detail in §§7–11 below.

### 6. Two entry points and three toggles

**Canonical entry point** (`htt/bass/spectrum/flrw_pipeline.py:1136`):

```python
def compute_flrw_d_ell(species, *, k_grid_mpc, pipeline_config=None,
                       assembly_config=None, n_workers=None,
                       bianchi_type="I") -> dict[str, Any]:
```

Returns the bundle `{"d_tt": ndarray, "d_ee": ndarray, "cl_tt": …, "cl_ee": …, "k_grid_mpc": …, "transfer_functions": list, "assembly_config": …}`.

**Linear-probe entry point** (`htt/bass/spectrum/flrw_pipeline.py:1171`):

```python
def compute_flrw_d_ell_linear_probe(species, *, k_grid_mpc,
                                    pipeline_config=None,
                                    assembly_config=None,
                                    probe_b_k_sq=1.0,
                                    calibration_factor=1.0,
                                    n_workers=None,
                                    bianchi_type="I") -> dict[str, Any]:
```

This wrapper internally **forces** three pipeline-config overrides (`flrw_pipeline.py:1288–1294`):

```python
probe_cfg = _dc_replace(
    base_cfg,
    primordial_b_k_sq=float(probe_b_k_sq),
    primordial_b_k_sq_fn=None,
    bias_subtraction=True,
    unit_amplitude_normalization=False,
)
```

The three toggles are:

- **`primordial_b_k_sq`** *(float, default 1.0; documented at `flrw_pipeline.py:143–158`)*. The **linear** primordial curvature amplitude `C ≈ ζ` of the Lowell §13.2 regular-adiabatic seed (Ma–Bertschinger 1995 §7 eq. 96; Lewis–Challinor 2002 App. C). Despite the historical `_sq` suffix (which dates to a CAMB-Notes geometric `β² = 1` convention in flat FLRW), every leading-order seed perturbation enters this parameter linearly — confirmed by 4 external Round-12 audits (2026-04-25). **Do NOT pass `A_s × (k/k_pivot)^(n_s-1)` here**: that `~ 2.1 × 10⁻⁹` value is the *variance* `P_R(k) = ⟨ζ²⟩`, and the `compute_flrw_*` pipeline pairs the unit-amplitude transfer with `P_R(k)` exactly once at C_ℓ assembly per eq. (3a).
- **`bias_subtraction`** *(bool, default False)*. When `True`, every k triggers two parallel solver runs (one at `b_k_sq = 0`, one at `b_k_sq = primordial_b_k_sq`); the pipeline returns `Δ_pure = Δ_target − Δ_bias`. Round-9 §5d (`docs/V5_ROUND9_FINDINGS.md`) located the bias source: the Lowell `_seed_formulae` populates `π_ν` and `G_3` *with the same `B_K_sq` factor as everything else*, but those moments are used as a constant offset by the IMEX evolution — the bias-floor is the response of the IMEX hierarchy to the amplitude-independent component of the seed. Bias-subtraction recovers the linear-in-amplitude response cleanly.
- **`unit_amplitude_normalization`** *(bool, default True)*. When `True`, every k's transfer function is divided by the seed-amplitude proxy `seed_amp = max(|Σ_±|, 1e-6)`. **In the FLRW limit `Σ_± = 0`, this floor pins `seed_amp` to `1e-6` regardless of the actual primordial amplitude**. Multiplying α by `1 / 1e-6 = 1e+6` and `|α|²` by `1e+12` is exactly the "two orders" scaling that the canonical-vs-linear-probe gap (2.04 × 10¹⁰ μK² vs 6.44 × 10³ μK²) shows.

Together these three toggles partition the configuration space into four regimes (§15 Table 4 below).

### 7. The Boltzmann hierarchy state vector

The IMEX integrator (`htt/bass/integration/imex_ark4.py` + `htt/bass/hierarchy/integrator.py`) evolves the packed state

```
state = (a, Σ_+, Σ_-, photon_T[L_max], photon_E[L_max], neutrino_reduced[4])
```

over `η ∈ [η_init, η_today]` ≈ `[261, 14147] Mpc` (`htt/bass/runtime/cosmological_config.py:77–148`). For the `test_d2_pstf_closure.py` standard configuration `L_max_tower = 8`, `ell_max_transfer = 8`, and `n_output = 64`. `photon_T` and `photon_E` are 1+3 covariant tetrad-PSTF tensors of rank ℓ ≤ L_max; in the m=0 slice they collapse onto the standard MB-95 tower. `neutrino_reduced` is a 4-vector `(δ_ν, θ_ν, π_ν, G_3)` because the massless free-streaming neutrino tower truncates at ℓ = 3 in the Lowell §13.2 leading-order asymptotic.

The IMEX equations in compact form:

```
M(η) U′(η)  =  f^E(η, U)  +  f^I(η, U)                                       (4)
```

where `f^E` is explicit (free-streaming `k · transport(T_{ℓ-1}, T_{ℓ+1})`, mode-mixing in Bianchi cases, metric back-reaction) and `f^I` is implicit (Thomson `−γ_T T_ℓ`, conditional TCA-relaxation at ℓ=2 m=0; see §11). The mass matrix `M(η)` is non-identity in non-trivial Bianchi backgrounds and identity in FLRW. The Kennedy–Carpenter ARK4(3)6L[2]SA stages are implemented at `htt/bass/integration/imex_ark4.py`.

The cosmological-range stability of this IMEX was a Round-14/15 blocker, closed by 8 patches (`docs/V5_RUNTIME_TRACK_DIAGNOSIS.md`) that brought `λ_max(A_right)` from `+0.175 / Mpc` down to `~ 4 × 10⁻¹⁶ / Mpc` (machine precision). Cosmological η = 261 → 14147 Mpc IMEX integration completes in 130 s on a single worker at `L_max = 4` and ~45 s/k at `L_max = 8`.

### 8. The Lowell §13.2 leading-order adiabatic seed

`htt/bass/perturbation/regular_adiabatic_ic.py::_seed_formulae` (lines 104–209) is the analytic IC. It returns a dict with all leading-order quantities at `η = η_init`:

```python
def _seed_formulae(*, k_comoving, eta_initial, a_initial, b_k_sq=1.0):
    R_nu     = constants.Omega_nu_0 / constants.Omega_r_0
    omega    = constants.H0_mpc * constants.Omega_m_0 / sqrt(constants.Omega_r_0)
    x        = k_comoving * eta_initial
    x2, x3   = x*x, x2*x
    denom    = 4*R_nu + 15
    amp      = b_k_sq

    eta_cov     = 2 * amp * (1 - x2/12 * (1 - 10/denom))
    delta_gamma = (amp/3)  * x2 - (amp/15) * omega * k**2 * eta_initial**3
    delta_b     = (amp/4)  * x2 - (amp/20) * omega * k**2 * eta_initial**3
    theta_gamma = (amp/27) * x3
    theta_nu    = (amp/27) * (4*R_nu + 23)/denom * x3
    pi_nu       = -amp * (4 / (3 * denom))  * x2          # note: ≠ 0 even at amp=0 in legacy
    G_3         = -amp * (4 / (21 * denom)) * x3          # before R10/R11 fix
    Z           = -(amp/2) * k * eta_init + (3*amp/20) * omega * k * eta_init**2

    tau_c    = 0.15 * eta_init / sqrt(a_init)              # heuristic radiation-era τ_c
    pi_gamma = -(32/45) * k * tau_c * theta_gamma
    E_2      = 0.25 * pi_gamma
```

These are the **leading-order** terms in the Lowell §13.2 expansion, which is asymptotic in `x = k · η_init`. The higher-order corrections are O(x⁴) in `δ_γ, δ_b`; O(x⁵) in `θ_γ, θ_ν`; O(x⁴) in `π_ν, G_3`. The expansion converges only for `x ≪ 1`. **At η_init = 261 Mpc the validity boundary is k ≈ 4 × 10⁻³ Mpc⁻¹** (Table 5 below). The k-grid the closure regression test uses (`np.logspace(-4.0, -1.5, 65)`) spans `x ∈ [0.026, 8.25]` — over half the points are in the catastrophic `x > 1` region, where O(x²) corrections to the leading O(x²) seed are themselves of the same order.

### 9. The line-of-sight projector and the closed D-1 defect

The LoS quadrature

```
Δ_ℓ^T(k)  =  ∫_{η_init}^{η_today} dη  S_T(k, η)  j_ℓ(k(η_0 − η))            (5)
```

was historically computed on the IMEX integrator's output η-grid (uniform-linear, 64 points over [261, 14147] Mpc, `Δη ≈ 220 Mpc`). Two scales are catastrophically aliased on this grid:

| Scale | Width | 220-Mpc samples per scale |
|---|---|---|
| Recombination visibility g(η) FWHM | 19 Mpc | **0.09** (one grid point lands inside it; everywhere else the visibility is captured at zero) |
| Bessel period `2π / k` at `k = 0.05 / Mpc` | 125 Mpc | **0.57** (well below Nyquist 2; the trapezoidal rule aliases the oscillation) |

The Round-15 §10 decisive test (`scripts/v5_round15_decisive_los_test.py`) fed *perfect* CAMB-Newtonian-gauge sources through the existing 64-point grid + projector and observed: 0/12 cells within 5% of CAMB direct, 4/12 sign-flipped, median |ratio| 8.30, max 3687 — confirming the LoS grid was the dominant defect ("Case D").

The Round-15 P0 fix (closed 2026-04-25) introduced `htt/bass/los/los_grid_builder.py::build_los_grid`, a per-k composite grid:

- **Zone 1** (recombination-refined): `[η_init, recomb_eta + 5·recomb_fwhm] = [η_init, ≈ 376 Mpc]` with `Δη = recomb_fwhm / n_per_recomb_fwhm ≈ 19/8 = 2.4 Mpc`. Captures the visibility peak with ~8 samples per FWHM.
- **Zone 2** (k-adapted oscillation band): `[Zone1_end, η_today]` with `Δη = (2π / k) / n_per_oscillation = period / 8`. Nyquist-resolves the Bessel kernel at every k.

Post-fix metrics: median |ratio| 8.30 → 1.00; max 3687 → 266; resolution-independent. Concrete cell improvement at the dominant `k=10⁻³, ℓ=2` mode: pre-fix `+0.651` vs CAMB `+4.54 × 10⁻²` (×14 over); post-fix `+1.28 × 10⁻³` (×0.03 under). The new module passes 30 unit tests (`htt/bass/los/test_los_grid_builder.py`).

**D-1 is closed.** The remaining 6.43× is *not* a quadrature defect — see §13.

### 10. C_ℓ assembly

`htt/bass/spectrum/cl_assembly.py` consumes a `BianchiTransferFunctions` callable (a `k → (Δ_ℓ^T, Δ_ℓ^E)` lookup) and integrates eq. (3a) on the user-supplied k-grid. The default Planck-2018 baseline is `A_s = 2.1 × 10⁻⁹`, `n_s = 0.9649`, `k_pivot = 0.05 Mpc⁻¹`, `T_CMB = 2.72548 K`. Trapezoid (`O(Δlnk²)`) and Simpson (`O(Δlnk⁴)`, requires odd-length grid) quadratures are both supported. The `test_d2_pstf_closure.py` standard configuration uses Simpson on an odd-length grid (`np.logspace(-4.0, -1.5, 65)`).

### 11. The conditional inline DAE-relaxation (the permitted TCA mechanism)

Once `Γ_T / H ≫ 1` in the radiation-dominated era, the photon quadrupole `Π_2` is algebraically slaved to its Thomson-collision steady state. A correct integrator either evolves the full Boltzmann hierarchy through this regime (numerically expensive — `Γ_T` ~ 10²·H requires extremely small steps) or pins `Π_2` to its algebraic value. BASS uses the second strategy *conditionally inline* in the IMEX RHS (`htt/bass/hierarchy/integrator.py:434–498`):

```python
# (5) Optional TCA dispatch at ℓ=2 m=0
tca_active = False
if isinstance(aux_state.closure, TCAClosure) and Gamma_T > 0.0:
    H_local = aux_state.H_local_at(eta)
    if H_local > 0.0 and Gamma_T / H_local > aux_state.gamma_T_over_H_threshold:
        tca_active = True
        # Compute the non-collision sources at ℓ=2 m=0
        rhs_T_free = hierarchy_rhs_photon(eta, state.photon_T.as_flat(), …,
                                          collision=ZeroCollisionOperator())
        rhs_E_free = hierarchy_rhs_photon(eta, state.photon_E.E.as_flat(), …,
                                          collision=ZeroCollisionOperator())
        slot   = _ell2_m0_slot_offset(L_max)
        a_val  = aux_state.a_at(eta)
        S_T_src = float(rhs_T_free[slot]) / a_val * (-1.0)
        S_E_src = float(rhs_E_free[slot]) / a_val * (-1.0)
        theta_2_alg, E_2_alg = _algebraic_tca_scalars(closure=…, S_T=S_T_src,
                                                     S_E=S_E_src, Gamma_T=…,
                                                     H_local=…)
        current_Pi2 = float(state.photon_T.tensors[2].components[2])
        current_E2  = float(state.photon_E.E.tensors[2].components[2])
        relax_rate = a_val * float(Gamma_T)
        rhs_T[slot] = -relax_rate * (current_Pi2 - theta_2_alg)
        rhs_E[slot] = -relax_rate * (current_E2  - E_2_alg)
```

The relaxation rate `a · Γ_T` collapses any gap `(Π_2 − Π_2,alg)` in `~ 1 / Γ_T`, but the ODE is integrated throughout — the hierarchy is **never replaced** by an analytic solution. This distinguishes the conditional inline DAE-relaxation from a "TCA pre-phase" (forbidden per `CLAUDE.md §6` and the project's "approximation-free truth engine" mandate). The smoothness of the switch is enforced by `htt/bass/hierarchy/test_tca_switch_smoothness.py`.

This mechanism is **load-bearing for the D-2 closure plan**: pushing `η_init` back to `z ≈ 10⁹` puts the integrator deep into the radiation-dominated tightly-coupled regime, where without DAE-relaxation the IMEX would either take ~10⁹ steps or fail. With DAE-relaxation it should pin Π_2 algebraically and free-stream the surviving lower-ℓ moments. See §29 for the full plan.

---

## Part III — The Failure: Where, When, Why, How

### 12. The 7-orders-of-magnitude canonical-path gap

```
canonical compute_flrw_d_ell:    D_2 = 2.0451 × 10¹⁰ μK²
                                       ↑ gap +2.04 × 10¹⁰ vs anchor (×2.04 × 10⁷)
linear-probe:                    D_2 = 6.4395 × 10³ μK²
                                       ↑ gap +5.4 × 10³  vs anchor (×6.43)
Rust MB-95 anchor:               D_2 = 1002.086744 μK²
```

The 6.4-order-of-magnitude jump from canonical to linear-probe is **cleanly attributable to one mechanism**: disabling the spurious 1e-6 floor that `unit_amplitude_normalization=True` applies in the FLRW limit.

The mechanism's algebra: when `Σ_± = 0` (FLRW), `seed_amp = max(|Σ_±|, 1e-6) = 1e-6`. The transfer function is divided by `seed_amp`, so each entry is multiplied by `1 / 1e-6 = 10⁶`. C_ℓ is `|α|²`-quadratic, so the assembly multiplies by `10¹²`. The ratio of the two paths is `2.04 × 10¹⁰ / 6.44 × 10³ ≈ 3.2 × 10⁶` — a half-decade smaller than the naive `10¹²` because the linear-probe path also bias-subtracts (which removes the `O(10⁻³)` ν-floor that the canonical path leaves in). The order-of-magnitude consistency is decisive: **the canonical-path gap is the 1e-6 floor, end of analysis**. PR-S13 sub-track (a) "primordial-amplitude alignment" reduces to either (i) switching the canonical entry point's default to invoke the linear-probe path, or (ii) disabling the floor in the canonical path directly.

### 13. The 6.43× linear-probe residual: triangulation to D-2

The remaining 6.43× residual is **not** a single missing convention factor. The Round-12-14 audit cycles tried four candidates (4√2 = `√(32)` PSTF normalization; n_output increase; k_min clipping; Doppler resampling) plus three internal Phase-A/B-fix diagnostics, with 10 external auditor verdicts across two rounds. **All four candidates were refuted** by Round-14 finding F1 (per-(k, ℓ) std/|mean| 108–357% across all candidate factors — i.e. the residual is k- and ℓ-dependent in a way no scalar correction can cancel). What was left was three architectural defects:

- **D-1 (CLOSED Round-15 P0)**: IMEX/LoS grid conflation. Fix landed `htt/bass/los/los_grid_builder.py`. See §9.
- **D-2 (OPEN, multi-month)**: Lowell seed validity range. The Lowell §13.2 leading-order expansion in `_seed_formulae` is valid only for `x = k · η_init ≪ 1`; at η_init = 261 Mpc the validity boundary is `k ≈ 4 × 10⁻³ Mpc⁻¹`, so over half the closure-test k-grid is in catastrophic territory.
- **D-3 (OPEN, sub-week, not yet started)**: Synchronous/Newtonian gauge mismatch in the source extractor (`tier_b_source_extraction.py:225`).

The 117× improvement R12-14 → R17 (`7.57 × 10² → 6.43`) came principally from D-1 closure plus the linear-probe wrapper plus 8 IMEX-stability patches. The remaining 6.43 has the D-2 signature: the IMEX integrator faithfully evolves wrongly-seeded sub-horizon modes forward, over-amplifying `Φ, Ψ, Θ_0` at recombination. This is the only defect of the three that can produce a residual that has the observed per-(k, ℓ) variance pattern, because the seed error itself is per-(k) (driven by `x = k · η_init`).

### 14. Why no simple calibration factor closes the gap (R12-14 consensus)

Round-9 §6 already showed the residual is N_k-dependent (N_k = 4 → 12 → 24 produced ratios `2.93 × 10⁴ → 1.70 × 10⁴ → 1.36 × 10⁴`) and probe-amplitude-dependent (factor 2 across `b_k_sq ∈ {1.0, 0.01}`). No single multiplicative constant has both N_k and probe-amplitude dependencies. Three further audit cycles searching for one is enough; the avenue is closed.

The 4√2 candidate is illustrative. Codex's Round-13 hypothesis was that a missing PSTF normalization `√(32) = 4√2 ≈ 5.66` would explain `(7.57e+2 / (4√2)²) ≈ 23.6 ≈ unity`. Initial Phase B-fix D7 looked confirming (`D_2 ratio = 1.005 at k_min = 10⁻³`). Round-14 found this was **fortuitous integrated averaging**: the per-(k, ℓ) ratios that average to 1.005 individually scattered with std/|mean| of 108–357% (Round-14 finding F1). Apply 4√2 at one (k, ℓ) and you over-correct by 250%; apply at another and you under-correct by 70%. The "convergence to unity" was a property of the trapezoid sum integrating positive over-corrections against negative under-corrections.

### 15. Conditional behavior — the four regimes

The three pipeline toggles partition the configuration space:

| Mode | `unit_amp_norm` | `bias_subtract` | path | typical D_2 (FLRW Planck-2018, N_k=65) | mechanism |
|---|:---:|:---:|---|---:|---|
| **Default canonical** | True | False | `compute_flrw_d_ell` | **2.04 × 10¹⁰ μK²** | 1e-6 floor + bias contamination |
| Canonical, no floor | False | False | `compute_flrw_d_ell` w/ override | ~ 10⁷ μK² | bias contamination only |
| Canonical, no bias | True | True | `compute_flrw_d_ell` w/ override | ~ 10¹⁰ μK² | floor only (bias gone) |
| **Linear-probe** | False | True | `compute_flrw_d_ell_linear_probe` | **6.44 × 10³ μK²** | D-2 only |
| **Reference (Rust)** | n/a | n/a | `bass_rs::dump_dl_spectrum_sparse` | **1002 μK²** | independent code path |

The "Default canonical" is what `test_d2_pstf_closure.py` invokes and what the xfail marker reports a `+2.04 × 10¹⁰ μK²` gap on. The "linear-probe" is what the 2026-04-27 measurement script (`scripts/v5_round17_linear_probe_measurement.py`) ran. The two single-toggle regimes ("no floor", "no bias") have not been exhaustively measured; they are bounded above by Round-9's pre-fix `unit_amp_norm=True` value (`1.7 × 10⁷ μK²`) and below by the linear-probe `6.44 × 10³ μK²`. The transition behavior across these toggles confirms (a) the dominant gap is the 1e-6 floor, (b) the secondary gap is the bias-floor, and (c) the residual after both is D-2.

### 16. Validity boundary table (D-2 in numbers)

```
At η_init = 261 Mpc, x = k · η_init:

  k [Mpc⁻¹]  |   x = k·η_init   |   Lowell §13.2 validity
  ──────────┼──────────────────┼───────────────────────
  1e-4      |    0.026         |   ✓ (tail of grid)
  1e-3      |    0.26          |   marginal (≈ 1% error from O(x²))
  3.83e-3   |    1.00          |   ★ boundary  (k_crit = 1/η_init)
  1e-2      |    2.6           |   invalid (O(x²) terms ≈ 6× leading)
  3.16e-2   |    8.25          |   catastrophic (k_max of test grid)
  5e-2      |   13             |   catastrophic (~170× leading)
```

The `test_d2_pstf_closure.py` k-grid is `np.logspace(-4.0, -1.5, 65)` = 65 points from `10⁻⁴` to `10⁻¹·⁵ ≈ 0.0316 Mpc⁻¹`. Counting points that land in `x > 1` (clear Lowell-expansion invalid regime, `k > 1/η_init ≈ 3.83 × 10⁻³ Mpc⁻¹`): the fraction is `(log₁₀ 10⁻¹·⁵ − log₁₀ 3.83 × 10⁻³) / (log₁₀ 10⁻¹·⁵ − log₁₀ 10⁻⁴) × 65 ≈ 0.918 / 2.5 × 65 ≈ 24 / 65 ≈ **37%**`. The marginal `x > 0.3` regime starts at `k ≈ 1.15 × 10⁻³` and contains ≈ 37/65 ≈ **57%** of points. So *about 37% of the test grid is in the clear `x > 1` invalid territory, and about 57% is in marginal `x > 0.3` asymptotic-danger territory* (not "~60%" as an earlier draft of this doc claimed; the corrected arithmetic was caught by Report 1 of the 2026-04-27 audit cycle). The IMEX faithfully evolves those wrongly-seeded modes forward, producing the observed 6.43× over-amplification at recombination.

---

## Part IV — Code-internal Algorithms (Selected)

### 17. Why `_seed_formulae` cannot be patched with higher-x corrections

Round-12-14 sub-option **(D-2b)** considered extending the Lowell §13.2 expansion to higher x. The expansion is asymptotic, not convergent, so the partial sums diverge for x ≳ 1 even with arbitrarily many terms. A worked estimate (Round-14): convergence at `x = 14` requires `~ 20` orders of expansion; the 21st order then diverges. For a 65-point k-grid spanning x ∈ [0.026, 8.25], the maximum order needed is ~16, but the precision of the lower-x partial sums degrades catastrophically because the alternating-sign higher orders cancel against each other. The arithmetic is hopeless without arbitrary-precision (`mpmath`-level) arithmetic, which BASS does not have. **(D-2b) is non-viable.**

### 18. Why the conditional inline DAE-relaxation is the right mechanism for D-2 closure (sub-option D-2a)

Push `η_init` back to `z ≈ 10⁹` (radiation-dominated, deep TCA regime). At `z = 10⁹`, `η ≈ 10⁻³ Mpc`; `x = k · η_init` for the entire Planck-relevant k-grid `[10⁻⁴, 10⁻¹] Mpc⁻¹` lies in `[10⁻⁷, 10⁻⁴]` — well inside the Lowell validity range. The integrator then evolves through 12 orders of magnitude in η to today.

The integration **must remain stable** across this 12-decade range. Two independent obstacles were closed by Round-14/15 (`docs/V5_RUNTIME_TRACK_DIAGNOSIS.md`):

1. **Operator stability (Blocker 2, CLOSED)**. The residual-joint affine operator's spectral abscissa was `λ_max(A_right) = +0.175 / Mpc` pre-session (a positive real eigenvalue → exponential growth of an unphysical mode). Eight algebraic patches (Round-1 + Round-2 audits, applied to `htt/bass/hierarchy/ver3_layout_protocol.py`) restored the physically correct sign structure: streaming becomes skew-symmetric (`A_X^T W = -W A_X` to machine precision), Thomson damping is negative-semidefinite. Post-fix `λ_max ≈ 4 × 10⁻¹⁶ / Mpc` (machine zero) at γ_T ∈ {0, 1}. Cosmological η = 261 → 14147 Mpc IMEX completes in 130 s.

2. **TCA regime handling (this section)**. With the conditional inline DAE-relaxation at `htt/bass/hierarchy/integrator.py:434–498`, the IMEX integrator pins `Π_2` to its algebraic Thomson-coupled value when `Γ_T / H > closure.gamma_threshold_over_H` (default 100). Free-streams ℓ ≥ 3, evolves ℓ = 0, 1 normally, and pins ℓ = 2 to its slip-driven steady state. This means the dynamics that *would* require `~10⁹` integrator steps (the period when photon quadrupole is `Γ_T`-fast) are instead pinned algebraically inside one outer step. The mechanism is **load-bearing**: without it, integration from `z = 10⁹` to today is computationally infeasible.

The mechanism is *not* a TCA pre-phase. The hierarchy is integrated throughout (no analytic replacement); only the ℓ = 2 m = 0 slot is algebraically pinned to its instantaneous slip-equation solution; the relaxation rate `a · Γ_T` makes the "pinning" a stiff ODE that the IMEX implicit stage handles explicitly. As `Γ_T → threshold·H` the pinning weakens smoothly and the ODE branch takes over.

### 19. Why `los_grid_builder` *is* the right mechanism for D-1 closure (already landed)

The integrator output grid serves three masters: (i) integrator step adaptation, (ii) source extraction, (iii) LoS quadrature. Decoupling (iii) from the others by computing it per-k from physical scales (visibility FWHM, Bessel period) lets each master use the grid that fits it. The integrator can use whatever uniform spacing the IMEX adapter prefers (currently 64-point linear). The source extractor evaluates `Θ_0, Θ_2, E_2, v_b` via PCHIP interpolation on this same integrator grid. The LoS projector then evaluates the same PCHIP callables on the per-k composite grid that satisfies (a) ≥8 samples per visibility FWHM, (b) ≥8 samples per Bessel period at the relevant k. This is the standard CAMB strategy (`cmbmain.f90` `IV_q` per-k integration grid + pre-tabulated `j_ℓ(x)`), retrofitted onto BASS.

The post-fix metrics — median |ratio| 8.30 → 1.00, max 3687 → 266, resolution-independent across `n_per_oscillation ∈ {8, 16, 32, 64, 128}` — are decisive. D-1 is closed.

---

## Part V — Forbidden Moves & Rationale

The following are explicitly forbidden and tested-against. An auditor proposing one of these is signaling unfamiliarity with the prior investigation history.

### 20. Doppler `/k` correction (RETRACTED 2026-04-26)

Round-16 PR-S13 was originally specified to apply `(1/k) · d/dη[g v_b]` as a "load-bearing fix" (Round-16 handoff §4.1, commit `607e759`). Empirical 2 × 28 min `compute_flrw_d_ell` measurement (2026-04-26): the patch shifts D_2 by **−0.012%, not the spec-claimed 0.5%**. The mandate was inherited from `docs/V5_ROUND15_P1_PSTF_DERIVATION_CHATGPT.md:22` (a parallel-cycle audit retracted as Appendix X "false trail" in the R7-authoritative `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md:9, 17, 405–407, 2218`). BASS's `v_b` slot already carries dimensionless `θ_b/k` (verified at `htt/bass/hierarchy/seed_compatibility.py:210`). Adding a `/k` would be a double-divide. The in-tree regression-armor test `htt/bass/los/test_flrw_bessel_projector.py::TestSharpVisibilityAnalyticOracles::test_sharp_visibility_doppler_analytic_protects_no_over_k_patch` enforces the canonical `(g v_b)′` form.

### 21. `test_d2_pstf_closure.py xpass` without numerical verify

The pre-2026-04-26 test was `L_max_tower=4, ell_max_transfer=8`, which fails `FLRWPipelineConfig.__post_init__` validation at construction time. The xfail marker hid both that latent config bug AND the +2.04 × 10¹⁰ μK² gap simultaneously. Visibility wins over coverage metrics: an xfail mask that hides actual numerics is worse than a failing test, because it falsely signals "PR-024c will be the closure" when in fact PR-024c was never the binding gate. The fixed test (post 2026-04-26) is `L_max_tower=8, ell_max_transfer=8, k_grid length=65 (odd, Simpson-compatible)`.

### 22. Single multiplicative `calibration_factor` for the 6.43× residual

The `compute_flrw_d_ell_linear_probe` API exposes `calibration_factor=1.0` (multiplies α post-extraction; D_ℓ scales as the square). **Do not bake a default value**. Round-14 finding F1 measured per-(k, ℓ) std/|mean| 108–357% across all candidate factors — incompatible with any single multiplicative constant. R9-D §6 already established the empirical ratio is N_k-dependent, so a constant factor frozen at one N_k would silently corrupt at any other N_k. `calibration_factor` is an opt-in diagnostic knob, not a production calibration.

### 23. Higher-x correction terms in `_seed_formulae`

(D-2b). See §17 above. The Lowell §13.2 series is asymptotic, not convergent; ~20 orders are needed at x = 14, after which the next term diverges. No realistic precision-arithmetic library can save this approach.

### 24. TCA pre-phase

The "approximation-free truth engine" is mandated (`docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` + `CLAUDE.md §6`). Three constructs are banned:

- **TCA pre-phase**: an unconditional analytic solution replacing the photon hierarchy in an initial η-window.
- **FLRW UFA**: ultra-fluid approximation that replaces the higher photon multipoles with their fluid limits.
- **Photon RSA**: radiation streaming approximation that replaces the photon transfer with a single-multipole streaming form.

The conditional inline DAE-relaxation at `htt/bass/hierarchy/integrator.py:434–498` is *not* a TCA pre-phase: the ODE is integrated throughout, the hierarchy is never replaced, the relaxation timescale `1 / Γ_T` collapses smoothly onto the off-TCA branch as `Γ_T / H → threshold`. A switch-smoothness audit is enforced by `htt/bass/hierarchy/test_tca_switch_smoothness.py`.

---

## Part VI — Reproduction & Verification

### 25. Reproducing the linear-probe 6.43× measurement

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
venv/bin/python scripts/v5_round17_linear_probe_measurement.py
```

Configuration (`scripts/v5_round17_linear_probe_measurement.py:75–104`):
- Planck-2018 `SpeciesBackgroundRegistry` with HYREC visibility (`recombination_warning_policy="ignore"`)
- `k_grid = np.logspace(-4.0, -1.5, 65)` (odd, Simpson-compatible)
- `FLRWPipelineConfig(L_max_tower=8, ell_max_transfer=8)`
- `CLAssemblyConfig(ell_max=8, k_grid=k_grid, quadrature="simpson")`
- `compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0, n_workers=4)`

Wall time ≈ 31 minutes on 4 workers (130 solver tasks → 33 rounds @ ~45 s/k at L_max=8).

Expected output (commit `02cb6c0`):
```
D_2 (Python linear-probe): 6.439500e+03 μK²
D_2 (Rust MB-95 anchor):   1002.086744 μK²
Absolute gap:              +5.437413e+03 μK²
Relative error:            5.426012e+00
```

### 26. Baseline test verification

Round-16 primitive baseline (287 tests, 9 modules):

```bash
cd htt
venv/bin/python -m pytest \
  bass/background/test_codazzi_tilt_rhs.py \
  bass/integration/test_imex_ark4.py \
  bass/hierarchy/test_mode_mixing_blocks.py \
  bass/hierarchy/test_seed_factory.py \
  bass/hierarchy/test_family_k_grid.py \
  bass/los/test_b_mode_projector.py \
  bass/los/family_propagators/ \
  bass/forward/test_map_producer.py \
  bass/inference/test_planck_likelihood.py \
  -q --tb=line
```

Expected: `287 passed in ~16 s` on commit `02cb6c0`.

### 27. Anchor verification (Rust)

```bash
cd bass_rs
cargo run --release --bin dump_dl_spectrum_sparse -- planck2018
# expected output line: "D_2 = 1002.086744 μK²"
```

The anchor has been bit-identical across 14+ consecutive commits + 8 residual-joint operator patches (2026-04-24 runtime-track work).

---

## Part VII — Sub-track Plan (Forward)

### 28. Sub-tracks enumeration

| ID | Name | Effort | Closes 6.43×? | Closes `xpass`? | Status |
|----|------|:------:|:------:|:------:|--------|
| **α** | (a-switch) Switch canonical default to linear-probe path (or disable 1e-6 floor in canonical) | 1–2 d | ❌ | ❌ | Pending user decision |
| **β** | (c) Real-IC injection at η(z_*); `BackgroundMonitor.from_recombination` constructor | 1–2 d | ❌ | ❌ | Pending user decision |
| **γ** | (b) State-layout migration `m=0 → m∈{-2..+2}`; wire Round-16 primitives into `hierarchy_rhs` | 3–5 d | ❌ | ❌ | Pending user decision |
| **δ** | (D-2) Push integrator `η_init` to `z ≈ 10⁹` via TCA-enabled startup | multi-month | ✅ | ✅ | Pending user decision |
| (D-3) | Synchronous → Newtonian gauge conversion in source extractor | sub-week | partial (uncertain magnitude) | ❌ | Documented, not started |

α is mechanical (~50 LoC). β closes a separate caveat (CLAUDE.md §3 Round-15 P2 monopole-frame) but is independent of the residual. γ enables off-axis Bianchi but doesn't touch the FLRW number. δ is the only path to bit-identity. D-3 (gauge mismatch in the source extractor `tier_b_source_extraction.py:225`) is parked but cleanly described.

### 29. Why δ is multi-month

Three concurrent work streams:

1. **Cosmological-range IMEX validation at z = 10⁹**. Blocker 2 closure validated η = 261 → 14147 Mpc (z ≈ 1100 → 0). Extending to z = 10⁹ is 6 additional decades; Blocker 2 work suggests the IMEX is stable across ~5 decades but each new decade requires re-validation against the conservation laws (Codazzi, momentum constraint, energy conservation).
2. **DAE-relaxation switch-smoothness across 6 decades of `Γ_T / H`**. Currently tested across the FLRW recombination transition (z = 1100, `Γ_T / H` peak ~ 10², transition through the ~10× threshold). At z = 10⁹, `Γ_T / H ~ 10⁹`. The integrator must handle the transition from full TCA (`Γ_T / H = 10⁹`) through the dropping ratio at z ≈ 10⁵ and onwards. Switch-smoothness must be re-audited.
3. **Real-IC injection at z = 10⁹**. The Lowell seed at z = 10⁹ is well inside its validity range (`x = 10⁻⁴ at k_max = 10⁻¹`), but the IMEX initial state needs every species correctly synchronized. Currently `cosmological_config.py::build_cosmological_integrator_config` defaults to `η_initial = η(z_*) − 20 Mpc` (recombination minus margin); a z = 10⁹ variant must populate the radiation-era IC for all species at the deeper anchor.

### 30. Open questions for the auditor

See `02_AUDIT_FOCUSED_SUMMARY.md` and `03_AUDIT_PROMPT.md`.

---

## Appendix A: Glossary

- **Anchor**: A regression-armored numerical value that an alternative implementation must reproduce. Production anchor: `D_2 = 1002.086744 μK²`. Has held bit-identical across 14+ consecutive commits.
- **BASS**: Bianchi Anisotropy Solver. The codebase covered by this analysis.
- **Bianchi types**: Eight non-trivial homogeneous anisotropic background cosmologies (I, II, III, IV, V, VI₀, VI_h, VII₀, VII_h, VIII, IX), classified by the structure constants of their isometry algebra.
- **CAMB**: Code for Anisotropies in the Microwave Background (Lewis & Challinor). The standard reference Boltzmann-Einstein solver in cosmology. Used in BASS as audit oracle only — *not* as a runtime dependency.
- **D-1, D-2, D-3**: The three architectural defects identified by the Round-12-14 audit cycle. D-1 = IMEX/LoS grid conflation (closed). D-2 = Lowell seed validity (open). D-3 = sync/Newt gauge mismatch in source extractor (open).
- **DAE**: Differential-algebraic equation. Used here in the conditional inline relaxation that pins ℓ=2 m=0 to its algebraic TCA limit.
- **FLRW**: Friedmann–Lemaître–Robertson–Walker cosmology (the homogeneous-and-isotropic limit; Bianchi type I with all shears zero).
- **HYREC**: Recombination history calculator (Ali-Haïmoud & Hirata 2010). The visibility `g(η)` peak position and FWHM are extracted from a HYREC table.
- **IMEX**: Implicit-Explicit time integrator. Here, Kennedy–Carpenter ARK4(3)6L[2]SA additive Runge–Kutta.
- **LoS**: Line-of-sight. Refers to eq. (2)/(5)'s integration along the photon's path from emission to observer.
- **MB-95**: Ma & Bertschinger 1995. The standard synchronous-gauge formulation of the linear Boltzmann-Einstein system in cosmology.
- **PSTF**: Projected symmetric trace-free. The 1+3 covariant tensor decomposition used by Ellis–van Elst that BASS adopts.
- **RH**: Radiation-dominated era. Approximately z > z_eq ≈ 3400.
- **TCA**: Tight-coupling approximation. The regime `Γ_T ≫ H` where the photon quadrupole is algebraically slaved.
- **Tetrad-PSTF**: The combination of a pre-chosen tetrad (Lorentz frame at every spacetime point) plus PSTF tensor decomposition. BASS's preferred formulation.
- **xfail / xpass**: pytest markers. `xfail` = expected failure, doesn't fail the suite; `xpass` = test passed despite being marked xfail, signals the marker should be removed.
- **ζ**: Comoving curvature perturbation. The standard linear primordial amplitude in inflationary cosmology.

---

## Appendix B: Numerical Reference Card

```
Anchor (Rust MB-95):              D_2 = 1002.086744 μK²
Python canonical:                 D_2 = 2.0451 × 10¹⁰ μK² (×2.04 × 10⁷)
Python linear-probe:              D_2 = 6.4395 × 10³  μK² (×6.43)
Round-9 (4-pt N_k):               ratio 2.93 × 10⁴
Round-9 (24-pt N_k):              ratio 1.36 × 10⁴
Round-12-14 (post-R11):           ratio 7.57 × 10²
Round-17 P2 (post-R15-P0/R16):    ratio 6.43

Planck-2018 cosmology:
  T_CMB         = 2.72548 K (Fixsen 2009)
  A_s           = 2.1 × 10⁻⁹
  n_s           = 0.9649
  k_pivot       = 0.05 Mpc⁻¹
  H_0           = (Planck 2018 baseline)
  Ω_m, Ω_b, …   = (Planck 2018 baseline)

Test grid:
  k_grid        = np.logspace(-4.0, -1.5, 65)  → k ∈ [10⁻⁴, 0.0316] Mpc⁻¹
  L_max_tower   = 8
  ell_max_transfer = 8
  quadrature    = simpson
  n_workers     = 4

η anchors:
  η_init        ≈ 261 Mpc  (z = 1089.94 minus 20 Mpc margin)
  η_*           ≈ 281 Mpc  (recombination)
  η_today       ≈ 14147 Mpc

Lowell §13.2 validity:
  boundary at η_init = 261 Mpc:  k ≲ 4 × 10⁻³ Mpc⁻¹  (x = k·η_init ≲ 1)
  boundary at z = 10⁹:           k ≲ 10² Mpc⁻¹      (always satisfied for Planck-relevant k)

IMEX stability (post Round-15):
  λ_max(A_right), γ_T = 0:  4 × 10⁻¹⁶ / Mpc
  λ_max(A_right), γ_T = 1:  7 × 10⁻¹⁶ / Mpc
  cosmological η = 261→14147:  130 s @ L_max=8 single worker
```

---

## Appendix C: File-path index

Code files (in `code/` of this bundle):

- `flrw_pipeline.py` (1338 lines) — `compute_flrw_d_ell` + `compute_flrw_d_ell_linear_probe` + `FLRWPipelineConfig`
- `cl_assembly.py` (837 lines) — `assemble_cl_TT_isotropic` + `compute_dl` + `CLAssemblyConfig`
- `regular_adiabatic_ic.py` (425 lines) — `_seed_formulae` (D-2 source code)
- `los_grid_builder.py` (184 lines) — `build_los_grid` (Round-15 P0 D-1 fix)
- `integrator.py` (742 lines) — IMEX + conditional inline DAE-relaxation (lines 434–498)
- `test_d2_pstf_closure.py` (105 lines) — the closure regression test (xfail)
- `v5_round17_linear_probe_measurement.py` (148 lines) — reproduction script

Reference docs (in `reference_docs/` of this bundle):

- `V5_ROUND17_PR_S13_REAL_SCOPE.md` — current scope ticket (this round)
- `V5_ROUND17_NEXT_SESSION_OPENER.md` — fresh-session bootstrap doc
- `V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md` — three-defect diagnosis (10-auditor consensus)
- `V5_ROUND9_FINDINGS.md` — linear-probe origins + ν seed bug-fix
- `V5_ROUND15_P0_D1_FIX_SUMMARY.md` — D-1 closure record
- `V5_RUNTIME_TRACK_DIAGNOSIS.md` — IMEX stability closure record (Blockers 1+2)
- `CHANGELOG_excerpts.md` — Unreleased + Round-16 P2 + Round-17 P2 entries

---

**End of detailed analysis.** For the audit-focused brief see `02_AUDIT_FOCUSED_SUMMARY.md`.
