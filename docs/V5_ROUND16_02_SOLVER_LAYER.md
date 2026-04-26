# V5 Round-16 — Solver Layer (Hierarchy, Mode Mixing, IC Factories, Collision, B-mode source)
_Authority: this doc + 00. Status: implementation-ready._

This document specifies the perturbation-layer architecture: the PSTF tower with full off-diagonal RHS k-mixing, off-axis spatial harmonics for the 8 anisotropic intrinsic families, family-specific IC factories, full massive-neutrino momentum hierarchy, exact electron-frame Thomson collision, and the B-mode source pathway. Each section ends with skeleton, pseudocode, tests, and adversarial audit.

## 1. State layout (frozen)

The hierarchy state vector is the per-mode tower:

```
U_pert(η; k, λ) = (
    Θ_ℓ_m  for ℓ ∈ {0..L_T},  m ∈ {-2..+2}        # photon temperature
    E_ℓ_m  for ℓ ∈ {2..L_E},  m ∈ {-2..+2}        # photon E-mode
    B_ℓ_m  for ℓ ∈ {2..L_B},  m ∈ {-2..+2}        # photon B-mode
    N_ℓ_m  for ℓ ∈ {0..L_ν},  m ∈ {-2..+2}        # neutrino (massless)
    F^q_ℓ_m  for q ∈ q_grid, ℓ ∈ {0..L_ν^m},      # massive neutrino momentum slice
                              m ∈ {-2..+2}
    δ_b, v_b_m  for m ∈ {-2..+2}                  # baryon
    δ_c, v_c_m  for m ∈ {-2..+2}                  # CDM
)
```

Defaults (in `bass/hierarchy/state_layout.py`):
```
L_T = 12   (production)         L_E = 8     L_B = 8
L_ν = 12   (massless)            L_ν^m = 4  (massive, per q-bin)
q_grid: Lesgourgues-Tram quadrature, default 50 bins (auto-up to 150)
m channels: {-2, -1, 0, +1, +2} for tilted; {0} for orthogonal-Type-I-isotropic
```

The `m` dimension is **always physical** in Round-16: even for orthogonal Type I the m=±2 channels carry the tensor mode and m=±1 the vector. The state allocator no longer collapses to m=0 for axisymmetric configurations; instead the integrator detects axisymmetry from the k-vector / shear structure and short-circuits the unused channels via sparse mask. This avoids the silent bug class where adding tilt later would have crashed with "m channel uninitialized".

## 2. Hierarchy RHS with off-diagonal mode coupling (closes G2)

### 2.1 Reference RHS (PSTF photon temperature, all 9 terms)

From Challinor-Lasenby 2000-I + Pereira-Pitrou-Uzan 2007 + Pontzen-Challinor 2007:

```
Π̇_{A_ℓ} = T1_{A_ℓ} + T2_{A_ℓ} + T3_{A_ℓ} + T4_{A_ℓ} + T5_{A_ℓ}
          + T6_{A_ℓ} + T7_{A_ℓ} + T8_{A_ℓ} + T9_{A_ℓ} - K_{A_ℓ}

T1 = -(2ℓ+1)/(2ℓ+1) D^B Π_{B A_{ℓ}}                    [free-streaming gradient]
T2 = -(ℓ+1)/(2ℓ+3) k Π_{A_{ℓ+1}}                       [k-recursion up]
T3 = +(ℓ)/(2ℓ-1) k Π_{A_{ℓ-1}}                         [k-recursion down]
T4 = -A^B Π_{B A_{ℓ}}                                  [acceleration]
T5 = -(2ℓ+1)/(ℓ+1) ω^{BC} Π_{C A_{ℓ}}                  [vorticity]
T6 = +Φ̇ δ_{ℓ0} - (k/3) Ψ δ_{ℓ1}                       [metric source]
T7 = -((ℓ-1)(ℓ+1)(ℓ+2))/((2ℓ+3)(2ℓ+5)) σ^{BC} Π_{A_{ℓ} BC}    [shear quad up]
T8 = +(5ℓ)/(2ℓ+3) σ^B_{⟨a_{ℓ}} Π_{A_{ℓ-1}⟩ B}                  [shear cross]
T9 = -(ℓ+2) σ_{⟨a_{ℓ} a_{ℓ-1}} Π_{A_{ℓ-2}⟩}                    [shear quad down]
K  = Γ_T (Π_{A_ℓ} - (1/10) Π δ_{ℓ2})                    [Thomson collision]
```

Indices `A_ℓ = (a_1 a_2 ... a_ℓ)` are PSTF symmetric-traceless multi-indices; `Π = Θ_2 - √6 E_2` is the polter combination (frozen SSoT).

### 2.2 Decomposition into m-channels

For BASS we use the *real-spherical-harmonic* PSTF basis with 5 slots per ℓ tower (m ∈ {-2, -1, 0, +1, +2} stripe; the other 2ℓ-3 slots vanish for the 5-component PSTF basis enforced by `bass/hierarchy/pstf_tensor.py`).

