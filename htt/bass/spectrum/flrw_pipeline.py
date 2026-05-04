"""End-to-end FLRW CMB D_ℓ pipeline (V5 step 4b).

Chains the V5 runtime track's building blocks into a single entry point
that produces Planck-2018 FLRW D_ℓ from real Tier-B physics:

    species + k_grid
        → per-k: execute_tier_b_solver (Blockers 1+2+3)
                  → extract_flrw_sources_from_tier_b (Round-5)
                  → build_scalar_sources_pair
                  → project_m_transfer  → Δ_ℓ^T(k), Δ_ℓ^E(k)
        → k-sweep parallelized via ProcessPoolExecutor
        → assemble_cl_TT_EE_TE_isotropic_from_grid
        → compute_dl → D_ℓ in μK²

This is the replacement for the reverted S8/S9 toy SW-plateau pipeline
(``85c2270``); every stage uses physical Tier-B output, no toy
approximations.

Optimization strategy
---------------------
Per-k cost is dominated by the Tier-B IMEX solver (~45 s at L_max=4 on
the cosmological η range). The k-sweep is embarrassingly parallel since
each k is an independent solver run. We use
``concurrent.futures.ProcessPoolExecutor`` with the default ``fork``
start method on Linux so each worker inherits the parent's
``SpeciesBackgroundRegistry`` via copy-on-write — no per-worker
registry rebuild cost.

Benchmark (Planck-2018, L_max=4, cosmological η-range):
    - Sequential 10 × k:      ~450 s
    - Parallel 10 × k (8 w):   ~60 s   (7.5× speedup, near-linear)

For a full 0.1% D_2 validation (N_k ~ 100–200), budget ~2–5 min with
8 workers. The validation is exposed as a ``@pytest.mark.slow`` test
rather than included in the default ~20 s fast baseline.
"""
from __future__ import annotations

import concurrent.futures as _cf
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Sequence

import numpy as np

from bass.background.bianchi_types import get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.forward.ver2_solver_output import BassReleaseMetadata
from bass.los.bianchi_propagator import BianchiTransferFunctions
from bass.los.flrw_bessel_projector import (
    FLRWBesselConfig,
    build_scalar_sources_pair,
    project_scalar_transfer_pair,
)
from bass.los.los_grid_builder import build_los_grid
from bass.recombination.reionization import (
    compute_kappa_from_tau_dot,
    compute_tau_dot_conformal_Mpc,
)
from bass.runtime import (
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    DEFAULT_PRE_RECOMBINATION_MARGIN_MPC,
    FeatureStatus,
    IntegratorFamily,
    PLANCK_2018_Z_STAR,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
    build_cosmological_integrator_config,
    cosmological_critical_etas,
    execute_tier_b_solver,
)
from bass.spectrum.cl_assembly import (
    CLAssemblyConfig,
    assemble_cl_TT_EE_TE_isotropic_from_grid,
    compute_dl,
)
from bass.spectrum.tier_b_source_extraction import (
    extract_flrw_sources_from_tier_b,
)
from bass.species.base import SpeciesLabel
from common.contracts import ArtifactManifest

if TYPE_CHECKING:
    from bass.species.registry import SpeciesBackgroundRegistry


__all__ = [
    "FLRWPipelineConfig",
    "_resolve_z_injection_for_k",
    "compute_transfer_function_at_k",
    "compute_transfer_function_grid",
    "compute_linear_probe_transfer_function",
    "compute_flrw_cl_tt",
    "compute_flrw_d_ell",
    "compute_flrw_d_ell_linear_probe",
    "build_visibility_and_kappa_callables",
]


def _resolve_primordial_b_k_sq(
    cfg: "FLRWPipelineConfig",
    k_mpc: float,
) -> float:
    """Resolve the primordial B_K² amplitude for a given k.

    Precedence: ``primordial_b_k_sq_fn`` (if callable) > the scalar
    ``primordial_b_k_sq``. Callable is evaluated in the PARENT process
    so per-k resolution survives ProcessPoolExecutor fork/spawn
    dispatch (workers only see pre-resolved floats).
    """
    fn = cfg.primordial_b_k_sq_fn
    if fn is not None:
        return float(fn(float(k_mpc)))
    return float(cfg.primordial_b_k_sq)


def _split_work_chunks(
    values: Sequence[Any],
    *,
    worker_count: int,
    chunk_size: int | None,
) -> list[list[Any]]:
    """Split work in-order for process-pool dispatch.

    ``chunk_size=None`` preserves the historical even split into at most
    one chunk per worker. A positive ``chunk_size`` creates fixed-size
    chunks; ``Executor.map`` keeps output order while allowing workers to
    pull the next chunk as soon as they finish the previous one.
    """

    n_values = len(values)
    if n_values == 0:
        return []
    if chunk_size is not None:
        size = int(chunk_size)
        if size <= 0:
            raise ValueError(f"chunk_size must be positive; got {chunk_size}")
        return [
            [values[j] for j in range(i, min(i + size, n_values))]
            for i in range(0, n_values, size)
        ]
    n_chunks = max(1, min(int(worker_count), n_values))
    index_chunks = np.array_split(np.arange(n_values), n_chunks)
    return [
        [values[int(i)] for i in idx]
        for idx in index_chunks
        if len(idx) > 0
    ]


@dataclass(frozen=True)
class FLRWPipelineConfig:
    """Configuration bundle for the end-to-end FLRW D_ℓ pipeline.

    Defaults target Planck-2018 FLRW with L_max = 4 (sufficient for
    ℓ ≤ 4 D_ℓ extraction; increase for higher ℓ or tighter quadrature).
    """

    L_max_tower: int = 4
    n_output: int = 64
    rtol: float = 1.0e-6
    atol: float = 1.0e-9
    anisotropic_stress: bool = True
    ell_max_transfer: int = 4
    quadrature: str = "trapezoid"
    gamma_T_over_H_threshold: float = 100.0
    z_injection: float = PLANCK_2018_Z_STAR
    """Nominal injection redshift used by the cosmological Tier-B run.

    The historical default is the Planck-2018 visibility peak
    ``z_* = 1089.94``. For transfer-function validation this may be
    raised explicitly, or automatically via
    ``superhorizon_x_max_at_start``, so the regular adiabatic seed is
    applied in a genuine ``k η_init << 1`` regime.
    """
    pre_recombination_margin_mpc: float = DEFAULT_PRE_RECOMBINATION_MARGIN_MPC
    """Conformal-time margin subtracted from ``η(z_injection)``.

    Set to zero for strict ``k η_init`` diagnostics, or keep the default
    20 Mpc ramp for the historical recombination-start path.
    """
    superhorizon_x_max_at_start: float | None = None
    """Optional per-k start resolver enforcing ``k * η_init <= x_max``.

    When set, each k may receive a different ``z_injection``. Shared
    background k-chunking is disabled in that mode because the
    background/visibility/integrator anchors are no longer common across
    k. This is a physics control, not a speed knob.
    """
    random_seed: int = 42
    unit_amplitude_normalization: bool = True
    max_step_factor: int = 1000
    """V5 Round-17 P3.5 perf knob (2026-04-27): forwarded to
    ``IntegratorConfig.max_step_factor``. Default 1000 preserves the
    legacy fine-step recombination sampling. Diagnostic / sweep callers
    that don't need recombination-resolution accuracy can drop this to
    ~100 for ~3× speedup. See ``IntegratorConfig.max_step_factor``
    docstring for the trade-off."""
    imex_explicit_update_limit: float = 0.05
    """Forwarded to ``IntegratorConfig.imex_explicit_update_limit``.
    Default 0.05 preserves the historical VER2 IMEX safety cap.
    Diagnostic sweeps may raise this only with a same-output fairness
    comparison against the default cap."""
    co_evolve_scalar_metric: bool = False
    """Forwarded to ``IntegratorConfig.co_evolve_scalar_metric``.

    When True, Tier-B runs co-evolve MB95 ``(etak, sigma)`` in the native
    state and runtime dispatch routes the solve to full-RHS BDF until the
    scalar-metric IMEX block is validated.
    """
    co_evolve_scalar_streaming: bool = False
    """Forwarded to ``IntegratorConfig.co_evolve_scalar_streaming``.

    This enables the MB95 scalar m=0 photon/neutrino intensity
    free-streaming recursion. It is a real implemented physics path, but
    remains opt-in because full-range BDF/TCA/cutoff stability is still under
    validation.
    """
    flrw_source_frame: str = "legacy_newtonian_constraint"
    """Source frame passed to ``extract_flrw_sources_from_tier_b``.

    ``"legacy_newtonian_constraint"`` is the current default. Use
    ``"mb95_synchronous_effective"`` only with
    ``co_evolve_scalar_metric=True`` for authority-style scalar-source
    experiments, or explicitly for post-hoc diagnostics.
    """
    k_solver_batch_mode: str = "shared_background"
    """k-solver execution mode inside a shared-background chunk.

    ``"shared_background"`` preserves the historical serial per-k solve
    after amortizing background/visibility/backend construction.
    ``"threaded"`` runs independent per-k solves concurrently inside
    the chunk, sharing read-only background/visibility state but using
    one fresh family backend per thread. ``"joint_imex"`` selects the
    staged IMEX batch wrapper controlled by ``joint_imex_schedule``:
    the default independent schedule is parity-first, ``"ragged"``
    interleaves native per-k substeps without a global common step, and
    ``"shared_step"`` remains the experimental true shared-step solver.
    """
    intra_chunk_threads: int = 1
    """Maximum thread count for ``k_solver_batch_mode="threaded"``.
    Defaults to 1 so existing process-level parallelism and bitwise
    regression behavior are unchanged."""
    k_chunk_size: int | None = None
    """Optional fixed k-count per process chunk.

    ``None`` preserves the historical one-chunk-per-worker split. A
    positive integer creates more, smaller chunks so large k-grids can
    load-balance across workers when per-k runtimes vary, while still
    amortizing background/visibility setup inside each chunk.
    """
    joint_imex_reference_check: bool = True
    """Fail-closed guard for ``k_solver_batch_mode="joint_imex"``.

    When enabled, the experimental joint-step batch result is compared
    against the ordinary independent per-k path before it is returned.
    This is intentionally expensive; it prevents a scheduler-level
    optimization from silently changing physical outputs while the
    joint IMEX path is still being matured.
    """
    joint_imex_reference_rtol: float = 1.0e-9
    joint_imex_reference_atol: float = 1.0e-9
    joint_imex_schedule: str = "independent"
    """Scheduler used by ``k_solver_batch_mode="joint_imex"``.

    ``"independent"`` is the parity-first staging path: each k keeps
    the native per-k IMEX adaptive schedule while the batch wrapper
    shares setup/result plumbing. ``"ragged"`` advances all k states
    through the extracted native one-substep primitive, but each k keeps
    its own accepted step size. ``"grouped"`` keeps the same per-k
    proposal rule and only buckets members with matching proposed
    substep targets. ``"shared_step"`` uses one common substep schedule
    across k and remains guarded experimental until it passes the
    reference drift check.
    """
    adiabatic_mode_seed: bool = True
    """V5 step-4b-(a) super-horizon adiabatic initial condition. When
    True (default for the V5 pipeline), the seed ratios follow
    ``δ_γ:δ_b:δ_c:δ_ν = 4/3:1:1:4/3`` with ``θ = 0`` — the physically
    correct adiabatic mode for a super-horizon k·η_init ≪ 1, which
    holds for the low-k range that drives D_2 (k < 1/η_init ≈
    4e-3 Mpc⁻¹ at η_init = 260 Mpc). This only toggles the canonical
    tracking placeholder; the physics-determining IC at each k comes
    from the Lowell §13.2 ``make_camb_regular_adiabatic_seed`` (see
    ``primordial_b_k_sq`` below)."""
    primordial_b_k_sq: float = 1.0
    """**Linear primordial curvature amplitude** ``C ≈ ζ`` of the
    Lowell §13.2 regular-adiabatic seed (Ma-Bertschinger 1995 §7
    eq. 96; Lewis-Challinor 2002 App. C). Despite the historical
    name (which dates to a CAMB Notes geometric ``β²`` convention
    that equals 1 in flat FLRW), every leading-order seed perturbation
    is **linear** in this parameter — confirmed by 4 independent
    external audits (V5-RUNTIME Round-12, 2026-04-25). Default 1.0
    gives unit-amplitude transfer functions for the linear-probe
    extraction.

    Do NOT pass ``A_s × (k/k_pivot)^(n_s-1)`` here. That value
    (~2.1e-9) is the *variance* spectrum ``P_R(k) = ⟨ζ²⟩`` and
    belongs in the C_ℓ assembly, not the seed. The ``compute_flrw_*``
    pipeline pairs the linear-probe transfer with ``P_R(k)`` exactly
    once via ``C_ℓ = 4π ∫ d ln k · P_R(k) · |α|²``."""
    primordial_b_k_sq_fn: Callable[[float], float] | None = None
    """V5 step-4b-(a) Round-7 k-dependent override. When set to a
    callable ``k → b_k_sq``, overrides the scalar ``primordial_b_k_sq``
    field per k. Used for diagnostic k-dependent amplitude probes; for
    the canonical pipeline that pairs a unit-amplitude transfer with
    ``P_R(k)`` in the assembly, leave ``None`` and use ``b_k_sq = 1.0``.

    The callable is evaluated in the PARENT process so per-k values are
    resolved to concrete floats before dispatch to fork workers
    (ProcessPoolExecutor-safe). Leaving ``None`` preserves the scalar
    ``primordial_b_k_sq`` convention.
    """
    bias_subtraction: bool = False
    """V5 step-4b-(a) Round-6 finding: the solver carries a
    seed-independent visibility-source contribution that produces
    non-zero Δ_ℓ even at ``primordial_b_k_sq → 0``. When
    ``bias_subtraction=True``, each k triggers TWO parallel solver
    runs (``b_k_sq = 0`` and ``b_k_sq = primordial_b_k_sq``) and the
    pipeline returns ``Δ_pure = Δ_target − Δ_bias``. Doubles per-k
    cost but isolates the pure seed response for transfer-function
    extraction. Defaults False (legacy single-run path)."""
    """When True (default), divide Δ_ℓ by the solver's seed amplitude so
    that the returned transfer function is the physical "unit
    primordial amplitude" response (C_ℓ = 4π ∫ P(k) |Δ|² dlnk then
    pairs Δ directly with the primordial P(k) in cl_assembly without
    double-counting). Set False if callers want the raw solver
    response scaled by the seed amplitude (e.g. for debugging
    linearity)."""

    def __post_init__(self) -> None:
        if self.L_max_tower < 2:
            raise ValueError(
                f"L_max_tower ≥ 2 required (E/B towers start at ℓ=2); "
                f"got {self.L_max_tower}"
            )
        if self.ell_max_transfer > self.L_max_tower:
            raise ValueError(
                f"ell_max_transfer={self.ell_max_transfer} exceeds tower "
                f"L_max_tower={self.L_max_tower}"
            )
        if self.n_output < 12:
            raise ValueError(
                f"n_output ≥ 12 required for meaningful cosmological "
                f"evolution; got {self.n_output}"
            )
        if self.quadrature not in ("trapezoid", "simpson"):
            raise ValueError(
                f"quadrature must be 'trapezoid' or 'simpson'; "
                f"got {self.quadrature!r}"
            )
        if not (float(self.z_injection) > 0.0):
            raise ValueError(
                f"z_injection must be positive; got {self.z_injection}"
            )
        if float(self.pre_recombination_margin_mpc) < 0.0:
            raise ValueError(
                "pre_recombination_margin_mpc must be non-negative; "
                f"got {self.pre_recombination_margin_mpc}"
            )
        if (
            self.superhorizon_x_max_at_start is not None
            and not (float(self.superhorizon_x_max_at_start) > 0.0)
        ):
            raise ValueError(
                "superhorizon_x_max_at_start must be positive when set; "
                f"got {self.superhorizon_x_max_at_start}"
            )
        if self.max_step_factor <= 0:
            raise ValueError(
                f"max_step_factor must be positive; got {self.max_step_factor}"
            )
        if self.imex_explicit_update_limit <= 0.0:
            raise ValueError(
                "imex_explicit_update_limit must be positive; "
                f"got {self.imex_explicit_update_limit}"
            )
        if self.flrw_source_frame not in {
            "legacy_newtonian_constraint",
            "mb95_synchronous_effective",
        }:
            raise ValueError(
                "flrw_source_frame must be 'legacy_newtonian_constraint' or "
                f"'mb95_synchronous_effective'; got {self.flrw_source_frame!r}"
            )
        if self.k_solver_batch_mode not in {
            "shared_background",
            "threaded",
            "joint_imex",
        }:
            raise ValueError(
                "k_solver_batch_mode must be one of "
                "'shared_background', 'threaded', or 'joint_imex'; "
                f"got {self.k_solver_batch_mode!r}"
            )
        if self.intra_chunk_threads <= 0:
            raise ValueError(
                "intra_chunk_threads must be positive; "
                f"got {self.intra_chunk_threads}"
            )
        if self.k_chunk_size is not None and self.k_chunk_size <= 0:
            raise ValueError(
                "k_chunk_size must be positive when set; "
                f"got {self.k_chunk_size}"
            )
        if self.joint_imex_reference_rtol < 0.0:
            raise ValueError(
                "joint_imex_reference_rtol must be non-negative; "
                f"got {self.joint_imex_reference_rtol}"
            )
        if self.joint_imex_reference_atol < 0.0:
            raise ValueError(
                "joint_imex_reference_atol must be non-negative; "
                f"got {self.joint_imex_reference_atol}"
            )
        if self.joint_imex_schedule not in {
            "independent",
            "ragged",
            "grouped",
            "shared_step",
        }:
            raise ValueError(
                "joint_imex_schedule must be 'independent', 'ragged', "
                "'grouped', or 'shared_step'; "
                f"got {self.joint_imex_schedule!r}"
            )


