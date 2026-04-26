# V5 Round-16 — Observables Layer (LoS, Maps, Atlas, MES, Statistics)
_Authority: this doc + 00. Status: implementation-ready._

This document specifies the observation-side architecture: family-specific Bianchi LoS propagators, real-space map producers, the 29-item observable atlas, the MES full-covariance bound layer, the (x, Q, F, Π, G) framework, and the 15-stage statistics gate ladder.

## 1. LoS source assembly (extends `flrw_bessel_projector.py`)

The LoS source S_T(η, k, m) is the same SW + ISW + Doppler structure as FLRW, but indexed per m-channel and per family:

```
S_T(η, k, m) = g(η) [Θ_0,m + Ψ_m + (1/4) Π_m]                  [SW + polter]
              + e^{-κ(η)} [Φ̇_m + Ψ̇_m]                          [ISW]
              + (1/k) d/dη [g(η) v_b,m(η)]                     [Doppler ← /k corrected]

S_E(η, k, m) = -(√6/4) g(η) Π_m                                 [E polter source]

S_B(η, k, m) = post-Thomson tensor source from σ_{ab}(η)        [Path B; §2.5]
```

The audit's R8 finding **Doppler `/k` factor missing** (Round-15 P1 §2 R7-corrected) is fixed in Round-16: the LoS source builder writes `(1/k) d/dη[g v_b]`, not `d/dη[g v_b]`. This is a one-line change in `bass/los/flrw_bessel_projector.py:assemble_temperature_source` but **changes D_2** at the 0.5% level — it is the load-bearing fix for PR-S13 (Python-side D_2 closure).

## 2. Family-specific LoS propagators (closes G6)

Each family produces a transfer function bundle `(transfer_T[k, ℓ, m], transfer_E[k, ℓ, m], transfer_B[k, ℓ, m])` from its source. The propagator depends on the family's spatial spectrum.

### 2.1 FLRW / Type I (frozen baseline)

```
Δ_ℓ^T(k, m) = ∫ dη  S_T(η, k, m) · j_ℓ(k(η_0 - η))
Δ_ℓ^E(k, m) = ∫ dη  S_E(η, k, m) · √((ℓ-1)ℓ(ℓ+1)(ℓ+2)) · j_ℓ(kΔη) / (kΔη)²
```

Already implemented; no change.

### 2.2 Type V (open hyperbolic; PR-S8)

The spatial harmonics are hyperbolic Legendre functions `P^μ_ν(cosh ξ)` on the open pseudosphere. The Bessel kernel j_ℓ(kΔη) is replaced by:

```
Φ_ℓ(k, η; η_0) = (sinh(k Δη/a_curv) / (k Δη/a_curv))^{1/2} · P^{-ℓ-1/2}_{i ν - 1/2}(cosh(...))
```

where ν = k/a_curv - 0.5 (Pereira-Pitrou-Uzan 2007; Sung-Wandelt 2010). The pre-factor reduces to `j_ℓ(kΔη)` in the limit a_curv → 0.

### 2.3 Type IX (compact SU(2); PR-S9)

For Type IX, the spatial spectrum is **discrete**: `ℓ_spec ∈ {1, 2, ...}` with eigenvalue `λ = -ℓ_spec(ℓ_spec + 2)`. The propagator uses Wigner-D functions `D^{ℓ_spec}_{MN}(α, β, γ)`:

```
Δ_ℓ^T(ℓ_spec, m) = Σ_M C^IX_{ℓ, m, M} ∫ dη S_T(η, ℓ_spec, m) D^{ℓ_spec}_{Mm}(0, β(η), 0)
```

where β(η) = k_eff (η_0 - η) is the angular argument and `C^IX` is the Type-IX-specific Wigner-recoupling coefficient.

### 2.4 Solvable-group families (II, III, IV, VI_0, VI_h, VII_0, VII_h, VIII; PR-S10)

These families have continuous spectra that lack closed-form propagators. The default fallback is **collocation projection**: solve the radial ODE on a grid and project against PSTF tower templates. This is the most expensive branch but correctly produces non-FLRW transfer functions.