The shear σ_ab decomposes into a quadrupole:
```
σ_ab(η) = Σ_{M=-2}^{2} σ_{2M}(η) Y^{2M}_{ab}(ê_basis)
```
where `Y^{2M}_{ab}` are spin-2 spherical harmonics evaluated in the tetrad basis of the family. The five `σ_{2M}` are the 5-vector `(σ_+, σ_-, σ_{×1}, σ_{×2}, σ_{×3})` from §1.3 of doc 01.

### 2.3 Off-diagonal shear-mixing coefficients (PSTF Wigner-3j)

The shear terms T7, T8, T9 produce off-diagonal couplings *between* m-channels:

```
T7 contribution to Π̇_{ℓ, m}:
    = -((ℓ-1)(ℓ+1)(ℓ+2))/((2ℓ+3)(2ℓ+5)) Σ_M σ_{2M} C_7(ℓ, m, M) Π_{ℓ+2, m-M}

T8 contribution to Π̇_{ℓ, m}:
    = +(5ℓ)/(2ℓ+3) Σ_M σ_{2M} C_8(ℓ, m, M) Π_{ℓ, m-M}

T9 contribution to Π̇_{ℓ, m}:
    = -(ℓ+2) Σ_M σ_{2M} C_9(ℓ, m, M) Π_{ℓ-2, m-M}
```

The Clebsch-Gordan / Wigner-3j coefficients are:
```
C_7(ℓ, m, M) = ⟨ℓ+2, m | ℓ, m-M; 2, M⟩
              = √((2ℓ+1)(2ℓ+5)/(2ℓ+3)) · w3j(ℓ, 2, ℓ+2; m-M, M, -m)
              · √((ℓ+m+2)!(ℓ-m+2)!(ℓ+m-M)!(ℓ-m+M)!)
              [normalized so C_7(ℓ, 0, 0) = 1 in the limit ℓ → ∞]

C_8(ℓ, m, M) = ⟨ℓ, m | ℓ, m-M; 2, M⟩  (same-ℓ recoupling)
C_9(ℓ, m, M) = ⟨ℓ-2, m | ℓ, m-M; 2, M⟩
```

These are *family-agnostic* — they depend only on ℓ, m, M and PSTF basis normalization. Pre-compute once at integrator init for ℓ ∈ {2..L_T} and store in `bass/hierarchy/wigner_coupling_table.py` (cached on disk for L_T ≤ 40).

**Equivalent E-mode and B-mode coefficients** (Pontzen-Challinor 2007 §3, eq. 23–25): the same C_7,8,9 with spin-2 weighting. For E↔B mixing:
```
T7_E→E:  same as T-channel
T7_E→B:  ∝ (m / (ℓ+2)) σ_{2M} C_7^{EB}(ℓ, m, M)         [parity-odd shear → B]
T7_B→E:  ∝ (m / (ℓ+2)) σ_{2M} C_7^{BE}(ℓ, m, M)
T7_B→B:  same as T-channel
```

Parity-odd shear (i.e. `σ_{2±1}` non-zero) drives E↔B mixing; for axisymmetric backgrounds (only `σ_{2,0}` non-zero) the mixing vanishes by parity.

### 2.4 Skeleton

