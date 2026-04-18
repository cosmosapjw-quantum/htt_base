# LB-3 — Closure and Truncation Specification

**Session LB-3**. Produces `bass/hierarchy/closure.py` and cross-consumes the existing `bass/closure/quadrupole_tca.py` (W6-04).

**Prerequisites**:
- LB-0 (`00_conventions.md`) — PSTF convention
- LB-2 (`02_multipole_hierarchy_spec.md`) — `PSTFTensor`, `ClosureStrategy` protocol, `hierarchy_rhs_photon`
- `bass.closure.quadrupole_tca` (W6-04; already in bass_py) — the ℓ=2 TCA closure used as a plug-in strategy

**Size estimate**: ~500 LoC implementation + ~300 LoC tests.

**Reference material**:

- **Ellis §4.6** — moment hierarchy, truncation
- **Ma-Bertschinger 1995** (arXiv:astro-ph/9506072) §6 — truncation schemes in FLRW Boltzmann
- **lowell §6** — L=4/6/8 discussion (minimum / baseline / convergence)
- **Baumann §4.6** — linear Boltzmann truncation (cleaner pedagogy)
- **Pitrou 2009** (*CQG* 26:065006) — non-FLRW truncation strategies

---

## Table of contents

1. Why closure matters (and why L=2 is insufficient)
2. Available closure strategies
3. The `ClosureStrategy` protocol
4. HardCutClosure (default)
5. FreeStreamingClosure
6. PowerLawExtrapolationClosure
7. TCAClosure at ℓ=2 (W6-04 reuse)
8. Closure error diagnostics
9. L=4 / L=6 / L=8 recommendations
10. Data contracts
11. Test criteria
12. Implementation checklist
13. Cite map

---

## 1. Why closure matters

The exact PSTF hierarchy (LB-2 §1) at ℓ = L references Π_{L+1} via term T3 (divergence of Π_{L} with one more index) and Π_{L+2} via term T7 (double shear-trace of Π_{L+2}). If we truncate the state vector at L, we must *supply* Π_{L+1} and Π_{L+2} from outside the state.

Options:

1. **Set to zero** — crude; introduces bounded-recurrence truncation error
2. **Extrapolate** from Π_{L-1}, Π_L — smoother; lower error at cost of assumption
3. **Algebraic closure** (TCA) — replace *dynamical* ODE at ℓ=2 with algebraic relation derived from the high-Γ_T limit

**L=2 is not self-consistent**. The ℓ=2 equation has term T9 = −(ℓ+2) σ_{⟨ab⟩} Π_{A_{ℓ-2}} = −4 σ_{ab} Π_0 (the famous shear-injection term), and also term T7 = −(ℓ-1)(ℓ+1)(ℓ+2)/((2ℓ+3)(2ℓ+5)) × σ^{cd} Π_{abcd} — which references Π_{abcd} at ℓ=4. **Closing ℓ=4 at zero introduces a systematic bias in the Bianchi-driven quadrupole** that is larger than observational sensitivity at Σ² ∼ 10⁻⁸.

lowell reference §6 is explicit:

> L=2는 self-consistent closure가 아니다. low-ℓ에서 L=4 (최소), L=6 (권장), L=8 (검증) 이라는 결론이 나온다.

LB-3 implements all three (L=4, 6, 8) as configuration, with L=6 as the default baseline.

---

## 2. Available closure strategies

| Strategy | Accuracy | Implementation cost | Best for |
|---|---|---|---|
| `HardCutClosure` | O(Π_{L+1}/Π_L) truncation error; ∝ (1/L) asymptotically | trivial | quick development, L=8 validation runs |
| `FreeStreamingClosure` | O(Π_{L+1}/Π_L × 1/(kη)) — improves over hard cut by a factor (kη)⁻¹ at super-horizon | easy | free-streaming regime (neutrinos, photons before recombination at k η > 1) |
| `PowerLawExtrapolationClosure` | matches assumed asymptotic Π_ℓ ∝ ℓ⁻α shape | moderate | post-recombination photon tail |
| `TCAClosure` at ℓ=2 | O(1/Γ_T²) error | already implemented (W6-04) | tight-coupling regime z > 10⁵ |

