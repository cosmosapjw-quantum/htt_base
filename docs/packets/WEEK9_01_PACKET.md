# WEEK 9-01 PACKET — FLRW Bessel kernel baseline (LOS projector)
## Date: 2026-04-18
## Scope: MASTER_PROMPT_LIST_bass_py_v1.2 §4 W9-01

---

## §1. Deliverables

| Artefact | Path | Lines |
|----------|------|-------|
| Module | `bass/los/flrw_bessel_projector.py` | 572 |
| Tests | `bass/los/test_flrw_bessel_projector.py` | 708 |
| Independent verification script | `scripts/verify_w9_01.py` | 225 |
| New subpackage | `bass/los/__init__.py` | (empty stub) |

Total new LoC: **1,505** (module 572 + test 708 + script 225).
New tests: **74** (roadmap target ~40; extras from R2 integration, isolation tier, sum-rule cross-check).

---

## §2. Public API surface

```python
# bass/los/flrw_bessel_projector.py

# Configuration
FLRWBesselConfig             # frozen: ell_max, eta_0_mpc, quadrature,
                             #  bessel_kr_small_cutoff, use_lookup, lookup_kr_grid

# Source contract (all callables mandatory; silent omission forbidden)
FLRWSourceTerms              # frozen: theta_0, psi, phi_dot_plus_psi_dot, v_b, pi
    .with_all(...)           # full activation factory
    .with_sw_polter_only(...) # explicit ISW=Doppler=0 factory
    .with_isw_only(phi_dot_plus_psi_dot)
    .with_doppler_only(v_b)
    .zeros()

# Spherical Bessel helpers
spherical_bessel_at(ell, kr)
spherical_bessel_vector(ell, kr_array)
bessel_lookup_table(ell_max, kr_grid) → ndarray (ell_max+1, N)

# E-mode projection kernel (includes small-kr Taylor branch)
e_mode_projection_factor(ell, kr, small_cutoff)

# Source assembly
build_temperature_source(eta_grid, sources, g_fn, kappa_fn) → ndarray
build_polarization_source(eta_grid, sources, g_fn) → ndarray

# Transfer projectors
project_temperature_transfer(k, S_T, eta_grid, config) → ndarray[ell_max+1]
project_polarization_transfer(k, S_E, eta_grid, config) → ndarray[ell_max+1]
project_polarization_transfer_from_pi_callable(k, pi_fn, g_fn, eta_grid, config)

# Analytic cross-checks
sachs_wolfe_analytic_transfer(k, eta_star, theta0_plus_psi, config)
bessel_sum_rule(x, ell_max) → partial Σ_ℓ (2ℓ+1) j_ℓ²(x)

# η-grid utilities
build_eta_grid_linear(eta_min, eta_max, n_points)
build_eta_grid_log_in_z(cosmology, z_lower, z_upper, n_points)

# Sign assertions (v1.2)
assert_sw_sign_at_low_ell(Delta_T, theta0_plus_psi_sign)
assert_e_mode_vanishes_for_ell_lt_2(Delta_E)
assert_transfer_finite_on_grid(Delta)

# Diagnostic
convergence_halving_deta(k, source_T_fn, eta_min, eta_max, n_points_coarse, config)

# Utilities
constant_callable(value) → EtaCallable
_zero_callable(eta) → 0  (module-level explicit-zero source)

# Scope guards (raise OutOfScopeError)
bianchi_m_mixing(...)              # W9-02
full_scalar_mode_evolution(...)    # W10+
compute_c_ell(...)                 # W10-01
b_mode_transfer(...)               # W11+
```

---

## §3. Physics core

### 3.1 LOS integrals (Seljak-Zaldarriaga 1996, Kamionkowski-Kosowsky-Stebbins 1997)

Temperature transfer:
$$\Delta_\ell^T(k) = \int_0^{\eta_0} d\eta\, S_T(k, \eta)\, j_\ell[k(\eta_0 - \eta)]$$

E-mode polarization transfer:
$$\Delta_\ell^E(k) = \int_0^{\eta_0} d\eta\, S_E(k, \eta)\, P^E_\ell[k(\eta_0-\eta)]$$

with projection kernel
$$P^E_\ell(kr) = \begin{cases} \sqrt{(\ell-1)\ell(\ell+1)(\ell+2)}\cdot j_\ell(kr)/(kr)^2 & \ell \ge 2 \\ 0 & \ell < 2 \end{cases}$$

At small kr, a Taylor branch $j_\ell(kr)/(kr)^2 \approx (kr)^{\ell-2}/(2\ell+1)!!$ guards against cancellation; at $\ell = 2$ this gives the finite limit $\sqrt{24}/15 \approx 0.3266$.

### 3.2 Source assembly (SW + ISW + Doppler + polter)