```python
# bass/hierarchy/mode_mixing_blocks.py  (NEW; closes G2)
import numpy as np
from sympy.physics.wigner import wigner_3j as _w3j_exact
from functools import lru_cache

@lru_cache(maxsize=8192)
def wigner_3j(j1, j2, j3, m1, m2, m3):
    """Cached Wigner-3j; returns float."""
    return float(_w3j_exact(j1, j2, j3, m1, m2, m3))

def build_shear_coupling_table(L_max: int) -> ShearCouplingTable:
    """
    Pre-compute C_7, C_8, C_9 for ℓ ∈ {2..L_max}, m ∈ {-2..2}, M ∈ {-2..2}.
    Returns a (3, L_max+1, 5, 5) array [coupling_kind, ℓ, m+2, M+2].
    """
    table = np.zeros((3, L_max + 1, 5, 5), dtype=np.float64)
    for ell in range(2, L_max + 1):
        for m in range(-2, 3):
            for M in range(-2, 3):
                if abs(m - M) > min(ell + 2, ell, ell - 2):
                    continue  # selection rule
                table[0, ell, m + 2, M + 2] = _C7(ell, m, M)
                table[1, ell, m + 2, M + 2] = _C8(ell, m, M)
                table[2, ell, m + 2, M + 2] = _C9(ell, m, M)
    return ShearCouplingTable(values=table, L_max=L_max)

def _C7(ell, m, M):
    """⟨ℓ+2, m | ℓ, m-M; 2, M⟩ in PSTF normalization (Pontzen-Challinor 2007 eq. 23)."""
    cg = wigner_3j(ell, 2, ell + 2, m - M, M, -m)
    norm = np.sqrt((2 * ell + 1) * (2 * ell + 5))
    sign = (-1) ** (ell - 2 + m)
    return sign * norm * cg

def _C8(ell, m, M):
    """⟨ℓ, m | ℓ, m-M; 2, M⟩."""
    cg = wigner_3j(ell, 2, ell, m - M, M, -m)
    norm = (2 * ell + 1)
    sign = (-1) ** (ell - 2 + m)
    return sign * norm * cg

def _C9(ell, m, M):
    """⟨ℓ-2, m | ℓ, m-M; 2, M⟩."""
    if ell < 2:
        return 0.0
    cg = wigner_3j(ell, 2, ell - 2, m - M, M, -m)
    norm = np.sqrt((2 * ell + 1) * (2 * ell - 3))
    sign = (-1) ** (ell - 2 + m)
    return sign * norm * cg

def assemble_A_mix_block(
    backend: FamilyBackend,
    truncation: TruncationSpec,
    bg_state: BackgroundEvolved,
    eta: float,
) -> sp.csr_matrix:
    """
    Build the sparse off-diagonal A_mix block for the photon-T tower at this η.
    Output shape: (5*(L_T+1), 5*(L_T+1)) since each ℓ has 5 m-slots.
    """
    L = truncation.L_T
    sigma_2M = bg_state.sigma_2M_at(eta)        # shape (5,)  — 5 quadrupole modes
    table = backend.shear_coupling_table         # built once at backend.__init__
    
    rows, cols, data = [], [], []
    for ell in range(2, L + 1):
        for m in range(-2, 3):
            row = ell_m_to_index(ell, m, L)
            for M in range(-2, 3):
                # T7: ℓ → ℓ+2
                if ell + 2 <= L:
                    target = ell_m_to_index(ell + 2, m - M, L)
                    coeff = -((ell - 1) * (ell + 1) * (ell + 2)
                              / ((2 * ell + 3) * (2 * ell + 5))) \
                            * sigma_2M[M + 2] * table.values[0, ell, m + 2, M + 2]
                    rows.append(row); cols.append(target); data.append(coeff)
                # T8: ℓ → ℓ
                target = ell_m_to_index(ell, m - M, L)
                coeff = (5 * ell / (2 * ell + 3)) \
                        * sigma_2M[M + 2] * table.values[1, ell, m + 2, M + 2]
                rows.append(row); cols.append(target); data.append(coeff)
                # T9: ℓ → ℓ-2
                if ell - 2 >= 2:
                    target = ell_m_to_index(ell - 2, m - M, L)
                    coeff = -((ell + 2)) \
                            * sigma_2M[M + 2] * table.values[2, ell, m + 2, M + 2]
                    rows.append(row); cols.append(target); data.append(coeff)
    n = 5 * (L + 1)
    return sp.csr_matrix((data, (rows, cols)), shape=(n, n))
```

### 2.5 Pseudocode for full hierarchy RHS

```python
def hierarchy_rhs_eta_v16(eta, U, *, bg, backend, source_tables, L_T, L_E, L_B, L_nu):
    """
    Round-16 hierarchy RHS with full off-diagonal mode mixing.
    """
    # 1. Sample background at η
    a, beta, sigma_2M, S_AB, k_eff = bg.sample(eta)
    Gamma_T = bg.opacity_at(eta)
    
    # 2. Diagonal blocks: free-streaming + k-recursion (T1-T6 + Thomson collision)
    rhs_T_diag = free_streaming_block(U.photon_T, L_T, k_eff) + thomson_collision_T(U, Gamma_T)
    rhs_E_diag = free_streaming_block(U.photon_E, L_E, k_eff) + thomson_collision_E(U, Gamma_T)
    rhs_B_diag = free_streaming_block(U.photon_B, L_B, k_eff) + thomson_collision_B(U, Gamma_T)
    rhs_nu_diag = free_streaming_block_nu(U.neutrino, L_nu, k_eff)
    
    # 3. Off-diagonal A_mix (T7-T9 shear couplings) per channel
    A_mix_T = assemble_A_mix_block(backend, truncation_T, bg, eta)
    A_mix_E = assemble_A_mix_block(backend, truncation_E, bg, eta, channel="E")
    A_mix_B = assemble_A_mix_block(backend, truncation_B, bg, eta, channel="B")
    
    # 4. Curvature anisotropy S_AB couplings (T1 with non-FLRW Laplacian eigenvalue
    #    correction; required for Class-B families with non-trivial spatial spectrum)
    A_curv_T = assemble_A_curv_block(backend, truncation_T, S_AB, k_vec)
    
    # 5. E↔B parity-odd mixing (drives B from σ_{2,±1})
    A_EB = assemble_EB_mixing_block(backend, truncation_E, sigma_2M)
    
    # 6. Source: metric, baryon-photon Doppler, polter
    src_T = build_source_T(eta, bg, source_tables, U)
    src_E = build_source_E(eta, bg, source_tables, U)
    
    # 7. Massive neutrino momentum hierarchy (Lesgourgues-Tram)
    rhs_nu_massive = massive_nu_rhs(U.neutrino_massive, bg, k_eff)
    
    # 8. Assemble
    rhs = pack(
        photon_T=rhs_T_diag + A_mix_T @ U.photon_T + A_curv_T @ U.photon_T + src_T,
        photon_E=rhs_E_diag + A_mix_E @ U.photon_E + A_EB @ U.photon_B + src_E,
        photon_B=rhs_B_diag + A_mix_B @ U.photon_B + A_EB.T @ U.photon_E,
        neutrino=rhs_nu_diag,
        neutrino_massive=rhs_nu_massive,
        baryon=baryon_rhs(eta, U, bg, source_tables),
        cdm=cdm_rhs(eta, U, bg),
    )
    
    # 9. TCA conditional dispatch (DAE-relaxation; pre-existing in integrator.py)
    apply_tca_relaxation_if_active(rhs, U, bg)
    
    return rhs
```