```
For each family-k tuple:
    1. Solve scalar spectral ODE (bianchi_design_pack_v5/03B §5) for P(z; k_C, λ).
    2. Discretize z on collocation grid; solve linear ODE → P_{i}(k_C).
    3. Compute angular projection ∫ dΩ_z ψ(z; k_C) Y^{ℓ}_m(Ω_z) → A^{ℓm}(k_C).
    4. Build kernel ∫ dz P_{i}(k_C) A^{ℓm}(k_C) → Φ_ℓ^family(k_C, η; η_0).
    5. Convolve with source: Δ_ℓ^family(k, m) = ∫ dη S(η, k, m) Φ_ℓ(k, η; η_0).
```

### 2.5 B-mode projector (Path B Wigner-D; PR-S11)

Saadeh-Pontzen-McEwen 2016 (ABSolve) construction:
```
Δ_ℓ^B(k, m) = Σ_M C^B_{ℓ, m, M} ∫ dη
              [g(η) (-(√6/4)) Π_m^{(B-channel)}(η)]
              · (-i) (D^{ℓ}_{Mm,+2} - D^{ℓ}_{Mm,-2}) / 2
              · j_ℓ(kΔη) / (kΔη)²
```

The factor `(D_{+2} - D_{-2})/2` selects the **parity-odd** spin-2 component (B-mode); `(D_{+2} + D_{-2})/2` selects parity-even (E-mode).

### 2.6 Skeleton

```python
# bass/los/bianchi_propagator/__init__.py  (NEW)
from typing import Protocol

class BianchiPropagator(Protocol):
    family: str
    def project_T(self, S_T_history, k_vec, eta_grid, ell_max) -> np.ndarray: ...
    def project_E(self, S_E_history, k_vec, eta_grid, ell_max) -> np.ndarray: ...
    def project_B(self, photon_B_history, sigma_2M_history, k_vec, eta_grid, ell_max) -> np.ndarray: ...

# bass/los/bianchi_propagator/type_v.py
class TypeVPropagator:
    family = "V"
    def __init__(self, *, a_curv: float = 1.0):
        self.a_curv = a_curv
    
    def project_T(self, S_T_history, k_vec, eta_grid, ell_max):
        k = np.linalg.norm(k_vec)
        nu = k / self.a_curv - 0.5j
        Delta = np.zeros((ell_max + 1, 5), dtype=np.complex128)
        for ell in range(ell_max + 1):
            for m in range(5):
                kernel = self._hyperbolic_kernel(ell, k, nu, eta_grid)
                Delta[ell, m] = np.trapezoid(S_T_history[:, m] * kernel, eta_grid)
        return Delta.real

    def _hyperbolic_kernel(self, ell, k, nu, eta_grid):
        Delta_eta = eta_grid[-1] - eta_grid
        x = k * Delta_eta / self.a_curv
        prefactor = np.sqrt(np.sinh(x) / np.maximum(x, 1e-30))
        legendre = scipy.special.lpmv(-ell - 0.5, complex(nu), np.cosh(x))
        return prefactor * legendre

# bass/los/bianchi_propagator/type_ix.py
class TypeIXPropagator:
    family = "IX"
    
    def project_T(self, S_T_history, k_vec, eta_grid, ell_max):
        ell_spec = int(k_vec[0])  # discrete spectral index
        Delta = np.zeros((ell_max + 1, 5), dtype=np.complex128)
        for ell in range(min(ell_spec + 1, ell_max + 1)):
            for m in range(-2, 3):
                wigner_D = wigner_d_matrix(ell_spec, M=m, N=m, theta=eta_grid)
                # ... Wigner-D propagator implementation ...
                Delta[ell, m + 2] = ...
        return Delta.real

# bass/los/bianchi_propagator/solvable_collocation.py
class SolvableCollocationPropagator:
    """Default fallback for II, III, IV, VI_0, VI_h, VII_0, VII_h, VIII."""
    family: str
    
    def __init__(self, family, *, n_collocation_z=64, n_collocation_kc=24):
        self.family = family
        self.n_z = n_collocation_z
        self.n_kc = n_collocation_kc
        self._radial_ode = _build_radial_ode(family)
    
    def project_T(self, S_T_history, k_vec, eta_grid, ell_max):
        # Solve radial ODE for P(z; k_C) once per k_vec
        P_grid = self._solve_radial(k_vec)
        # Angular projection at each ℓ, m
        A_lm = self._angular_projection(P_grid, ell_max)
        # Convolve with source
        Delta = ...
        return Delta
```

