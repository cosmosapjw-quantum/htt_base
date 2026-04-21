# WEEK 4 DAY 3 PACKET — Thomson Tensor Axisymmetric Skeleton

**Date**: 2026-04-17
**Scope**: First real BASS runtime consumer of W3 `CanonicalDecision` machinery — photon Thomson collision source in the axisymmetric Bianchi I limit
**New module**: `bass/collision/thomson_tensor.py` (~310 LoC)
**New subpackage**: `bass/collision/`
**Tests**: 50 across 9 classes + 3 ownership updates
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings
**Cumulative**: 957 tests, 51.51 s runtime

---

## §1 — Scope and architectural significance

This is the **first module that actively consumes W3's `CanonicalDecision`
allow/block machinery**. Every public entry calls `require_allow_reduction(...)`
before numerical work, making W3 contract enforcement real in production paths
(not just test infrastructure). If the decision blocks (β policy fail, Σ² floor
fail, or $D_{\geq 2}$ tangency fail), the collision evaluator raises
`CanonicalBlockError` carrying the full decision for logging.

Scope is **axisymmetric Bianchi I**: every rank-2 STF tensor has one scalar
DOF, parametrized by amplitude + symmetry axis. This is the minimal non-FLRW
geometry where the Thomson tensor exercises its full structure without the
full Bianchi I tensorial bookkeeping. W5+ extends to off-axis STF components.

---

## §2 — Physical equations implemented

### 2.1 Photon Thomson collision (ch05 Eq. Thomson-damping)

$$\mathcal{C}^{(\gamma)}_{ab} = -\dot{\tau}\,\Theta^{(\gamma)}_{ab} + \frac{\dot{\tau}}{10}\,\Pi_{ab}$$

Opacity $\dot{\tau} = n_e\,\sigma_T$.

### 2.2 STF polarization source

$$\Pi^{\rm STF}_{ab} = \Theta^{(\gamma)}_{ab} + E^{(\gamma)}_{ab}$$

The trace-carrying $E^{(\gamma)}_0\,h_{ab}/3$ term in the published formula
drops from the rank-2 STF equation (pure-trace additions have zero STF
component). Module implements the STF-projected form directly.

### 2.3 Quasi-static balance (pre-recombination)

$$\Theta^{(\gamma)}_{ab} \simeq \frac{\Sigma^{(\gamma)}_2}{\dot{\tau}}\,\sigma_{ab}$$

Valid when $\dot{\tau} \gg H$, diagnosed by $\dot\tau/H > 10$ threshold.

### 2.4 Shear-source coefficient (ch05 Eq. shear-source)

$$\Sigma^{(\gamma)}_2 = \frac{8}{15}\frac{\mathcal{I}_4}{\mathcal{I}_3}\bigg|_{\rm BE,\,\eta=0} = \frac{8}{15}\cdot\frac{24\,\zeta(5)}{\pi^4/15} \approx 2.04386$$

Matches the L0 dashboard `Sigma_2[BE]` cross-check from W3D5a to machine
precision.

### 2.5 E-mode Thomson source (Paper VI P2)

$$\dot E^{(\gamma,1)}_{ab}\Big|_{\rm Th} = -\frac{2}{5}\,\dot{\tau}\,c_\xi\,T^{(\gamma,1)}_{ab}$$

---

## §3 — Axisymmetric STF representation

Every STF tensor in this module is parametrized as:

$$A_{ab} = a \cdot \frac{3\,n_a n_b - h_{ab}}{2}$$

where $n$ is a unit vector along one of `{X, Y, Z}` symmetry axes and $a$ is
the scalar amplitude. For $n = \hat z$ this gives:

- $A_{xx} = A_{yy} = -a/2$
- $A_{zz} = +a$
- Off-diagonal $\equiv 0$
- $\mathrm{Tr}(A) = 0$ exactly

Module operations (add, scale, inner product) all reduce to scalar ops on the
amplitude. The `to_matrix()` diagnostic reconstructs the full 3×3 form for
visualization and tests.

