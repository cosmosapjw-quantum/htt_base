# WEEK 4 DAY 1 PACKET — merged v4.1 (Pastén Option B, Part 1)

**Date**: 2026-04-17
**Scope**: MES re-derivation core with Planck 2018 Commander data — closes the 29-year COBE→Planck gap for the kinematic bound hierarchy
**New module**: `bass/observational/planck_mes_bounds.py` (~270 LoC)
**New subpackage**: `bass/observational/` (first entry)
**Tests**: 44 across 8 classes
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings
**Cumulative**: 867 tests, 47.72 s runtime

---

## §1 — Scope and research-gap significance

Stoeger, Araujo & Gebbie (ApJ 476, 435, 1997) applied the MES (Maartens-Ellis-Stoeger)
covariant limit-equations scheme to COBE quadrupole/octupole data, producing the bound
$\dot{u}/\Theta < 10^{-4}$. This bound has never been formally updated with Planck data
in a dedicated analysis — Maluf & Neves (2021, arXiv:2105.08659) did the closest analog
in a bumblebee-gravity context ($\epsilon_2 \approx 1.1 \times 10^{-5}$,
$\epsilon_3 \approx 2.6 \times 10^{-5}$) but not as a general MES update. Pastén
(arXiv:2603.20963, 2026) introduced a $z$-dependent tomographic formalism but did not
publish a Planck all-sky bound either.

This module performs the general re-derivation. Scope for D1 is the numerical core —
constants, conversions, bound formulas, documented-value reproduction. D2 handles
integration with VT-07, production illustrative-value replacement in `sigma_floor`, and
the comparison table artifact.

---

## §2 — Mathematical derivation

### 2.1 Power-spectrum conversion

$$C_\ell = \frac{2\pi\,D_\ell}{\ell(\ell+1)}$$

Function: `compute_C_ell(D_ell, ell) → float`.

### 2.2 Covariant multipole amplitude (MES Paper II Eq. 2.4)

$$\epsilon_\ell^{\,2} = \frac{2\ell+1}{4\pi} \cdot \frac{C_\ell}{T_0^{\,2}} = \frac{2\ell+1}{2\ell(\ell+1)} \cdot \frac{D_\ell}{T_0^{\,2}}$$

Function: `compute_epsilon_ell(D_ell, ell, T0_microK) → float`.

### 2.3 MES kinematic bounds (Paper II Eqs. 2.5a-c)

$$\frac{\sigma}{\Theta} \le 2\epsilon_2,\qquad \frac{\omega}{\Theta} \le \sqrt{3}\,\epsilon_2,\qquad \frac{\dot{u}}{\Theta} \le \max\bigl(3\epsilon_1^{\mathrm{res}},\, 2\epsilon_2,\, \epsilon_3\bigr)$$

The acceleration bound is a three-way max. In the Planck regime (§3), $2\epsilon_2$
dominates because residual dipole after kinematic subtraction is taken $\epsilon_1^{\mathrm{res}} = 0$
and because $2\epsilon_2 > \epsilon_3$ in the measured TT spectrum.

### 2.4 Planck 2018 Commander low-ℓ TT inputs (arXiv:1807.06205 Table 2)

$$D_2 = 201.5 \pm 96.6\,\mu\mathrm{K}^{\,2},\qquad D_3 = 1034 \pm 236\,\mu\mathrm{K}^{\,2}$$

$T_0 = 2.7255\,\mathrm{K}$ (Fixsen, ApJ 707, 916, 2009).

Frozen data class `PlanckLowL_Commander` exposes these as immutable attributes.

---

## §3 — Verified results (production values)

### 3.1 Central-value bounds

$$\epsilon_2 = 3.362 \times 10^{-6},\quad \epsilon_3 = 6.372 \times 10^{-6}$$

