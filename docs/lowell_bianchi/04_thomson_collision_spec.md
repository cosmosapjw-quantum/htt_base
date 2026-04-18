# LB-4 — Thomson Collision Operator Specification

**Session LB-4**. Extends `bass/collision/thomson_tensor.py` and LB-2's `CollisionOperator` interface to provide the full PSTF Thomson collision source for the multipole hierarchy.

**Prerequisites**:
- LB-0 (`00_conventions.md`) — frame split rule (§4)
- LB-2 (`02_multipole_hierarchy_spec.md`) — `CollisionOperator` Protocol, `PSTFHierarchyState`
- Y-Block `bass.tilt.species_tilt` — for tilted collision frame handling
- `bass.collision.thomson_tensor` (existing W3) — the scalar-level Thomson rate machinery
- `bass.closure.quadrupole_tca` (W6-04) — the ℓ=2 TCA form (used as cross-check)

**Size estimate**: ~400 LoC implementation + ~300 LoC tests.

**Reference material**:

- **Ellis §5.5** — Thomson scattering tensor and its 1+3 decomposition
- **Kolb §5.1** — Boltzmann equation, collision integrals
- **Kolb §5.4** — recombination (Thomson damping evolution)
- **Kolb §6.4** — simplified Boltzmann equations with Thomson source
- **Chandrasekhar 1960** "Radiative Transfer" Ch IX — original classical Thomson kernel derivation
- **Zaldarriaga & Seljak 1997** (arXiv:astro-ph/9609170) — polarization coupling T ↔ E at ℓ=2
- **Portsmouth-Bertschinger** 2004 (arXiv:astro-ph/0412094) — covariant Thomson source in PSTF form
- **lowell §4, §9.2, §11** — project-specific Thomson tensor expressions

---

## Table of contents

1. Physical content
2. PSTF form of the Thomson source
3. Frame issue: electron rest frame vs n^a frame
4. Monopole, dipole, quadrupole sources
5. Polter coupling (E-mode)
6. Higher-ℓ damping
7. Tight-coupling limit check
8. Tilted extension (deferred to LB-4b)
9. Data contracts
10. Test criteria
11. Implementation checklist
12. Cite map

---

## 1. Physical content

Thomson scattering of photons off non-relativistic electrons has a classical differential cross-section

```
dσ / dΩ = (r_e² / 2) × (1 + cos² θ)
```

where `r_e = e² / (m_e c²)` is the classical electron radius and θ is the scattering angle in the electron rest frame. Integrated total cross section is the Thomson cross section

```
σ_T = (8π / 3) r_e² ≈ 6.6524587321 × 10⁻²⁹ m²
```

(Kolb eq 5.2). The rate per photon is

```
Γ_T(x, η) = n_e(x, η) × x_e(x, η) × σ_T × a(η)
```

conformal-time rate in Mpc⁻¹ units. At *background* level (homogeneous), `n_e` and `x_e` are functions of η only; `bass.recombination.recombination_ingest` supplies this as `τ̇(z)`.

For photons in a thermal bath with temperature T_γ, the Thomson interaction is:

- **Elastic in photon energy to O(v_e / c)** — Compton scattering preserves energy at classical level
- **Isotropic in angle to O(v_e / c)** — the (1 + cos²θ) modulation introduces the polter coupling
- **Linear in photon distribution**

The key O(v_e²) corrections are ignored at LB-4 scope (they are second-order SW / non-standard-model effects; cf Challinor-van Leeuwen 2002).

---

## 2. PSTF form of the Thomson source

In the 1+3 covariant PSTF formalism (Ellis §5.5, Portsmouth-Bertschinger 2004 §3), the collision term entering the brightness moment hierarchy reads

```
[ D Π_{A_ℓ} / D η ]_coll = Γ_T × M_ell × Π_{A_ℓ}  +  source terms
```

where the **moment-decay structure** M_ell is:

| ℓ | M_ell (coefficient on Π_{A_ℓ} itself) | Source term |
|---|---|---|
| 0 | 0 | 0 (monopole conserved) |
| 1 | −1 | +v_b (baryon velocity — drives dipole) |
| 2 | −9/10 | −(√6/10) E_2 (polter coupling) |
| ≥3 | −1 | 0 |

Meanwhile for E-mode polarization:

| ℓ | Collision coefficient on E_ell | Source |
|---|---|---|
| 2 | −2/5 | −(3/(5√6)) Θ_2 |
| ≥3 | −1 (standard damping) | 0 |

These are the canonical LCDM coefficients from Ma-Bertschinger 1995 (their eq 63–65), Dodelson 2003 Ch 5, and Zaldarriaga-Seljak 1997. **The coefficients are universal** across FLRW and Bianchi — the specifically-Bianchi part is in the *kinematic* terms of the hierarchy RHS (LB-2), not in the collision source.

**LB-4's task** is to implement this *as a PSTF tensor source* on the `PSTFHierarchyState`, using the frame-split rule from LB-0.

---

## 3. Frame issue: electron rest frame vs n^a frame

Per LB-0 `§4` — "transport in n^a, collision in u_e^a". The Thomson tensor is most simply expressed in the **electron rest frame** (Ellis §5.5). For *orthogonal* Bianchi, where u_e^a = n^a, the two frames coincide and the collision source can be written directly in the hierarchy basis.

For *tilted* backgrounds (baryon species with `v_b^a ≠ 0`), the electron 4-velocity is

```
u_e^a = γ_e (n^a + v_e^a)
```

and the Thomson tensor evaluated in u_e^a frame must be **boosted back** to the n^a frame for use in the hierarchy RHS. This boost affects the dipole source (`K_1` becomes `Γ_T (v_b − Π_1)` *in the electron frame*, which in the n^a frame picks up O(v_e) corrections) and higher ℓ.

**LB-4 scope**: orthogonal-only (v_e = 0 at background). Tilted extension is **LB-4b**.

---

## 4. Monopole, dipole, quadrupole sources

### 4.1 Monopole (ℓ = 0)

**K_0 = 0**. Thomson scattering conserves photon number; at the monopole level (the total intensity) the collision term is identically zero.

Implementation: a no-op in LB-4.

### 4.2 Dipole (ℓ = 1)

**K_1 = Γ_T (v_b − Π_1)** where v_b is the baryon bulk 3-velocity and Π_1 is the photon dipole 3-vector.

This is the **Compton drag** — the collision source at ℓ=1 drives Π_1 toward v_b at rate Γ_T. In the tight-coupling regime, Π_1 ≈ v_b and photons co-move with baryons.

In PSTF form, v_b enters via its 3-vector components transformed into the real-spherical-harmonic basis:

```
K_1^{i}      = Γ_T × (v_b^{i} − Π_1^{i})
K_1^{m=−1}  = Γ_T × (v_b^{m=−1} − Π_1^{m=−1})
K_1^{m= 0}  = Γ_T × (v_b^{m= 0} − Π_1^{m= 0})
K_1^{m=+1}  = Γ_T × (v_b^{m=+1} − Π_1^{m=+1})
```

Implementation (LB-4):

```python
def K_dipole(state: PSTFHierarchyState,
              v_b_real_sph: np.ndarray,   # (3,) in real-SH basis
              Gamma_T: float) -> PSTFTensor:
    """K_1 = Γ_T (v_b − Π_1), all (3,) components."""
    Pi_1 = state.tensors[1]
    comps = Gamma_T * (v_b_real_sph - Pi_1.components)
    return PSTFTensor(ell=1, components=comps)
```

### 4.3 Quadrupole (ℓ = 2)

**K_2 = −Γ_T × (9/10) × Π_2 − Γ_T × (√6/10) × E_2** — the quadrupole damps at rate 9 Γ_T / 10 and couples to the E-mode.

The full (2ℓ+1=5) component form in the real-SH basis:

```python
def K_quadrupole(state: PSTFHierarchyState,
                  E2_real_sph: np.ndarray,  # (5,) real-SH of E_2
                  Gamma_T: float) -> PSTFTensor:
    """K_2 = -Γ_T × (9/10) × Π_2 - Γ_T × (√6/10) × E_2."""
    Pi_2 = state.tensors[2]
    sqrt6 = np.sqrt(6.0)
    comps = Gamma_T * (-(9.0 / 10.0) * Pi_2.components
                         - (sqrt6 / 10.0) * E2_real_sph)
    return PSTFTensor(ell=2, components=comps)
```

### 4.4 Higher ℓ (ℓ ≥ 3)