### 2.7 Tests + tolerances

```
test_bianchi_propagator_per_family.py
- test_typeI_recovers_FLRW: Type I propagator output bit-identical to FLRW
- test_typeV_isotropic_limit: a_curv → 0, hyperbolic propagator → FLRW Bessel j_ℓ
    (within 1e-3 at ℓ < 50)
- test_typeIX_compact_anchor: at large ℓ_spec, Type IX → Type I within 1e-2
- test_typeVIII_off_axis_produces_distinct_spectrum:
    different (μ, s) integration paths give distinct Δ_ℓ shapes (not all ≈ FLRW)
- test_b_mode_propagator_zero_for_axisymmetric:
    σ_{2M} = δ_{M,0} → Δ_ℓ^B = 0 within 1e-12
- test_b_mode_propagator_nonzero_for_off_axis:
    σ_{2,1} ≠ 0 → Δ_ℓ^B ≠ 0; magnitude ~ 0.01 × Δ_ℓ^E at peak
```

### 2.8 Adversarial audit (PR-S8, S9, S10, S11)

```
A1: grep for "fallback to FLRW Bessel" in any non-FLRW propagator: zero hits
A2: verify the hyperbolic / Wigner / collocation kernels are full implementations,
    not naive interpolation between Type-I and Type-V/IX endpoints
A6: per family: Δ_ℓ^T differs from FLRW Δ_ℓ^T by ≥ 1e-3 at ℓ=2 for σ_2M ≠ 0
A8 (CAMB external): For FLRW + Type I: per-ℓ ≤ 1% vs CAMB at ℓ ∈ [2, 30]
```

## 3. Real-space map producer (closes G10)

The `map_T/Q/U` fields of `SolverCoreOutput` become populated by an inverse spherical-harmonic transform applied to the deterministic aℓm.

### 3.1 Skeleton

```python
# bass/forward/map_producer.py  (NEW; closes G10)
import healpy as hp
import numpy as np

def alm_to_map(alm_T, alm_E, alm_B, *, nside: int = 64) -> dict:
    """
    Inverse SHT producing T, Q, U HEALPix maps. Wraps healpy.alm2map.
    """
    # Convert from BASS (m-major lexicographic real-spherical) to healpy ordering
    alm_T_hp = bass_alm_to_healpy(alm_T, lmax=infer_lmax(alm_T))
    alm_E_hp = bass_alm_to_healpy(alm_E, lmax=infer_lmax(alm_E))
    alm_B_hp = bass_alm_to_healpy(alm_B, lmax=infer_lmax(alm_B))
    
    map_T = hp.alm2map(alm_T_hp, nside, lmax=infer_lmax(alm_T))
    map_Q, map_U = hp.alm2map_spin([alm_E_hp, alm_B_hp], nside,
                                    spin=2, lmax=infer_lmax(alm_E))
    return {"map_T": map_T, "map_Q": map_Q, "map_U": map_U}

def populate_map_outputs(output: SolverCoreOutput, *, nside: int = 64) -> SolverCoreOutput:
    """
    Fill map_T/Q/U fields and switch metadata flag to 'producer_attached'.
    """
    if output.alm_T is None or output.alm_E is None or output.alm_B is None:
        raise ValueError("alm fields must be populated before producing maps")
    maps = alm_to_map(output.alm_T, output.alm_E, output.alm_B, nside=nside)
    new_metadata = dict(output.metadata)
    new_metadata["map_output_support"] = "producer_attached"
    return dataclasses.replace(
        output,
        map_T=maps["map_T"], map_Q=maps["map_Q"], map_U=maps["map_U"],
        metadata=new_metadata,
    )
```

