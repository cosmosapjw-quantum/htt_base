# LB-2 — PSTF Multipole Hierarchy Specification

**Session LB-2**. Produces `bass/hierarchy/` subpackage: the `PSTFTensor` container and the exact 1+3 covariant multipole hierarchy RHS.

**Prerequisites**:
- LB-0 (`00_conventions.md`) — PSTF packing convention (§5), shear invariant normalisation (§4)
- LB-1 `bass/species/` — species backgrounds supplying ρ_s(η), Θ(η) for the expansion term
- Y-Block `bass.background.tetrad_state.TetradBackgroundState` — σ_ab(η), ω_ab(η), ³R_ab(η)
- Y-Block `bass.tilt.species_tilt` — for tilted-frame source couplings (LB-2 uses orthogonal-only; tilted extension is LB-2b)
- Existing `bass.closure.quadrupole_tca` (W6-04) — LB-3 will reuse as ℓ=2 closure

**Size estimate**: ~1200 LoC implementation + ~700 LoC tests.

**Reference material**:

- **Ellis §4.5** — moment expansion of the photon distribution function
- **Ellis §4.6** — multipole hierarchy equations
- **Ellis §5.2** — stress-energy decomposition (as source at ℓ=0, 1, 2)
- **Ellis §18.4** — adaptation to Bianchi tetrad
- **Kolb §5.1** — Boltzmann equation in FLRW
- **Kolb §6.4** — simple Boltzmann equations and their moments
- **lowell §6** — exact equation with all couplings (this is the canonical form we implement)
- **Baumann §4.6** — linearised hierarchy (modern cleaner notation for cross-check)

---

## Table of contents

1. The hierarchy equation in full
2. PSTF tensor data structure
3. Index contractions — packed ↔ full-tensor
4. Hierarchy RHS — term by term
5. Orthogonal simplification
6. Truncation hook (forward reference to LB-3)
7. Collision hook (forward reference to LB-4)
8. Integration with TetradBackgroundState
9. Data contracts
10. Edge cases
11. Test criteria
12. Implementation checklist
13. Cite map

---

## 1. The hierarchy equation in full

The exact 1+3 covariant PSTF multipole hierarchy (from Ellis §4.6, also lowell reference §6) for a distribution-function moment `Π_{A_ℓ}` (brightness = energy-integrated perturbation) is

```
Π̇_{⟨A_ℓ⟩}
    + (4/3) Θ Π_{A_ℓ}                                                              [T1: expansion]
    + ∇̃_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}                                                        [T2: gradient]
    + ((ℓ+1) / (2ℓ+3)) ∇̃^b Π_{A_ℓ b}                                               [T3: divergence]
    − ((ℓ+1)(ℓ−2) / (2ℓ+3)) A^b Π_{A_ℓ b}                                          [T4: accel × divergence]
    + (ℓ+3) A_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}                                                  [T5: accel × gradient]
    + ℓ ω^b η_{bc⟨a_ℓ} Π_{A_{ℓ−1}⟩}^{c}                                            [T6: vorticity × dipole-level]
    − ((ℓ−1)(ℓ+1)(ℓ+2) / ((2ℓ+3)(2ℓ+5))) σ^{bc} Π_{A_ℓ bc}                         [T7: shear → ℓ+2]
    + (5ℓ / (2ℓ+3)) σ^b_{⟨a_ℓ} Π_{A_{ℓ−1}⟩ b}                                      [T8: shear stays at ℓ]
    − (ℓ+2) σ_{⟨a_ℓ a_{ℓ−1}} Π_{A_{ℓ−2}⟩}                                          [T9: shear → ℓ−2]
= K_{A_ℓ}                                                                          [collision source]
```

Notation:
- **ℓ ≥ 0**. For ℓ = 0, 1, 2 several terms drop because indexed quantities require `ℓ ≥ N` for some N (explicit in code via conditionals).
- `Π_{⟨A_ℓ⟩}` is the **PSTF projection** of `Π_{A_ℓ}` (symmetrise on spatial indices then remove traces). Applied to make the equation self-consistent at each ℓ.
- **Overdot** `Π̇` = `u^a ∇_a Π` = time derivative along the congruence. In η-parameterisation this is `Π'(η) / a(η)` where prime = d/dη. See §4.1 below.
- **Spatial derivative** `∇̃_a` = `h_a^b ∇_b` — projected onto the hypersurface orthogonal to u^a.
- **Kinematic variables** Θ, σ_ab, ω_ab, A_a as defined in `00_conventions.md §3`.
- `η_{bc a}` is the spatial 3-Levi-Civita (not to be confused with conformal time η). It appears **only** with vorticity.