**K_ℓ = −Γ_T × Π_ℓ** — full Thomson damping, no source.

```python
def K_high_ell(state: PSTFHierarchyState,
                ell: int,
                Gamma_T: float) -> PSTFTensor:
    """K_ℓ = -Γ_T × Π_ℓ for ℓ ≥ 3."""
    Pi_ell = state.tensors[ell]
    return PSTFTensor(ell=ell, components=-Gamma_T * Pi_ell.components)
```

---

## 5. Polter coupling (E-mode)

The E-mode multipole E_ℓ has its own Thomson collision source. At ℓ=2, the E-mode couples to the temperature quadrupole Π_2:

```
[ D E_2 / D η ]_coll = −Γ_T × (2/5) × E_2 − Γ_T × (3/(5√6)) × Π_2
```

For ℓ ≥ 3, standard damping:

```
[ D E_ℓ / D η ]_coll = −Γ_T × E_ℓ
```

**Design choice**: LB-4 tracks E_ℓ as a **second PSTF hierarchy state** alongside the temperature tower. A parallel `PSTFHierarchyState` instance for E (and later B) mode.

```python
@dataclass
class PolarizationHierarchyState:
    """E-mode PSTF tower.  B-mode is zero for scalar modes in FLRW but
    can be non-zero in Bianchi — tracked separately (LB-4 scope: E only;
    B is LB-4c).
    """
    E: PSTFHierarchyState

def K_E_quadrupole(E_state: PolarizationHierarchyState,
                    Pi_2: PSTFTensor,  # temperature quadrupole
                    Gamma_T: float) -> PSTFTensor:
    """K^E_2 = -Γ_T × (2/5) E_2 - Γ_T × (3/(5√6)) Π_2."""
    E_2 = E_state.E.tensors[2]
    sqrt6 = np.sqrt(6.0)
    comps = Gamma_T * (-(2.0/5.0) * E_2.components
                         - (3.0 / (5.0*sqrt6)) * Pi_2.components)
    return PSTFTensor(ell=2, components=comps)
```

---

## 6. Higher-ℓ damping

For ℓ ≥ 3, both Π_ℓ (temperature) and E_ℓ receive a simple exponential-damping source:

```
K_ℓ     = −Γ_T × Π_ℓ       (ℓ ≥ 3)
K^E_ℓ   = −Γ_T × E_ℓ       (ℓ ≥ 3)
```

The high-ℓ damping is strong — Π_ℓ ∝ exp(−∫ Γ_T dη) — so at pre-recombination the photon tower is effectively truncated dynamically. This is where the tight-coupling approximation (§7) becomes useful.

---

## 7. Tight-coupling limit check

In the TCA limit Γ_T η ≫ 1, setting dΠ_2/dη = dE_2/dη = 0 and solving the 2×2 coupled system gives the W6-04 closure (LB-3 TCAClosure). The LB-4 collision operator must **reproduce the Y-Block cross-check values** when Γ_T → ∞.

Test:

```python
def test_TCA_limit_matches_W6_04():
    """When Γ_T is large and d/dη ≈ 0, the LB-4 collision source
    balances the non-collision source, giving (Θ_2, E_2) values that
    match W6-04 solve_tca_closure exactly."""
    ...
```

This is the **critical integration test** between LB-4 and LB-3 / W6-04.

---

## 8. Tilted extension (LB-4b, deferred)

At tilted background, the electron 4-velocity is `u_e^a = γ_e (n^a + v_e^a)` with `v_e^a ≠ 0`. The Thomson tensor evaluated in the u_e^a frame must be Lorentz-boosted to the n^a frame. The leading correction is:

- **Dipole source**: `K_1 = Γ_T (v_b − Π_1)` becomes `K_1 = Γ_T (v_b − Π_1) + O(v_e) corrections from boost`.
- **Visibility**: becomes direction-dependent `g̃(η, e) = Γ̃_T × exp(−κ̃(e))` (lowell §11.3).

LB-4b spec details:

- Extension adds `BoostedThomsonCollisionOperator` that takes `v_e^a(η)` from the species registry (tilted extension LB-1b).
- Boost rule for PSTF moments: `Ĩ_{A_ℓ} = h̃_{⟨A_ℓ⟩}^{B_ℓ} I_{B_ℓ} + O(v_e) corrections` (lowell §13.5 eq).
- Integration with the collisionless transport (LB-2) requires a boost at each step.