---

## §4 — Verified numerical results

### 4.1 Bit-exact formula reproductions

| Scenario | Inputs | Output (observed) | Expected |
|----------|--------|-------------------|----------|
| $C_{ab}$ Thomson | $\Theta = 10^{-5}, E = 2\times 10^{-6}, \dot\tau = 10^3$ | $-8.800 \times 10^{-3}$ | $-8.8 \times 10^{-3}$ |
| $\Pi^{\rm STF}$ | $\Theta = 3\times 10^{-5}, E = 7\times 10^{-6}$ | $3.700 \times 10^{-5}$ | $3.7 \times 10^{-5}$ |
| Quasi-static $\Theta$ | $\sigma = 10^{-6}, \dot\tau = 10^3$ | $2.0439 \times 10^{-9}$ | $2.0439 \times 10^{-9}$ |
| E-mode $\dot E$ | $T = 10^{-5}, \dot\tau = 10^3, c_\xi = 1$ | $-4.000 \times 10^{-3}$ | $-4 \times 10^{-3}$ |
| $\Sigma^{(\gamma)}_2$ | (closed form) | $2.043856$ | $\sim 2.044$ |

All agreements are bit-exact (rel err $< 10^{-14}$).

### 4.2 Physical invariants verified

- **STF trace**: every `to_matrix()` output has $\mathrm{Tr} = 0$ to machine precision across all three axes and amplitude signs.
- **Fine-tuned cancellation**: when $\Theta = 0.1, E = 0.9$ so $\Pi = \Theta + E = 1 = 10\Theta$, the collision vanishes exactly ($\mathcal{C}_{ab} = -\dot\tau(\Theta - \Pi/10) = 0$).
- **Linearity in opacity**: $\mathcal{C}(\dot\tau_1)/\mathcal{C}(\dot\tau_2) = \dot\tau_1/\dot\tau_2$ to $10^{-14}$.
- **Sign preservation**: $\mathrm{sign}(\dot E_{ab}) = -\mathrm{sign}(T_{ab})$ always.

### 4.3 Quasi-static regime diagnostic

At $\dot\tau = 10^3, H = 30$ → $\dot\tau/H = 33.3 > 10$ threshold → `in_quasi_static_regime = True` ✓.
At $\dot\tau = 0.1, H = 30$ → $\dot\tau/H = 0.003$ → flag correctly False.

---

## §5 — Runtime gating contract

Every public entry point performs:

```python
require_allow_reduction(decision, context="<function_name>")
```

as its first executable step. Verified behaviors:

| Function | Blocked decision raises | Error context string |
|----------|-------------------------|----------------------|
| `compute_photon_thomson_collision` | ✅ `CanonicalBlockError` | `"thomson_collision"` |
| `compute_quasi_static_theta` | ✅ `CanonicalBlockError` | `"quasi_static_theta"` |
| `compute_e_mode_thomson_source` | ✅ `CanonicalBlockError` | `"e_mode_thomson"` |

The raised exception's `.decision` attribute carries the full `CanonicalDecision`
object, enabling upstream callers to log the specific failure mode (β_policy_pass,
sigma_min_above_floor, or source_Dge2_gate_pass).

This is the **production realization** of the W3D1 design contract. Consumers
now cannot sidestep the gate; attempting to do so raises a distinguished error
type caught at the solver driver level.

---

## §6 — Implementation ledger