### 1.1 Special cases by ℓ

For our low-ℓ tower (L ≤ 8) we get simplified versions:

| ℓ | Active terms | Dropped terms | Remark |
|---|---|---|---|
| 0 (monopole Π) | T1, T3 | T2, T4, T5, T6, T7, T8, T9 require ℓ ≥ 1 or 2 | monopole only sees expansion and divergence of dipole |
| 1 (dipole Π_a) | T1, T2, T3, T4, T5, T6, T8, T9 | T7 requires ℓ+2 ≤ L; T9 needs ℓ−2 ≥ 0 → drops | dipole has acceleration and shear-to-monopole terms |
| 2 (quadrupole Π_ab) | all 9 terms | (T9 connects to monopole: `σ_{⟨ab⟩} Π`) | **the shear-injection term −4 σ_ab Π drives the quadrupole in tilted Bianchi** |
| 3..L | all 9 terms | T9 truncates naturally when ℓ−2 exists | standard free-streaming tower |
| L (truncation) | T1, T2, T4, T5, T6, T8, T9 only | T3 and T7 refer to Π_{ℓ+1} and Π_{ℓ+2} — closure (LB-3) fills these | **truncation residual** |

### 1.2 Collision source K_{A_ℓ}

For photons at ℓ ≤ 2:

```
K_0       = 0                                                    (monopole conserved by Thomson)
K_1       = Γ_T × (v_b − Π_1)                                    (Doppler drag on dipole)
K_2       = −Γ_T × (9/10) Π_2 − Γ_T × (√6/10) E_2                (Thomson damping + polter)
K_{ℓ ≥ 3} = −Γ_T × Π_{A_ℓ}                                       (full Thomson damping)
```

The polter term `E_2` comes from the E-mode multipole, coupled at ℓ = 2. For LB-2 the scalar `E_2` is carried as a parallel variable; LB-4 spec'd the full polarization coupling in detail.

For neutrinos: `K_{A_ℓ} = 0` for all ℓ (collisionless after decoupling). LB-2 uses the same hierarchy machinery for ν with Γ_T = 0 passed in.

---

## 2. PSTF tensor data structure

### 2.1 Data layout

```python
# bass/hierarchy/pstf_tensor.py

@dataclass
class PSTFTensor:
    """A rank-ℓ projected symmetric trace-free tensor on 3-space.

    Storage: (2ℓ+1,) packed array of "spherical-harmonic" amplitudes
    aligned with the tetrad basis from tetrad_state.

    Component index mapping:
      i = 0, 1, ..., 2ℓ   ↔   m = -ℓ, -ℓ+1, ..., 0, ..., +ℓ-1, +ℓ

    For ℓ = 0: one real component (the scalar moment).
    For ℓ = 1: three components corresponding to m = -1, 0, +1.
    For ℓ = 2: five components (the axisymmetric m=0 plus m = ±1, ±2).
    ...

    Reference: 00_conventions.md §5 for packing convention;
               Ellis §4.5.2 for moment decomposition.
    """
    ell: int
    components: np.ndarray  # shape (2*ell + 1,), dtype float64 (or complex for m ≠ 0?)

    def __post_init__(self):
        if self.ell < 0:
            raise ValueError(f"ell must be non-negative, got {self.ell}")
        if self.components.shape != (2 * self.ell + 1,):
            raise ValueError(
                f"components shape {self.components.shape} != (2ℓ+1,) "
                f"= ({2*self.ell+1},)"
            )
```

**Real vs complex components**. Two choices:

1. **Real packing** — store (2ℓ+1) real numbers with the convention that m = 0 is the central entry, and ±m entries pair up to form real and imaginary parts of the spherical-harmonic coefficient. Compact but awkward for tensor operations.
2. **Real spherical harmonics basis** — replace {Y_ℓm} with real basis {Y_ℓm^R, Y_ℓm^I}. All (2ℓ+1) components stay purely real.

**LB-2 choice: real spherical harmonics basis**. Rationale: shear σ_ab and vorticity ω_ab are real 3-tensors, and the physical Π_{A_ℓ} are real PSTF tensors; using real basis avoids casting complex → real at every step. Standard reference: Arfken-Weber-Harris "Mathematical Methods" Ch 16 on real spherical harmonics.

### 2.2 Invariants