$$\sigma/\Theta = 6.724 \times 10^{-6},\quad \omega/\Theta = 5.823 \times 10^{-6},\quad \dot{u}/\Theta = 6.724 \times 10^{-6}$$

### 3.2 2σ upper-limit bounds — the Pastén Option B headline numbers

$$\epsilon_2 = 4.705 \times 10^{-6},\quad \epsilon_3 = 7.690 \times 10^{-6}$$

$$\sigma/\Theta = 9.410 \times 10^{-6},\quad \omega/\Theta = 8.150 \times 10^{-6},\quad \dot{u}/\Theta = 9.410 \times 10^{-6}$$

### 3.3 Cross-check against documented reference (§2.2 of `tomographic_MES_framework.md`)

| Quantity | Observed (this code) | Documented (2σ) | Rel err |
|----------|---------------------|-----------------|---------|
| $\epsilon_2$ | $4.705 \times 10^{-6}$ | $4.7 \times 10^{-6}$ | 0.11% ✓ |
| $\epsilon_3$ | $7.690 \times 10^{-6}$ | $7.7 \times 10^{-6}$ | 0.13% ✓ |
| $\sigma/\Theta$ | $9.410 \times 10^{-6}$ | $9.4 \times 10^{-6}$ | 0.11% ✓ |
| $\omega/\Theta$ | $8.150 \times 10^{-6}$ | $8.2 \times 10^{-6}$ | 0.61% ✓ |
| $\dot{u}/\Theta$ | $9.410 \times 10^{-6}$ | $9.4 \times 10^{-6}$ | 0.11% ✓ |

All within 0.7%. The limiting precision is the 2-sig-fig rounding of the documented
reference values, not numerical precision of the code path.

### 3.4 Physics sanity invariants

- $\omega/\sigma = \sqrt{3}/2 = 0.8660$ exactly (both are multiples of $\epsilon_2$)
- $\dot{u}/\sigma = 1$ in the Planck regime because $2\epsilon_2$ dominates the three-way max
- $2\epsilon_2 > \epsilon_3$ at Planck precision: $9.41 \times 10^{-6} > 7.69 \times 10^{-6}$
  — shear channel bounds acceleration, consistent with SAG97 and Maluf-Neves findings
- Improvement over COBE: $1.0 \times 10^{-4} / 4.7 \times 10^{-6} \approx 21\times$ for
  $\epsilon_2$; $10\times$ for $\dot{u}/\Theta$ (less because SAG97 was already conservative)

---

## §4 — Implementation ledger

| Component | Function / class | Role |
|-----------|-----------------|------|
| `T_CMB_K`, `T_CMB_MICROK` | §1 | CMB monopole in K and μK (Fixsen 2009) |
| `PlanckLowL_Commander` | §1 | Frozen dataclass holding $D_2$, $D_3$ + 1σ errors |
| `PLANCK_2018_COMMANDER` | §1 | Canonical instance |
| `ReferenceSource` enum | §1 | Provenance tag: COBE_SAG97 / MALUF_NEVES_2021 / PLANCK_2018_THIS_WORK |
| `compute_C_ell` | §2 | $D_\ell \to C_\ell$ conversion |
| `compute_epsilon_ell` | §2 | $D_\ell \to \epsilon_\ell$ via MES Eq. 2.4 |
| `MESBounds` frozen dataclass | §3 | Holds ($\epsilon_2$, $\epsilon_3$, $\sigma/\Theta$, $\omega/\Theta$, $\dot{u}/\Theta$, source, confidence_level) |
| `compute_mes_bounds` | §3 | Full evaluation from ($D_2$, $D_3$) |
| `compute_mes_bounds_2sigma_upper` | §3 | Planck + 2σ widening shortcut |
| `compute_planck_central_bounds` | §3 | Central-value shortcut |
| `DocumentedReferenceTable` | §4 | Regression constants from project knowledge |
| `format_bounds` | §5 | Single-line human-readable summary |

### 4.1 Import graph (clean)