LB-4b is ~400 LoC + tests, 1 session.

---

## 9. Data contracts

### 9.1 Module file layout

```
bass_py/bass/collision/
├── thomson_tensor.py              — existing W3 (retain)
├── thomson_pstf.py                — NEW: PSTF Thomson collision operator
├── polarization.py                — NEW: E-mode / polter machinery
├── test_thomson_tensor.py          — existing
├── test_thomson_pstf.py           — NEW
└── test_polarization.py           — NEW
```

### 9.2 Public API

```python
from bass.collision.thomson_pstf import (
    ThomsonPSTFCollisionOperator,
    apply_thomson_collision,
)
from bass.collision.polarization import (
    PolarizationHierarchyState,
    E_mode_collision_source,
)

class ThomsonPSTFCollisionOperator:
    """Thomson collision source for the photon PSTF multipole tower
    (temperature + E-mode).

    At ℓ = 0: K = 0 (monopole conserved)
    At ℓ = 1: K_1 = Γ_T (v_b − Π_1)
    At ℓ = 2: K_2 = -Γ_T (9/10) Π_2 - Γ_T (√6/10) E_2
              K^E_2 = -Γ_T (2/5) E_2 - Γ_T (3/(5√6)) Π_2
    At ℓ ≥ 3: K_ℓ = -Γ_T Π_ℓ, K^E_ℓ = -Γ_T E_ℓ

    Reference: Ma-Bertschinger 1995 eq (63-65); Zaldarriaga-Seljak
    1997; Ellis §5.5; lowell §9.2.
    """

    def evaluate_temperature(self,
                              state: PSTFHierarchyState,
                              E_state: PolarizationHierarchyState,
                              v_b_real_sph: np.ndarray,
                              Gamma_T: float,
                              ) -> PSTFHierarchyState:
        """Return the full K_{A_ℓ} tower for temperature."""
        ...

    def evaluate_polarization(self,
                               state: PSTFHierarchyState,
                               E_state: PolarizationHierarchyState,
                               Gamma_T: float,
                               ) -> PSTFHierarchyState:
        """Return the full K^E_{A_ℓ} tower for E-mode."""
        ...
```

### 9.3 Integration with LB-2

LB-2's `hierarchy_rhs_photon` accepts a `collision: CollisionOperator`. LB-4 provides the concrete `ThomsonPSTFCollisionOperator`. No structural change to LB-2 is needed; LB-4 is purely a plug-in.

---

## 10. Test criteria

### 10.1 Monopole / dipole / quadrupole tests

| # | Test | Target | Tol |
|---|---|---|---|
| TC-01 | K_0 ≡ 0 regardless of state | 0 | exact |
| TC-02 | K_1 at Π_1 = v_b: K_1 = 0 | 0 | 1e-15 |
| TC-03 | K_1 at v_b = 0, Π_1 ≠ 0: K_1 = −Γ_T × Π_1 | exact | 1e-12 |
| TC-04 | K_2 at E_2 = 0, Π_2 ≠ 0: K_2 = −(9/10) Γ_T Π_2 | exact | 1e-12 |
| TC-05 | K_2 at Π_2 = 0, E_2 ≠ 0: K_2 = −(√6/10) Γ_T E_2 | exact | 1e-12 |
| TC-06 | K^E_2 at Π_2 = 0, E_2 ≠ 0: K^E_2 = −(2/5) Γ_T E_2 | exact | 1e-12 |
| TC-07 | K^E_2 at Π_2 ≠ 0, E_2 = 0: K^E_2 = −(3/(5√6)) Γ_T Π_2 | exact | 1e-12 |
| TC-08 | K_3 = −Γ_T × Π_3 | exact | 1e-12 |
| TC-09 | K^E_3 = −Γ_T × E_3 | exact | 1e-12 |

### 10.2 TCA limit test

| # | Test | Target | Tol |
|---|---|---|---|
| TC-10 | When dΠ_2/dη = dE_2/dη = 0, solving K_2 + S_T = 0 and K^E_2 + S_E = 0 gives (Θ_2, E_2) matching `solve_tca_closure(S_T, S_E, Γ_T)` from W6-04 | bit-identical | 1e-14 |
| TC-11 | The canonical polter ratio E_2 / Θ_2 = −√6/4 at S_E = 0 reproduces (already in Y-Block) | −√6/4 | 1e-12 |