| Component | Role |
|-----------|------|
| `SIGMA_2_PHOTON_BE` | $\Sigma^{(\gamma)}_2 \approx 2.044$ |
| `THOMSON_POLARIZATION_COEFF` | $1/10$ factor on $\Pi$ |
| `E_MODE_THOMSON_COEFF` | $2/5$ factor on E-mode source |
| `QUASI_STATIC_TAU_H_THRESHOLD` | $10$ (default regime boundary) |
| `SymmetryAxis` enum | `{X, Y, Z}` |
| `AxisymmetricSTFTensor` frozen dataclass | Amplitude + axis, `to_matrix()`, `trace()`, `scale()`, `add()` |
| `ThomsonCollisionResult` frozen dataclass | Full result container with diagnostic flags |
| `compute_photon_thomson_collision` | Main intensity collision entry |
| `compute_quasi_static_theta` | Pre-recombination balance |
| `compute_e_mode_thomson_source` | Paper VI P2 E-mode source |
| `verify_quasi_static_regime` | Standalone diagnostic |
| `photon_Sigma_2_coefficient` | Publicly-exposed constant |

### 6.1 Import graph

```
bass/collision/thomson_tensor  ──→  bass/runtime/canonical_decision
                               ──→  scipy.special.zeta, numpy, math
```

Only W3 runtime imported; no TSC imports (kept via ownership_freeze enforcement).

---

## §7 — Three-tier claim taxonomy

### 7.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| $\mathcal{C}^{(\gamma)}_{ab}$ formula correctly implemented | 8 tests in `TestPhotonThomsonCollision` with bit-exact agreement |
| $\Pi^{\rm STF} = \Theta + E$ (h-trace drops) | 4 tests in `TestPolarizationSourceSTF` |
| Quasi-static $\Theta = \Sigma_2/\dot\tau \cdot \sigma$ | 5 tests in `TestQuasiStaticLimit` |
| E-mode source $-\frac{2}{5}\dot\tau c_\xi T$ | 5 tests in `TestEModeThomsonSource` |
| $\Sigma^{(\gamma)}_2 \approx 2.044$ from closed form | 6 tests in `TestPhotonSigma2Coefficient` |
| Axisymmetric STF is trace-free | `test_is_trace_free` across all axes/amplitudes |
| STF arithmetic preserves trace-free property | `test_sum_remains_STF` |
| All 3 public functions gate on `CanonicalDecision` | 5 tests in `TestRuntimeGating` |
| `CanonicalBlockError` carries full decision for diagnostics | `test_blocked_error_carries_decision` |
| Quasi-static regime diagnostic correctly distinguishes regimes | 6 tests in `TestQuasiStaticRegimeDiagnostic` |
| No regression in 904 prior tests | 957/957 green |

### 7.2 CONDITIONAL

| Claim | Condition |
|-------|-----------|
| Axisymmetric scope adequate for thesis | Bianchi I tilt has axisymmetric background geometry; off-axis contributions enter via tilt coupling at W5+. Current axisymmetric is correct for Phase 1. |
| $c_\xi = 1$ default | Linear-order Paper VI convention. More elaborate spectral-statistics dependence may emerge at higher order — deferred. |
| STF "drop $E_0 h/3$" interpretation | Standard in the PSTF 1+3 convention (e.g., Challinor-Lasenby 1999). Formulation in ch05 is identical. |
| $\Sigma^{(\gamma)}_2$ valid for BE at $\eta=0$ | General $\eta \neq 0$ case uses different $I_4/I_3$; override-able via `Sigma_2` parameter to `compute_quasi_static_theta`. |

### 7.3 NOT ESTABLISHED (deferred)