These four are **mutually compatible** — TCAClosure at ℓ=2 can be combined with HardCutClosure at L_max. The `ClosureStrategy` protocol allows per-ℓ dispatch.

---

## 3. The `ClosureStrategy` protocol

### 3.1 Baseline protocol shipped at LB-2a (canonical)

LB-2a shipped the minimal protocol actually consumed by the
``hierarchy_rhs_photon`` driver:

```python
# bass/hierarchy/closure_interface.py  (LB-2a)

from typing import Protocol, runtime_checkable
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor


@runtime_checkable
class ClosureStrategy(Protocol):
    """Pluggable tower-closure interface.

    Called by the LB-2b driver whenever it needs ``Π_ℓ`` at a rank
    beyond the tower's top multipole. Strategies must return a valid
    ``PSTFTensor`` of the requested rank; returning a defensive *copy*
    of any tensor read out of ``state`` (HardCut precedent) is
    required to keep the call side-effect-free.
    """

    def get_closure(
        self, state: PSTFHierarchyState, ell_requested: int
    ) -> PSTFTensor: ...
```

**All four LB-3 strategies implement this single method.** The driver
(LB-2b ``hierarchy_rhs_photon``) calls ``closure.get_closure(state,
ell+1)`` to resolve ``Π_{L+1}`` for T3/T4 and ``closure.get_closure(
state, ell+2)`` for T7 at the top of the tower.

### 3.2 Algebraic-override extension (TCA; LB-5 consumer)

The ℓ=2 algebraic TCA path (W6-04 ``solve_tca_closure``) is *not*
triggered through ``get_closure`` — the ODE-vs-algebraic dispatch is
an integrator-level decision (LB-5). ``TCAClosure`` therefore exposes
two additional methods that LB-5's stepper consults:

```python
class TCAClosure:
    # Standard protocol (delegates to an inner closure for tower top).
    def get_closure(self, state, ell_requested): ...

    # Algebraic-override extension — consumed by the LB-5 integrator,
    # not by the LB-2b RHS driver.
    def override_at_ell(self, ell: int) -> bool: ...
    def algebraic_closure(
        self, state, ell, eta, *,
        source_T: float, source_E: float, Gamma_T: float,
    ) -> PSTFTensor: ...
```

``override_at_ell(2) == True`` only signals *TCA is available*; the
actual decision to use TCA vs. the ODE at a given η is made by
checking ``Γ_T / H`` at runtime. LB-5 owns that dispatch logic.

### 3.3 Design-history note

An earlier draft of this spec proposed a multi-method baseline
protocol (``closure_next`` + ``closure_next_next`` + ``override_at_ell``
+ ``algebraic_closure``). LB-2a consolidated those under a single
``get_closure(state, ell_requested)`` entry point: driver-side the
distinction between "ℓ+1" and "ℓ+2" is purely an integer argument,
and splitting into two methods bought no extra type-safety. The
algebraic-override hooks survive as a TCA-only extension (§3.2).

---

## 4. HardCutClosure (default)

> **Implementation note (supersedes pseudocode below)**. All four
> strategies expose the single LB-2a method ``get_closure(state,
> ell_requested)`` (§3.1). The ``closure_next`` / ``closure_next_next``
> forms shown in §4–§7 are pedagogical — read them as ``get_closure``
> called with the appropriate rank. The algebraic-override pair
> ``override_at_ell`` / ``algebraic_closure`` survives on TCAClosure
> only (§3.2).