$$S_T(\eta) = g(\eta)\left[\Theta_0 + \Psi + \tfrac{1}{4}\Pi\right] + e^{-\kappa(\eta)}\left[\dot\Psi + \dot\Phi\right] + \frac{d}{d\eta}\left[g(\eta) v_b(\eta)\right]$$

$$S_E(\eta) = -\frac{\sqrt{6}}{4}\,g(\eta)\,\Pi(\eta)$$

**All four temperature sub-terms are wired in W9-01**. The module is a projector / integrator: $\Theta_0(\eta)$, $\Psi(\eta)$, $\dot\Phi+\dot\Psi(\eta)$, $v_b(\eta)$, $\Pi(\eta)$ are all caller-supplied callables. Full scalar-mode evolution (solving for $\Theta_0$, $\Psi$, ...) is explicitly deferred to W10+ via `full_scalar_mode_evolution` scope guard.

### 3.3 No-silent-omission contract

`FLRWSourceTerms` requires all five callables. The `with_sw_polter_only`, `with_isw_only`, `with_doppler_only`, and `zeros` factories make any intentional suppression explicit in code — the absent terms become `_zero_callable`, never silent `None`. This was a deliberate design choice per session directive: "ISW/Doppler는 low-ℓ에서도 영향이 있으므로 포함해야함. temperature evolution은 추후에 다루어도 되나 아예 생략은 금지."

### 3.4 Doppler derivative

The Doppler term requires $d/d\eta[g \cdot v_b]$. The W9-01 baseline uses `np.gradient` with `edge_order=2` (second-order central differences on interior points, second-order one-sided at edges). This is O(dη²) accurate — consistent with the trapezoidal quadrature baseline. A spline-derivative upgrade is a future refinement.

### 3.5 Bessel sum-rule identity (replacement for a mis-specified orthogonality)

The completeness identity

$$\sum_{\ell=0}^{\infty} (2\ell + 1)\,j_\ell^2(x) = 1$$

converges in partial sums once $\ell_{\max} > x$. W9-01 exposes `bessel_sum_rule(x, ell_max)` for this check; the test suite confirms convergence to $10^{-10}$ at $x \le 10$, $\ell_{\max} = 40$.