### 3.2 Tests

```
test_map_producer.py
- test_zero_alm_yields_zero_map: identical zeros within 1e-15
- test_pure_dipole_alm_yields_dipole_map: a_{1,0} = 1, all others zero →
    map = sqrt(3/4π) cos(θ) within 1e-12
- test_round_trip_alm_to_map_back: map2alm(alm2map(alm)) ≈ alm within 1e-6
    (limited by HEALPix quadrature)
- test_producer_attached_flag_set: after populate_map_outputs,
    metadata.map_output_support == "producer_attached"
- test_post_init_validates_consistency:
    inconsistent metadata (alm None + flag = "producer_attached") raises
```

### 3.3 Adversarial audit (PR-S12)

```
A1: grep for "interpolated map", "fake map": zero hits
A3: verify alm_to_map uses healpy (not a custom 30-line approximation)
A6: maps for non-FLRW family must contain ℓ ≥ 1 power (not constant);
    monopole-only would indicate the family-specific aℓm path was lost
A10 (gate): assert that populating maps does NOT bypass the existing
    SolverCoreOutput.__post_init__ check; flag must be flipped explicitly.
```

## 4. Observable atlas (29 items; consolidates ver2_upgrade)

The `bass/observational/atlas.py` (NEW) module implements the canonical computation of the 29 observables from `ver2_upgrade/BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md`. Each observable carries metadata: ℓ-range, mask treatment, monopole/dipole subtraction policy, deterministic/stochastic/mixed flag, covariance assumption.

### 4.1 Atlas structure

```python
# bass/observational/atlas.py  (NEW)
@dataclass(frozen=True)
class Observable:
    name: str
    kind: Literal["scalar", "vector", "matrix"]
    ell_range: tuple[int, int]
    mask_treatment: str
    monopole_dipole_policy: str
    component_status: Literal["deterministic", "stochastic", "mixed"]
    covariance_required: bool
    compute: Callable[[BoostArchive], Any]

ATLAS = (
    Observable(
        name="C_TT",
        kind="vector",
        ell_range=(2, None),
        mask_treatment="full_sky_or_apodized",
        monopole_dipole_policy="exclude_l_le_1",
        component_status="mixed",
        covariance_required=True,
        compute=lambda ba: _compute_Cl(ba, channel="TT"),
    ),
    Observable(
        name="Q_2",   # quadrupole power
        kind="scalar",
        ell_range=(2, 2),
        mask_treatment="full_sky_or_apodized",
        monopole_dipole_policy="exclude",
        component_status="mixed",
        covariance_required=True,
        compute=lambda ba: _compute_Cl_at(ba, ell=2, channel="TT"),
    ),
    Observable(
        name="S_one_half",   # large-angle correlation suppressor
        kind="scalar",
        ell_range=(2, 50),
        mask_treatment="full_sky_or_apodized",
        monopole_dipole_policy="exclude",
        component_status="mixed",
        covariance_required=True,
        compute=lambda ba: _compute_S_half(ba, ell_min=2, ell_max=50),
    ),
    # ... (24 more) ...
    Observable(
        name="A_M_dipole_modulation",
        kind="vector",   # (A_M, hat_p)
        ell_range=(2, 64),
        mask_treatment="full_sky_or_apodized",
        monopole_dipole_policy="exclude",
        component_status="mixed",
        covariance_required=True,
        compute=lambda ba: _fit_dipole_modulation(ba),
    ),
    Observable(
        name="A_template",   # template fit amplitude
        kind="scalar",
        ell_range=(2, 32),
        mask_treatment="full_sky_or_apodized",
        monopole_dipole_policy="declared",
        component_status="deterministic",
        covariance_required=True,
        compute=lambda ba, *, template: _fit_template_amplitude(ba, template),
    ),
)
```