### 10.3 Frame consistency

| # | Test | Target | Tol |
|---|---|---|---|
| TC-12 | At v_e = 0 (orthogonal), LB-4 collision matches electron-frame source tensor trivially | — | exact |
| TC-13 | PSTF packing: component at m = 0 for axisymmetric Π_2 corresponds to (real) Θ_2 in the W6-04 scalar convention | — | 1e-14 |

### 10.4 Integration consistency with LB-2

| # | Test | Target | Tol |
|---|---|---|---|
| TC-14 | Plugging `ThomsonPSTFCollisionOperator` into `hierarchy_rhs_photon` and integrating: at Γ_T → ∞, tower reaches TCA equilibrium | matches LB-3 `TCAClosure` | 1% |
| TC-15 | At Γ_T = 0, `ThomsonPSTFCollisionOperator` returns zero everywhere, LB-2 RHS reduces to free-streaming | 0 | exact |

### 10.5 Higher-ℓ damping

| # | Test | Target | Tol |
|---|---|---|---|
| TC-16 | Exponential decay rate at ℓ ≥ 3: τ_decay = 1/Γ_T | matches analytical | 1e-10 at ℓ=3, 1e-8 at ℓ=8 |

Total: 16+ tests.

---

## 11. Implementation checklist

- [ ] Review LB-0 §4 (frame split rule) and LB-2 §7 (CollisionOperator protocol)
- [ ] Implement `bass/collision/polarization.py` with `PolarizationHierarchyState` dataclass and `E_mode_collision_source` function; tests TC-06, TC-07
- [ ] Implement `bass/collision/thomson_pstf.py` with `ThomsonPSTFCollisionOperator` class; tests TC-01 through TC-09
- [ ] Implement TCA-limit test (TC-10, TC-11) as cross-check with W6-04
- [ ] Add integration tests (TC-14, TC-15) verifying LB-2 + LB-4 compose correctly
- [ ] Full bass_py regression
- [ ] Commit as `LB-4: Thomson PSTF collision source with E-mode coupling`

---

## 12. Cite map

| Component | Citations |
|---|---|
| `ThomsonPSTFCollisionOperator` docstring | Ellis §5.5; Ma-Bertschinger 1995 eq (63–65); Zaldarriaga-Seljak 1997 eq (7); lowell §4, §9.2 |
| `K_dipole` | Kolb §5.1 eq (5.8) (Compton drag form); Ma-Bertschinger 1995 eq (63) |
| `K_quadrupole` | Zaldarriaga-Seljak 1997 eq (7); Portsmouth-Bertschinger 2004 §3 |
| `K_E_quadrupole` | Zaldarriaga-Seljak 1997 eq (17); Ma-Bertschinger 1995 eq (64) |
| `K_high_ell` | Kolb §6.4 eq (6.47) |
| TCA limit consistency with W6-04 | Y-Block `test_reference_cross_check.py`; lowell §10 |

---

## 13. What LB-4 does NOT do

- **Does not implement B-mode**: B ≡ 0 for scalar-mode sources in LCDM. In Bianchi, scalar B is still zero but *tensor-mode* B is non-zero; deferred to LB-4c.
- **Does not handle tilted visibility**: visibility becomes direction-dependent `g̃(η, e)` for tilted backgrounds; LB-4b.
- **Does not solve the combined (Θ_2, E_2) algebraic system**: that's LB-3 TCAClosure + W6-04.
- **Does not extract C_ℓ from Π_ℓ**: that's the line-of-sight projection in a later phase (after LB-6).

---

## 14. LB-4 extensions (deferred)

- **LB-4b — Tilted collision** (1 session, ~400 LoC): electron-frame evaluation + boost to n^a frame
- **LB-4c — B-mode tensor source** (1 session, ~300 LoC): non-trivial for Bianchi VIIh/VIII/IX; zero for Types I/V/VII₀
- **LB-4d — Higher-order v_e² corrections** (optional, ~200 LoC): Compton-energy-exchange at second order (Challinor-van Leeuwen)