```
bass/observational/planck_mes_bounds  ──→  math + stdlib only
```

No cross-layer imports. `observational/` is a leaf in the dependency graph — it supplies
constants/bounds to downstream consumers (`baryon_only_policy`, `sigma_floor`) but does
not import them.

---

## §5 — Three-tier claim taxonomy

### 5.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| C_ℓ and ε_ℓ formulas implemented per MES Paper II Eq. 2.4 | 9 unit tests in TestPowerSpectrumConversion |
| Three MES bounds (σ/Θ, ω/Θ, u̇/Θ) correctly encoded | 9 tests in TestMESBounds covering all max-branch cases |
| 2σ upper-limit bounds reproduce documented values within 0.7% | 5 tests in TestDocumentedValueReproduction |
| Planck-over-COBE improvement factor ≥ 10 for ε₂ | `test_improvement_over_cobe_is_order_of_magnitude` |
| ω/σ ratio = √3/2 exactly | `test_omega_sigma_ratio_is_sqrt3_over_2` |
| `MESBounds` and `PlanckLowL_Commander` frozen | 2 immutability tests |
| Shear channel (2ε₂) dominates u̇/Θ in Planck regime | `test_udot_bound_is_2eps2_when_eps3_smaller` |
| Central-value bounds strictly below 2σ upper | `test_upper_exceeds_central` |

### 5.2 CONDITIONAL

| Claim | Condition |
|-------|-----------|
| Bound values represent "Planck 2018 this work" as a standalone paper | Currently a derivation without foreground-marginalisation Bayesian analysis; caveated in project knowledge as "short dedicated publication opportunity". Our code reproduces the derived numbers; the bound's publication-readiness is a separate question. |
| ε₁^res = 0 default | Standard convention after kinematic-dipole subtraction. A nonzero residual (if detected from frame-specific analysis) would activate the 3ε₁^res channel; supported by the API. |
| Two-sigma frequentist upper limit via central + 2σ | Conservative. A full Bayesian posterior upper limit with cosmic-variance modeling (one-sided) would differ slightly; order-of-magnitude result is stable. |
| MES scheme applicability | Requires almost-FLRW ansatz. Validated at our precision — holds because measured anisotropies are ε ≪ 1. |

### 5.3 NOT ESTABLISHED (deferred)