### 4.2 Per-observable safety

Every entry in `ATLAS` is computable from a `BoostArchive`. The Atlas does **not** compute statistics (likelihoods, p-values); those are gated behind §6.

## 5. MES full-covariance bound layer

Implements `mes_full_covariance_extension_self_contained.md` Theorem 11.1:

```
B_j^{final} = min{B_j^{diag}, B_j^{cov}, B_j^{dyn}}
```

with morphology information gain `I_j^{morph} = B_j^{diag} / B_j^{final} ≥ 1`.

### 5.1 Skeleton

```python
# bass/observational/mes_full_covariance.py  (NEW)
@dataclass(frozen=True)
class MESBoundResult:
    block: Literal["sigma", "omega", "acceleration", "kappa"]
    B_diag: float
    B_cov: float | None
    B_dyn: float | None
    B_final: float
    morphology_info_gain: float
    rank_status: Literal["full_rank", "rank_deficient", "no_claim"]
    nuisance_projection_used: bool

def compute_mes_bound(
    *,
    block: str,
    response_R: np.ndarray,           # (n_obs, n_param)
    nuisance_R: np.ndarray | None,    # (n_obs, n_nuis)
    obs_covariance: np.ndarray,        # (n_obs, n_obs)
    epsilon_alpha: float,               # tail bound
    diag_bound: float,                  # B^diag from kinematic theorem
    dyn_bound: float | None = None,
) -> MESBoundResult:
    """
    Theorem 11.1. Returns explicit no-claim if rank-deficient.
    """
    sqrt_N_inv = scipy.linalg.sqrtm(np.linalg.pinv(obs_covariance))
    R_white = sqrt_N_inv @ response_R
    if nuisance_R is not None:
        R_nuis = sqrt_N_inv @ nuisance_R
        P_perp = np.eye(R_white.shape[0]) - R_nuis @ np.linalg.pinv(R_nuis)
        R_eff = P_perp @ R_white
    else:
        R_eff = R_white
    smin = np.linalg.svd(R_eff, compute_uv=False)[-1]
    if smin < 1e-12:
        return MESBoundResult(block=block, B_diag=diag_bound, B_cov=None,
                              B_dyn=dyn_bound, B_final=diag_bound,
                              morphology_info_gain=1.0,
                              rank_status="no_claim",
                              nuisance_projection_used=nuisance_R is not None)
    B_cov = epsilon_alpha / smin
    B_final = min([b for b in (diag_bound, B_cov, dyn_bound) if b is not None])
    return MESBoundResult(
        block=block, B_diag=diag_bound, B_cov=B_cov, B_dyn=dyn_bound,
        B_final=B_final,
        morphology_info_gain=diag_bound / B_final,
        rank_status="full_rank",
        nuisance_projection_used=nuisance_R is not None,
    )
```

### 5.2 Tests

```
test_mes_full_covariance.py
- test_diag_only_returns_B_diag: response = identity → B_cov ≥ B_diag → final = B_diag
- test_rank_deficient_returns_no_claim: response = zero → rank_status == "no_claim"
- test_morphology_information_gain_is_unity_when_no_offdiag:
    nuisance_R = None, response_R = identity → I = 1
- test_nuisance_projection_separates_local_boost_from_global_tilt
```

## 6. Statistics gate ladder (15 stages, extends existing GATE_LADDER)

The Round-16 ladder upgrades the existing 15-stage `GATE_LADDER` with:

(a) `tilt_evolution_status` (reads `runtime_controls.tilt_freeze`) — added to `tilt_boost_separation_gate`.
(b) `template_card_authorized` (added to `ic_provenance_gate` per R15-AUDIT-PATCH P-07).
(c) `b_mode_output_support` (added to `output_split_gate` per R15-AUDIT-PATCH P-05).
(d) `map_output_support` (added to `output_split_gate` per R15-AUDIT-PATCH P-08).