### 2.6 Tests + tolerances

```
test_mode_mixing_blocks.py
- test_wigner_3j_known_values: w3j(2,2,2; 0,0,0) = -√(2/35) etc.
- test_shear_coupling_table_diagonal_in_m_when_axisymmetric:
    σ_{2M} = δ_{M,0} → A_mix is m-diagonal
- test_T7_T9_zero_when_shear_zero: σ_2M ≡ 0 → A_mix == 0
- test_C7_at_high_ell_normalization: C_7(20, 0, 0) ≈ 1.0 (asymptotic)
- test_axisymmetric_with_tilt_drives_m_eq_2_only:
    pure σ_{2,0} → photon m=±2 channels stay zero through evolution
- test_off_axis_drives_all_m: σ_{2,1}, σ_{2,-1} non-zero → m=±1 driven from m=0
- test_eb_mixing_parity_odd: σ_{2,±1} non-zero → B-mode generated even from
    initially zero B at recombination

test_hierarchy_rhs_v16_flrw_limit.py
- test_FLRW_limit_recovers_pre_v16_RHS:
    σ_2M = 0, S_AB = 0, k diagonal → bit-identical to legacy hierarchy_rhs.py
    output for the m=0 slice; m=±1, m=±2 slots stay zero. (Critical for G1
    closure: this preserves D_2 anchor.)
- test_type_v_curvature_correction_present: S_AB ≠ 0 → A_curv ≠ 0;
    the resulting Δ_ℓ^T is shifted from FLRW by ≥ 1e-6 at ℓ=2
```

### 2.7 Adversarial audit (PR-S3)

```
A1: grep for "ignore m mixing", "axisymmetric only" — every hit downgraded
A2: verify off-diagonal C_7,8,9 are computed with full σ_{2M} (5-component),
    not σ_+ alone. Common bug: σ_- silently dropped.
A5: verify A_mix is built EVERY η (not at IC only); shear evolves so mixing
    coefficients evolve
A6: assert that for Type V (Class-B, non-trivial S_AB), A_curv is non-zero
    when sampled at a random η, k=1e-3 Mpc⁻¹
A7: convergence: increase L_T from 12 to 20 → ||A_mix(L=20)|| / ||A_mix(L=12)||
    bounded by analytic estimate ~ (20/12)·max|σ|; not unbounded
A9: parallel-vs-sequential bit-identity — A_mix is a deterministic function of
    (bg, family, η, L), so hash(A_mix.toarray()) must match across n_workers
```

## 3. Off-axis modes for class-A intrinsic and class-B families (closes G3)

Currently (audit finding) Types II/III/IV/VI₀/VI_h/VII₀/VII_h/VIII restrict to axis-aligned k-vectors (k₂=0 or Cartan-axis only). Round-16 lifts this restriction by integrating multiple k-vector orientations and combining via family-specific Plancherel measure.

### 3.1 Per-family k-grid

| Family | k-vec parametrization | Number of off-axis samples |
|--------|----------------------|---------------------------|
| II      | (k_1, k_2) ∈ ℝ × ℤ_{≥0}     | k_1 ∈ log-grid (24); k_2 ∈ {0..N_max=24} |
| VI₀     | (k_1, k_3, k_2) | (24, 24) × 5 lattice points |
| VII₀    | (k_⊥, φ, k_3) | k_⊥(24) × φ(8) × k_3(24) |
| VIII    | (μ, s) ∈ [-1/2, 1/2) × ℝ_{≥0} (continuous Plancherel) + D^±_λ discrete | (16, 32) + 8 discrete |
| IX      | ℓ_spectral ∈ {1, 2, ...}; pre-determined | discrete; up to ℓ_spec=20 |
| III/IV/VI_h/VII_h | continuous k + h-dependent λ | 24 × 24 |

Integration: for each (family, k_index), one independent IMEX run; bundle aggregation yields family-specific transfer functions. The dispatch lives in `bass/hierarchy/family_k_grid.py`.

### 3.2 Skeleton