- Off-axis ($m \neq 0$) STF components — W5+ Bianchi I extension
- Nonlinear Θ⁴ bridge coupling into collision — W4D5
- Second-order quadratic sources ($v_b \times \Theta$, $\Theta^2$ terms from Paper II/BFK) — W5+
- E ↔ B free-streaming mixing (Σ_{nn'} matrix) — W5+
- Tight-coupling approximation (TCA) as explicit stiffness resolution — documented in existing CAMB-TCA mapping doc

---

## §8 — Self-audit (PHYS-MATH-CODE)

| Check | Status |
|-------|--------|
| ASCII banners | ✅ |
| Banned vocabulary scan (module + test) | ✅ clean |
| Frozen dataclasses for all containers | ✅ `AxisymmetricSTFTensor`, `ThomsonCollisionResult` |
| Type hints on all public functions | ✅ |
| Docstrings cite primary references (ch05, Paper VI) | ✅ |
| Every public function enforces runtime gate first | ✅ 3/3 |
| Input validation: negative opacity, zero Hubble, mismatched axes | ✅ 4 dedicated tests |
| No cross-layer leakage (TSC import) | ✅ enforced by `test_ownership_freeze` |
| Ownership freeze updated (2 parametrized + 1 module import entry) | ✅ |
| Full-suite regression clean | ✅ 957/957 |

**P0 / P1 findings: 0 / 0.**

---

## §9 — API surface

```python
from bass.collision.thomson_tensor import (
    # Constants
    SIGMA_2_PHOTON_BE,               # ≈ 2.044
    THOMSON_POLARIZATION_COEFF,      # 1/10
    E_MODE_THOMSON_COEFF,            # 2/5
    QUASI_STATIC_TAU_H_THRESHOLD,    # 10

    # Types
    SymmetryAxis,                    # enum {X, Y, Z}
    AxisymmetricSTFTensor,           # frozen dataclass
    ThomsonCollisionResult,          # frozen dataclass

    # Main entry points (all gate on CanonicalDecision)
    compute_photon_thomson_collision,
    compute_quasi_static_theta,
    compute_e_mode_thomson_source,

    # Diagnostic
    verify_quasi_static_regime,
    photon_Sigma_2_coefficient,
)

# Typical call
theta = AxisymmetricSTFTensor(amplitude=1e-5, axis=SymmetryAxis.Z)
E     = AxisymmetricSTFTensor(amplitude=2e-6, axis=SymmetryAxis.Z)
result = compute_photon_thomson_collision(
    theta_gamma=theta, E_gamma=E,
    n_e_sigmaT=1e3,
    decision=make_canonical_decision(...),
    hubble_rate=30.0,
)
# result.collision.amplitude = -8.8e-3
# result.in_quasi_static_regime = True
```

---

## §10 — Numerical ledger

| Quantity | Value |
|----------|-------|
| New tests | 50 (9 classes) + 3 ownership updates |
| Cumulative tests | 957 |
| Full-suite runtime | 51.51 s |
| New module LoC | ~310 |
| New subpackage | `bass/collision/` (first entry) |
| $\Sigma^{(\gamma)}_2$ | 2.043856 |
| $C_{ab}$ bit-exact precision | < 10⁻¹⁴ rel err |
| Gating calls per module | 3 (all public entries) |
| `CanonicalBlockError` paths verified | 3 (one per entry) |
| P0 / P1 findings | 0 / 0 |

---

## §11 — Next action (W4D4 — Ray transport axisymmetric skeleton)

D4 scope: `bass/transport/ray_transport.py` — axisymmetric photon/neutrino
free-streaming transport. The counterpart to D3's collision source.

Physics (ch05 + Paper I hierarchy):

- Free-streaming divergence $\nabla_a \Theta^{(s)}_{ab}$ for multipole coupling
- Shear-source injection at $\ell = 2$: $\dot\Theta^{(s)}_{ab} \supset (8/15)\,\sigma_{ab}$
- Hubble damping rate $\Gamma^{(s)}_\ell$
- Neutrino free-streaming (no collision): $\dot\Theta^{(\nu)}_{ab} + \Gamma_2^{(\nu)}\Theta^{(\nu)}_{ab} = \Sigma_2^{(\nu)}\,\sigma_{ab}$

Skeleton interface should include:
1. Single-species $\ell = 2$ transport equation solver (Euler step for testability)
2. Shear injection from a background $\sigma_{ab}$ tensor
3. Collision-free (neutrino) and collision-coupled (photon + baryon) variants
4. Same gating contract as D3: `require_allow_reduction(...)` at every entry

Target: ~45 new tests, cumulative ~1000.

---

**End of W4D3 packet. Awaiting approval for D4.**