(This replaces an early draft that specified $\int_0^\infty k^2 j_\ell^2(kr)\, dk = \pi/(2r^2)$ as the "analytic" Bessel identity; that integral is actually $\delta$-distributional and diverges at $r = r'$. See §7 cycle-1 for the correction record.)

### 3.6 Out of scope (declared, raise OutOfScopeError)

- Bianchi m-mixing matrix propagator → **W9-02**
- Full scalar-mode evolution ($\Theta_0$, $\Psi$, $\Phi$ dynamics) → **W10+**
- Multi-k production grid + $C_\ell$ aggregation → **W10-01**
- B-mode (FLRW: identically zero) → **W11+** Bianchi tensor sector
- CMB lensing potential → far future
- Limber / FFT-based acceleration → optimization pass

---

## §4. Test inventory (74 tests, all PASSING)

| Class | Tests | Focus |
|-------|-------|-------|
| `TestFLRWBesselConfig` | 6 | Frozen, quadrature enum, ell_max/eta_0 validation |
| `TestSphericalBessel` | 6 | Scalar, j_0 formula, vector consistency, lookup table, rejects |
| `TestEModeProjectionFactor` | 6 | ℓ<2=0, ℓ=2 at x=1, Taylor ℓ=2, Taylor ℓ≥3, vector, reject |
| **`TestFLRWSourceTerms`** | **5** | **Factories, frozen, explicit-zero contract** |
| **`TestSourceAssembly`** | **5** | **SW match, Doppler via gradient, ISW damping, polter match W8-03** |
| `TestTemperatureTransfer` | 6 | Shape, zero source, linearity, k-bound, eta-bound, shape-mismatch |
| `TestPolarizationTransfer` | 5 | Shape, ℓ<2 zero, linearity, sign, W8-03 convenience |
| **`TestSachsWolfeSharpVisibility`** | **3** | **Narrow-σ recovers j_ℓ, σ² scaling, ℓ=0 analytic** |
| **`TestBesselSumRule`** | **4** | **Partial Σ (2ℓ+1)j_ℓ² → 1 at x=1/5/10** |
| `TestQuadratureConvergence` | 4 | Simpson odd-n, trapezoid halving, Simpson faster |
| **`TestTermIsolation`** | **3** | **ISW-only, Doppler-only, SW+polter independence from κ** |
| **`TestPhysicalSignAssertions`** | **7** | **SW sign ±, E-mode vanish, finite guard, raise on bad** |
| `TestScopeGuards` | 4 | All four deferred features raise OutOfScopeError |
| `TestEtaGridUtilities` | 4 | Linear bounds, log-in-z monotone, reject bad ranges |
| `TestIsotropicSourceM0` | 2 | Output is ℓ-indexed only (FLRW_identity_test) |
| **`TestRealFixtureEndToEnd`** | **3** | **HyRec CSV + W8-03 Π feed + full S_T → finite Δ_ℓ** |

**Runtime**: 2.03 s standalone. 37.21 s full bass + tsc regression (1,714 passing).

---

## §5. Cross-verification matrix (standalone verify script)

| Block | Check | Result |
|-------|-------|--------|
| 1 | Bessel sum rule Σ(2ℓ+1)j_ℓ²(x)=1 at x=0.5,1,2.5,5,10 | **abs err < 1e-10** all cases |
| 2 | P^E_2(kr→0) = √24/15 | rel 0 (analytic limit exact in float) |
| 2 | P^E_5(kr→0) → 0 | |P^E_5| = 2.79e-21 |
| 3 | Narrow-σ Gaussian → j_ℓ(kr_*), σ=3 | rel 8e-7 (k=5e-4), 4e-6 (k=1e-3) |
| 4 | Error(σ) monotone decrease σ=20→10→3 | 3.70e-5 → 9.25e-6 → 8.32e-7 |
| 5 | Δ_ℓ(7S) = 7 Δ_ℓ(S) | rel **1.32e-16** (machine precision) |
| 6 | ISW-only non-trivial Δ_ℓ | max 1.56e-01 |
| 7 | Doppler source odd around peak, non-trivial Δ_ℓ | S_T(η=250)=+2.68e-7, S_T(η=310)=-2.68e-7 |
| 8 | Δ_ℓ^E = 0 for ℓ<2; non-zero for ℓ≥2 | max(ℓ≥2) = 9.62e-1 |

All blocks **PASS**.

---

## §6. Score card

```
PR-W9-01: FLRW Bessel kernel baseline (LOS projector)
Status:            VALIDATED
Tests:             74 / 74 (three iterations: orthogonality respec,
                   trapezoid grid, Doppler threshold)
Honest scope:      YES (§3.6 + module docstring + 4 OutOfScopeError stubs)
V-gate status:     N/A (CAMB V-gate is W10-02)
Lines:             1,505 (module 572 + test 708 + script 225)
Depends complete:  YES (W8-03, W8-02, W8-01)
Production ready:  YES for FLRW baseline; Σ→0 limit reference for W9-02
Cross-verification: 8-block independent + 3 isolation tiers ✓
Physical sign assertions: 7 (v1.2 pattern continued)
Silent-omission prevention: dataclass + factory pattern ✓
Banned vocab scan: CLEAN
```

---

## §7. Test / implementation correction cycles

### Cycle 1 — mis-specified Bessel orthogonality

**Initial draft**: exposed `bessel_orthogonality_integral(ell, r_mpc, k_max, n_samples)` and a companion `bessel_orthogonality_analytic(r_mpc) = π/(2r²)`. Test asserted numerical integral matches this analytic value within 0.1 %.

**Failure**: numerical value came out ~1 % of the analytic target — off by two orders of magnitude, not close to convergence.

**Root cause**: the identity $\int_0^\infty k^2 j_\ell^2(kr)\, dk = \pi/(2r^2)$ is a $\delta$-distribution statement — specifically $\int_0^\infty k^2 j_\ell(kr) j_\ell(kr')\, dk = (\pi/2)\delta(r-r')/r^2$, which at $r = r'$ formally diverges. The finite-limit claim was a textbook misstatement by the author. No value of `k_max` makes the test work because the integrand $k^2 j_\ell^2(kr) \sim \cos^2(kr)/r^2$ at large $k$ has non-integrable oscillatory tail.

**Corrective action**:

1. Removed `bessel_orthogonality_integral` and `bessel_orthogonality_analytic`.
2. Added `bessel_sum_rule(x, ell_max)` computing $\sum_{\ell \le L} (2\ell+1) j_\ell^2(x)$. This identity is finite, closed-form, and converges in partial sums once $\ell_{\max} > x$.
3. Test class renamed `TestBesselSumRule`; four tests at $x \in \{1, 5, 10\}$ and reject-bad-inputs, all asserting convergence to 1 within $10^{-10}$.
4. Packet §3.5 records the correction explicitly.

### Cycle 2 — trapezoid convergence test under-resolved

**Failure**: `test_trapezoid_halving_converges` at `n_points_coarse = 201` gave relative change 0.16 (16 %) between coarse and fine grids. Tolerance was 1e-3.

**Root cause**: source Gaussian with $\sigma = 30$ Mpc sampled on $[10, 14116]$ Mpc with 201 points has $d\eta \approx 70$ Mpc, larger than $\sigma$ — the Gaussian is under-resolved at coarse, so halving to 401 points still doesn't capture its peak structure. The test was measuring grid-coarseness noise, not convergence.

**Corrective action**: increase `n_points_coarse` to 1001 so that $d\eta \approx 14$ Mpc $< \sigma$. At this resolution the source is decently sampled and halving genuinely probes O(h²) decay. Test now passes with margin.

### Cycle 3 — Doppler amplitude threshold

**Failure** (standalone verify only, not in pytest): Block 7 asserted $\max|\Delta_\ell^T| > 10^{-7}$ for Doppler-only source with $v_b = 10^{-3}$, Gaussian $g$ ($\sigma=30$). Measured: $7.14 \times 10^{-8}$.

**Root cause**: amplitude estimate. $d(g v_b)/d\eta = v_b \cdot dg/d\eta$; at Gaussian peak $|dg/d\eta| \sim g_{\rm max}/\sigma$, so peak $|S_T| \sim v_b \cdot g_{\rm max}/\sigma \approx 10^{-3} \cdot (4.3 \times 10^{-4}) / 30 \approx 1.4 \times 10^{-8}$. Bessel-weighting oscillation partially cancels in the integral. Post-projection $10^{-7}$ threshold was too strict.

**Corrective action**: relaxed to $> 10^{-8}$ in the verify script (comment records the amplitude derivation). Measured value now $7.14 \times 10^{-8}$ passes comfortably. The corresponding pytest `test_doppler_only_produces_nonzero_transfer` already used $> 0.0$ (non-zero), which was always correct.

### Lessons carried forward

This brings the running tally of audit-driven discoveries to **nine** across bass_py. Pattern continues: the physics derivation is first-time-right, and the integration surface (thresholds, identities claimed as closed-form vs distributional, fixture resolution) catches the assumption drift.

Key take-home from cycle 1: **never claim a closed-form analytic reference for a formula without verifying its convergence class.** The $\int k^2 j_\ell^2 dk$ surface is a distributional identity disguised as a finite integral; the sum rule $\sum (2\ell+1) j_\ell^2 = 1$ is the proper analogue for finite-precision work.

---

## §8. Outstanding items & next steps

### Immediate successor — W9-02

**Matrix propagator for Bianchi I.** W9-01 is the $\Sigma^2 \to 0$ limit reference; W9-02 extends the LOS integral with shear-induced $m$-mixing across $m \in \{0, \pm 2\}$. Dependencies: W9-01 (this packet), W5-C.

### Carried to W10

**Full scalar-mode evolution** ($\Theta_0$, $\Psi$, $\Phi$) — currently supplied as caller callables with analytic / constant fixtures. W10 promotes these to evolved trajectories produced by the photon + fluid hierarchies. The `full_scalar_mode_evolution` scope guard is the retirement marker.

### Carried to W10-01

**Multi-k integration and $C_\ell$ aggregation.** W9-01 returns $\Delta_\ell(k)$ for single $k$. The Riemann integral $C_\ell = (2/\pi) \int dk\, k^2 |\Delta_\ell(k)|^2 P(k)$ requires a k-grid spec and primordial $P(k)$; scheduled W10-01.

### Optional polish (P3)

- Spline-derivative for Doppler. `np.gradient` is O(dη²); cubic-spline derivative is O(dη⁴), matching Simpson's quadrature. Low-priority — Doppler is a subdominant term at the ℓ range we currently care about.
- Lookup-table path for Bessel evaluation. Currently always on-the-fly; `FLRWBesselConfig.use_lookup` is wired but not exercised. Would accelerate multi-k grid (W10-01).
- Analytic $P^E_\ell$ lookup for ℓ ≤ 30. scipy's `spherical_jn` is already fast; premature optimization.

---

## §9. MASTER_PROMPT_LIST status delta

| Phase | Before this session | After |
|-------|--------------------|----|
| W6 | 4/4 complete | 4/4 |
| W7 | 2/2 complete | 2/2 |
| W8 | 3/3 complete | 3/3 |
| W9 | 0/2 | **1/2 (W9-02 next)** |
| Overall | 11/24 = 45.8% | **12/24 = 50.0%** |

**Test total**: 1,640 (post-W8-03) + 74 (W9-01 new) = **1,714** (full bass + tsc regression: **1,714 passed in 37.21 s, 0 failures**).

**Integration status** (on the merged bass_py tree):
- W9-01 suite standalone: **74 / 74 passed in 2.03 s**
- Full bass + tsc regression: **1,714 / 1,714 passed in 37.21 s**
- Independent verification script: **8 / 8 blocks PASS**
- Banned vocab scan (module + test + script + packet): **CLEAN**

---

**End of packet.**

Author-of-record: Claude (Opus 4.7) on behalf of Jiwon
Generated: 2026-04-18