```python
# bass/hierarchy/family_k_grid.py  (NEW; closes G3)
def build_family_k_grid(family: str, *, k_min=1e-4, k_max=0.3, n_k=24,
                         backend: FamilyBackend) -> FamilyKGrid:
    """
    Return the family-specific k-grid with Plancherel weights.
    For each k-vector, the integrator runs once; LoS aggregates with weights.
    """
    if family == "FLRW" or family == "I":
        # 1-D log-grid, weight = 1
        k_log = np.logspace(np.log10(k_min), np.log10(k_max), n_k)
        return FamilyKGrid(
            family=family, k_vectors=[(k, 0.0, 0.0) for k in k_log],
            weights=np.ones(n_k), branch_label="continuous_1d",
        )
    
    elif family == "II":
        # Heisenberg: k_1 continuous, k_2 ∈ ℤ_{≥0}
        k_1 = np.logspace(np.log10(k_min), np.log10(k_max), n_k)
        k_2 = np.arange(0, 25)   # discrete lattice
        kvecs = [(k1, k2, 0.0) for k1 in k_1 for k2 in k_2]
        weights = backend.plancherel_weights("II", kvecs)
        return FamilyKGrid(family="II", k_vectors=kvecs, weights=weights,
                            branch_label="heisenberg_lattice")
    
    elif family == "VIII":
        # SL(2,R): continuous (μ, s) + discrete D^±_λ
        kvecs_cont = [(s, mu, 0.0) for s in np.geomspace(0.01, 5.0, 32)
                                    for mu in np.linspace(-0.5 + 0.05, 0.5 - 0.05, 16)]
        weights_cont = [(1/(4*np.pi**2)) * s * np.sinh(2*np.pi*s) /
                        (np.cosh(2*np.pi*s) + np.cos(2*np.pi*mu))
                        for (s, mu, _) in kvecs_cont]
        kvecs_disc = [(0.0, 0.0, l) for l in np.arange(0.5, 4.5, 1.0)]
        weights_disc = [(1/(4*np.pi**2)) * (l - 0.5) for (_, _, l) in kvecs_disc]
        return FamilyKGrid(
            family="VIII",
            k_vectors=kvecs_cont + kvecs_disc,
            weights=np.array(weights_cont + weights_disc),
            branch_label="sl2r_continuous_plus_discrete",
        )
    
    elif family == "IX":
        # SU(2): discrete spectrum ℓ_spec ∈ {1, 2, ..., ell_max_spec}
        ell_max_spec = 20
        kvecs = [(float(l), 0.0, 0.0) for l in range(1, ell_max_spec + 1)]
        weights = np.array([(2*l + 1) for l in range(1, ell_max_spec + 1)])
        weights = weights.astype(np.float64) / np.sum(weights)
        return FamilyKGrid(family="IX", k_vectors=kvecs, weights=weights,
                            branch_label="su2_discrete")
    
    # ... other families ...

def integrate_per_k(kvec, *, family, backend, bg_evolved, ...) -> KModeResult:
    """
    One independent IMEX run per k-vector. Embarrassingly parallel.
    """
    # ... (as per existing flrw_pipeline.compute_transfer_function_grid)
    ...
```

### 3.3 Validation: orthogonal-limit recovery

Each family's off-axis grid must reproduce the existing axis-aligned limit when restricted to k₂=0 (etc.). Test cases:

```
test_off_axis_modes_per_family.py
- test_typeII_axis_aligned_limit_matches_existing: restrict k_2=0 → existing
    Type II output bit-identical
- test_typeVIII_axis_aligned_limit_matches_existing: restrict to Cartan k_1=0 → match
- test_typeIX_isotropic_limit: σ→0 → spectrum approaches FLRW (Type I) at ≤ 1e-3
- test_typeV_off_axis_residual_zero_in_isotropic_limit: at σ=0, off-axis k_⊥ samples
    produce same Δ_ℓ as on-axis up to spatial-curvature term Ω_k a²
```

### 3.4 Adversarial audit (PR-S6, PR-S7)

```
A1: grep for "axis_aligned_only", "k2=0 hardcoded": no production hits
A6: per family: assert FamilyKGrid contains > 1 distinct k-direction (for II–VIII)
    ; otherwise the family is silently FLRW
A7: assert that off-axis weight integration recovers the analytic Plancherel
    measure; e.g. for Type IX: Σ_l w_l = 1 within 1e-12; for Type VIII:
    ∫ ρ^cont(μ, s) dμ ds finite
```

## 4. Family-specific IC factories (closes G9)

Each family must have its own seed factory producing a `SeedPack` aligned with its template card. The factory is dispatched on `(family, branch, k_vector)`.

### 4.1 Per-family IC structure

| Family | IC strategy | Function |
|--------|-------------|----------|
| FLRW   | Adiabatic regular MB-95 §7 | `_flrw_regular_seed(k, η_init)` |
| I      | Adiabatic + axis-aligned PSTF expansion | `_type_i_regular_seed` |
| V      | Hyperbolic super-curvature mode (Pereira-Pitrou-Uzan-style) | `_type_v_hyperbolic_seed` |
| IX     | Wigner-D anchored unit-L²-norm seed (already implemented) | `_type_ix_compact_seed` |
| II/VIII | Frobenius series in chart variable + collocation projection | `_type_intrinsic_collocation_seed` |
| III/IV | Frobenius series + chart-specific normalization | `_type_classB_collocation_seed` |
| VII₀/VII_h | Helical Bessel + mode-locked phase | `_type_vii_helical_seed` |
| VI₀/VI_h | Solvable plane-wave with twist-dependent damping | `_type_vi_seed` |

### 4.2 Frobenius series for intrinsic-anisotropic families (II, VIII)

For Type II (Heisenberg chart x ∈ ℝ³ with [E_2, E_3] = E_1):
```
ζ(x; q_native) = e^{i k_1 x_1 + i k_2 x_2} φ(x_3; q)
where φ satisfies a 1D Sturm-Liouville with Hermite-like eigenfunctions.

Frobenius series at x_3 → 0:
    φ(x_3) = Σ_{n=0}^{N_F} a_n x_3^n
    a_0, a_1: free; a_{n+2} = -((k_2² x_3² + λ - k_1²) / ((n+1)(n+2))) a_n  (recursion)

Truncate at N_F = 12; collocation-project onto orthogonal basis.
```