```python
class HardCutClosure:
    """Π_{L+1} = Π_{L+2} = 0.

    Simplest closure.  Introduces a truncation error of
        |Π_L+1| / |Π_L| ~ (k η / L)
    in the free-streaming regime (Ma-Bertschinger 1995 §6).

    For L >= 6 this is below 5% for all modes k η < 1 at the Bianchi-
    driven quadrupole amplitude.  For L=4, error reaches ~15% at
    recombination; reserve L=4 for geometry-exploration only.
    """

    def closure_next(self, state, ell, eta, a, Theta, Gamma_T):
        return zero_pstf(ell + 1)

    def closure_next_next(self, state, ell, eta, a, Theta, Gamma_T):
        return zero_pstf(ell + 2)

    def override_at_ell(self, ell: int) -> bool:
        return False

    def algebraic_closure(self, *args, **kwargs):
        raise RuntimeError("HardCutClosure has no algebraic mode")
```

**Default strategy**. Use for initial LB-2 integration smoke tests.

---

## 5. FreeStreamingClosure

Ma-Bertschinger 1995 §6 (eq 53) gives the free-streaming truncation

```
Π_{L+1} = ((2L + 1) / (k η)) × Π_L − Π_{L-1}
```

This is obtained by assuming the high-ℓ tower is dominated by the free-streaming recursion and setting the 1/η evolution equal to the gradient term.

```python
class FreeStreamingClosure:
    """Ma-Bertschinger 1995 free-streaming truncation.

    Valid when Γ_T << H (collisionless regime).  For neutrinos this is
    true for all z < 10^10 on our grid; for photons only after
    recombination.
    """

    def __init__(self, k_mpc_inv: float):
        """k in Mpc⁻¹ — the mode wavenumber.  For background-only
        integration, pass k = 0; the closure then degenerates to
        hard-cut (since k η → 0 in the numerator limit).
        """
        self.k = k_mpc_inv

    def closure_next(self, state, ell, eta, a, Theta, Gamma_T):
        Pi_L = state.tensors[ell]
        Pi_L_minus_1 = state.tensors[ell - 1] if ell >= 1 else zero_pstf(0)
        k_eta = self.k * eta
        if k_eta < 1e-15:
            return zero_pstf(ell + 1)
        coeff_curr = (2 * ell + 1) / k_eta
        # Component-wise; no rank conversion needed
        comps = coeff_curr * Pi_L.components - Pi_L_minus_1.components[:2*ell+1] if ell >= 1 else coeff_curr * Pi_L.components
        # Note: shapes need reconciliation; utility helpers in closure.py
        ...

    def closure_next_next(self, state, ell, eta, a, Theta, Gamma_T):
        # Apply the recursion twice
        ...

    def override_at_ell(self, ell: int) -> bool:
        return False
```

**When to use**: for post-recombination photon integration or neutrinos at any epoch. **Not** for pre-recombination photons (tight coupling regime breaks the free-streaming assumption).

---

## 6. PowerLawExtrapolationClosure

Assume Π_ℓ ∝ ℓ⁻α for ℓ > L_extrap:

```
Π_{L+1} = Π_L × ((L+1) / L)⁻α
Π_{L+2} = Π_L × ((L+2) / L)⁻α
```

```python
class PowerLawExtrapolationClosure:
    """Power-law extrapolation: Π_ℓ ∝ ℓ⁻α beyond L.

    α must be supplied at construction.  Typical values:
        α = 2 for free-streaming radiation (Kolb §9)
        α = 3 for damped tails post-recombination
    """

    def __init__(self, alpha: float):
        if alpha <= 0:
            raise ValueError(f"alpha must be positive, got {alpha}")
        self.alpha = alpha
```

**When to use**: diagnostic — compare with HardCut to quantify truncation sensitivity.

---

## 7. TCAClosure at ℓ=2 (W6-04 reuse)

The existing `bass.closure.quadrupole_tca.solve_tca_closure` produces the algebraic ℓ=2 closure for (Θ_2, E_2) given the non-collision source (S_T, S_E) and Γ_T. LB-3 wraps this:

```python
class TCAClosure:
    """Algebraic ℓ=2 closure via W6-04 quadrupole-aware TCA.

    Replaces the ℓ=2 ODE by
        (Θ_2, E_2) = M⁻¹ × (S_T, S_E) / Γ_T
    when Γ_T > gamma_threshold.  Outside the tight-coupling regime,
    delegates to an inner_strategy.

    Reference: Y-Block cross-check (c3dc68c); W6-04 quadrupole_tca.py;
    lowell §10 (identical up to sign convention).
    """

    def __init__(self,
                 inner_strategy: ClosureStrategy,
                 gamma_threshold_over_H: float = 100.0):
        """inner_strategy: closure to use when Γ_T / H < threshold.
        E.g. HardCutClosure or FreeStreamingClosure for post-recombination.
        """
        self.inner = inner_strategy
        self.threshold = gamma_threshold_over_H

    def closure_next(self, state, ell, eta, a, Theta, Gamma_T):
        # ℓ+1 = 3: not affected by TCA; delegate
        return self.inner.closure_next(state, ell, eta, a, Theta, Gamma_T)

    def closure_next_next(self, state, ell, eta, a, Theta, Gamma_T):
        return self.inner.closure_next_next(state, ell, eta, a, Theta, Gamma_T)

    def override_at_ell(self, ell: int) -> bool:
        # Actually, the override depends on Gamma_T at runtime, but
        # the protocol signature here has to know *whether* to use
        # algebraic mode at ell=2.  We return True only for ell=2
        # and let algebraic_closure dispatch based on Gamma_T inside.
        return ell == 2

    def algebraic_closure(self, state, ell, eta, *, source_T, source_E, Gamma_T):
        if ell != 2:
            raise RuntimeError(f"TCAClosure only handles ell=2; got {ell}")
        H_local = state.Theta / 3.0 if hasattr(state, 'Theta') else ...
        if Gamma_T / H_local < self.threshold:
            # Fall back to ODE — caller should check override_at_ell again
            # and realise TCA isn't active; strategy here indicates "no algebraic".
            raise RuntimeError("TCA not active at this Γ_T/H; caller should use ODE path")

        from bass.closure.quadrupole_tca import solve_tca_closure
        from bass.runtime.canonical_decision import make_canonical_decision
        # construct an always-allow decision for TCA integration
        ...
        theta_2_scalar, E_2_scalar = solve_tca_closure(
            S_T=source_T, S_E=source_E,
            gamma_T=Gamma_T, decision=dec,
        )
        # Pack into PSTFTensor: (Θ_2, E_2) are scalars in the m=0 basis;
        # here we return Π_2 axisymmetric (real-sph-harm packing with m=0).
        comps = np.zeros(5, dtype=np.float64)
        comps[2] = theta_2_scalar  # m = 0 is index 2 for ℓ = 2
        return PSTFTensor(ell=2, components=comps)
```

**Crucial design point**: `override_at_ell(2) == True` only indicates *TCA is available*; the actual decision to use TCA vs ODE at a given η is made by checking `Γ_T / H` at that η. LB-5's integrator is responsible for the dispatch logic.

---

## 8. Closure error diagnostics

For validation, LB-3 provides a utility:

```python
def measure_closure_error(
    hierarchy_state: PSTFHierarchyState,
    L_reference: int,
    L_truncated: int,
) -> dict:
    """Compare an L_reference-integrated tower to an L_truncated tower.

    Returns per-ℓ relative error
        err_ℓ = | Π_ℓ^{L_ref} - Π_ℓ^{L_trunc} | / | Π_ℓ^{L_ref} |
    for ℓ ∈ [0, L_truncated].

    Usage: integrate once at L=8, once at L=4, compare. At L=6, the
    expected error at Π_2 is below 1% for standard Bianchi I / Planck
    cosmology.
    """
    ...
```

This is used in LB-3 tests to verify that L=6 is accurate enough.

---

## 9. L=4 / L=6 / L=8 recommendations