Post-construction `PSTFTensor` guarantees:

1. `len(components) == 2*ell + 1`
2. `dtype == np.float64` (enforced in `__post_init__`)
3. Zero-tensor of any rank is valid: `PSTFTensor(ell=3, components=np.zeros(7))`

Invariants **not** checked in `__post_init__` (too expensive):
- The full-tensor form actually being symmetric-trace-free. Use `verify_pstf_invariants()` as an explicit diagnostic.

### 2.3 Construction factories

```python
def zero_pstf(ell: int) -> PSTFTensor:
    return PSTFTensor(ell=ell, components=np.zeros(2*ell+1, dtype=np.float64))


def pstf_from_tensor(tensor: np.ndarray) -> PSTFTensor:
    """Convert a full (3,3,...,3) ℓ-rank tensor to packed (2ℓ+1,) PSTF.

    Ellis §4.5 Clebsch-Gordan decomposition: any rank-ℓ tensor on 3-space
    has a unique decomposition into (STF part at ℓ) ⊕ (traces at ℓ-2) ⊕ ...
    This function extracts the STF-at-ℓ part and projects it onto the
    real spherical harmonic basis.
    """
    ...


def pstf_to_tensor(pstf: PSTFTensor) -> np.ndarray:
    """Inverse of pstf_from_tensor: produce the (3,3,...,3) full tensor."""
    ...
```

The explicit transformation matrices for ℓ = 0, 1, 2, 3, 4, 5, 6, 7, 8 are pre-computed at import time and cached; this keeps the forward-backward symmetric trip exact to machine precision.

### 2.4 Arithmetic

```python
class PSTFTensor:
    def __add__(self, other: 'PSTFTensor') -> 'PSTFTensor':
        if self.ell != other.ell:
            raise ValueError(f"ℓ mismatch: {self.ell} vs {other.ell}")
        return PSTFTensor(ell=self.ell, components=self.components + other.components)

    def __mul__(self, scalar: float) -> 'PSTFTensor':
        return PSTFTensor(ell=self.ell, components=self.components * scalar)

    def norm(self) -> float:
        """||Π||² = Π_{A_ℓ} Π^{A_ℓ} — scalar invariant."""
        return float(np.sum(self.components ** 2))
```

Tensor contractions (needed by T7–T9 in §1) are not methods on PSTFTensor but utility functions in `bass/hierarchy/contractions.py` — see §3.

### 2.5 Tower container

A full multipole tower up to L is

```python
@dataclass
class PSTFHierarchyState:
    """A full tower {Π_0, Π_1, ..., Π_L} of PSTF tensors."""
    L: int                         # highest ℓ retained
    tensors: list[PSTFTensor]      # length L+1, tensors[ℓ].ell == ℓ

    def as_flat(self) -> np.ndarray:
        """Concatenate all component arrays into one 1D vector.

        This is the format consumed by scipy.integrate.solve_ivp.
        """
        return np.concatenate([t.components for t in self.tensors])

    @classmethod
    def from_flat(cls, flat: np.ndarray, L: int) -> 'PSTFHierarchyState':
        """Inverse: split a flat vector into (L+1) PSTF tensors."""
        ...

    @property
    def total_size(self) -> int:
        return sum(2*ell + 1 for ell in range(self.L + 1))
```

For L=8: total_size = 1 + 3 + 5 + 7 + 9 + 11 + 13 + 15 + 17 = 81 components per species per k. LB-2 does one species (photon) without k-dependence; LB-5 will generalise.

---

## 3. Index contractions — packed ↔ full-tensor

The nine RHS terms require various contractions. To keep code tractable, the plan is:

1. **Convert packed PSTF → full (3,…,3) tensor** for each Π in the tower
2. **Perform contractions in full-tensor form** using `np.einsum` with clear index labels
3. **Convert result back to packed PSTF** at the end

This is slightly wasteful (storage is O(3^ℓ) vs O(2ℓ+1)) but keeps the contraction code identical to the textbook form. At L=8 the full-tensor form has 3^8 = 6561 entries per Π_ℓ — still manageable.

A more efficient implementation using direct spherical-harmonic couplings (Clebsch-Gordan via Wigner 3-j coefficients) is possible but deferred to a future optimisation pass; LB-2 prioritises readability.

### 3.1 Example: term T8 (shear stays at ℓ)

```
T8_{A_ℓ} = (5ℓ / (2ℓ+3)) σ^b_{⟨a_ℓ} Π_{A_{ℓ−1}⟩ b}
```