### 4.3 Skeleton

```python
# bass/hierarchy/seed_factory.py  (NEW; closes G9)
from typing import Protocol

class SeedFactory(Protocol):
    def __call__(
        self,
        family: str,
        branch: str,
        k_vec: np.ndarray,
        eta_init: float,
        *,
        primordial_amplitude: float,
        L_max: int,
    ) -> SeedPack:
        ...

def get_seed_factory(family: str) -> SeedFactory:
    """Dispatch table; one entry per family."""
    return {
        "FLRW":   _flrw_regular_seed,
        "I":      _type_i_regular_seed,
        "II":     _type_intrinsic_collocation_seed_II,
        "III":    _type_classB_collocation_seed_III,
        "IV":     _type_classB_collocation_seed_IV,
        "V":      _type_v_hyperbolic_seed,
        "VI_0":   _type_vi_seed,
        "VI_h":   _type_vi_seed,
        "VII_0":  _type_vii_helical_seed,
        "VII_h":  _type_vii_helical_seed,
        "VIII":   _type_intrinsic_collocation_seed_VIII,
        "IX":     _type_ix_compact_seed,
    }[family]

def _type_intrinsic_collocation_seed_II(family, branch, k_vec, eta_init,
                                         *, primordial_amplitude, L_max):
    """
    Type II Heisenberg chart Frobenius series. Mandatory contract:
    seed_pack.ic_provenance_status = 'template-card', not 'strong'.
    """
    if family != "II":
        raise ValueError(f"_type_intrinsic_collocation_seed_II called for {family}")
    
    k1, k2, _ = k_vec
    # Frobenius coefficients
    a = np.zeros(13)
    a[0] = primordial_amplitude
    a[1] = 0.0  # by construction (regular at x3=0)
    for n in range(0, 11):
        a[n + 2] = -((k2 ** 2 - k1 ** 2) / ((n + 1) * (n + 2))) * a[n]
    
    # Project onto PSTF tower at η_init
    psi_initial = _frobenius_to_pstf_tower(a, k_vec, L_max=L_max)
    
    return SeedPack(
        family="II",
        branch=branch,
        chart="heisenberg_native",
        seed_mode="template_card_family_adapted",   # not 'isotropic_anchor_continuation'!
        variables=psi_initial,
        normalization={
            "amp_ref": "disc_L2_unit",
            "mu_ref": "heisenberg_x3_chart",
            "inner_product": "<phi,psi>_h = sum_q w_q phi_q^* psi_q",
            "norm_rule": "<phi,phi>_h = 1",
            "phase_rule": "phi(0) in R_{>0}",
        },
        residual_summary={
            "frobenius_truncation_error": _frobenius_residual(a, k_vec),
            "seed_regularity_status": "regular",
        },
        metadata={
            "ic_provenance_status": "template-card",
            "k_vector": tuple(k_vec),
        },
    )

def _type_v_hyperbolic_seed(family, branch, k_vec, eta_init,
                             *, primordial_amplitude, L_max):
    """
    Type V super-curvature open-FLRW: hyperbolic Legendre P^μ_ν on the unit
    pseudosphere. Pereira-Pitrou-Uzan 2007 + super-curvature mode formalism.
    """
    if family != "V":
        raise ValueError(f"_type_v_hyperbolic_seed called for {family}")
    
    k = np.linalg.norm(k_vec)
    # Normalized hyperbolic mode: ν = k/a_curv - i/2; μ from PSTF rank
    nu = k / 1.0 - 0.5j   # a_curv = 1 in normalized units
    psi_initial = _hyperbolic_to_pstf_tower(k, nu, primordial_amplitude, L_max=L_max)
    
    return SeedPack(
        family="V", branch=branch, chart="open_pseudosphere",
        seed_mode="isotropic_anchor_continuation",  # V is isotropic anchor in B-class
        variables=psi_initial,
        normalization={
            "amp_ref": "disc_L2_unit",
            "mu_ref": "hyperbolic_continuous_k",
            "inner_product": "L2_pseudosphere",
            "norm_rule": "<phi,phi>_h = 1",
            "phase_rule": "phi(0) in R_{>0}",
        },
        residual_summary={"seed_regularity_status": "regular_hyperbolic"},
        metadata={"ic_provenance_status": "strong", "k_vector": tuple(k_vec)},
    )
```

### 4.4 Tests + tolerances

```
test_seed_factory_per_family.py
- test_flrw_seed_matches_existing_build_flrw_regular_seed: bit-identical
- test_type_v_isotropic_anchor_recovers_type_i_at_zero_curvature:
    a_curv → 0 → seed identical to Type I within 1e-10
- test_type_ii_template_card_status_set:
    seed.metadata.ic_provenance_status == "template-card"
- test_type_ix_compact_seed_l2_norm: <φ, φ>_compact = 1 within 1e-12
- test_each_family_seed_has_required_normalization_fields
- test_no_two_families_share_seed_pack_object: object identity check
```

### 4.5 Adversarial audit (PR-S5)

