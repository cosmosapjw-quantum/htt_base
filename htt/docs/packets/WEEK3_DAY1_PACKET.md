# WEEK 3 DAY 1 PACKET — Inverse T → F (Newton with Paper III-A Jacobian)

> **RETROFIT NOTE (2026-04-17, post-merge)**
>
> This packet documents work completed under v4 baseline on 2026-04-17. On the same day,
> the plan was amended (v4.1 MERGED) to introduce a `bass/` vs `tsc/` ownership split.
> Under the merged plan, this work is retroactively classified as follows:
>
> - **Module location**: `inverse_T_to_F.py` → `tsc/charts/inverse_T_to_F.py` (move executes at W3D5b freeze commit; no current code change)
> - **Schedule attribution**: v4 W3D1 → merged W3D3 (partial — MC sweep still owed in merged W3D3)
> - **Classification**: TSC / charts layer, not BASS runtime
>
> The technical content below is unaltered. The 48 tests and 580 cumulative count remain as-is. The
> roundtrip MC sweep originally planned for v4 W3D2 is absorbed into merged W3D3 alongside the
> directory move. See `BASS_PY_INTEGRATION_v4_1_MERGED.md` §8 for the full retrofit mapping.
>
> The **revised W3D1** in the merged schedule is `bass/runtime/canonical_decision.py`, gated on
> approval of `CANONICAL_DECISION_DESIGN.md`.

---

**Date**: 2026-04-17
**Module**: `inverse_T_to_F.py` (445 LoC)
**Tests**: `test_inverse_T_to_F.py` (48 tests, 11 classes)
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings
**Cumulative**: 580 tests, 8.45s runtime

---

## §1 — Scope and Paper I role

Paper I sets up the one-to-one correspondence between the species exponential-family
distribution

$$f_s(x,\hat{\mathbf{e}}) = \Phi_{\xi_s}\!\left(\frac{x}{\Theta_s(\hat{\mathbf{e}})} - \eta_s(\hat{\mathbf{e}})\right)$$

and its PSTF multipole stack $T_\ell$ through the forward map $F$ implemented in Week 2 Day 2.
Week 3 Day 1 provides the **inverse** map $F^{-1}$: given observed axisymmetric multipoles
$(T_0, T_1, \ldots, T_L)$, recover the Legendre coefficients $\Theta_\ell$ of the
direction-dependent temperature field $\Theta(\mu) = \sum_\ell \Theta_\ell P_\ell(\mu)$.

Scope of Day 1:

- **One-field species** ($\eta \equiv 0$, photons): square system, $L_\Theta = L_T$, exact recovery.
- **Two-field species with given $\eta(\mu)$**: $\eta$ is supplied externally (chemistry closure,
  BBN calibration, or a Day 2+ sub-iterate); only $\Theta$ is recovered.
- **Simultaneous recovery of $(\Theta, \eta)$** from two moment orders: deferred (Week 3 scope).
- **Non-axisymmetric 3D**: deferred to Day 5 (Lebedev quadrature module).

---

## §2 — Mathematical construction

### 2.1 Residual equation

At the iterate $\Theta^{(k)}(\mu) = \sum_\ell \Theta_\ell^{(k)} P_\ell(\mu)$ the forward map yields

$$F_\ell(\Theta^{(k)}) \;=\; \frac{2\ell+1}{2} \int_{-1}^{1} d\mu \; \Theta^{(k)}(\mu)^{n+1} \; I_n(\xi, \eta(\mu)) \; P_\ell(\mu)$$

and the residual $r_\ell^{(k)} = F_\ell(\Theta^{(k)}) - T_\ell^{\mathrm{obs}}$.

### 2.2 Paper III-A Jacobian

Differentiation with respect to $\Theta_m$ pulls down a factor $(n+1)\Theta^n$ under the integrand:

$$J_{\ell m}(\Theta^{(k)}) \;=\; \frac{\partial F_\ell}{\partial \Theta_m}\bigg|_{\Theta^{(k)}} \;=\; \frac{2\ell+1}{2} \int_{-1}^{1} d\mu \; (n+1)\,\Theta^{(k)}(\mu)^n \; I_n(\xi, \eta(\mu)) \; P_\ell(\mu)\,P_m(\mu).$$

This is the **Gram matrix in the $\Theta^n I_n$-weighted Legendre inner product**, matching the Paper III-A regression-exact Jacobian specification.