def _resolve_z_injection_for_k(
    species: "SpeciesBackgroundRegistry",
    cfg: FLRWPipelineConfig,
    k_mpc: float,
) -> float:
    """Resolve the injection redshift for one transfer-function k.

    With ``superhorizon_x_max_at_start=None`` this returns the explicit
    ``cfg.z_injection``. Otherwise it raises ``z_injection`` only when
    the current start would violate ``k η_init <= x_max``. The returned
    value is derived from the shared FLRW background table; no CAMB or
    fitted external timing is used.
    """

    k = float(k_mpc)
    if not (k > 0.0):
        raise ValueError(f"k_mpc must be positive; got {k_mpc}")
    if cfg.superhorizon_x_max_at_start is None:
        return float(cfg.z_injection)

    anchors = cosmological_critical_etas(
        species,
        z_injection=float(cfg.z_injection),
        pre_recombination_margin_mpc=float(cfg.pre_recombination_margin_mpc),
    )
    current_eta_initial = float(anchors["eta_initial_mpc"])
    target_eta_initial = min(
        current_eta_initial,
        float(cfg.superhorizon_x_max_at_start) / k,
    )
    if np.isclose(
        target_eta_initial,
        current_eta_initial,
        rtol=0.0,
        atol=1.0e-12,
    ):
        return float(cfg.z_injection)

    eta_star_target = (
        target_eta_initial + float(cfg.pre_recombination_margin_mpc)
    )
    bg_table = species.bg_table
    eta_min = float(bg_table.eta[0])
    eta_today = float(bg_table.eta_today)
    if eta_star_target < eta_min or eta_star_target >= eta_today:
        raise ValueError(
            "superhorizon_x_max_at_start requests an injection anchor "
            "outside the species background table: "
            f"k={k:.6e}, eta_star_target={eta_star_target:.6e} Mpc, "
            f"eta_range=[{eta_min:.6e}, {eta_today:.6e}]"
        )

    a_target = float(np.asarray(bg_table.interp_a(eta_star_target)))
    z_target = 1.0 / a_target - 1.0
    if z_target < float(cfg.z_injection):
        return float(cfg.z_injection)
    return float(z_target)


def _pipeline_manifest(label: str) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=f"bass.v5.flrw_pipeline.{label}",
        artifact_path=f"artifacts/bass/v5_flrw_pipeline_{label}.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="flrw_pipeline",
        git_commit="unknown",
        config_hash=f"v5-flrw-pipeline-{label}",
        input_hashes=["planck2018"],
        code_version="v5-runtime",
        schema_version="1.0.0",
        required_gates=["runtime"],
        passed_gates=["runtime"],
    )


def _pipeline_release(label: str, seed: int) -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="research_candidate",
        run_label=f"v5-flrw-pipeline-{label}",
        config_hash=f"v5-flrw-pipeline-{label}",
        code_version="v5-runtime",
        schema_version="1.0.0",
        git_commit="unknown",
        random_seed=seed,
    )


def _pipeline_runtime_controls(config: FLRWPipelineConfig) -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=SolverTier.TIER_B_PSTF,
        integrator_family=IntegratorFamily.IMEX_SPLIT,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=config.L_max_tower,
        rtol=config.rtol,
        atol=config.atol,
        checkpoint=CheckpointPolicy(enabled=False),
        constraint_projection=ConstraintProjectionPolicy(
            enabled=True,
            every_n_steps=4,
            status=FeatureStatus.APPROXIMATE,
        ),
        random_seed=config.random_seed,
    )


def _pipeline_feature_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.APPROXIMATE,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def build_visibility_and_kappa_callables(
    species: "SpeciesBackgroundRegistry",
) -> tuple[Callable[[np.ndarray], np.ndarray], Callable[[np.ndarray], np.ndarray]]:
    """Build (g_of_eta, kappa_of_eta) callables from the species registry.

    Both callables convert η → z via the FLRW background table's
    ``interp_a(η)`` and query the baryon's HYREC recombination interp
    ``.query_visibility(z)`` / ``.query_kappa(z)``.

    The returned callables accept scalar or array η and return arrays
    of matching shape.
    """

    baryon = species[SpeciesLabel.BARYON]
    recomb = baryon._recomb  # noqa: SLF001 — stable internal accessor
    bg_table = species.bg_table
    cosmo = baryon._cosmology_for_recombination()  # noqa: SLF001
    z_min = float(recomb.table.z_min)
    z_max = float(recomb.table.z_max)
    z_bg_max = float(1.0 / float(bg_table.a[0]) - 1.0)

    if z_bg_max > z_max:
        z_early_grid = np.geomspace(z_max, z_bg_max, 4096)
        z_early_grid[0] = z_max
        x_e_full = np.full_like(
            z_early_grid,
            1.0 + 2.0 * cosmo.f_He,
            dtype=np.float64,
        )
        tau_dot_early_grid = np.asarray(
            compute_tau_dot_conformal_Mpc(z_early_grid, x_e_full, cosmo),
            dtype=np.float64,
        )
        kappa_z_max = float(np.asarray(recomb.query_kappa(z_max)))
        kappa_early_grid = (
            kappa_z_max
            + compute_kappa_from_tau_dot(
                z_early_grid,
                tau_dot_early_grid,
                cosmo,
            )
        )
    else:
        z_early_grid = np.array([z_max], dtype=np.float64)
        tau_dot_early_grid = np.array(
            [float(np.asarray(recomb.query_tau_dot(z_max)))],
            dtype=np.float64,
        )
        kappa_early_grid = np.array(
            [float(np.asarray(recomb.query_kappa(z_max)))],
            dtype=np.float64,
        )

    def _z_of_eta(eta: np.ndarray) -> np.ndarray:
        a = np.asarray(bg_table.interp_a(eta), dtype=np.float64)
        return 1.0 / np.maximum(a, 1.0e-30) - 1.0

    def g_of_eta(eta: np.ndarray) -> np.ndarray:
        z = _z_of_eta(np.asarray(eta, dtype=np.float64))
        scalar = z.ndim == 0
        z_arr = np.atleast_1d(z).astype(np.float64)
        out = np.empty_like(z_arr, dtype=np.float64)
        table_mask = z_arr <= z_max
        if np.any(table_mask):
            z_clipped = np.clip(z_arr[table_mask], z_min, z_max)
            out[table_mask] = np.asarray(
                recomb.query_visibility(z_clipped),
                dtype=np.float64,
            )
        early_mask = ~table_mask
        if np.any(early_mask):
            tau_dot = np.interp(
                z_arr[early_mask],
                z_early_grid,
                tau_dot_early_grid,
            )
            kappa = np.interp(
                z_arr[early_mask],
                z_early_grid,
                kappa_early_grid,
            )
            out[early_mask] = tau_dot * np.exp(-kappa)
        return out[0] if scalar else out

    def kappa_of_eta(eta: np.ndarray) -> np.ndarray:
        z = _z_of_eta(np.asarray(eta, dtype=np.float64))
        scalar = z.ndim == 0
        z_arr = np.atleast_1d(z).astype(np.float64)
        out = np.empty_like(z_arr, dtype=np.float64)
        table_mask = z_arr <= z_max
        if np.any(table_mask):
            z_clipped = np.clip(z_arr[table_mask], z_min, z_max)
            out[table_mask] = np.asarray(
                recomb.query_kappa(z_clipped),
                dtype=np.float64,
            )
        early_mask = ~table_mask
        if np.any(early_mask):
            out[early_mask] = np.interp(
                z_arr[early_mask],
                z_early_grid,
                kappa_early_grid,
            )
        return out[0] if scalar else out

    return g_of_eta, kappa_of_eta


def _los_and_wrap(
    integration_result: Any,
    species: "SpeciesBackgroundRegistry",
    k_mpc: float,
    cfg: FLRWPipelineConfig,
    seed_amp_for_norm: float | None,
    visibility_callables: tuple[
        Callable[[np.ndarray], np.ndarray],
        Callable[[np.ndarray], np.ndarray],
    ] | None = None,
) -> BianchiTransferFunctions:
    """Run Round-5 extractor + LoS projectors + optional seed-amp
    normalization for a single k. Shared helper between the high-level
    ``compute_transfer_function_at_k`` and the chunked low-level path.
    """

    sources = extract_flrw_sources_from_tier_b(
        integration_result,
        species,
        k=float(k_mpc),
        anisotropic_stress=cfg.anisotropic_stress,
        source_frame=str(cfg.flrw_source_frame),
    )
    if visibility_callables is None:
        g_of_eta, kappa_of_eta = build_visibility_and_kappa_callables(species)
    else:
        g_of_eta, kappa_of_eta = visibility_callables

    # V5 Round-15 P0 D-1 fix: decouple LoS quadrature grid from the IMEX
    # integrator output grid. The integrator's 64-point uniform-linear
    # η-grid (Δη ≈ 220 Mpc) under-resolves both the recombination
    # visibility (FWHM ≈ 19 Mpc) and the Bessel oscillation period
    # (2π/k ≈ 125 Mpc at k = 0.05 /Mpc). The §10 decisive test (commit
    # b2a9736) confirmed this aliases the LoS integral with median
    # |error| factor 8.30 even when fed CAMB-perfect Newtonian-gauge
    # sources. Build a per-k composite grid: recombination-refined
    # zone (Δη ≈ 2.4 Mpc) + k-adapted oscillation zone (Δη ≈ 2π/(8k)).
    integrator_eta = np.asarray(integration_result.eta, dtype=np.float64)
    eta_0_mpc = float(species.bg_table.eta_today)
    # PCHIP source interpolators use extrapolate=False — clamp the LoS
    # lower bound to the integrator's first η to avoid NaN evaluation
    # at the very first sample.
    eta_init_los = float(np.maximum(integrator_eta[0], 0.0))
    # Safety: zone 2 upper bound must respect the integrator's last η
    # so PCHIP sources stay in-domain at the observer end too.
    eta_today_los = float(np.minimum(integrator_eta[-1], eta_0_mpc))
    eta_for_los = build_los_grid(
        k=float(k_mpc),
        eta_today=eta_today_los,
        eta_init=eta_init_los,
    )

    bessel_config = FLRWBesselConfig(
        ell_max=cfg.ell_max_transfer,
        eta_0_mpc=eta_0_mpc,
        quadrature=cfg.quadrature,
    )
    source_T, source_E = build_scalar_sources_pair(
        eta_for_los, sources, g_of_eta, kappa_of_eta
    )
    delta_T, delta_E = project_scalar_transfer_pair(
        float(k_mpc), source_T, source_E, eta_for_los, bessel_config
    )

    if cfg.unit_amplitude_normalization and seed_amp_for_norm is not None:
        if not (seed_amp_for_norm > 0.0):
            raise ValueError(
                f"seed_amp must be positive for unit-amplitude normalization; "
                f"got {seed_amp_for_norm!r}"
            )
        delta_T = delta_T / seed_amp_for_norm
        delta_E = delta_E / seed_amp_for_norm

    zero_template = np.zeros_like(delta_T)
    return BianchiTransferFunctions(
        delta_T_m0=delta_T,
        delta_T_m_plus2=zero_template.copy(),
        delta_T_m_minus2=zero_template.copy(),
        delta_E_m0=delta_E,
        delta_E_m_plus2=zero_template.copy(),
        delta_E_m_minus2=zero_template.copy(),
        delta_B_all_zero=np.zeros(cfg.ell_max_transfer + 1, dtype=np.float64),
    )