```
A1: grep for "fallback to FLRW seed" in seed_factory.py: zero hits
A2: verify Frobenius series uses real recursion (not truncated linear approx)
    by checking residual decreases as a_n / a_0 → ε^n
A3: each family seed must declare seed_regularity_status; null/missing → FAIL
A6: For non-FLRW families: assert _flrw_regular_seed not called from inside
    _type_*_seed
A6 (cross-check): Run hard_gate_before_fitting on a Type II run with default
    runtime_controls (allow_template_card=False). Assert allowed=False with
    missing_gates ⊃ ["ic_provenance_gate"].
```

## 5. Exact electron-frame Thomson collision (already implemented; tightened in Round-16)

The existing implementation in `bass/collision/electron_frame.py:139-160` uses the exact `γ_e (1 - v_e · ê)` non-perturbative rate. Round-16 changes only:

(a) The collision must read `β(η)` from the **evolved** background (not static) — already wired through `aux_state.beta_at(eta)` interface.

(b) The polarization basis transport must include **E↔B mixing** when shear is parity-odd (i.e. `σ_{2,±1} ≠ 0`). The current `tilted_eb_mixing.py` implements this; Round-16 only verifies the *call site* in `electron_frame.py:281` is reached for non-axisymmetric tilts (this is currently the case but un-tested for non-axisymmetric β-direction).

### 5.1 Skeleton (new test only)

```python
# bass/collision/test_eb_mixing_under_parity_odd_shear.py
def test_parity_odd_shear_drives_B_from_E():
    """
    Inject σ_{2,1} ≠ 0 (parity-odd component); evolve hierarchy to z=z_*+1 with
    initial B_2 = 0; assert B_2 generated at amplitude > 1e-6 of E_2.
    """
    bg = make_evolved_background_with_shear(sigma_2_modes={"2_+1": 1e-3})
    state_init = make_initial_state_with_E2_only()
    sol = run_imex_short(state_init, bg, eta_span=(z_to_eta(z_star + 5), z_to_eta(z_star)))
    B_2 = unpack_state(sol.y[-1])["photon_B_l2"]
    E_2 = unpack_state(sol.y[-1])["photon_E_l2"]
    assert np.abs(B_2 / E_2) > 1.0e-6
```

## 6. B-mode source pathway (Path B: Wigner-D, closes G5)

The current FLRW Bessel projector returns 0 for B; Round-16 implements a Bianchi-tensor projector that *can* produce non-zero B-mode via:

(a) **Direct shear-driven**: tensor-mode component of σ_ab couples to spin-2 B harmonics.
(b) **Free-streaming E→B mixing**: post-recombination, the parity-odd shear mode `σ_{2,±1}` rotates E into B over Δη ~ Hubble.

Both are handled by Path B from `V5_ROUND16_00_MASTER_PLAN.md §3.3`: spin-2 Wigner-D propagator. See `V5_ROUND16_03_OBSERVABLES_LAYER.md §2.5` for the projector spec; the *source* (this layer) is just the photon-B tower from §2 of this doc, propagated through the LoS.

### 6.1 Skeleton interface (defined here, implemented in 03 §2.5)

```python
# bass/los/b_mode_projector.py  (NEW; closes G5)
def project_B_mode_transfer(
    *,
    photon_B_tower_history: np.ndarray,      # (N_eta, L_B+1, 5)
    photon_E_tower_history: np.ndarray,
    sigma_2M_history: np.ndarray,             # (N_eta, 5)
    eta_grid: np.ndarray,
    backend: FamilyBackend,
    ell_max: int,
) -> np.ndarray:
    """
    Bianchi-tensor B-mode LoS projector. Returns Δ_ℓ^B(k) per (ℓ, m) channel.
    Implementation in V5_ROUND16_03_OBSERVABLES_LAYER.md §2.5.
    """
    ...  # implementation in 03
```

The PR-S11 deliverable is the implementation of this function plus its tests.

## 7. Massive-neutrino full momentum hierarchy (Lesgourgues-Tram 2011)

Currently the massive-ν background uses a degenerate-mass approximation `Σm_ν / 3` per eigenstate. Round-16 implements the full momentum-resolved CLASS-IV hierarchy.

### 7.1 Quadrature setup

Lesgourgues-Tram 2011 recommends 50 momentum bins for sub-1% precision; CLASS uses up to 150 for high precision. The quadrature is *not* uniform in q — it is optimized via comparing analytic Fermi-Dirac moments to discretized sums and adjusting node positions until match is within ε.

### 7.2 Skeleton