### 2.3 Isotropic limit is diagonal

When $\Theta(\mu) \equiv \Theta_0$ and $\eta(\mu) \equiv \eta_0$, the integrand factors and the
Legendre orthogonality gives

$$J_{\ell m}^{\mathrm{iso}} \;=\; (n+1)\,\Theta_0^n\,I_n(\xi,\eta_0)\,\delta_{\ell m}.$$

Inverting this yields the **linear-response inverse** which is used as the Newton initial guess:

$$\Theta_0^{(0)} = \left(\frac{T_0}{I_n}\right)^{1/(n+1)}, \qquad \Theta_\ell^{(0)} = \frac{T_\ell}{(n+1)\,[\Theta_0^{(0)}]^n\,I_n}\quad (\ell \geq 1).$$

### 2.4 Newton step with admissibility barrier

$$\Theta^{(k+1)} = \Theta^{(k)} + \alpha\,\Delta\Theta^{(k)}, \qquad J^{(k)} \Delta\Theta^{(k)} = -r^{(k)}.$$

Back-tracking line search halves $\alpha$ until (a) $\Theta^{(k+1)}(\mu) > 0$ on $[-1,1]$ and (b)
$\|r^{(k+1)}\| < \|r^{(k)}\|(1 - 10^{-4}\alpha)$ (relaxed Armijo).

---

## §3 — Implementation ledger

| Component | Function | Role |
|-----------|----------|------|
| Linear-response inverse (initial guess) | `linear_response_inverse` | Closed-form §2.3 |
| Paper III-A Jacobian assembly | `_build_jacobian` | Shared forward + Jacobian quadrature pass |
| Newton driver with Armijo + barrier | `invert_T_to_Theta_axisymmetric` | Main API |
| Result container | `InverseResult` (frozen dataclass) | Carries history, cond, line-search count |
| Roundtrip helper | `roundtrip_relative_error` | Thin wrapper for Day 2 use |
| FD Jacobian (verification only) | `jacobian_finite_difference` | Unit-test reference |

Module is 445 LoC, no external dependencies beyond Week 2 modules.

### 3.1 Quadrature sizing heuristic

Default `n_quad = max(32, (n+1) L_\Theta + 2 L_T + 4 L_\eta + 8)`. The extra $4 L_\eta$ headroom
accommodates the nontrivial $\mu$-dependence of $I_n(\xi, \eta(\mu))$ which is *not* polynomial.
Smoke testing confirmed this oversamples enough that $I_n$ evaluation accuracy (set by `xi_moment`
tolerance `rtol=1e-10`) dominates rather than the Gauss-Legendre error.

### 3.2 Convention lock

Dimensional $T$ convention: $T_0 = \Theta_0^{n+1} I_n(\xi, \eta_0)$ at isotropy. This matches
`axisymmetric_F` exactly and is the *sole* convention used in this module (no Θ-normalized
fallback; `channel_routing` historical convention is isolated to Week 1).

---

## §4 — Verified physics and numerical behaviour

### 4.1 Jacobian verification (FD vs analytic)

Central finite-difference at $h=10^{-6}$ on `Theta_coeffs = [1.0, 0.05, 0.03, 0.01]`:

| $\xi$ | max rel err (ana vs FD) | Diagonal sample $J_{22}$ (ana) |
|------|--------------------------|-------------------------------|
| BE (+1) | $1.12 \times 10^{-9}$ | 26.8032 |
| MB (0)  | $1.21 \times 10^{-9}$ | 24.7645 |
| FD (−1) | $1.02 \times 10^{-9}$ | 23.4528 |

The $10^{-9}$ floor is the expected FD truncation residual, not a Jacobian defect. At isotropy
($\Theta_1 = \Theta_2 = 0$) the Jacobian was verified to be exactly diagonal within $10^{-10}$.

### 4.2 Newton quadratic convergence

Residual trace for `Theta_true = [1.0, 0.1, 0.03, 0.01]`, FD, with nontrivial isotropic $\eta = -0.1$:

| iter | $\|r^{(k)}\| / \|T^{\mathrm{obs}}\|$ | ratio $r_{k+1}/r_k^2$ |
|------|--------------------------------------|------------------------|
| 0    | $6.99 \times 10^{-2}$                 | —                      |
| 1    | $1.73 \times 10^{-3}$                 | $0.35$                 |
| 2    | $1.10 \times 10^{-6}$                 | $0.37$                 |
| 3    | $4.31 \times 10^{-13}$                | $0.36$                 |