In code:

```python
def term_T8(ell: int, Pi_ell_minus_1_full: np.ndarray, sigma_tensor: np.ndarray) -> np.ndarray:
    """T8: (5ℓ/(2ℓ+3)) σ^b_{<a_ℓ} Π_{A_{ℓ-1}> b}, returned as full tensor.

    Contract σ (3,3) with Π_{ℓ-1} (3,...,3, ℓ-1 indices) over two indices,
    then symmetrise-trace-free over the remaining ℓ indices.
    """
    prefactor = 5.0 * ell / (2.0 * ell + 3.0)
    # Contract σ^b_c with Π_{a1 a2 ... a_{ℓ-1} b}, over the last index and b
    # leaving ℓ free indices (ℓ−1 from Π plus one from σ).
    # Use einsum with explicit labels.
    ...
    # Symmetrise-trace-free
    return sym_trace_free(raw)
```

Each of the 9 terms (T1 through T9) gets its own pure function `term_Tn(ell, Pi_lm_prev, Pi_lm_curr, Pi_lm_next, Pi_lm_next_next, sigma, omega, accel, expansion)` returning a full-rank-ℓ tensor. The full RHS sums them.

### 3.2 Symmetrisation and trace removal

A utility function:

```python
def sym_trace_free(tensor: np.ndarray) -> np.ndarray:
    """Project a rank-ℓ tensor onto its symmetric-trace-free part.

    Algorithm: symmetrise by averaging over all ℓ! permutations,
    then remove traces iteratively until a PSTF projection of the
    result equals itself (numerically to tol = 1e-14).

    For ℓ = 0: returns scalar unchanged.
    For ℓ = 1: returns vector unchanged (no traces).
    For ℓ ≥ 2: iteratively removes h_{ab}-traces.
    """
```