def _build_results_from_joint_imex_states(
    integrators: Sequence[Any],
    eta_out: np.ndarray,
    states_by_run: Sequence[Sequence[np.ndarray] | np.ndarray],
    *,
    nfev: Sequence[int],
    tca_trackers: Sequence[list[bool]],
) -> list[Any]:
    """Reconstruct ``IntegrationResult`` objects from shared-step states.

    This mirrors the no-checkpoint branch of
    ``Ver2TierBIntegrator.run``. The helper is intentionally private to
    the FLRW spectrum path because it relies on the VER2 native
    integrator's private state layout.
    """

    from bass.hierarchy.ver2_native_integrator import (
        _BARYON_LOCAL_DOF,
        _LOCAL_MATTER_DOF,
        _PRIMARY_LOCAL_DOF,
    )

    out: list[Any] = []
    eta_arr = np.asarray(eta_out, dtype=np.float64)
    for idx, integrator in enumerate(integrators):
        tower_size = (int(integrator.config.L_max) + 1) ** 2
        raw_states = states_by_run[idx]
        if isinstance(raw_states, np.ndarray):
            state_table = np.asarray(raw_states, dtype=np.float64)
            if state_table.ndim != 2:
                raise ValueError(
                    "joint IMEX state history array must be two-dimensional; "
                    f"got shape {state_table.shape}"
                )
            if state_table.shape[0] == eta_arr.size:
                states = state_table.T
            elif state_table.shape[1] == eta_arr.size:
                states = state_table
            else:
                raise ValueError(
                    "joint IMEX state history array does not match eta grid: "
                    f"shape={state_table.shape}, eta_size={eta_arr.size}"
                )
        else:
            states = np.asarray(
                np.column_stack(raw_states),
                dtype=np.float64,
            )
        residual_local_start = 4 * tower_size + _PRIMARY_LOCAL_DOF
        residual_local_stop = residual_local_start + integrator._residual_local_dof
        residual_harmonic_stop = (
            residual_local_stop + integrator._residual_harmonic_dof
        )
        result = integrator._build_result(
            eta=eta_arr,
            photon_T_tower=np.asarray(states[:tower_size].T, dtype=np.float64),
            photon_E_tower=np.asarray(
                states[tower_size : 2 * tower_size].T,
                dtype=np.float64,
            ),
            photon_B_tower=np.asarray(
                states[2 * tower_size : 3 * tower_size].T,
                dtype=np.float64,
            ),
            neutrino_tower=np.asarray(
                states[3 * tower_size : 4 * tower_size].T,
                dtype=np.float64,
            ),
            baryon_local_history=np.asarray(
                states[
                    4 * tower_size : 4 * tower_size + _BARYON_LOCAL_DOF
                ].T,
                dtype=np.float64,
            ),
            cdm_local_history=np.asarray(
                states[
                    4 * tower_size
                    + _BARYON_LOCAL_DOF : 4 * tower_size
                    + _LOCAL_MATTER_DOF
                ].T,
                dtype=np.float64,
            ),
            source_local_history=np.asarray(
                states[
                    4 * tower_size
                    + _LOCAL_MATTER_DOF : 4 * tower_size
                    + _PRIMARY_LOCAL_DOF
                ].T,
                dtype=np.float64,
            ),
            residual_local_history=np.asarray(
                states[residual_local_start:residual_local_stop].T,
                dtype=np.float64,
            ),
            residual_harmonic_history=np.asarray(
                states[residual_local_stop:residual_harmonic_stop].T,
                dtype=np.float64,
            ),
            residual_source_history=np.asarray(
                states[residual_harmonic_stop:].T,
                dtype=np.float64,
            ),
            nfev=int(nfev[idx]),
            njev=0,
            nlu=0,
            status=0,
            message=(
                "The joint IMEX k-batch executor successfully reached "
                "the end of the integration interval."
            ),
            tca_tracker=tca_trackers[idx],
            checkpoint_write_count=0,
            restart_used=False,
        )
        result.layout_auxiliary_bundle = (
            integrator.build_layout_auxiliary_history_bundle(result)
        )
        result.solver_info["layout_auxiliary_bundle_cached"] = True
        reionization_amplitude = (
            0.0
            if integrator.visibility_source.contract.events is None
            else float(integrator.visibility_source.contract.events.tau_reion)
        )
        result.runtime_execution_trace = integrator.build_runtime_execution_trace(
            result,
            reionization_amplitude=reionization_amplitude,
        )
        result.solver_info["runtime_execution_trace_cached"] = True
        result.solver_info["k_solver_batch_mode"] = "joint_imex"
        result.solver_info["k_solver_batch_size"] = int(len(integrators))
        out.append(result)
    return out


_TRANSFER_FIELDS = (
    "delta_T_m0",
    "delta_T_m_plus2",
    "delta_T_m_minus2",
    "delta_E_m0",
    "delta_E_m_plus2",
    "delta_E_m_minus2",
    "delta_B_all_zero",
)


_INTEGRATION_HISTORY_FIELDS = (
    "photon_T_tower",
    "photon_E_tower",
    "photon_B_tower",
    "neutrino_tower",
    "baryon_local_history",
    "cdm_local_history",
    "source_history",
    "residual_local_history",
    "residual_harmonic_history",
    "residual_source_history",
)


def _max_integration_history_reference_drift(
    reference: Sequence[Any],
    candidate: Sequence[Any],
) -> tuple[float, float, str]:
    if len(reference) != len(candidate):
        raise ValueError("reference and candidate integration lists have different lengths")
    max_abs = 0.0
    max_ref = 0.0
    max_field = ""
    for ref_result, cand_result in zip(reference, candidate):
        for field_name in _INTEGRATION_HISTORY_FIELDS:
            ref_value = getattr(ref_result, field_name, None)
            cand_value = getattr(cand_result, field_name, None)
            if ref_value is None and cand_value is None:
                continue
            if ref_value is None or cand_value is None:
                return float("inf"), max_ref, field_name
            ref_arr = np.asarray(ref_value, dtype=np.float64)
            cand_arr = np.asarray(cand_value, dtype=np.float64)
            if ref_arr.shape != cand_arr.shape:
                raise ValueError(
                    f"integration field {field_name} shape mismatch: "
                    f"{ref_arr.shape} != {cand_arr.shape}"
                )
            diff = np.asarray(cand_arr - ref_arr, dtype=np.float64)
            if np.any(~np.isfinite(diff)):
                return float("inf"), max_ref, field_name
            field_abs = float(np.max(np.abs(diff), initial=0.0))
            field_ref = float(np.max(np.abs(ref_arr), initial=0.0))
            if field_abs > max_abs:
                max_abs = field_abs
                max_field = field_name
            max_ref = max(max_ref, field_ref)
    return max_abs, max_ref, max_field


def _max_transfer_reference_drift(
    reference: Sequence[BianchiTransferFunctions],
    candidate: Sequence[BianchiTransferFunctions],
) -> tuple[float, float]:
    if len(reference) != len(candidate):
        raise ValueError("reference and candidate transfer lists have different lengths")
    max_abs = 0.0
    max_ref = 0.0
    for ref_tf, cand_tf in zip(reference, candidate):
        for field_name in _TRANSFER_FIELDS:
            ref_arr = np.asarray(getattr(ref_tf, field_name), dtype=np.float64)
            cand_arr = np.asarray(getattr(cand_tf, field_name), dtype=np.float64)
            if ref_arr.shape != cand_arr.shape:
                raise ValueError(
                    f"transfer field {field_name} shape mismatch: "
                    f"{ref_arr.shape} != {cand_arr.shape}"
                )
            diff = np.asarray(cand_arr - ref_arr, dtype=np.float64)
            if np.any(~np.isfinite(diff)):
                return float("inf"), max_ref
            max_abs = max(max_abs, float(np.max(np.abs(diff), initial=0.0)))
            max_ref = max(max_ref, float(np.max(np.abs(ref_arr), initial=0.0)))
    return max_abs, max_ref