```python
# bass/species/massive_neutrino/momentum_hierarchy.py  (NEW; replaces degenerate-mass approx)
def build_lesgourgues_tram_quadrature(
    *,
    m_nu: float,                # mass of this species (eV)
    n_q: int = 50,
    target_accuracy: float = 1e-4,
) -> MomentumQuadrature:
    """
    Construct optimized q-grid + weights such that analytic moments
    ∫_0^∞ q^k f_FD(q) dq are reproduced to target_accuracy.
    """
    q_nodes = _initial_log_grid(n_q, q_min=1e-3, q_max=20.0)
    weights = _initial_weights(q_nodes)
    
    for moment_k in [0, 1, 2, 3, 4]:
        analytic = _analytic_FD_moment(k=moment_k)
        discrete = np.sum(weights * q_nodes ** moment_k * _f_FD_at_nodes(q_nodes))
        if abs(discrete - analytic) / analytic > target_accuracy:
            # Iterate: shift nodes, re-fit weights
            q_nodes, weights = _iterate_quadrature(q_nodes, weights, moment_k, analytic)
    
    return MomentumQuadrature(q=q_nodes, w=weights, m_nu=m_nu, n_q=n_q,
                              accuracy=target_accuracy)

def massive_nu_momentum_rhs(
    eta: float,
    F_q_lm: np.ndarray,   # shape (n_q, L+1, 5)
    *,
    quadrature: MomentumQuadrature,
    bg: BackgroundEvolved,
    k_eff: float,
) -> np.ndarray:
    """
    Boltzmann hierarchy in (q, ℓ, m) space.
    Below the Hubble radius, switch to viscous-fluid description (CLASS IV §3.4).
    """
    rhs = np.zeros_like(F_q_lm)
    a = bg.a(eta)
    for q_idx, q in enumerate(quadrature.q):
        epsilon_q = np.sqrt(q**2 + (a * quadrature.m_nu)**2)
        v_factor = q / epsilon_q
        for ell in range(F_q_lm.shape[1]):
            for m in range(5):
                rhs[q_idx, ell, m] = (
                    free_streaming_term(F_q_lm[q_idx, ell, m], k_eff, v_factor, ell, m)
                    + metric_source(eta, ell, m, bg)
                )
    return rhs
```

### 7.3 Tests

```
test_massive_neutrino_momentum_hierarchy.py
- test_quadrature_recovers_FD_moments: ∫ q^k f_FD dq matches analytic to <1e-4
- test_zero_mass_limit_recovers_massless: m_nu → 0 → identical to massless ν
- test_high_z_radiation_dominated_recovery:
    Total Ω_ν(a) at z=10^6 matches analytic ρ_ν^FD/ρ_crit
- test_sub_hubble_viscous_fluid_match:
    For k > 100 H, viscous-fluid description matches full hierarchy ≤ 1%
```

## 8. End-of-layer adversarial audit (cross-cutting)

```
P1. Authority RHS path
   grep for `def hierarchy_rhs_*`: only one production entry point;
   no "hierarchy_rhs_legacy" silently called.

P2. Mode mixing always on
   For each non-FLRW family: assert A_mix block is allocated AND populated when
   sigma_2M is non-zero. Common failure: A_mix.nnz == 0 for non-FLRW.

P3. Off-axis k-grid not silently collapsed
   For each family in {II, III, IV, VI_0, VI_h, VII_0, VII_h, VIII}:
   FamilyKGrid.k_vectors must contain ≥ 2 distinct directions (not all (k, 0, 0))

P4. Family IC must not pull from FLRW
   For each family != FLRW: seed_pack.metadata.ic_provenance_status must NOT be
   silently overridden to "strong" when the registry says "template-card".

P5. Massive-ν not collapsed to degenerate-mass
   When m_nu > 0 and Σ m_nu / 3 differs from per-eigenstate masses (e.g.
   normal hierarchy 0, 0.009, 0.05 eV), assert the per-q hierarchy is used,
   not the legacy degenerate approximation.

P6. B-mode pathway probe
   With injected σ_{2,±1} > 0: assert |B_l=2| > 1e-7 of |E_l=2| at z=z_*-100

P7. Wigner-3j coefficients
   Cross-check 100 random (l, m, M) values against sympy.physics.wigner;
   max relative error < 1e-12

P8. TCA smoothness regression (ports R15-AUDIT-PATCH P-03)
   Existing test_tca_switch_smoothness must still pass.

P9. Cosmological-range stability regression
   Run η = 261 → 14147 Mpc IMEX as in CLAUDE.md §3 Blocker-2;
   wall-time still ≤ 1.5× pre-Round-16 baseline.
```

## 9. Code-port helpers (Rust → Python)

For developers porting `sync_gauge_camb.rs` Bianchi extensions:

| Rust symbol | Python | Status |
|-------------|--------|--------|
| `BianchiHierarchy::rhs_eta` | `bass/hierarchy/hierarchy_rhs.py::hierarchy_rhs_eta_v16` | NEW |
| `BianchiHierarchy::assemble_A_mix` | `bass/hierarchy/mode_mixing_blocks.py::assemble_A_mix_block` | NEW |
| `BianchiHierarchy::A_curv_block` | `bass/hierarchy/mode_mixing_blocks.py::assemble_A_curv_block` | NEW |
| `BianchiSeedFactory::for_family` | `bass/hierarchy/seed_factory.py::get_seed_factory` | NEW |
| `MassiveNuQuadrature::build` | `bass/species/massive_neutrino/momentum_hierarchy.py::build_lesgourgues_tram_quadrature` | NEW |

The Python implementation must produce the same `transfer_T`, `transfer_E`, `transfer_B` arrays as the Rust path at the same (rtol, atol), to within 1e-10 relative. Cross-checks live in `htt/bass/validation/test_rust_python_hierarchy_parity.py`.

---

**End of Solver Layer.** Continue to `V5_ROUND16_03_OBSERVABLES_LAYER.md`.