- Integration into VT-07 β-gate threshold (D2 scope)
- Replacement of illustrative ε₁=0.02 in `sigma_floor` (D2)
- Comparison table artifact across COBE, Maluf-Neves, this-work (D2)
- z-dependent tomographic bound (Pastén's contribution, W6+)
- Foreground-marginalised Bayesian analysis (out of thesis scope)

---

## §6 — Self-audit (PHYS-MATH-CODE)

### 6.1 Findings

| Check | Status |
|-------|--------|
| ASCII section banners | ✅ |
| Banned vocabulary scan | ✅ clean |
| Frozen dataclasses for all data-carrying types | ✅ `PlanckLowL_Commander`, `MESBounds`, `DocumentedReferenceTable` |
| Type hints on all public functions | ✅ |
| Docstrings cite primary references (MES Paper II, Fixsen, arXiv Planck) | ✅ |
| Source provenance preserved through `ReferenceSource` enum | ✅ |
| Unit documentation (μK vs K) explicit in docstrings and parameter names | ✅ |
| No hidden hardcoded constants — all named and frozen | ✅ |
| No cross-layer imports; leaf in dependency graph | ✅ |
| ownership_freeze test updated for new subpackage | ✅ 3 additional parametrized tests |
| Full-suite regression clean | ✅ 867/867 |

### 6.2 Design tension noted

The documented ε₃ value $7.7 \times 10^{-6}$ and computed $7.690 \times 10^{-6}$ differ by
$0.13\%$. At face value the computed $7.69 \times 10^{-6}$ rounds to $7.7 \times 10^{-6}$,
so the documented figure is consistent with a truncation to 2 sig figs. However, if
someone tightens the `TOLERANCE = 0.03` in `TestDocumentedValueReproduction` to $10^{-3}$,
that test starts failing for $\omega/\Theta$ (0.61% rel err because 8.2 is more aggressively
rounded than 9.4). The 3% tolerance is deliberate — any tighter and the documentation's
rounding becomes a false positive.

**Not a P0 / P1 finding**. Documented as a test-tolerance design choice.

---

## §7 — API surface

```python
from bass.observational.planck_mes_bounds import (
    # Constants
    T_CMB_K, T_CMB_MICROK,
    PLANCK_2018_COMMANDER,
    DOCUMENTED_REFERENCE,

    # Provenance
    ReferenceSource,

    # Conversions
    compute_C_ell,
    compute_epsilon_ell,

    # Main entry points
    compute_mes_bounds,
    compute_mes_bounds_2sigma_upper,
    compute_planck_central_bounds,

    # Helpers
    format_bounds,
)

# Typical usage
bounds = compute_mes_bounds_2sigma_upper()
print(format_bounds(bounds))
# → [2sigma_upper, PLANCK_2018_THIS_WORK] ε₂=4.705e-06, ε₃=7.690e-06, ...

# Downstream consumer (D2):
#     beta_max = bounds.epsilon_2_like / (1 + eta_u_dot)
```

---

## §8 — Numerical ledger

| Quantity | Value |
|----------|-------|
| New tests | 44 (8 classes) |
| Cumulative tests | 867 |
| Full-suite runtime | 47.72 s |
| New module LoC | ~270 |
| New subpackage | `bass/observational/` |
| Planck 2018 Commander D_2 central ± 1σ | 201.5 ± 96.6 μK² |
| Planck 2018 Commander D_3 central ± 1σ | 1034 ± 236 μK² |
| CMB monopole T_0 | 2.7255 K |
| **2σ upper ε_2** | **4.705 × 10⁻⁶** |
| **2σ upper ε_3** | **7.690 × 10⁻⁶** |
| **2σ upper σ/Θ** | **9.410 × 10⁻⁶** |
| **2σ upper ω/Θ** | **8.150 × 10⁻⁶** |
| **2σ upper u̇/Θ** | **9.410 × 10⁻⁶** |
| Documented-value reproduction worst rel err | 0.61% (ω/Θ) |
| Planck-vs-COBE improvement ε₂ | ~21× |
| Planck-vs-COBE improvement u̇/Θ | ~10× |
| P0 / P1 findings | 0 / 0 |

---

## §9 — Next action (W4D2 — Pastén Option B Part 2)

D2 scope:

1. **VT-07 β threshold re-derivation** — replace the illustrative `ε₁ = 0.02` currently
   wired into `sigma_floor` with the Planck-derived value. This involves:
   - New function `compute_beta_threshold_from_planck(eta_u_dot, safety_factor)`
   - Update policy inputs but NOT production numbers until reviewed
2. **Comparison table artifact** — generate a Markdown table comparing
   COBE SAG97, Maluf-Neves 2021, and Planck 2018 this-work across all five bound
   quantities, with improvement factors and a notes column
3. **Integration tests** — end-to-end from `compute_mes_bounds_2sigma_upper` through
   β threshold through `sigma_floor` + `beta_policy_gate`, verifying the new threshold
   propagates consistently
4. **Generate `PASTEN_OPTION_B_REPORT.md` + `PASTEN_OPTION_B_COMPARISON.csv`** as
   presentable deliverables

Target: ~30 new tests, cumulative ~897. No source code in `sigma_floor.py` or
`baryon_only_policy.py` changes — threshold override is supplied via a new optional
parameter, preserving backward compatibility with the ε₁=0.02 illustrative configuration.

---

**End of W4D1 packet. Awaiting approval for D2.**