| L | Purpose | Truncation error | Runtime cost |
|---|---|---|---|
| **4** | Minimum self-consistent (T7 still truncated; use for geometry exploration only) | Π_2 error ~15% at recombination | fastest |
| **6** | **Baseline — use this for all LB-6 integration tests** | Π_2 error ~1% | moderate |
| **8** | Convergence verification — compare L=6 output to L=8 output to check LB-6 accuracy claims | Π_2 error ~0.1% | slow |

Recommendation: **LB-5 integrator defaults to L=6**. LB-6 regression tests include an L=8 verification run on a reduced cosmology.

---

## 10. Data contracts

### 10.1 Module file layout

```
bass_py/bass/hierarchy/
├── closure.py              — ClosureStrategy, HardCutClosure,
│                             FreeStreamingClosure,
│                             PowerLawExtrapolationClosure,
│                             TCAClosure
├── closure_diagnostics.py  — measure_closure_error, convergence plots
├── test_closure.py
└── test_closure_diagnostics.py
```

### 10.2 Public API

```python
from bass.hierarchy.closure import (
    HardCutClosure,
    FreeStreamingClosure,
    PowerLawExtrapolationClosure,
    TCAClosure,
    build_default_closure,
)
from bass.hierarchy.closure_interface import ClosureStrategy  # LB-2a

def build_default_closure(
    L_max: int,
    strategy_name: str = "freestream",
    *,
    k_mpc_inv: float = 0.0,
    alpha: float = 2.0,
    gamma_threshold_over_H: float = 100.0,
) -> ClosureStrategy:
    """Factory dispatch by name.

    Parameters
    ----------
    L_max : int
        Top multipole of the tower (closure supplies ℓ = L_max+1 and
        ℓ = L_max+2 slots).
    strategy_name : {'hardcut', 'freestream', 'powerlaw', 'tca'}
        Named strategy. Raises ``ValueError`` on unknown names.
    k_mpc_inv : float
        Wavenumber used by ``FreeStreamingClosure``; ignored by others.
    alpha : float
        Power-law exponent used by ``PowerLawExtrapolationClosure``.
    gamma_threshold_over_H : float
        TCA activation threshold (see ``TCAClosure``).
    """
```

---

## 11. Test criteria

### 11.1 HardCutClosure / protocol tests (C-01..C-04)

| # | Test | Target | Tol |
|---|---|---|---|
| C-01 | `HardCutClosure().get_closure(state, L+1)` returns ``zero_pstf(L+1)`` and is protocol-conformant | 0 tensor | exact |
| C-02 | `FreeStreamingClosure`, `PowerLawExtrapolationClosure`, `TCAClosure` all satisfy `isinstance(..., ClosureStrategy)` | True | exact |
| C-03 | All four strategies: `get_closure(state, L+2)` returns a PSTF tensor of rank L+2 — never mutates the input state | — | 1e-14 |
| C-04 | `FreeStreamingClosure(k=0)`: `get_closure` reduces to `HardCut` (zero tensor of the requested rank) | 0 | exact |

### 11.2 FreeStreaming / PowerLaw numeric targets (C-05..C-08)

| # | Test | Target | Tol |
|---|---|---|---|
| C-05 | At k·η finite, `FreeStreamingClosure.get_closure(state, ell+1)` matches Ma-Bertschinger eq 53 `((2ℓ+1)/(kη)) Π_ℓ − Π_{ℓ−1}` | analytic | 1e-12 |
| C-06 | `closure_next_next` (i.e. `get_closure(state, ell+2)`) applies the recursion twice consistently | analytic | 1e-12 |
| C-07 | `PowerLawExtrapolationClosure.get_closure(state, L+1)`: every component scaled by `(L/(L+1))^α` | analytic | 1e-14 |
| C-08 | PowerLaw at L+2: component scaled by `(L/(L+2))^α` — exact | analytic | 1e-14 |