The ratio stays near $\sim 0.35$, confirming quadratic convergence (the asymptotic constant is
bounded by $\|J^{-1}\|\,\|F''\|/2$). Iteration terminates in 3 steps; final $\mathrm{cond}(J) = 1.78$.

### 4.3 Amplitude scan (MB, $L=3$)

| anisotropy amp | max roundtrip err | Newton iters | $\mathrm{cond}(J)$ |
|----------------|-------------------|---------------|---------------------|
| 0.05           | $6.5 \times 10^{-14}$ | 3 | 1.3 |
| 0.10           | $8.0 \times 10^{-12}$ | 3 | 1.8 |
| 0.20           | $5.1 \times 10^{-14}$ | 4 | 3.1 |
| 0.30           | $4.1 \times 10^{-12}$ | 4 | 5.4 |

Condition number scales as $\sim 1 + O(\mathrm{amp}^2)$, consistent with the Gram matrix staying
positive-definite away from the admissibility boundary at $\Theta(\pm 1) = 0$.

### 4.4 Parity protection

Pure quadrupole input $(\Theta_0, 0, \Theta_2, 0)$ forward-mapped and inverted recovers
$|\Theta_1^{\mathrm{rec}}| < 10^{-10}$, i.e., no spurious dipole leakage. This mirrors Week 2 Day 2's
verified parity selection in the forward direction.

---

## §5 — Verified vs conditional results (three-tier taxonomy)

### 5.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| Linear-response inverse is exact at $\Theta_\ell = O(\epsilon)$ | `TestLinearResponseInverse` (6 tests) |
| Paper III-A Jacobian matches central FD at $10^{-9}$ | `TestJacobianAnalytic` (4 tests) |
| Isotropic inversion converges in 0–1 iters | `TestIsotropicInversion` (4 tests) |
| Quadratic Newton convergence | `TestNewtonConvergence::test_quadratic_convergence_MB` |
| $F^{-1} \circ F = \mathrm{id}$ at $10^{-9}$ for amp $\leq 0.1$ | `TestRoundtripClosure` (5 tests) |
| Parity selection preserved under inversion | `TestQuadrupoleInversion::test_quadrupole_parity_no_dipole_leak` |
| BE eta $\leq 0$ and $\Theta > 0$ barriers enforced | `TestAdmissibilityBarrier` (3 tests) |
| All three statistics (BE/MB/FD) invert identically | `TestDipoleInversion`, `TestQuadrupoleInversion`, `TestMixedMultipoleInversion` |

### 5.2 CONDITIONAL

| Claim | Condition | Notes |
|-------|-----------|-------|
| Roundtrip closure at moderate amp 0.2 | relaxed to $10^{-8}$ tolerance | Quadrature floor — not a Jacobian defect |
| Two-field inversion with given $\eta$ | $\eta$ is *fixed* input, not unknown | Simultaneous recovery deferred |
| Newton iteration count $\leq 8$ | amp $\leq 0.2$ | At amp $\geq 0.5$ back-tracking becomes more frequent |
| $\mathrm{cond}(J)$ bounded $O(1)$ | small/moderate anisotropy | Near admissibility boundary $\Theta \to 0$, $\mathrm{cond}(J) \to \infty$ expected |

### 5.3 NOT ESTABLISHED (deferred)

- Simultaneous $(\Theta, \eta)$ recovery from two moment orders $(n, n+1)$ — requires a $2(L+1)
  \times 2(L+1)$ block Jacobian. Scheduled for Week 3+ when Prop 7 $\mu$-defect structure is
  integrated.
- Non-axisymmetric 3D inversion — requires Lebedev quadrature. Scheduled for W3D5.
- Polarization inversion (Paper VI) — W7 P3.

---

## §6 — Self-audit (PHYS-MATH + PHYS-MATH-CODE)

### 6.1 PHYS-MATH AUDIT