def _run_joint_imex_k_batch(integrators: Sequence[Any]) -> list[Any]:
    """Advance multiple orthogonal IMEX k states with one shared step loop.

    The equations and per-k operators are unchanged: every RHS,
    collision, source, and residual call still goes through the owning
    ``Ver2TierBIntegrator``. The batching is at the time-step scheduler
    level, using the most restrictive explicit-update cap across the k
    batch. This is deliberately opt-in because shared adaptive steps can
    change floating-point trajectories relative to fully independent
    per-k solves.
    """

    if len(integrators) == 0:
        return []
    from bass.hierarchy.ver2_native_integrator import (
        _ImexStepCache,
        _ImexStepTuning,
    )

    first = integrators[0]
    if str(first.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
        raise ValueError("joint_imex batching requires IMEX_MIDPOINT_BDF")
    if abs(float(first.config.tilt_rapidity)) > 0.0:
        raise ValueError("joint_imex batching is orthogonal-only")

    eta_out = np.linspace(
        float(first.config.eta_initial_mpc),
        float(first.config.eta_final_mpc),
        int(first.config.n_output),
    )
    for integrator in integrators:
        if str(integrator.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
            raise ValueError("all joint_imex integrators must use IMEX_MIDPOINT_BDF")
        if abs(float(integrator.config.tilt_rapidity)) > 0.0:
            raise ValueError("joint_imex batching is orthogonal-only")
        if int(integrator.config.L_max) != int(first.config.L_max):
            raise ValueError("joint_imex batching requires a common L_max")
        candidate_eta = np.linspace(
            float(integrator.config.eta_initial_mpc),
            float(integrator.config.eta_final_mpc),
            int(integrator.config.n_output),
        )
        if not np.allclose(candidate_eta, eta_out, rtol=0.0, atol=1.0e-12):
            raise ValueError("joint_imex batching requires a common eta output grid")

    y_current = [
        np.asarray(integrator.initial_state(), dtype=np.float64)
        for integrator in integrators
    ]
    states_by_run = [
        np.empty((eta_out.size, state.size), dtype=np.float64)
        for state in y_current
    ]
    for idx, state in enumerate(y_current):
        states_by_run[idx][0, :] = state
    tca_trackers: list[list[bool]] = [[] for _ in integrators]
    nfev = [0 for _ in integrators]
    step_caches = [_ImexStepCache() for _ in integrators]
    explicit_buffers = [np.empty_like(state, dtype=np.float64) for state in y_current]

    total_span = max(
        float(first.config.eta_final_mpc - first.config.eta_initial_mpc),
        1.0e-12,
    )
    nominal_interval = max(float(np.max(np.diff(eta_out))), 1.0e-12)
    max_step_factor = max(float(getattr(first.config, "max_step_factor", 1000)), 1.0)
    configured_step = total_span / max_step_factor
    split_step = min(nominal_interval, configured_step)
    min_step = max(min(configured_step, total_span / 50000.0), 1.0e-8)
    explicit_update_limit = max(
        float(getattr(first.config, "imex_explicit_update_limit", 0.05)),
        1.0e-12,
    )
    shared_substeps = 0

    for output_index, (left, right) in enumerate(zip(eta_out[:-1], eta_out[1:]), start=1):
        eta_current = float(left)
        eta_target = float(right)
        while eta_current < eta_target - 1.0e-15:
            remaining = eta_target - eta_current
            state_scales = [
                max(float(np.linalg.norm(state, ord=np.inf)), 1.0)
                for state in y_current
            ]
            explicit_scales: list[float] = []
            explicit_left_values: list[np.ndarray] = []
            for idx, integrator in enumerate(integrators):
                with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                    rhs = np.asarray(
                        integrator._explicit_rhs(
                            eta_current,
                            y_current[idx],
                            out=explicit_buffers[idx],
                        ),
                        dtype=np.float64,
                    )
                nfev[idx] += 1
                if np.any(~np.isfinite(rhs)):
                    state_norm = float(np.linalg.norm(y_current[idx], ord=np.inf))
                    raise RuntimeError(
                        "joint IMEX k-batch executor encountered non-finite "
                        "explicit RHS before shared-step proposal: "
                        f"member={idx}, eta_current={eta_current:.17g}, "
                        f"state_norm={state_norm:.17g}"
                    )
                explicit_left_values.append(rhs)
                explicit_scales.append(
                    float(np.linalg.norm(rhs, ord=np.inf)) / state_scales[idx]
                )
            common_h = min(
                remaining,
                split_step,
                explicit_update_limit / max(max(explicit_scales), 1.0e-12),
            )
            common_h = (
                remaining
                if remaining <= min_step
                else max(min(common_h, remaining), min_step)
            )
            accepted = False
            last_failure_reason = "no trial attempted"
            last_trial_h = float(common_h)
            max_explicit_scale = float(max(explicit_scales, default=0.0))
            for attempt in range(20):
                target_next = float(eta_current + common_h)
                last_trial_h = float(common_h)
                outcomes: list[Any] = []
                trial_trackers = [list(tracker) for tracker in tca_trackers]
                for idx, integrator in enumerate(integrators):
                    try:
                        outcome = integrator._imex_advance_one_substep(
                            eta_current=float(eta_current),
                            eta_target=target_next,
                            y_current=np.asarray(y_current[idx], dtype=np.float64),
                            tca_tracker=trial_trackers[idx],
                            tuning=_ImexStepTuning(
                                split_step=float(common_h),
                                min_step=float(min_step),
                                explicit_update_limit=float(explicit_update_limit),
                                fixed_point_iters=6,
                            ),
                            cache=step_caches[idx],
                            explicit_0=explicit_left_values[idx],
                            initial_trial_h=float(common_h),
                        )
                    except RuntimeError as exc:
                        last_failure_reason = (
                            f"member={idx} failed native substep on attempt={attempt}: {exc}"
                        )
                        outcomes = []
                        break
                    outcomes.append(outcome)
                if len(outcomes) != len(integrators):
                    common_h *= 0.5
                    if common_h < min_step:
                        break
                    continue
                eta_next_values = [float(outcome.eta_next) for outcome in outcomes]
                if not all(
                    np.isclose(eta_next, target_next, rtol=0.0, atol=1.0e-12)
                    for eta_next in eta_next_values
                ):
                    last_failure_reason = (
                        "native substep returned inconsistent eta_next values: "
                        f"target_next={target_next:.17g}, "
                        f"eta_next_values={eta_next_values!r}"
                    )
                    common_h *= 0.5
                    if common_h < min_step:
                        break
                    continue
                for idx, outcome in enumerate(outcomes):
                    nfev[idx] += int(outcome.nfev)
                    step_caches[idx] = outcome.cache
                    y_current[idx] = np.asarray(outcome.y_next, dtype=np.float64)
                tca_trackers = trial_trackers
                eta_current = float(target_next)
                shared_substeps += 1
                accepted = True
                break
            if not accepted:
                raise RuntimeError(
                    "joint IMEX k-batch executor failed to find a finite "
                    "accepted shared substep: "
                    f"eta_current={eta_current:.17g}, "
                    f"eta_target={eta_target:.17g}, "
                    f"last_trial_h={last_trial_h:.17g}, "
                    f"min_step={min_step:.17g}, "
                    f"max_explicit_scale={max_explicit_scale:.17g}, "
                    f"last_failure={last_failure_reason}"
                )
        for idx, state in enumerate(y_current):
            states_by_run[idx][output_index, :] = np.asarray(state, dtype=np.float64)

    results = _build_results_from_joint_imex_states(
        integrators,
        eta_out,
        states_by_run,
        nfev=nfev,
        tca_trackers=tca_trackers,
    )
    for result in results:
        result.solver_info["k_solver_batch_schedule"] = "shared_step"
        result.solver_info["k_solver_batch_shared_substeps"] = int(shared_substeps)
    return results


def _run_ragged_imex_k_batch(integrators: Sequence[Any]) -> list[Any]:
    """Advance a k batch with per-member native IMEX substep sizes.

    This is the next staging point after ``"independent"``: it uses the
    extracted native one-substep primitive for every k, but does not force
    a global common step. That preserves the per-k adaptive schedule while
    creating a single interleaved batch loop that later vectorized
    primitive kernels can target.
    """

    if len(integrators) == 0:
        return []
    from bass.hierarchy.ver2_native_integrator import (
        _ImexStepCache,
        _ImexStepTuning,
    )

    first = integrators[0]
    if str(first.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
        raise ValueError("ragged IMEX batching requires IMEX_MIDPOINT_BDF")
    if abs(float(first.config.tilt_rapidity)) > 0.0:
        raise ValueError("ragged IMEX batching is orthogonal-only")

    eta_out = np.linspace(
        float(first.config.eta_initial_mpc),
        float(first.config.eta_final_mpc),
        int(first.config.n_output),
    )
    for integrator in integrators:
        if str(integrator.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
            raise ValueError("all ragged IMEX integrators must use IMEX_MIDPOINT_BDF")
        if abs(float(integrator.config.tilt_rapidity)) > 0.0:
            raise ValueError("ragged IMEX batching is orthogonal-only")
        if int(integrator.config.L_max) != int(first.config.L_max):
            raise ValueError("ragged IMEX batching requires a common L_max")
        candidate_eta = np.linspace(
            float(integrator.config.eta_initial_mpc),
            float(integrator.config.eta_final_mpc),
            int(integrator.config.n_output),
        )
        if not np.allclose(candidate_eta, eta_out, rtol=0.0, atol=1.0e-12):
            raise ValueError("ragged IMEX batching requires a common eta output grid")

    y_current = [
        np.asarray(integrator.initial_state(), dtype=np.float64)
        for integrator in integrators
    ]
    states_by_run = [
        np.empty((eta_out.size, state.size), dtype=np.float64)
        for state in y_current
    ]
    for idx, state in enumerate(y_current):
        states_by_run[idx][0, :] = state
    tca_trackers: list[list[bool]] = [[] for _ in integrators]
    nfev = [0 for _ in integrators]
    step_caches = [_ImexStepCache() for _ in integrators]
    explicit_buffers = [np.empty_like(state, dtype=np.float64) for state in y_current]

    total_span = max(
        float(first.config.eta_final_mpc - first.config.eta_initial_mpc),
        1.0e-12,
    )
    nominal_interval = max(float(np.max(np.diff(eta_out))), 1.0e-12)
    max_step_factor = max(float(getattr(first.config, "max_step_factor", 1000)), 1.0)
    configured_step = total_span / max_step_factor
    tuning = _ImexStepTuning(
        split_step=float(min(nominal_interval, configured_step)),
        min_step=float(max(min(configured_step, total_span / 50000.0), 1.0e-8)),
        explicit_update_limit=float(
            max(float(getattr(first.config, "imex_explicit_update_limit", 0.05)), 1.0e-12)
        ),
        fixed_point_iters=6,
    )

    ragged_substeps = 0
    for output_index, (left, right) in enumerate(zip(eta_out[:-1], eta_out[1:]), start=1):
        eta_current_by_run = [float(left) for _ in integrators]
        eta_target = float(right)
        while True:
            active = [
                idx
                for idx, eta_current in enumerate(eta_current_by_run)
                if eta_current < eta_target - 1.0e-15
            ]
            if not active:
                break
            progressed = False
            for idx in active:
                eta_current = float(eta_current_by_run[idx])
                state = np.asarray(y_current[idx], dtype=np.float64)
                with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                    explicit_left = np.asarray(
                        integrators[idx]._explicit_rhs(
                            eta_current,
                            state,
                            out=explicit_buffers[idx],
                        ),
                        dtype=np.float64,
                    )
                nfev[idx] += 1
                if np.any(~np.isfinite(explicit_left)):
                    state_norm = float(np.linalg.norm(state, ord=np.inf))
                    raise RuntimeError(
                        "ragged IMEX k-batch executor encountered non-finite "
                        "explicit RHS before native substep: "
                        f"member={idx}, eta_current={eta_current:.17g}, "
                        f"state_norm={state_norm:.17g}"
                    )
                state_scale = max(float(np.linalg.norm(state, ord=np.inf)), 1.0)
                explicit_scale = (
                    float(np.linalg.norm(explicit_left, ord=np.inf)) / state_scale
                )
                remaining = float(eta_target) - eta_current
                proposed_h = min(
                    remaining,
                    float(tuning.split_step),
                    float(tuning.explicit_update_limit) / max(explicit_scale, 1.0e-12),
                )
                proposed_h = (
                    remaining
                    if remaining <= float(tuning.min_step)
                    else max(min(proposed_h, remaining), float(tuning.min_step))
                )
                try:
                    outcome = integrators[idx]._imex_advance_one_substep(
                        eta_current=eta_current,
                        eta_target=eta_target,
                        y_current=state,
                        tca_tracker=tca_trackers[idx],
                        tuning=tuning,
                        cache=step_caches[idx],
                        explicit_0=explicit_left,
                        initial_trial_h=float(proposed_h),
                    )
                except RuntimeError as exc:
                    raise RuntimeError(
                        "ragged IMEX k-batch executor failed native substep: "
                        f"member={idx}, eta_current={eta_current:.17g}, "
                        f"eta_target={eta_target:.17g}, error={exc}"
                    ) from exc
                eta_next = float(outcome.eta_next)
                if eta_next <= eta_current + 1.0e-15:
                    raise RuntimeError(
                        "ragged IMEX k-batch executor received a non-advancing "
                        "native substep: "
                        f"member={idx}, eta_current={eta_current:.17g}, "
                        f"eta_next={eta_next:.17g}"
                    )
                if eta_next > eta_target + 1.0e-10:
                    raise RuntimeError(
                        "ragged IMEX k-batch executor received an overshooting "
                        "native substep: "
                        f"member={idx}, eta_next={eta_next:.17g}, "
                        f"eta_target={eta_target:.17g}"
                    )
                nfev[idx] += int(outcome.nfev)
                step_caches[idx] = outcome.cache
                y_current[idx] = np.asarray(outcome.y_next, dtype=np.float64)
                eta_current_by_run[idx] = eta_next
                ragged_substeps += 1
                progressed = True
            if not progressed:
                raise RuntimeError(
                    "ragged IMEX k-batch executor failed to advance any member "
                    f"before η={eta_target:.17g}"
                )
        for idx, state in enumerate(y_current):
            states_by_run[idx][output_index, :] = np.asarray(state, dtype=np.float64)

    results = _build_results_from_joint_imex_states(
        integrators,
        eta_out,
        states_by_run,
        nfev=nfev,
        tca_trackers=tca_trackers,
    )
    for result in results:
        result.solver_info["k_solver_batch_schedule"] = "ragged"
        result.solver_info["k_solver_batch_ragged_substeps"] = int(ragged_substeps)
    return results


def _run_grouped_imex_k_batch(integrators: Sequence[Any]) -> list[Any]:
    """Advance a ragged k batch while bucketing matching proposed targets.

    This keeps the native per-k IMEX proposal rule. It does not force a
    common step; it only identifies members whose native first trial would
    land at the same target and advances those members as one bucket. The
    current implementation still calls the native primitive per member,
    but the bucket metadata is the compatibility layer for a future
    vectorized primitive.
    """

    if len(integrators) == 0:
        return []
    from bass.hierarchy.ver2_native_integrator import (
        _ImexStepCache,
        _ImexStepTuning,
    )

    first = integrators[0]
    if str(first.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
        raise ValueError("grouped IMEX batching requires IMEX_MIDPOINT_BDF")
    if abs(float(first.config.tilt_rapidity)) > 0.0:
        raise ValueError("grouped IMEX batching is orthogonal-only")

    eta_out = np.linspace(
        float(first.config.eta_initial_mpc),
        float(first.config.eta_final_mpc),
        int(first.config.n_output),
    )
    for integrator in integrators:
        if str(integrator.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
            raise ValueError("all grouped IMEX integrators must use IMEX_MIDPOINT_BDF")
        if abs(float(integrator.config.tilt_rapidity)) > 0.0:
            raise ValueError("grouped IMEX batching is orthogonal-only")
        if int(integrator.config.L_max) != int(first.config.L_max):
            raise ValueError("grouped IMEX batching requires a common L_max")
        candidate_eta = np.linspace(
            float(integrator.config.eta_initial_mpc),
            float(integrator.config.eta_final_mpc),
            int(integrator.config.n_output),
        )
        if not np.allclose(candidate_eta, eta_out, rtol=0.0, atol=1.0e-12):
            raise ValueError("grouped IMEX batching requires a common eta output grid")

    y_current = [
        np.asarray(integrator.initial_state(), dtype=np.float64)
        for integrator in integrators
    ]
    states_by_run = [
        np.empty((eta_out.size, state.size), dtype=np.float64)
        for state in y_current
    ]
    for idx, state in enumerate(y_current):
        states_by_run[idx][0, :] = state
    tca_trackers: list[list[bool]] = [[] for _ in integrators]
    nfev = [0 for _ in integrators]
    step_caches = [_ImexStepCache() for _ in integrators]
    explicit_buffers = [np.empty_like(state, dtype=np.float64) for state in y_current]

    total_span = max(
        float(first.config.eta_final_mpc - first.config.eta_initial_mpc),
        1.0e-12,
    )
    nominal_interval = max(float(np.max(np.diff(eta_out))), 1.0e-12)
    max_step_factor = max(float(getattr(first.config, "max_step_factor", 1000)), 1.0)
    configured_step = total_span / max_step_factor
    split_step = float(min(nominal_interval, configured_step))
    min_step = float(max(min(configured_step, total_span / 50000.0), 1.0e-8))
    explicit_update_limit = float(
        max(float(getattr(first.config, "imex_explicit_update_limit", 0.05)), 1.0e-12)
    )
    tuning = _ImexStepTuning(
        split_step=split_step,
        min_step=min_step,
        explicit_update_limit=explicit_update_limit,
        fixed_point_iters=6,
    )

    grouped_substeps = 0
    grouped_bucket_count = 0
    grouped_max_bucket_size = 0
    bucket_atol = 1.0e-12
    for output_index, (left, right) in enumerate(zip(eta_out[:-1], eta_out[1:]), start=1):
        eta_current_by_run = [float(left) for _ in integrators]
        eta_target = float(right)
        while True:
            active = [
                idx
                for idx, eta_current in enumerate(eta_current_by_run)
                if eta_current < eta_target - 1.0e-15
            ]
            if not active:
                break
            proposals: dict[int, list[tuple[int, float, float, np.ndarray]]] = {}
            for idx in active:
                eta_current = float(eta_current_by_run[idx])
                state = np.asarray(y_current[idx], dtype=np.float64)
                with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                    explicit_left = np.asarray(
                        integrators[idx]._explicit_rhs(
                            eta_current,
                            state,
                            out=explicit_buffers[idx],
                        ),
                        dtype=np.float64,
                    )
                nfev[idx] += 1
                if np.any(~np.isfinite(explicit_left)):
                    state_norm = float(np.linalg.norm(state, ord=np.inf))
                    raise RuntimeError(
                        "grouped IMEX k-batch executor encountered non-finite "
                        "explicit RHS before native substep: "
                        f"member={idx}, eta_current={eta_current:.17g}, "
                        f"state_norm={state_norm:.17g}"
                    )
                state_scale = max(float(np.linalg.norm(state, ord=np.inf)), 1.0)
                explicit_scale = (
                    float(np.linalg.norm(explicit_left, ord=np.inf)) / state_scale
                )
                remaining = float(eta_target) - eta_current
                proposed_h = min(
                    remaining,
                    split_step,
                    explicit_update_limit / max(explicit_scale, 1.0e-12),
                )
                proposed_h = (
                    remaining
                    if remaining <= min_step
                    else max(min(proposed_h, remaining), min_step)
                )
                proposed_target = float(eta_current + proposed_h)
                bucket_key = int(np.rint(proposed_target / bucket_atol))
                proposals.setdefault(bucket_key, []).append(
                    (idx, float(proposed_h), proposed_target, explicit_left)
                )
            if not proposals:
                raise RuntimeError(
                    "grouped IMEX k-batch executor failed to propose any member "
                    f"before η={eta_target:.17g}"
                )
            for bucket in proposals.values():
                grouped_bucket_count += 1
                grouped_max_bucket_size = max(grouped_max_bucket_size, len(bucket))
                for idx, proposed_h, proposed_target, explicit_left in bucket:
                    eta_current = float(eta_current_by_run[idx])
                    state = np.asarray(y_current[idx], dtype=np.float64)
                    try:
                        outcome = integrators[idx]._imex_advance_one_substep(
                            eta_current=eta_current,
                            eta_target=float(proposed_target),
                            y_current=state,
                            tca_tracker=tca_trackers[idx],
                            tuning=tuning,
                            cache=step_caches[idx],
                            explicit_0=explicit_left,
                            initial_trial_h=float(proposed_h),
                        )
                    except RuntimeError as exc:
                        raise RuntimeError(
                            "grouped IMEX k-batch executor failed native substep: "
                            f"member={idx}, eta_current={eta_current:.17g}, "
                            f"eta_target={proposed_target:.17g}, error={exc}"
                        ) from exc
                    eta_next = float(outcome.eta_next)
                    if eta_next <= eta_current + 1.0e-15:
                        raise RuntimeError(
                            "grouped IMEX k-batch executor received a non-advancing "
                            "native substep: "
                            f"member={idx}, eta_current={eta_current:.17g}, "
                            f"eta_next={eta_next:.17g}"
                        )
                    if eta_next > eta_target + 1.0e-10:
                        raise RuntimeError(
                            "grouped IMEX k-batch executor received an overshooting "
                            "native substep: "
                            f"member={idx}, eta_next={eta_next:.17g}, "
                            f"eta_target={eta_target:.17g}"
                        )
                    nfev[idx] += int(outcome.nfev)
                    step_caches[idx] = outcome.cache
                    y_current[idx] = np.asarray(outcome.y_next, dtype=np.float64)
                    eta_current_by_run[idx] = eta_next
                    grouped_substeps += 1
        for idx, state in enumerate(y_current):
            states_by_run[idx][output_index, :] = np.asarray(state, dtype=np.float64)

    results = _build_results_from_joint_imex_states(
        integrators,
        eta_out,
        states_by_run,
        nfev=nfev,
        tca_trackers=tca_trackers,
    )
    for result in results:
        result.solver_info["k_solver_batch_schedule"] = "grouped"
        result.solver_info["k_solver_batch_grouped_substeps"] = int(grouped_substeps)
        result.solver_info["k_solver_batch_grouped_bucket_count"] = int(
            grouped_bucket_count
        )
        result.solver_info["k_solver_batch_grouped_max_bucket_size"] = int(
            grouped_max_bucket_size
        )
    return results


def _run_independent_imex_k_batch(integrators: Sequence[Any]) -> list[Any]:
    """Run a batch wrapper while preserving each k's native IMEX schedule.

    This is the parity-first staging path for ``joint_imex`` refactors:
    every k advances through ``Ver2TierBIntegrator._solve_segment_imex``
    independently, so state histories should match ``integrator.run``.
    Later shared-step/vectorized schedulers can be compared against this
    path before any speed claim is promoted.
    """

    if len(integrators) == 0:
        return []
    first = integrators[0]
    eta_out = np.linspace(
        float(first.config.eta_initial_mpc),
        float(first.config.eta_final_mpc),
        int(first.config.n_output),
    )
    states_by_run: list[np.ndarray] = []
    nfev: list[int] = []
    tca_trackers: list[list[bool]] = []
    for integrator in integrators:
        if str(integrator.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
            raise ValueError("independent IMEX batching requires IMEX_MIDPOINT_BDF")
        if abs(float(integrator.config.tilt_rapidity)) > 0.0:
            raise ValueError("independent IMEX batching is orthogonal-only")
        candidate_eta = np.linspace(
            float(integrator.config.eta_initial_mpc),
            float(integrator.config.eta_final_mpc),
            int(integrator.config.n_output),
        )
        if not np.allclose(candidate_eta, eta_out, rtol=0.0, atol=1.0e-12):
            raise ValueError("independent IMEX batching requires a common eta grid")
        tracker: list[bool] = []
        sol = integrator._solve_segment_imex(
            eta_start=float(candidate_eta[0]),
            eta_stop=float(candidate_eta[-1]),
            y0=np.asarray(integrator.initial_state(), dtype=np.float64),
            eta_eval=candidate_eta,
            tca_tracker=tracker,
        )
        states_by_run.append(np.asarray(sol.y.T, dtype=np.float64))
        nfev.append(int(sol.nfev))
        tca_trackers.append(tracker)
    results = _build_results_from_joint_imex_states(
        integrators,
        eta_out,
        states_by_run,
        nfev=nfev,
        tca_trackers=tca_trackers,
    )
    for result in results:
        result.solver_info["k_solver_batch_schedule"] = "independent"
        result.solver_info["k_solver_batch_size"] = int(len(integrators))
    return results


def compute_transfer_function_at_k(
    species: "SpeciesBackgroundRegistry",
    k_mpc: float,
    *,
    config: FLRWPipelineConfig | None = None,
    bianchi_type: str = "I",
) -> BianchiTransferFunctions:
    """Run Tier-B + extractor + LoS at a single k, return Δ_ℓ transfer.

    This is the unit of parallelizable work in the k-sweep. It chains
    Blockers 1+2+3 + Round-5 extractor + LoS projector in a single call.
    For Bianchi I, the m = ±2 channels vanish identically; the returned
    BianchiTransferFunctions has zero m = ±2 arrays.
    """

    if not (float(k_mpc) > 0.0):
        raise ValueError(f"k_mpc must be positive; got {k_mpc}")
    cfg = config or FLRWPipelineConfig()
    z_injection = _resolve_z_injection_for_k(species, cfg, float(k_mpc))

    integrator_config = build_cosmological_integrator_config(
        species,
        z_injection=z_injection,
        pre_recombination_margin_mpc=float(cfg.pre_recombination_margin_mpc),
        L_max=cfg.L_max_tower,
        n_output=cfg.n_output,
        rtol=cfg.rtol,
        atol=cfg.atol,
        bianchi_cosmo=BianchiCosmology(structure=get_type(bianchi_type), beta=0.0),
        gamma_T_over_H_threshold=cfg.gamma_T_over_H_threshold,
        adiabatic_mode_seed=cfg.adiabatic_mode_seed,
        # Per-k resolution (Round-7): callable override takes precedence
        # over the scalar; evaluated HERE in the parent process, so fork
        # workers only see a resolved float.
        primordial_b_k_sq=_resolve_primordial_b_k_sq(cfg, k_mpc),
        # Round-17 P3.5 perf knob: forward max_step_factor to the integrator.
        max_step_factor=int(getattr(cfg, "max_step_factor", 1000)),
        imex_explicit_update_limit=float(
            getattr(cfg, "imex_explicit_update_limit", 0.05)
        ),
        co_evolve_scalar_metric=bool(getattr(cfg, "co_evolve_scalar_metric", False)),
        co_evolve_scalar_streaming=bool(
            getattr(cfg, "co_evolve_scalar_streaming", False)
        ),
    )

    # execute_tier_b_solver requires k_grid_mpc with ≥ 2 entries for the
    # off-diagonal covariance diagnostic, but only the MINIMUM positive
    # entry drives the tower ODE (see _representative_seed_k in
    # ver2_execution.py line 1400). Use the caller's k as the minimum and
    # a dummy second value for the diagnostic surface.
    k_grid_pair = np.array([float(k_mpc), 2.0 * float(k_mpc)], dtype=np.float64)

    run = execute_tier_b_solver(
        manifest=_pipeline_manifest(f"k{k_mpc:.6e}"),
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=integrator_config,
        runtime_controls=_pipeline_runtime_controls(cfg),
        feature_flags=_pipeline_feature_flags(),
        release=_pipeline_release(f"k{k_mpc:.6e}", cfg.random_seed),
        k_grid_mpc=k_grid_pair,
    )

    seed_amp = (
        float(run.trace.seed_projection.projected_seed.amplitude)
        if cfg.unit_amplitude_normalization
        else None
    )
    return _los_and_wrap(
        run.integration_result,
        species,
        float(k_mpc),
        cfg,
        seed_amp_for_norm=seed_amp,
    )


# ------------------------------------------------------------------------
# Chunked k-scan: reuse background_monitor + visibility across k's in a
# chunk to amortize the 0.8 s / k k-independent setup cost.
# ------------------------------------------------------------------------


def _run_chunk_shared_bg(
    species: "SpeciesBackgroundRegistry",
    k_values: Sequence[float],
    *,
    cfg: FLRWPipelineConfig,
    bianchi_type: str,
) -> list[BianchiTransferFunctions]:
    specs = [
        (float(k_mpc), _resolve_primordial_b_k_sq(cfg, float(k_mpc)))
        for k_mpc in k_values
    ]
    return _run_chunk_shared_bg_for_specs(
        species,
        specs,
        cfg=cfg,
        bianchi_type=bianchi_type,
    )


def _run_chunk_shared_bg_for_specs(
    species: "SpeciesBackgroundRegistry",
    run_specs: Sequence[tuple[float, float]],
    *,
    cfg: FLRWPipelineConfig,
    bianchi_type: str,
) -> list[BianchiTransferFunctions]:
    """Low-level k-loop that shares background_monitor + visibility_source
    + backend + canonical_decision + runtime_decision across all k's in
    ``run_specs``. Each spec is ``(k_mpc, primordial_b_k_sq)``. Only the
    integrator (via ``seed_k_comoving`` and the per-run seed amplitude)
    is rebuilt per run.

    Uses the ver2_execution private API directly; profile (see CHANGELOG)
    shows this saves ~0.8 s per k-run after the first in each chunk.
    """

    from dataclasses import replace as _dc_replace

    from bass.hierarchy.aux_state import build_integrator_canonical_decision
    from bass.hierarchy.ver2_native_integrator import Ver2TierBIntegrator
    from bass.los.family_backend_protocol import build_backend
    from bass.runtime.ver2_execution import (
        _build_background_monitor,
        _build_runtime_decision,
        _build_tier_b_executable_run,
        _build_tier_b_runtime_request,
        _build_visibility_source,
        _default_validation_matrix,
        _native_runtime_config,
        _TierBPreparedRuntimeContext,
        plan_solver_execution,
    )

    if len(run_specs) == 0:
        return []
    specs = [(float(k), float(b_k_sq)) for k, b_k_sq in run_specs]
    if cfg.superhorizon_x_max_at_start is not None and len(specs) > 1:
        raise ValueError(
            "shared-background chunking is incompatible with per-k "
            "superhorizon_x_max_at_start because each k can require a "
            "different z_injection"
        )
    z_injection = _resolve_z_injection_for_k(species, cfg, float(specs[0][0]))

    rc = _pipeline_runtime_controls(cfg)
    ff = _pipeline_feature_flags()

    # k-independent shared build — done ONCE per chunk, reused across k.
    template_integrator_config = build_cosmological_integrator_config(
        species,
        z_injection=z_injection,
        pre_recombination_margin_mpc=float(cfg.pre_recombination_margin_mpc),
        L_max=cfg.L_max_tower,
        n_output=cfg.n_output,
        rtol=cfg.rtol,
        atol=cfg.atol,
        bianchi_cosmo=BianchiCosmology(structure=get_type(bianchi_type), beta=0.0),
        gamma_T_over_H_threshold=cfg.gamma_T_over_H_threshold,
        adiabatic_mode_seed=cfg.adiabatic_mode_seed,
        primordial_b_k_sq=float(specs[0][1]),
        # Round-17 P3.5 perf knob: forward max_step_factor to the integrator.
        max_step_factor=int(getattr(cfg, "max_step_factor", 1000)),
        imex_explicit_update_limit=float(
            getattr(cfg, "imex_explicit_update_limit", 0.05)
        ),
        co_evolve_scalar_metric=bool(getattr(cfg, "co_evolve_scalar_metric", False)),
        co_evolve_scalar_streaming=bool(
            getattr(cfg, "co_evolve_scalar_streaming", False)
        ),
    )
    template_request = _build_tier_b_runtime_request(
        manifest=_pipeline_manifest("chunked"),
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=template_integrator_config,
        runtime_controls=rc,
        feature_flags=ff,
        release=_pipeline_release("chunked", cfg.random_seed),
        k_grid_mpc=np.array([float(specs[0][0]), 2.0 * float(specs[0][0])]),
    )
    runtime_config, family_realization = _native_runtime_config(
        template_request.bianchi_type,
        template_request.integrator_config,
        template_request.runtime_controls,
    )
    background_monitor = _build_background_monitor(
        bianchi_type=template_request.bianchi_type,
        config=runtime_config,
        species=species,
        tilt_background_owner=rc.tilt_background_owner,
    )
    visibility_source = _build_visibility_source(
        species=species,
        config=runtime_config,
        background_monitor=background_monitor,
    )
    canonical_decision = build_integrator_canonical_decision(
        beta=float(runtime_config.bianchi_cosmo.beta),
        sigma_squared=max(
            0.5 * float(np.sum(background_monitor.sigma_tensor[0] ** 2)),
            1.0e-12,
        ),
    )
    backend_instance = build_backend(
        template_request.bianchi_type,
        truncation={"ell_max": int(rc.multipole_cutoff)},
        chart_options={},
    )
    reionization_amp = (
        0.0
        if visibility_source.contract.events is None
        else float(visibility_source.contract.events.tau_reion)
    )
    runtime_decision = _build_runtime_decision(
        feature_flags=ff,
        canonical_decision=canonical_decision,
    )
    execution_plan = plan_solver_execution(
        runtime_controls=rc,
        feature_flags=ff,
        runtime_decision=runtime_decision,
        validation_matrix=_default_validation_matrix(
            bianchi_type=template_request.bianchi_type,
            integrator_config=runtime_config,
            suite="tier_b_smoke",
        ),
    )
    shared_visibility_callables = build_visibility_and_kappa_callables(species)

    def _build_context_for_spec(
        k_mpc: float,
        per_k_b_k_sq: float,
        *,
        backend_for_run: Any,
        owner: str,
    ):
        k_grid_pair = np.array([float(k_mpc), 2.0 * float(k_mpc)], dtype=np.float64)
        seed_k_comoving = float(k_mpc)
        per_k_runtime_config = _dc_replace(
            runtime_config, primordial_b_k_sq=per_k_b_k_sq
        )
        integrator = Ver2TierBIntegrator(
            per_k_runtime_config,
            species,
            backend=backend_for_run,
            background_monitor=background_monitor,
            visibility_source=visibility_source,
            canonical_decision=canonical_decision,
            seed_k_comoving=seed_k_comoving,
        )
        prepared = _TierBPreparedRuntimeContext(
            runtime_config=per_k_runtime_config,
            family_realization=family_realization,
            restart_state=None,
            background_monitor=background_monitor,
            visibility_source=visibility_source,
            k_grid_mpc=k_grid_pair,
            seed_k_comoving=seed_k_comoving,
            backend=backend_for_run,
            reionization_amplitude=reionization_amp,
            integrator=integrator,
            runtime_decision=runtime_decision,
            execution_plan=execution_plan,
            checkpoint_callback=None,
            checkpoint_paths=[],
            metadata={"owner": owner},
        )
        # Per-k request carries the k_grid_pair + a fresh manifest/release
        # so downstream artefact identifiers stay distinct per k.
        per_k_request = _dc_replace(
            template_request,
            manifest=_pipeline_manifest(f"chunked-k{k_mpc:.6e}"),
            release=_pipeline_release(f"chunked-k{k_mpc:.6e}", cfg.random_seed),
            integrator_config=per_k_runtime_config,
            k_grid_mpc=k_grid_pair,
        )
        return float(k_mpc), integrator, prepared, per_k_request

    def _wrap_context_result(context, result) -> BianchiTransferFunctions:
        k_mpc, integrator, prepared, per_k_request = context
        del integrator
        run = _build_tier_b_executable_run(
            request=per_k_request,
            prepared=prepared,
            result=result,
        )
        seed_amp = (
            float(run.trace.seed_projection.projected_seed.amplitude)
            if cfg.unit_amplitude_normalization
            else None
        )
        return _los_and_wrap(
            run.integration_result,
            species,
            float(k_mpc),
            cfg,
            seed_amp_for_norm=seed_amp,
            visibility_callables=shared_visibility_callables,
        )

    def _run_context(context) -> BianchiTransferFunctions:
        _k_mpc, integrator, _prepared, _per_k_request = context
        result = _run_integration_context(context)
        return _wrap_context_result(context, result)

    def _run_integration_context(context):
        _k_mpc, integrator, _prepared, _per_k_request = context
        return integrator.run(
            checkpoint_every_n_steps=None,
            checkpoint_callback=None,
            restart_state=None,
        )

    batch_mode = str(getattr(cfg, "k_solver_batch_mode", "shared_background"))

    # ``joint_imex`` is staged: default independent scheduling preserves
    # per-k native IMEX trajectories; ``joint_imex_schedule="ragged"``
    # interleaves native substeps without a common global step;
    # ``"grouped"`` only buckets matching native proposed targets; and
    # ``"shared_step"`` remains guarded experimental.
    if batch_mode == "joint_imex" and len(specs) >= 2:
        if str(runtime_config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
            raise ValueError("joint_imex batching requires IMEX_MIDPOINT_BDF")
        if abs(float(runtime_config.tilt_rapidity)) > 0.0:
            raise ValueError("joint_imex batching is orthogonal-only")
        contexts = [
            _build_context_for_spec(
                k_mpc,
                per_k_b_k_sq,
                backend_for_run=backend_instance,
                owner="flrw_pipeline._run_chunk_shared_bg.joint_imex",
            )
            for k_mpc, per_k_b_k_sq in specs
        ]
        joint_schedule = str(getattr(cfg, "joint_imex_schedule", "independent"))
        if joint_schedule == "independent":
            integration_results = _run_independent_imex_k_batch(
                [context[1] for context in contexts]
            )
        elif joint_schedule == "ragged":
            integration_results = _run_ragged_imex_k_batch(
                [context[1] for context in contexts]
            )
        elif joint_schedule == "grouped":
            integration_results = _run_grouped_imex_k_batch(
                [context[1] for context in contexts]
            )
        else:
            integration_results = _run_joint_imex_k_batch(
                [context[1] for context in contexts]
            )
        if bool(getattr(cfg, "joint_imex_reference_check", True)):
            reference_backend = build_backend(
                template_request.bianchi_type,
                truncation={"ell_max": int(rc.multipole_cutoff)},
                chart_options={},
            )
            reference_contexts = [
                _build_context_for_spec(
                    k_mpc,
                    per_k_b_k_sq,
                    backend_for_run=reference_backend,
                    owner="flrw_pipeline._run_chunk_shared_bg.joint_imex_reference",
                )
                for k_mpc, per_k_b_k_sq in specs
            ]
            reference_integration_results = [
                _run_integration_context(context) for context in reference_contexts
            ]
            state_max_abs, state_max_ref, state_field = (
                _max_integration_history_reference_drift(
                    reference_integration_results,
                    integration_results,
                )
            )
            state_tolerance = float(getattr(cfg, "joint_imex_reference_atol", 1.0e-9)) + (
                float(getattr(cfg, "joint_imex_reference_rtol", 1.0e-9))
                * state_max_ref
            )
            if not (state_max_abs <= state_tolerance):
                raise RuntimeError(
                    "joint_imex batch failed same-physics state-history guard: "
                    f"field={state_field}, max_abs_drift={state_max_abs:.6e} "
                    f"exceeds tolerance={state_tolerance:.6e} "
                    f"(max_reference={state_max_ref:.6e})"
                )
            max_abs, max_ref = _max_transfer_reference_drift(
                [
                    _wrap_context_result(context, result)
                    for context, result in zip(
                        reference_contexts,
                        reference_integration_results,
                    )
                ],
                [
                    _wrap_context_result(context, result)
                    for context, result in zip(contexts, integration_results)
                ],
            )
            transfer_tolerance = float(getattr(cfg, "joint_imex_reference_atol", 1.0e-9)) + (
                float(getattr(cfg, "joint_imex_reference_rtol", 1.0e-9))
                * max_ref
            )
            if not (max_abs <= transfer_tolerance):
                raise RuntimeError(
                    "joint_imex batch failed same-physics transfer guard: "
                    f"max_abs_drift={max_abs:.6e} exceeds tolerance={transfer_tolerance:.6e} "
                    f"(max_reference={max_ref:.6e})"
                )
        batched_transfers = [
            _wrap_context_result(context, result)
            for context, result in zip(contexts, integration_results)
        ]
        return batched_transfers

    if batch_mode == "threaded" and len(specs) >= 2:
        thread_count = min(int(getattr(cfg, "intra_chunk_threads", 1)), len(specs))
        if thread_count >= 2:
            def _thread_task(spec: tuple[float, float]) -> BianchiTransferFunctions:
                k_mpc, per_k_b_k_sq = spec
                # Use a fresh backend per thread. Background/visibility are
                # read-only after construction; the backend is the only
                # object likely to carry mutable layout caches.
                thread_backend = build_backend(
                    template_request.bianchi_type,
                    truncation={"ell_max": int(rc.multipole_cutoff)},
                    chart_options={},
                )
                context = _build_context_for_spec(
                    k_mpc,
                    per_k_b_k_sq,
                    backend_for_run=thread_backend,
                    owner="flrw_pipeline._run_chunk_shared_bg.threaded",
                )
                return _run_context(context)

            with _cf.ThreadPoolExecutor(max_workers=thread_count) as exe:
                return list(exe.map(_thread_task, specs))

    # Per-k: only rebuild the integrator (with this k's seed_k_comoving
    # and its per-k resolved primordial_b_k_sq) and re-run the IMEX
    # integration. Background_monitor + visibility_source + backend +
    # canonical_decision + runtime_decision + execution_plan are reused.
    out: list[BianchiTransferFunctions] = []
    for k_mpc, per_k_b_k_sq in specs:
        context = _build_context_for_spec(
            k_mpc,
            per_k_b_k_sq,
            backend_for_run=backend_instance,
            owner="flrw_pipeline._run_chunk_shared_bg",
        )
        out.append(_run_context(context))
    return out


# ------------------------------------------------------------------------
# Parallel k-sweep support
# ------------------------------------------------------------------------


def _worker_init(_noop: bool = True) -> None:  # pragma: no cover — worker-side
    """Fork-safe worker initializer (module-level so it pickles).

    Under the default Linux ``fork`` start method, each worker inherits
    the parent's memory, so the species registry is already loaded and
    needs no re-initialization. This hook is a no-op on fork; the only
    reason it exists is so tests running on non-fork systems have a
    single place to install spawn-side setup.
    """
    return None


# Module-level singleton used by the worker closure so that the species
# registry created in the parent process is inherited via fork without
# re-pickling it into the child. Set by ``compute_transfer_function_grid``
# before the pool spawns.
_WORKER_SPECIES: "SpeciesBackgroundRegistry | None" = None
_WORKER_CONFIG: FLRWPipelineConfig | None = None
_WORKER_BIANCHI_TYPE: str = "I"


def _worker_task(k_mpc: float) -> BianchiTransferFunctions:  # pragma: no cover
    """Worker-side single-k entry point (per-k full Tier-B setup)."""
    assert _WORKER_SPECIES is not None, "worker globals not initialized"
    return compute_transfer_function_at_k(
        _WORKER_SPECIES,
        float(k_mpc),
        config=_WORKER_CONFIG,
        bianchi_type=_WORKER_BIANCHI_TYPE,
    )


def _worker_task_bias_pair(
    k_and_bk_sq: tuple[float, float],
) -> BianchiTransferFunctions:  # pragma: no cover
    """Worker that runs ONE solver at a specified ``b_k_sq``, used by
    the bias-subtraction pipeline to run the bias + target runs in
    parallel across the pool."""
    assert _WORKER_SPECIES is not None, "worker globals not initialized"
    assert _WORKER_CONFIG is not None, "worker config not initialized"
    k_mpc, b_k_sq = k_and_bk_sq
    from dataclasses import replace

    cfg_override = replace(_WORKER_CONFIG, primordial_b_k_sq=float(b_k_sq))
    return compute_transfer_function_at_k(
        _WORKER_SPECIES,
        float(k_mpc),
        config=cfg_override,
        bianchi_type=_WORKER_BIANCHI_TYPE,
    )


def compute_linear_probe_transfer_function(
    species: "SpeciesBackgroundRegistry",
    k_mpc: float,
    *,
    config: FLRWPipelineConfig | None = None,
    bianchi_type: str = "I",
    probe_b_k_sq: float = 1.0,
) -> BianchiTransferFunctions:
    """V5 step-4b-(a) Round-8 linear-probe transfer extraction.

    Returns the *linear coefficient* α(k) = (Δ(b_k_sq=probe) − Δ(b_k_sq=0)) /
    probe_b_k_sq — the seed-independent slope of the solver response
    in the linear regime.

    Background (Round-8 findings):
      - The solver response to primordial_b_k_sq is LINEAR for
        ``b_k_sq ∈ [~1e-3, ~10]`` (confirmed by diagnostic sweep).
      - Below that range the output is dominated by the
        seed-independent visibility-source bias (~O(1e-3)); seed
        signal disappears into float precision noise.
      - Above ~10, the seed formula's ``eta_cov = 2·B_K·(1 - x²/12 ·
        (B_K - 10/denom))`` picks up a quadratic B_K² term that
        saturates the response.
      - Physical Planck ζ (~4.6e-5) is BELOW the bias noise floor, so
        directly running at physical amplitude gives unreliable
        output. Instead: probe in the linear regime, extract α(k),
        then analytically scale to Planck ζ² via C_ℓ assembly.

    This function dispatches TWO solver runs (``b=0`` bias +
    ``b=probe`` target) in parallel (2 workers) and returns
    α(k) = (target − bias) / probe_b_k_sq for every Δ field.

    Notes
    -----
    The returned "α" transfer function has units **"per unit linear
    curvature amplitude"** (i.e., per unit ``C ≈ ζ``). It pairs
    directly with ``P_R(k) = ⟨ζ²⟩`` in the canonical C_ℓ assembly
    ``C_ℓ = 4π ∫ d ln k · P_R(k) · |α|²`` — no additional rescaling.

    The historical "B_K_sq" naming dates to a CAMB Notes geometric
    ``β²`` convention that equals 1 in flat FLRW. Resolved by 4
    independent external audits (V5-RUNTIME Round-12, 2026-04-25);
    see ``docs/audits/SSOT_NU_SEED_DRIFT_2026-04-25.md`` Section 9.
    """

    from dataclasses import replace as _dc_replace
    from concurrent.futures import ProcessPoolExecutor as _PPE
    import multiprocessing as _mp

    cfg = config or FLRWPipelineConfig()
    if not (probe_b_k_sq > 0.0):
        raise ValueError(
            f"probe_b_k_sq must be positive for linear extrapolation; "
            f"got {probe_b_k_sq}"
        )
    if not (1.0e-4 <= probe_b_k_sq <= 10.0):
        import warnings

        warnings.warn(
            f"probe_b_k_sq={probe_b_k_sq} is outside the Round-8 "
            f"verified linear regime [1e-4, 10]; results may be "
            f"dominated by bias (below) or quadratic saturation "
            f"(above). See docs for the b_k_sq response sweep.",
            stacklevel=2,
        )

    tasks = [
        (float(k_mpc), 0.0),
        (float(k_mpc), float(probe_b_k_sq)),
    ]

    global _WORKER_SPECIES, _WORKER_CONFIG, _WORKER_BIANCHI_TYPE

    _WORKER_SPECIES = species
    _WORKER_CONFIG = cfg
    _WORKER_BIANCHI_TYPE = bianchi_type
    try:
        ctx = _mp.get_context("fork")
        with _PPE(max_workers=2, mp_context=ctx, initializer=_worker_init) as exe:
            bias_tf, target_tf = list(exe.map(_worker_task_bias_pair, tasks))
    finally:
        _WORKER_SPECIES = None
        _WORKER_CONFIG = None
        _WORKER_BIANCHI_TYPE = "I"

    inv = 1.0 / float(probe_b_k_sq)
    return BianchiTransferFunctions(
        delta_T_m0=(target_tf.delta_T_m0 - bias_tf.delta_T_m0) * inv,
        delta_T_m_plus2=(target_tf.delta_T_m_plus2 - bias_tf.delta_T_m_plus2) * inv,
        delta_T_m_minus2=(target_tf.delta_T_m_minus2 - bias_tf.delta_T_m_minus2) * inv,
        delta_E_m0=(target_tf.delta_E_m0 - bias_tf.delta_E_m0) * inv,
        delta_E_m_plus2=(target_tf.delta_E_m_plus2 - bias_tf.delta_E_m_plus2) * inv,
        delta_E_m_minus2=(target_tf.delta_E_m_minus2 - bias_tf.delta_E_m_minus2) * inv,
        delta_B_all_zero=(target_tf.delta_B_all_zero - bias_tf.delta_B_all_zero) * inv,
    )


def _subtract_transfer_functions(
    target: BianchiTransferFunctions,
    bias: BianchiTransferFunctions,
) -> BianchiTransferFunctions:
    """Return target − bias element-wise for every Δ field."""
    return BianchiTransferFunctions(
        delta_T_m0=target.delta_T_m0 - bias.delta_T_m0,
        delta_T_m_plus2=target.delta_T_m_plus2 - bias.delta_T_m_plus2,
        delta_T_m_minus2=target.delta_T_m_minus2 - bias.delta_T_m_minus2,
        delta_E_m0=target.delta_E_m0 - bias.delta_E_m0,
        delta_E_m_plus2=target.delta_E_m_plus2 - bias.delta_E_m_plus2,
        delta_E_m_minus2=target.delta_E_m_minus2 - bias.delta_E_m_minus2,
        delta_B_all_zero=target.delta_B_all_zero - bias.delta_B_all_zero,
    )


def _scale_transfer_function(
    tf: BianchiTransferFunctions, factor: float
) -> BianchiTransferFunctions:
    """Multiply every Δ field by a scalar factor."""
    return BianchiTransferFunctions(
        delta_T_m0=tf.delta_T_m0 * factor,
        delta_T_m_plus2=tf.delta_T_m_plus2 * factor,
        delta_T_m_minus2=tf.delta_T_m_minus2 * factor,
        delta_E_m0=tf.delta_E_m0 * factor,
        delta_E_m_plus2=tf.delta_E_m_plus2 * factor,
        delta_E_m_minus2=tf.delta_E_m_minus2 * factor,
        delta_B_all_zero=tf.delta_B_all_zero * factor,
    )


def _worker_task_chunk(k_values: Sequence[float]) -> list[BianchiTransferFunctions]:  # pragma: no cover
    """Worker-side chunk entry point — amortizes the ~0.8 s k-independent
    Tier-B setup (background_monitor, visibility_source, backend,
    canonical_decision, runtime_decision, execution_plan) across
    ``len(k_values)`` k-runs by calling the low-level
    ``_run_chunk_shared_bg`` path.
    """
    assert _WORKER_SPECIES is not None, "worker globals not initialized"
    assert _WORKER_CONFIG is not None, "worker config not initialized"
    return _run_chunk_shared_bg(
        _WORKER_SPECIES,
        list(k_values),
        cfg=_WORKER_CONFIG,
        bianchi_type=_WORKER_BIANCHI_TYPE,
    )


def _worker_task_bias_pair_chunk(
    k_and_target_values: Sequence[tuple[float, float]],
) -> list[tuple[BianchiTransferFunctions, BianchiTransferFunctions]]:  # pragma: no cover
    """Worker-side bias-subtraction chunk.

    Each input pair is ``(k_mpc, target_b_k_sq)``. The worker runs the
    bias and target solves for each k through one shared-background
    context, preserving the exact same per-run equations while avoiding
    duplicate background/visibility/backend construction when workers
    are the limiting resource.
    """
    assert _WORKER_SPECIES is not None, "worker globals not initialized"
    assert _WORKER_CONFIG is not None, "worker config not initialized"
    specs: list[tuple[float, float]] = []
    for k_mpc, target_b_k_sq in k_and_target_values:
        specs.append((float(k_mpc), 0.0))
        specs.append((float(k_mpc), float(target_b_k_sq)))
    raw = _run_chunk_shared_bg_for_specs(
        _WORKER_SPECIES,
        specs,
        cfg=_WORKER_CONFIG,
        bianchi_type=_WORKER_BIANCHI_TYPE,
    )
    return [(raw[2 * i], raw[2 * i + 1]) for i in range(len(k_and_target_values))]


def compute_transfer_function_grid(
    species: "SpeciesBackgroundRegistry",
    k_grid_mpc: Sequence[float] | np.ndarray,
    *,
    config: FLRWPipelineConfig | None = None,
    bianchi_type: str = "I",
    n_workers: int | None = None,
    chunked: bool = True,
) -> list[BianchiTransferFunctions]:
    """Parallel k-sweep with optional shared-background chunking.

    Parameters
    ----------
    species
        Planck-2018 species registry (inherited to workers via fork).
    k_grid_mpc
        Array of comoving wavenumbers (Mpc⁻¹).
    config
        ``FLRWPipelineConfig``; defaults chosen for Planck-2018 FLRW.
    bianchi_type
        Defaults to "I" (FLRW).
    n_workers
        Process count; default = ``os.cpu_count()`` capped at the
        k-grid length.
    chunked
        When True (default), each worker processes a chunk of k-values
        with background_monitor + visibility_source + backend +
        canonical_decision built ONCE per chunk and reused across k's.
        Profiled savings: ~0.8 s per k after the first in each chunk
        (the IMEX integrator itself still dominates at ~42 s / k).
        Chunking only amortizes setup when ``N_k > n_workers``; when
        chunk size would be 1 (``N_k ≤ n_workers``) the scheduler
        automatically falls back to the per-k path to avoid a tiny
        wrapping overhead. Set explicitly False to force per-k for
        isolation testing.

    Returns
    -------
    List of ``BianchiTransferFunctions``, one per k in order.

    Notes
    -----
    Falls back to sequential execution if ``n_workers == 1``. Uses the
    default ``fork`` start method on Linux so species + module state
    are inherited as COW memory.
    """

    global _WORKER_SPECIES, _WORKER_CONFIG, _WORKER_BIANCHI_TYPE

    k_array = np.asarray(k_grid_mpc, dtype=np.float64).ravel()
    if k_array.size == 0:
        raise ValueError("k_grid_mpc must be non-empty")
    if np.any(k_array <= 0.0):
        raise ValueError("k_grid_mpc entries must all be positive")
    cfg = config or FLRWPipelineConfig()

    max_parallel = n_workers if n_workers is not None else os.cpu_count() or 1
    # Task count = N_k for the standard path, 2·N_k for bias_subtraction
    # (one bias + one target run per k). Effective worker count saturates
    # at the task count so small-k runs don't spin up idle workers.
    task_count = 2 * int(k_array.size) if cfg.bias_subtraction else int(k_array.size)
    effective = max(1, min(int(max_parallel), task_count))

    # When bias_subtraction is enabled, each k triggers 2 solver runs
    # (b_k_sq=0 and b_k_sq=primordial_b_k_sq). Dispatched in parallel
    # across the same worker pool; pairwise subtracted at the end.
    if cfg.bias_subtraction:
        return _compute_transfer_function_grid_bias_subtracted(
            species,
            k_array,
            cfg=cfg,
            bianchi_type=bianchi_type,
            effective=effective,
        )

    if effective == 1:
        # Single-worker path — run sequentially. Use shared-bg chunk when
        # the caller asked for it so the savings still materialize.
        if (
            chunked
            and cfg.superhorizon_x_max_at_start is None
            and k_array.size >= 2
        ):
            return _run_chunk_shared_bg(
                species, k_array.tolist(), cfg=cfg, bianchi_type=bianchi_type
            )
        return [
            compute_transfer_function_at_k(
                species, float(k), config=cfg, bianchi_type=bianchi_type
            )
            for k in k_array
        ]

    # Fork-inherited worker globals (parent installs; children read).
    _WORKER_SPECIES = species
    _WORKER_CONFIG = cfg
    _WORKER_BIANCHI_TYPE = bianchi_type

    import multiprocessing as _mp

    ctx = _mp.get_context("fork")

    # Auto-disable chunking when chunk size would be 1 (N_k ≤ n_workers)
    # — no amortization possible and tiny wrapper overhead is strictly
    # negative.
    use_chunking = (
        bool(chunked)
        and cfg.superhorizon_x_max_at_start is None
        and (int(k_array.size) > int(effective))
    )

    try:
        if use_chunking:
            # Split k-grid into chunks. The default preserves the
            # historical one-chunk-per-worker behavior; k_chunk_size lets
            # large grids use smaller chunks for better load balancing.
            chunks = [
                [float(k) for k in chunk]
                for chunk in _split_work_chunks(
                    k_array,
                    worker_count=effective,
                    chunk_size=cfg.k_chunk_size,
                )
            ]
            chunks = [chunk for chunk in chunks if chunk]
            with _cf.ProcessPoolExecutor(
                max_workers=effective,
                mp_context=ctx,
                initializer=_worker_init,
            ) as exe:
                chunk_results = list(exe.map(_worker_task_chunk, chunks))
            results: list[BianchiTransferFunctions] = []
            for chunk in chunk_results:
                results.extend(chunk)
        else:
            with _cf.ProcessPoolExecutor(
                max_workers=effective,
                mp_context=ctx,
                initializer=_worker_init,
            ) as exe:
                results = list(exe.map(_worker_task, k_array.tolist()))
    finally:
        # Always clear worker globals so the parent's memory doesn't
        # hold lingering references after the pool exits.
        _WORKER_SPECIES = None
        _WORKER_CONFIG = None
        _WORKER_BIANCHI_TYPE = "I"

    return results


# ------------------------------------------------------------------------
# C_ℓ / D_ℓ assembly wrappers
# ------------------------------------------------------------------------


def _compute_transfer_function_grid_bias_subtracted(
    species: "SpeciesBackgroundRegistry",
    k_array: np.ndarray,
    *,
    cfg: FLRWPipelineConfig,
    bianchi_type: str,
    effective: int,
) -> list[BianchiTransferFunctions]:
    """V5 step-4b-(a) Round-6 bias-subtraction path.

    For each k, dispatches two parallel Tier-B runs:
      - ``b_k_sq = 0`` → visibility-source-only Δ_bias
      - ``b_k_sq = cfg.primordial_b_k_sq`` → target Δ_target
    and returns ``Δ_pure = Δ_target − Δ_bias`` per k.

    Dispatches all ``2 × N_k`` runs across the shared ProcessPoolExecutor
    pool so wall time is ``max(2·N_k / effective_workers, 1) × 45 s``.

    Used when ``FLRWPipelineConfig.bias_subtraction=True``.
    """
    global _WORKER_SPECIES, _WORKER_CONFIG, _WORKER_BIANCHI_TYPE

    # Build concrete (k, target_b_k_sq) pairs in the parent process
    # (handles callable primordial_b_k_sq_fn correctly under
    # ProcessPoolExecutor; workers only see floats).
    target_pairs: list[tuple[float, float]] = []
    for k_mpc in k_array:
        per_k_target = _resolve_primordial_b_k_sq(cfg, float(k_mpc))
        target_pairs.append((float(k_mpc), per_k_target))

    _WORKER_SPECIES = species
    _WORKER_CONFIG = cfg
    _WORKER_BIANCHI_TYPE = bianchi_type

    try:
        # If workers are the limiting resource, keep each k's bias and
        # target solve in the same shared-background chunk. If there are
        # enough workers to run all 2*N solves concurrently, retain the
        # old per-run dispatch to minimize wall time.
        use_pair_chunking = (
            cfg.superhorizon_x_max_at_start is None
            and int(effective) <= len(target_pairs)
        )
        if use_pair_chunking:
            worker_count = max(1, min(int(effective), len(target_pairs)))
            pair_chunks = [
                [(float(k), float(target)) for k, target in chunk]
                for chunk in _split_work_chunks(
                    target_pairs,
                    worker_count=worker_count,
                    chunk_size=cfg.k_chunk_size,
                )
            ]
            pair_chunks = [chunk for chunk in pair_chunks if len(chunk) > 0]
            worker_count = max(1, min(worker_count, len(pair_chunks)))
            if effective == 1:
                pair_results = [
                    pair
                    for chunk in pair_chunks
                    for pair in _worker_task_bias_pair_chunk(chunk)
                ]
            else:
                import multiprocessing as _mp

                ctx = _mp.get_context("fork")
                with _cf.ProcessPoolExecutor(
                    max_workers=worker_count,
                    mp_context=ctx,
                    initializer=_worker_init,
                ) as exe:
                    chunk_results = list(exe.map(_worker_task_bias_pair_chunk, pair_chunks))
                pair_results = [pair for chunk in chunk_results for pair in chunk]
        else:
            tasks: list[tuple[float, float]] = []
            for k_mpc, per_k_target in target_pairs:
                tasks.append((float(k_mpc), 0.0))
                tasks.append((float(k_mpc), float(per_k_target)))
            import multiprocessing as _mp

            ctx = _mp.get_context("fork")
            with _cf.ProcessPoolExecutor(
                max_workers=effective,
                mp_context=ctx,
                initializer=_worker_init,
            ) as exe:
                raw_results = list(exe.map(_worker_task_bias_pair, tasks))
            pair_results = [
                (raw_results[2 * i], raw_results[2 * i + 1])
                for i in range(len(target_pairs))
            ]
    finally:
        _WORKER_SPECIES = None
        _WORKER_CONFIG = None
        _WORKER_BIANCHI_TYPE = "I"

    out: list[BianchiTransferFunctions] = []
    for bias_tf, target_tf in pair_results:
        out.append(_subtract_transfer_functions(target_tf, bias_tf))
    return out


def _transfer_fn_from_grid(
    k_grid: np.ndarray,
    results: Sequence[BianchiTransferFunctions],
) -> Callable[[float], BianchiTransferFunctions]:
    """Build a ``TransferFunctionAtK`` callable from a tabulated k-sweep.

    ``assemble_cl_TT_isotropic`` iterates over ``config.k_grid`` and calls
    ``transfer_fn(float(k))`` at each. We return an exact-match lookup
    keyed on the k_grid values the sweep was run at.
    """

    table = {float(k): tf for k, tf in zip(np.asarray(k_grid, dtype=np.float64), results)}

    def lookup(k: float) -> BianchiTransferFunctions:
        key = float(k)
        if key not in table:
            # Tolerate tiny float drift (< 1e-14 relative) from numpy
            # array indexing — rare but possible with logspace grids.
            for stored, tf in table.items():
                if abs(stored - key) <= max(abs(stored), 1.0e-30) * 1.0e-12:
                    return tf
            raise KeyError(
                f"transfer-function grid has no entry for k={key!r}; "
                f"keys={sorted(table)[:3]}... (first three)"
            )
        return table[key]

    return lookup


def compute_flrw_cl_tt(
    species: "SpeciesBackgroundRegistry",
    *,
    k_grid_mpc: np.ndarray,
    pipeline_config: FLRWPipelineConfig | None = None,
    assembly_config: CLAssemblyConfig | None = None,
    n_workers: int | None = None,
    bianchi_type: str = "I",
) -> dict[str, Any]:
    """Compute C_ℓ^TT, C_ℓ^EE, and C_ℓ^TE from a k-sweep of Tier-B transfer functions.

    Returns a dict::

        {
            "k_grid_mpc": k_array,
            "transfer_functions": list[BianchiTransferFunctions],
            "cl_tt": np.ndarray,
            "cl_ee": np.ndarray,
            "cl_te": np.ndarray,
            "assembly_config": CLAssemblyConfig,
        }
    """

    k_array = np.asarray(k_grid_mpc, dtype=np.float64).ravel()
    p_cfg = pipeline_config or FLRWPipelineConfig()

    if assembly_config is None:
        assembly_config = CLAssemblyConfig(
            ell_max=p_cfg.ell_max_transfer,
            k_grid=k_array,
            quadrature="trapezoid",
        )
    elif not np.array_equal(
        np.asarray(assembly_config.k_grid, dtype=np.float64), k_array
    ):
        raise ValueError(
            "assembly_config.k_grid must match the pipeline k_grid_mpc "
            "exactly — the transfer-function lookup is keyed on k values"
        )

    results = compute_transfer_function_grid(
        species,
        k_array,
        config=p_cfg,
        bianchi_type=bianchi_type,
        n_workers=n_workers,
    )
    cl_tt, cl_ee, cl_te = assemble_cl_TT_EE_TE_isotropic_from_grid(
        results, assembly_config
    )
    return {
        "k_grid_mpc": k_array,
        "transfer_functions": results,
        "cl_tt": cl_tt,
        "cl_ee": cl_ee,
        "cl_te": cl_te,
        "assembly_config": assembly_config,
    }


def compute_flrw_d_ell(
    species: "SpeciesBackgroundRegistry",
    *,
    k_grid_mpc: np.ndarray,
    pipeline_config: FLRWPipelineConfig | None = None,
    assembly_config: CLAssemblyConfig | None = None,
    n_workers: int | None = None,
    bianchi_type: str = "I",
) -> dict[str, Any]:
    """End-to-end FLRW D_ℓ pipeline.

    Returns the ``compute_flrw_cl_tt`` bundle augmented with:

        "d_tt" : np.ndarray    # D_ℓ^TT in μK²
        "d_ee" : np.ndarray    # D_ℓ^EE in μK²
        "d_te" : np.ndarray    # D_ℓ^TE in μK²

    The Route-B MM-curve anchor reports ``D_2^TT = 1002.086744 μK²`` for
    Planck-2018. For ~50+ k-grid points this extraction path should
    reproduce it to within the trapezoid k-quadrature error (~0.1%).
    """

    bundle = compute_flrw_cl_tt(
        species,
        k_grid_mpc=k_grid_mpc,
        pipeline_config=pipeline_config,
        assembly_config=assembly_config,
        n_workers=n_workers,
        bianchi_type=bianchi_type,
    )
    t_cmb_K = float(bundle["assembly_config"].T_CMB_K)
    bundle["d_tt"] = compute_dl(bundle["cl_tt"], T_CMB_K=t_cmb_K)
    bundle["d_ee"] = compute_dl(bundle["cl_ee"], T_CMB_K=t_cmb_K)
    bundle["d_te"] = compute_dl(bundle["cl_te"], T_CMB_K=t_cmb_K)
    return bundle


def compute_flrw_d_ell_linear_probe(
    species: "SpeciesBackgroundRegistry",
    *,
    k_grid_mpc: np.ndarray,
    pipeline_config: FLRWPipelineConfig | None = None,
    assembly_config: CLAssemblyConfig | None = None,
    probe_b_k_sq: float = 1.0,
    calibration_factor: float = 1.0,
    n_workers: int | None = None,
    bianchi_type: str = "I",
) -> dict[str, Any]:
    """V5 step-4b-(a) Round-9: D_ℓ via N_k parallel linear probes.

    Round-8 established that the Tier-B solver response to
    ``primordial_b_k_sq`` is clean and linear inside
    ``b_k_sq ∈ [~1e-3, ~10]`` but is dominated by the visibility-source
    bias below that range and saturated by the seed formula's quadratic
    B_K² term above. Physical Planck ζ ≈ 4.6e-5 sits below the noise
    floor, so direct extraction at the physical amplitude is impossible.

    This wrapper instead runs the linear-probe extraction at every k in
    ``k_grid_mpc`` (probe amplitude inside the linear regime), recovers
    the slope α(k) = (Δ_target − Δ_bias) / probe_b_k_sq, and pairs it
    with the standard Planck-2018 P_R(k) in the C_ℓ assembly. The
    result is the linearly-extrapolated D_ℓ at any primordial amplitude
    that the assembly P_R encodes, decoupled from the bias floor.

    Implementation
    --------------
    Reuses ``compute_transfer_function_grid(..., bias_subtraction=True)``
    which dispatches ``2 × N_k`` parallel solver runs (bias + target per
    k) across ``min(cpu_count, 2·N_k)`` workers. The bias-subtracted
    transfer functions are then divided by ``probe_b_k_sq`` (so they
    represent the per-unit-B_K² response) and optionally multiplied by
    ``calibration_factor`` (R9-C: B_K² → ζ² convention factor; default
    1.0 assumes the Lowell §13.2 unit-amplitude convention is exact).

    Parameters
    ----------
    species
        Planck-2018 species registry (inherited to workers via fork).
    k_grid_mpc
        Array of comoving wavenumbers (Mpc⁻¹).
    pipeline_config
        Base ``FLRWPipelineConfig``. Any ``primordial_b_k_sq`` /
        ``primordial_b_k_sq_fn`` / ``bias_subtraction`` field is
        overridden internally to set the probe amplitude and force the
        bias-subtraction path.
    assembly_config
        Optional ``CLAssemblyConfig``. Defaults to Planck-2018
        (``A_s=2.1e-9, n_s=0.9649, k_pivot=0.05 Mpc⁻¹``) with
        ``ell_max = pipeline_config.ell_max_transfer`` and the
        pipeline's ``k_grid``.
    probe_b_k_sq
        Probe amplitude inside the Round-8 linear regime
        ``[1e-4, 10]``. Default 1.0.
    calibration_factor
        R9-C calibration multiplier for α(k). Default 1.0 (no
        correction); set to the empirically-measured
        ``D_2^Route-B / D_2^probe`` square root once R9-B has been run.
    n_workers
        Process count; default = ``os.cpu_count()`` capped at ``2·N_k``.
    bianchi_type
        Defaults to "I" (FLRW).

    Returns
    -------
    dict with keys::

        "k_grid_mpc"               : np.ndarray
        "alpha_transfer_functions" : list[BianchiTransferFunctions]
        "probe_b_k_sq"             : float
        "calibration_factor"       : float
        "cl_tt"                    : np.ndarray
        "cl_ee"                    : np.ndarray
        "cl_te"                    : np.ndarray
        "d_tt"                     : np.ndarray  (μK²)
        "d_ee"                     : np.ndarray  (μK²)
        "d_te"                     : np.ndarray  (μK²)
        "assembly_config"          : CLAssemblyConfig

    Notes
    -----
    Wall time scales as ``ceil(2·N_k / n_workers) × 45 s``. For
    N_k = 6 with 8 workers: 12 tasks → 2 rounds → ~90 s.
    """

    from dataclasses import replace as _dc_replace

    k_array = np.asarray(k_grid_mpc, dtype=np.float64).ravel()
    if k_array.size == 0:
        raise ValueError("k_grid_mpc must be non-empty")
    if np.any(k_array <= 0.0):
        raise ValueError("k_grid_mpc entries must all be positive")
    if not (probe_b_k_sq > 0.0):
        raise ValueError(
            f"probe_b_k_sq must be positive; got {probe_b_k_sq}"
        )
    if not (1.0e-4 <= probe_b_k_sq <= 10.0):
        import warnings

        warnings.warn(
            f"probe_b_k_sq={probe_b_k_sq} is outside the Round-8 "
            f"verified linear regime [1e-4, 10]; α(k) may be "
            f"contaminated by visibility-source bias (below) or "
            f"quadratic saturation (above). See the b_k_sq response "
            f"sweep for context.",
            stacklevel=2,
        )

    base_cfg = pipeline_config or FLRWPipelineConfig()
    # ``unit_amplitude_normalization=True`` divides each run by
    # ``seed_amp = max(|Σ_±|, 1e-6)`` which for Bianchi I (Σ_±=0) is the
    # uniform 1e-6 floor — NOT the primordial amplitude. That floor
    # multiplies α by ~1e+6 (and |α|² by 1e+12) without carrying any
    # physical content, so the linear-probe path forces it OFF and lets
    # the explicit ``probe_b_k_sq`` division handle normalization. With
    # ``primordial_b_k_sq_fn`` cleared the probe runs at a uniform
    # amplitude across k.
    probe_cfg = _dc_replace(
        base_cfg,
        primordial_b_k_sq=float(probe_b_k_sq),
        primordial_b_k_sq_fn=None,
        bias_subtraction=True,
        unit_amplitude_normalization=False,
    )

    # 2 × N_k parallel runs via the bias-subtracted grid path. Returns
    # one bias-subtracted Δ per k; each is the raw seed response at
    # ``b_k_sq = probe_b_k_sq``.
    raw_diffs = compute_transfer_function_grid(
        species,
        k_array,
        config=probe_cfg,
        bianchi_type=bianchi_type,
        n_workers=n_workers,
    )

    inv_probe = float(calibration_factor) / float(probe_b_k_sq)
    alpha_list = [_scale_transfer_function(diff, inv_probe) for diff in raw_diffs]

    if assembly_config is None:
        assembly_config = CLAssemblyConfig(
            ell_max=probe_cfg.ell_max_transfer,
            k_grid=k_array,
            quadrature="trapezoid",
        )
    elif not np.array_equal(
        np.asarray(assembly_config.k_grid, dtype=np.float64), k_array
    ):
        raise ValueError(
            "assembly_config.k_grid must match k_grid_mpc exactly — "
            "the transfer-function lookup is keyed on k values"
        )

    cl_tt, cl_ee, cl_te = assemble_cl_TT_EE_TE_isotropic_from_grid(
        alpha_list, assembly_config
    )
    t_cmb_K = float(assembly_config.T_CMB_K)
    return {
        "k_grid_mpc": k_array,
        "alpha_transfer_functions": alpha_list,
        "probe_b_k_sq": float(probe_b_k_sq),
        "calibration_factor": float(calibration_factor),
        "cl_tt": cl_tt,
        "cl_ee": cl_ee,
        "cl_te": cl_te,
        "d_tt": compute_dl(cl_tt, T_CMB_K=t_cmb_K),
        "d_ee": compute_dl(cl_ee, T_CMB_K=t_cmb_K),
        "d_te": compute_dl(cl_te, T_CMB_K=t_cmb_K),
        "assembly_config": assembly_config,
    }