### 11.3 TCAClosure tests (C-09..C-12)

| # | Test | Target | Tol |
|---|---|---|---|
| C-09 | `TCAClosure.override_at_ell(ℓ)` == True iff ℓ == 2 | True/False | exact |
| C-10 | `TCAClosure.algebraic_closure(..., source_T, source_E, Gamma_T)` at ℓ=2 is bit-identical to `solve_tca_closure` (W6-04) on (Θ_2, E_2) | bit-identical | 1e-14 |
| C-11 | At `Γ_T / H < threshold`, `algebraic_closure` raises `RuntimeError` | RuntimeError | exact |
| C-12 | `TCAClosure.get_closure(state, ell_requested)` (the tower-top closure) delegates identically to `inner_strategy.get_closure(...)` for all ℓ > L_max | — | 1e-14 |

### 11.4 Convergence tests (C-13..C-16)

| # | Test | Target | Tol |
|---|---|---|---|
| C-13 | `measure_closure_error(state, driver, L_ref=6, L_trunc=4, closure)`: Π_2 Frobenius norm difference is finite and > 0 on a shear-driven state | finite > 0 | — |
| C-14 | `measure_closure_error(...)` with identical L_ref == L_trunc: every returned error is exactly 0 | 0 | 1e-14 |
| C-15 | Integration smoke: each strategy produces finite, PSTF-preserving `dy/dη` at a representative Bianchi I η | finite; PSTF | 1e-10 |
| C-16 | `build_default_closure(L_max=4, strategy_name='freestream')` returns a `FreeStreamingClosure`; `strategy_name='tca'` returns a `TCAClosure` wrapping a `FreeStreamingClosure` inner; unknown name raises `ValueError` | structural | — |

---

## 12. Implementation checklist

- [ ] Review `02_multipole_hierarchy_spec.md §6` (truncation hook)
- [ ] Implement `HardCutClosure`; tests C-01 to C-03
- [ ] Implement `FreeStreamingClosure`; tests C-04 to C-06
- [ ] Implement `PowerLawExtrapolationClosure`; tests C-07 to C-08
- [ ] Implement `TCAClosure` wrapping W6-04 `solve_tca_closure`; tests C-09 to C-12
- [ ] Implement `measure_closure_error` and convergence plots; tests C-13 to C-15
- [ ] Implement `build_default_closure` factory; test C-16
- [ ] Integrate with LB-2's `hierarchy_rhs_photon`: verify all strategies plug in without additional LB-2 changes
- [ ] Full bass_py regression
- [ ] Commit as `LB-3: hierarchy truncation strategies (HardCut, FreeStream, PowerLaw, TCA)`

---

## 13. Cite map

| Component | Citations |
|---|---|
| `HardCutClosure` | Ma-Bertschinger 1995 §6 — truncation error scaling |
| `FreeStreamingClosure` | Ma-Bertschinger 1995 §6 eq (53) |
| `PowerLawExtrapolationClosure` | Kolb §9.4 — fluid approximation Π_ℓ ∝ ℓ⁻α |
| `TCAClosure` | W6-04 `quadrupole_tca.py`; lowell §10; Pontzen-Challinor 2007 §5 |
| `measure_closure_error` | Pitrou 2009 (CQG 26:065006) §4 — convergence study methodology |
| `L=6 default` recommendation | lowell §6 ("L=6 실전 baseline") |

---

## 14. What LB-3 does NOT do

- **No stiffness handling** — that is LB-5 (integrator). LB-3 provides the algebraic closure *form*; the runtime decision to use TCA vs ODE at a given η is made in LB-5's step-control logic.
- **No automatic α selection** for `PowerLawExtrapolationClosure` — caller supplies α.
- **No adaptive L**. LB-3 assumes L is fixed at construction; adaptive-L runs are a future optimisation.
- **No E/B polarization closure beyond ℓ=2** — deferred to LB-4 (collision spec) which extends the polter at higher ℓ.