The ladder remains the same 15 names; the *content* of each gate's `forbidden_shortcut_checks` block is enriched. New required fields per gate are spec'd in `V5_ROUND16_05_SHIP_GATES_AND_ADVERSARIAL_AUDIT.md §1`.

### 6.1 Real-data Planck likelihood scaffold (closes G8)

```python
# bass/inference/planck_likelihood.py  (NEW; closes G8)
class PlanckLikelihood:
    """
    Real-data Planck likelihood binding. Currently Planck 2018 Plik low-l (TT only).
    """
    def __init__(self, dataset_path: Path, *, ell_min: int = 2, ell_max: int = 30):
        self._cls_obs = self._load_planck_2018_lowl(dataset_path)  # (ell, C_l_obs, sigma)
        self.ell_min = ell_min
        self.ell_max = ell_max
    
    def log_likelihood(self, theory_C_l: np.ndarray) -> float:
        """
        Plik low-ℓ Gaussian likelihood (Planck 2018 §2.2.3, eq. 6).
        Caller must pass theory C_ℓ at same ℓ-grid as the observations.
        """
        diff = theory_C_l[self.ell_min:self.ell_max+1] - self._cls_obs.C_l
        log_lkl = -0.5 * np.sum((diff / self._cls_obs.sigma) ** 2)
        return log_lkl
    
    @staticmethod
    def _load_planck_2018_lowl(path: Path):
        # Placeholder — wire to actual Plik low-l fixture
        ...
```

The scaffold intentionally starts with TT-only Plik low-ℓ (the simplest, gauge-invariant likelihood). Polarization (TE, EE, BB), high-ℓ (Plik HL), and full Planck 2018 wrapper are deferred until Tier-C ship gate. The wrapper is gated:

```python
# bass/inference/__main__.py  (modify; G8 closure)
if dataset.kind == "planck2018_plik_low_l_tt_only":
    if not gate_decision.allowed:
        raise FittingBlockedError(
            "Real-data Planck fitting blocked until all 15 gates open.\n"
            f"Missing: {gate_decision.missing_gates}"
        )
    likelihood = PlanckLikelihood(dataset.path)
    # ... emcee / nested sampling driver ...
```

### 6.2 Adversarial audit (PR-S14)

```
A4: synthetic-only check enforced — without dataset.kind whitelist explicitly
    set to "planck2018_plik_low_l_tt_only" AND all 15 gates green AND
    template_card_authorized=True for any non-strong family, fitting raises
A6: assert that the Planck likelihood does NOT silently fall back to a
    synthetic surrogate when the real fixture is missing
A10: end-to-end gate ladder test: with real Planck data and one missing gate,
    log_likelihood raises FittingBlockedError; with all gates green it returns
    a finite scalar
```

## 7. (x, Q, F, Π, G) framework integration

The framework (§7 of ver2_upgrade brief) exposes the **claim tier** semantics via a single dispatch:

```python
# bass/observational/x_Q_F_Pi_G.py  (NEW)
@dataclass(frozen=True)
class ClaimTierResult:
    tier: Literal["C0", "C1", "C2", "C3", "C4", "C5"]
    F: float | None
    F_certified: bool
    Pi_at_q_50: float | None
    Pi_at_q_95: float | None
    G_F: dict[tuple[float, float], float]   # (z_a, z_b) → ratio
    failure_reason: str | None

def evaluate_claim_tier(
    *,
    bass_output: BoostArchive,
    mes_result: dict[str, MESBoundResult],   # per-block
    null_ensemble_pvalues: dict[str, float],
    coherence_test_passed: bool,
    redshift_evolution_passed: bool,
    morphology_compatibility_passed: bool,
    family_id_passed: bool,
) -> ClaimTierResult:
    """
    Walks the C0 → C5 tier ladder per ver2_upgrade x_Q_F_Pi_G spec.
    Returns the *highest* tier supported by the inputs, or C0 with reason.
    """
    # C0: F invalid → no claim
    F_certified = all(m.rank_status == "full_rank" for m in mes_result.values()) \
                   and bass_output["alm_T"].size > 0
    if not F_certified:
        return ClaimTierResult(tier="C0", F=None, F_certified=False,
                                Pi_at_q_50=None, Pi_at_q_95=None, G_F={},
                                failure_reason="F invalid: rank-deficient or empty")
    
    F_value = _compute_F_from_archive(bass_output, mes_result)
    # ... walk C1..C5 with explicit gates per ver2_upgrade ...
    return ClaimTierResult(tier=highest_tier, F=F_value, F_certified=True,
                            Pi_at_q_50=..., Pi_at_q_95=..., G_F={...},
                            failure_reason=None)
```