Naive symmetrisation at ℓ = 8 has 8! = 40320 permutations — too slow. Use the Young-projector formula or a recursive symmetrisation. **Reference implementation** (deferred to LB-2 author's discretion): Ellis-Bruni-Ellis 1992, Appendix B, where explicit PSTF projectors up to ℓ = 8 are tabulated.

**Alternative (more practical)**: implement `sym_trace_free` by direct projection through the Clebsch-Gordan matrices (inverting §2.3 `pstf_from_tensor` + `pstf_to_tensor`). This side-steps the permutation explosion.

---

## 4. Hierarchy RHS — term by term

### 4.1 Time derivative convention

We work in conformal-time η. The covariant overdot is

```
Π̇ = u^a ∇_a Π
```

which for `u^a = n^a` in an FLRW-like frame reduces to

```
Π̇ = (1 / a) × Π'(η)         where prime = d/dη
```

The LHS of the hierarchy equation is **Π̇_{⟨A_ℓ⟩}** — the PSTF projection of the overdot. In code:

```python
def rhs_term_dot_Pi(ell: int, dPi_deta_full: np.ndarray, a: float) -> np.ndarray:
    """LHS time-derivative term in η-parameterisation."""
    return sym_trace_free(dPi_deta_full / a)
```

The full hierarchy RHS is then:

```python
def hierarchy_rhs_photon(
    eta: float,
    state: PSTFHierarchyState,
    E2_components: np.ndarray,          # E-mode ℓ=2 polarisation components
    bg_table: FLRWBackgroundTable,
    tetrad_state: TetradBackgroundState,
    v_b_dipole: np.ndarray,             # (3,) baryon velocity for Thomson drag
    tau_dot: float,                     # a n_e σ_T at this η
    L_max: int,
    closure_strategy: 'ClosureStrategy',  # LB-3
) -> np.ndarray:
    """dstate/dη for the photon brightness tower.

    Computes:
        Π̇_{A_ℓ} = −(4/3) Θ Π_{A_ℓ}
                  − ∇̃_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}
                  − ((ℓ+1)/(2ℓ+3)) ∇̃^b Π_{A_ℓ b}
                  + (shear/vorticity/accel terms)
                  + K_{A_ℓ}

    Returns a flat vector matching state.as_flat() shape.
    """
    ...
```

### 4.2 Term-by-term implementation

Each term `T1` through `T9` is a pure function taking the tower, kinematic variables, and returning the contribution at ℓ:

```python
# bass/hierarchy/terms.py

def T1_expansion(ell: int, Pi_ell_full: np.ndarray, Theta: float) -> np.ndarray:
    """(4/3) Θ Π_{A_ℓ}"""
    return (4.0 / 3.0) * Theta * Pi_ell_full


def T2_gradient(ell: int, Pi_ell_minus_1_full: np.ndarray,
                 nabla_operator: Callable) -> np.ndarray:
    """∇̃_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}. The ∇̃ operator is supplied by the
    caller — at the Bianchi tetrad level it reduces to specific
    structure-constant contractions (Ellis §18.4).
    """
    if ell == 0:
        return np.zeros(())  # no ℓ-1 = -1 tensor
    ...


def T3_divergence(ell: int, Pi_ell_plus_1_full: np.ndarray,
                   nabla_operator: Callable) -> np.ndarray:
    """((ℓ+1)/(2ℓ+3)) ∇̃^b Π_{A_ℓ b}"""
    ...


# ... T4 through T9 similarly
```

**Key**: at background level (orthogonal Bianchi, u^a = n^a on the homogeneous hypersurface), the spatial-derivative operator `∇̃` reduces to the **structure-constant contraction** `C^i_{jk} Π^{...}`. The expression is concretely:

```
∇̃^b Π_{A_ℓ b} = (1/a) × e^{αi}(C^i_{bk} - δ^i_k C^m_{mb}) × Π_{A_ℓ ...}^{...b}
```

For Types I, V, VII₀ (class A with flat or open ³R) this simplifies dramatically. Details in `02_multipole_hierarchy_spec` extension file LB-2a (separate doc if deep type dispatch becomes unwieldy).

**LB-2 implementation shortcut**: because we are at background (no k-dependence), `∇̃ Π = 0` at the FLRW limit (all spatial gradients vanish by homogeneity). For Bianchi I with orthogonal shear, **∇̃-terms in the background are exactly zero** — the structure constants are all zero. This drops terms T2 and T3 entirely for Bianchi I background.

**Non-trivial at background** for Types V, VI_h, VII_h, VIII, IX where `a_i ≠ 0` or n_i have non-vanishing diagonal elements. LB-2 handles **Types I, V, VII₀** first; other types return `NotImplementedError` from the `∇̃` operator (as in Y-Block).

### 4.3 Orthogonal-Bianchi simplification

For orthogonal Bianchi (u^a = n^a, `A_a = ω_a = 0`), the hierarchy equation (§1) drops terms T4, T5, T6 entirely:

```
Π̇_{⟨A_ℓ⟩}
    + (4/3) Θ Π_{A_ℓ}                          [T1]
    + ∇̃_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}                    [T2 — zero for Types I if structure const = 0]
    + ((ℓ+1)/(2ℓ+3)) ∇̃^b Π_{A_ℓ b}              [T3 — zero for Types I]
    − ((ℓ−1)(ℓ+1)(ℓ+2)/((2ℓ+3)(2ℓ+5))) σ^{bc} Π_{A_ℓ bc}  [T7]
    + (5ℓ/(2ℓ+3)) σ^b_{⟨a_ℓ} Π_{A_{ℓ−1}⟩ b}     [T8]
    − (ℓ+2) σ_{⟨a_ℓ a_{ℓ−1}} Π_{A_{ℓ−2}⟩}       [T9]
= K_{A_ℓ}
```

For **Bianchi I flat orthogonal** this reduces further to just T1, T7, T8, T9 + collision. This is the baseline LB-2 scenario — we integrate the photon brightness tower for Bianchi I with a single vector Σ_+ of shear turning on T7/T8/T9 couplings.

---

## 5. Orthogonal-only activation in LB-2

LB-2 **only implements orthogonal Bianchi** (u^a = n^a for all species). Tilted species are deferred to LB-2b.

Explicitly:

- The `v_b_dipole` argument in `hierarchy_rhs_photon` represents the *perturbation dipole* (small deviation from homogeneity), not a background tilt. At *background* level we will have `v_b = 0`; the dipole is injected by the shear-quadrupole coupling T9 and the `K_1 = Γ_T (v_b − Π_1)` collision source.
- The `A_a` (4-acceleration) and `ω_a` (vorticity) kinematic variables are zero at Type I, V, VII_0 orthogonal.
- Tilted extension (LB-2b) will activate `u_(s)^a = γ_s (n^a + v_(s)^a)` and the corresponding collision-frame boost.

---

## 6. Truncation hook (forward reference to LB-3)

The hierarchy RHS at ℓ = L references Π_{L+1} (in T3 and T7). LB-3 provides closure strategies:

```python
# In hierarchy_rhs_photon:
if ell == L_max:
    Pi_ell_plus_1_full = closure_strategy.closure_next(state, ell)
    Pi_ell_plus_2_full = closure_strategy.closure_next_next(state, ell)
else:
    Pi_ell_plus_1_full = pstf_to_tensor(state.tensors[ell + 1])
    Pi_ell_plus_2_full = pstf_to_tensor(state.tensors[ell + 2]) if ell + 2 <= L_max else zero

```

Strategies available from LB-3:
- `HardCutClosure` — Π_{L+1} = 0 (crude but simple)
- `FreeStreamingClosure` — Π_{L+1} from the ℓ = L equation in the free-streaming limit
- `TCAClosure` at ℓ = 2 — the W6-04 quadrupole closure (already in bass_py)

LB-2 ships with `HardCutClosure` as the default; the interface accepts any strategy.

---

## 7. Collision hook (forward reference to LB-4)

The collision source `K_{A_ℓ}` is computed by a pluggable collision operator:

```python
class CollisionOperator(Protocol):
    def evaluate(self, ell: int, state: PSTFHierarchyState,
                 E2: np.ndarray, v_b: np.ndarray, tau_dot: float) -> np.ndarray:
        ...
```

LB-2 ships with `ThomsonCollisionOperator` from the existing `bass.collision.thomson_tensor`; LB-4 will extend it to the full PSTF form with E-mode coupling at ℓ = 2.

---

## 8. Integration with TetradBackgroundState

The hierarchy RHS consumes:

| Input | Source | Access pattern |
|---|---|---|
| Θ(η) | `FLRWBackgroundTable.Theta` (LB-1) | interpolated scalar |
| σ_ab(η) | `TetradBackgroundState.sigma_tensor` (Y-Block) | full (3,3) array, nearest-grid lookup or spline |
| ω_ab(η) | `TetradBackgroundState` (Y-Block; currently zero for supported types) | (3,3), zero for Types I, V, VII₀ |
| A_a(η) | — (zero at background for orthogonal Bianchi) | |
| a(η) | `FLRWBackgroundTable.a` | scalar |
| Γ_T = τ̇(η) | `BaryonBackground` (LB-1) | scalar |

For `σ_ab(η)` interpolation, LB-2 should use `CubicSpline` applied to each (i, j) component independently (9 splines; 6 independent due to symmetry). `tetrad_state` stores on a grid — splines are built at LB-5 integrator setup time.

---

## 9. Data contracts

### 9.1 Module file layout

```
bass_py/bass/hierarchy/
├── __init__.py
├── pstf_tensor.py          — PSTFTensor, PSTFHierarchyState, pstf_from_tensor, pstf_to_tensor
├── contractions.py         — sym_trace_free and packed-full conversions
├── terms.py                — T1...T9 pure functions
├── hierarchy_rhs.py        — hierarchy_rhs_photon, hierarchy_rhs_neutrino drivers
├── collision_interface.py  — CollisionOperator Protocol + ThomsonCollisionOperator adapter
├── closure_interface.py    — ClosureStrategy Protocol + HardCutClosure
├── test_pstf_tensor.py
├── test_contractions.py
├── test_terms.py
├── test_hierarchy_rhs.py
├── test_closure_interface.py
└── test_collision_interface.py
```

### 9.2 Public API signatures

```python
# Primary entry point
def hierarchy_rhs_photon(
    eta: float,
    y_flat: np.ndarray,                    # packed state
    L_max: int,
    bg_table: FLRWBackgroundTable,
    tetrad_state: TetradBackgroundState,
    Gamma_T_of_eta: Callable[[float], float],
    v_b_dipole_of_eta: Callable[[float], np.ndarray],
    closure: ClosureStrategy,
    collision: CollisionOperator,
) -> np.ndarray:
    """dy/dη for the photon multipole tower at one η.

    Signature is solve_ivp-compatible.  Driver LB-5 supplies the
    callable backgrounds (bg_table, tetrad_state, v_b_dipole) so
    this function is pure wrt (eta, y_flat).
    """
```

### 9.3 State vector packing

`y_flat` has shape `(sum(2ℓ+1 for ℓ in range(L_max+1)),)`. Packing order:

- Indices 0 → 0: Π_0 components (1 element)
- Indices 1 → 3: Π_1 components (3 elements)
- Indices 4 → 8: Π_2 components (5 elements)
- Indices 9 → 15: Π_3 components (7 elements)
- … and so on

Utility: `pack_pstf_hierarchy(state) → y_flat` and `unpack_pstf_hierarchy(y_flat, L_max) → state`.

---

## 10. Edge cases

1. **ℓ = 0 (monopole)**: Terms T2, T4, T5, T6, T9 require ℓ ≥ 1 and drop to zero. Verified in T1-only FLRW test.
2. **ℓ = 1 (dipole)**: Term T9 requires ℓ ≥ 2 and drops. T7 requires ℓ+2 ≤ L.
3. **L_max = 0**: only monopole tracked — valid for isotropic-only tests (T01 below).
4. **Zero shear at Bianchi I**: T7, T8, T9 all vanish by linearity. Hierarchy is FLRW-equivalent.
5. **Vorticity non-zero**: only supported for Types not yet implemented in `tetrad_state` — `NotImplementedError` from that module propagates.
6. **Γ_T = 0 (collisionless)**: all K_{A_ℓ} vanish; neutrinos use this path.
7. **Γ_T → ∞ (tight coupling)**: higher-ℓ Π_{ℓ ≥ 3} are driven to zero; dipole Π_1 → v_b/3; quadrupole Π_2, E_2 driven to their TCA values (W6-04). LB-2 integrates this **stiffly**; LB-5 handles stiffness via LSODA.

---

## 11. Test criteria

### 11.1 PSTF tensor tests (test_pstf_tensor.py)

| # | Test | Target | Tol |
|---|---|---|---|
| H-01 | `zero_pstf(ℓ)` has shape (2ℓ+1,) for ℓ ∈ 0..8 | — | exact |
| H-02 | `PSTFTensor(ℓ=2, components=np.zeros(5))` valid | — | exact |
| H-03 | `PSTFTensor(ℓ=2, components=np.zeros(4))` raises | ValueError | — |
| H-04 | `pstf_from_tensor(pstf_to_tensor(t)) == t` for ℓ = 0, 1, 2, 3 | — | 1e-14 |
| H-05 | `pstf_to_tensor(t)` is symmetric | — | 1e-14 |
| H-06 | `pstf_to_tensor(t)` is trace-free | `np.einsum('ii...', T) == 0` | 1e-14 |
| H-07 | `t + (-t) == zero_pstf(ℓ)` | — | 1e-14 |
| H-08 | `t * 2 == t + t` | — | 1e-14 |

### 11.2 Contraction tests (test_contractions.py)

| # | Test | Target | Tol |
|---|---|---|---|
| H-09 | `sym_trace_free(I)` for identity-like tensor → 0 (all trace) | 0 | 1e-14 |
| H-10 | `sym_trace_free(antisymmetric)` → 0 | 0 | 1e-14 |
| H-11 | `sym_trace_free(already PSTF)` → identity | unchanged | 1e-14 |
| H-12 | T8 at ℓ = 2 with σ = diag(Σ_+, ...) and Π_1 aligned: explicit hand-worked value | closed form | 1e-12 |

### 11.3 Term tests (test_terms.py)

| # | Test | Target | Tol |
|---|---|---|---|
| H-13 | T1 at Θ = 1, Π_2 = unit → (4/3) × unit | (4/3) × unit | exact |
| H-14 | T7 at σ = 0 → 0 for any Π_4 | 0 | exact |
| H-15 | T9 at ℓ = 1 → 0 (no monopole from dipole shear) | 0 | exact |
| H-16 | T9 at ℓ = 2 with σ = Σ_+ diagonal, Π_0 = 1 → −4 × σ_ab | −4 σ | 1e-14 |
| H-17 | Sum of all terms for FLRW (σ = ω = A = 0): reduces to T1 + T3 + T2 | — | 1e-14 |

### 11.4 Hierarchy RHS tests (test_hierarchy_rhs.py)

| # | Test | Target | Tol |
|---|---|---|---|
| H-18 | `hierarchy_rhs_photon` at FLRW + zero Π → zero dy/dη (no sources) | 0 | 1e-14 |
| H-19 | At Γ_T = 0, Π_1 = 0, σ = 0: RHS = free-streaming tower | −(4/3) Θ Π_ℓ + ∇̃ terms | 1e-12 |
| H-20 | At Γ_T = 0, Π_1 = 1, Π_ℓ≥2 = 0: RHS couples Π_2 via T2, otherwise nothing | T2 contribution only | 1e-12 |
| H-21 | At Γ_T → ∞, Π_1 initially = 0, v_b = 1: RHS at ℓ=1 = Γ_T × (1) | +Γ_T | exact |
| H-22 | At σ_ab ≠ 0, Π_0 = 1: RHS at ℓ=2 gets T9 = −4 σ_ab | explicit check | 1e-12 |
| H-23 | Truncation at L=4: Π_5 closure = 0 (HardCut) → RHS at ℓ=4 drops T3, T7 | — | 1e-14 |

### 11.5 Integration sanity (test_hierarchy_rhs.py extended)

Using `solve_ivp` on a minimal (L = 2, Bianchi I orthogonal, constant Σ_+) setup:

| # | Test | Target | Tol |
|---|---|---|---|
| H-24 | Free-streaming: Π_1 oscillates with period ~ 2π/k for an axisymmetric plane wave seed | period matches | 5% |
| H-25 | Γ_T large: Π_2 → TCA value (W6-04) within 1 e-fold | agreement with `solve_tca_closure` | 1e-4 |
| H-26 | Pure σ injection: Π_2 grows linearly with σ_ab · t before damping onset | slope matches T9 coefficient | 2% |

### 11.6 Required total

Minimum 35 tests for LB-2 (across all test files).

---

## 12. Implementation checklist

- [ ] Review `00_conventions.md` §4 (Σ² normalisation) and §5 (PSTF packing)
- [ ] Create `bass/hierarchy/` subpackage layout
- [ ] Implement `PSTFTensor` + `PSTFHierarchyState` + factories; tests H-01 to H-08
- [ ] Implement Clebsch-Gordan basis transformation matrices up to ℓ=8 (pre-computed at import)
- [ ] Implement `sym_trace_free` via packed-full round trip; tests H-09 to H-11
- [ ] Implement T1 through T9 as pure functions; tests H-12 to H-17
- [ ] Implement `hierarchy_rhs_photon` driver; tests H-18 to H-23
- [ ] Implement `HardCutClosure` (default for LB-2; full LB-3 in next session)
- [ ] Implement adapter around `bass.collision.thomson_tensor` for the `CollisionOperator` protocol
- [ ] Run `solve_ivp`-based integration tests H-24 to H-26
- [ ] Full bass_py regression
- [ ] Commit as `LB-2: PSTF multipole hierarchy for photons (orthogonal Bianchi)`

---

## 13. Cite map

Required citations in top-of-file module docstrings:

| File | Required citations |
|---|---|
| `pstf_tensor.py` | Ellis §4.5 (moment expansion); Arfken Ch 16 (real sph harm) |
| `contractions.py` | Ellis-Bruni-Ellis 1992 (PSTF projector, explicit forms up to ℓ=8) |
| `terms.py` | lowell §6 (source equation); Ellis §4.6 (derivation); Baumann §4.6 (cross-check) |
| `hierarchy_rhs.py` | lowell §6 + §9.2; Kolb §6.4 (simple Boltzmann moments) |
| `collision_interface.py` | Ellis §5.5 (Thomson tensor); Kolb §5.1 |
| `closure_interface.py` | Ellis §4.6 (truncation); Ma-Bertschinger 1995 §6 (truncation schemes) |

Additionally, each non-trivial function has a minimum 3-line docstring citing the specific equation. Example:

```python
def term_T9(ell, Pi_ell_minus_2_full, sigma_tensor):
    """T9: -(ℓ+2) σ_{⟨a_ℓ a_{ℓ-1}} Π_{A_{ℓ-2}⟩}.

    Shear couples ℓ down to ℓ-2. At ℓ=2 this term gives
    -4 σ_{ab} × Π (monopole), which is the mechanism by which
    Bianchi shear injects a quadrupole into the CMB.

    Reference: lowell §6 (eq, 3rd line of the ℓ=2 worked example);
               Ellis §4.6 (derivation); Pontzen-Challinor 2007 eq (C4).
    """
```

---

## 14. LB-2b extension (tilted species, deferred)

After LB-2 is green, LB-2b lifts the orthogonal assumption:

- Replace `u_(s)^a = n^a` with `u_(s)^a = γ_s (n^a + v_(s)^a)` for each species
- Thomson collision tensor (LB-4) evaluated in the u_e^a frame; boost back to n^a frame via `species_tilt.decompose_tilted_species` machinery
- Visibility becomes direction-dependent `g̃(η, e)` (lowell §11.3)
- ν and γ distribution moments acquire species-specific boost corrections (lowell §13.5 eq — the PSTF boost rule)

Estimated LB-2b: ~400 LoC + ~200 LoC tests, 1 session.