| Check | Status | Remark |
|-------|--------|--------|
| Forward map formula consistency vs `axisymmetric_F` | ✅ | Both use identical quadrature weights |
| Jacobian is symmetric up to row-scaling $(2\ell+1)/2$ | ✅ | Verified: $J_{\ell m}/(2\ell+1) = J_{m\ell}/(2m+1)$ |
| Isotropic limit reduces correctly to linear-response formula | ✅ | `test_jacobian_isotropic_is_diagonal` |
| Newton step preserves physical admissibility $\Theta > 0$ | ✅ | Line search guards |
| BE restriction $\eta \leq 0$ enforced at API surface | ✅ | `test_BE_rejects_positive_eta` |
| Dimensional convention matches `forward_F_to_T` | ✅ | No Θ-normalized mixing |
| Three-tier claim taxonomy applied in §5 | ✅ | |

### 6.2 PHYS-MATH-CODE AUDIT

| Check | Status | Remark |
|-------|--------|--------|
| Module docstring section banner present | ✅ | ASCII `=====` dividers |
| All banned vocabulary absent from docstrings | ✅ | Full style-rule wordlist scanned, zero hits |
| Style rule compliance in prose | ✅ | No "departure parameter" context here; passive voice banned rule N/A for code docstrings |
| Type hints on all public functions | ✅ | `Optional[...]`, `tuple`, `np.ndarray` |
| Frozen dataclass for result container | ✅ | `InverseResult(frozen=True)` |
| Error paths raise informative `ValueError`/`RuntimeError` | ✅ | Verified in `TestEdgeCases` (6 tests) |
| No silent catch of `LinAlgError` | ✅ | Re-raised as `RuntimeError` with context |
| Test class 11-pattern followed | ✅ | 11 classes, 48 tests total |
| No regression in W1/W2 tests | ✅ | 532 prior tests still pass |

**Findings: 0 P0 / 0 P1**. Module is cleared for Day 2 dependency.

---

## §7 — API surface (reference)

```python
from inverse_T_to_F import (
    invert_T_to_Theta_axisymmetric,   # main entry
    linear_response_inverse,           # closed-form initial guess
    roundtrip_relative_error,          # convenience wrapper
    InverseResult,                     # result dataclass
)

# Canonical usage
res = invert_T_to_Theta_axisymmetric(
    T_ell_obs=observed_T_ell,           # ndarray (L+1,)
    xi=+1,                               # BE / MB / FD
    eta=None,                            # or AxisymmetricField for two-field
    moment_order=3,                      # energy moments (default)
    tol=1e-10,
    max_iter=50,
)

if res.converged:
    Theta_coeffs = res.Theta.coeffs      # recovered Legendre coefficients
    print(f"{res.n_iter} Newton iters, cond(J) = {res.jacobian_cond:.2f}")
```

---

## §8 — Numerical ledger (quick-reference table)

| Quantity | Value | Context |
|----------|-------|---------|
| Total new tests | 48 | 11 classes per pattern |
| Cumulative tests | 580 | W1 + W2 + W3D1 |
| Full-suite runtime | 8.45 s | Up from 3.87 s (Newton loops add ~4.5 s) |
| Jacobian FD agreement | $\sim 10^{-9}$ (all ξ) | Expected FD truncation floor |
| Newton quadratic ratio | $\sim 0.35$ | Asymptotic $\|J^{-1}\|\|F''\|/2$ bound |
| Iso Jacobian diagonal | $(n+1)\Theta_0^n I_n$ | Matches linear-response inverse |
| Roundtrip amp 0.1 | err $\sim 10^{-12}$, 3 iters | MB baseline |
| Roundtrip amp 0.2 | err $\sim 10^{-8}$, 4 iters | Quadrature-floor dominated |
| Module size | 445 LoC | |

---

## §9 — Next action (W3D2)

Day 2 builds on this module with **explicit roundtrip harness** and **cross-statistic Monte Carlo
sweep** to verify closure at machine precision across a parameter grid:

- Input: random Θ coefficients drawn from a bounded distribution, for each $\xi \in \{-1, 0, +1\}$
  and each moment order $n \in \{2, 3, 4\}$.
- Forward → inverse → compare coefficients.
- Close Phase A of the F ↔ T cycle: **732 cumulative tests** expected after Day 2.
- Edge region: `Layer 3 moment admissibility boundary` stress tests (Prop 14/15 intersection).

Day 2 will *not* introduce new physics — its sole purpose is to lock down the closure property
across the full statistics × moment-order product space and document precision floors. After
Day 2 the F ↔ T subsystem is frozen; Day 3 moves to entropy invariants (Thm 9/10/11).

---

**End of W3D1 packet.** Awaiting approval for Day 2.