## 8. Output archive: deterministic / stochastic / boost split

Already implemented in `BoostArchive` per R15-AUDIT-PATCH P-05. Round-16 only requires that:
- The deterministic component (from solver) carries `component_kind="deterministic"` and `component_status="solver_native"`.
- Stochastic (Monte Carlo on theory C_ℓ) carries `component_kind="stochastic"` and metadata `n_realizations`.
- Boost (post-processing observer dipole) carries `component_kind="boost"` and `boost_applied=True`.

The atlas evaluator (§4) reads from the `det+stoch` mixture; the boost contribution is *removed* before atlas evaluation (per `BoostArchive.split_semantics="output_only_local_boost"`).

## 9. End-of-layer adversarial audit (cross-cutting)

```
P1. Atlas coverage
   For each Observable in ATLAS: assert it has a non-trivial compute() that
   does NOT short-circuit to the FLRW Cℓ when called on a Bianchi BoostArchive.

P2. LoS propagator non-FLRW
   For each non-FLRW family at σ ≠ 0:
     assert |Δ_ℓ^family - Δ_ℓ^FLRW| / |Δ_ℓ^FLRW| ≥ 1e-3 at ℓ ∈ [2, 10]

P3. Map producer wiring
   populate_map_outputs(...) → metadata.map_output_support == "producer_attached"
   AND maps are not all-zero AND maps are not constant (ℓ ≥ 1 power present)

P4. B-mode pathway probe (cross-cuts §2.5)
   With injected σ_{2,1} ≠ 0:
     transfer_B[ℓ=2..10, m=±1] is non-zero AND has expected parity-odd morphology

P5. Doppler /k correction
   Re-run FLRW pipeline post-Round-16; D_2(post) - D_2(pre) ≈ -5 μK² (the
   audit-flagged shift from missing 1/k factor; see V5 R15 P1 §2 R7).
   Cross-check with CAMB at the same params: |Δ_2^BASS - Δ_2^CAMB| < 1%.

P6. MES no-claim probe
   Build a deliberately rank-deficient response_R; compute_mes_bound returns
   MESBoundResult with rank_status="no_claim". Does NOT silently
   downcast to B_diag.

P7. Statistics gate ladder regression
   With one upstream gate closed: hard_gate_before_fitting().allowed == False
   With all 15 open: allowed == True

P8. Real-data fitting blockade
   Without dataset.kind whitelist + template_card_authorized: raise
   FittingBlockedError. Cannot bypass via env-var or config flag.
```

## 10. Code-port helpers

Rust → Python:

| Rust symbol | Python | Status |
|-------------|--------|--------|
| `BianchiPropagator::project_T` | `bass/los/bianchi_propagator/{type_v,type_ix,...}.py::TypeXPropagator.project_T` | NEW |
| `MapProducer::alm_to_map` | `bass/forward/map_producer.py::alm_to_map` | NEW |
| `MES::compute_full_cov_bound` | `bass/observational/mes_full_covariance.py::compute_mes_bound` | NEW |
| `PlanckPlikLowL::log_likelihood` | `bass/inference/planck_likelihood.py::PlanckLikelihood.log_likelihood` | NEW |

Bit-identity required for FLRW limit only (Bianchi propagators may differ at solver-level discretization choices but must agree on observables to <1%).

---

**End of Observables Layer.** Continue to `V5_ROUND16_04_NUMERICS_AND_RUNTIME.md`.
