"""End-to-end FLRW CMB D_ℓ pipeline (V5 step 4b).

Chains the V5 runtime track's building blocks into a single entry point
that produces Planck-2018 FLRW D_ℓ from real Tier-B physics:

    species + k_grid
        → per-k: execute_tier_b_solver (Blockers 1+2+3)
                  → extract_flrw_sources_from_tier_b (Round-5)
                  → build_temperature_source + build_polarization_source
                  → project_m_transfer  → Δ_ℓ^T(k), Δ_ℓ^E(k)
        → k-sweep parallelized via ProcessPoolExecutor
        → assemble_cl_TT_isotropic / assemble_cl_EE_isotropic
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
    build_polarization_source,
    build_temperature_source,
    project_polarization_transfer,
    project_temperature_transfer,
)
from bass.runtime import (
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
    build_cosmological_integrator_config,
    execute_tier_b_solver,
)
from bass.spectrum.cl_assembly import (
    CLAssemblyConfig,
    assemble_cl_EE_isotropic,
    assemble_cl_TT_isotropic,
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
    "compute_transfer_function_at_k",
    "compute_transfer_function_grid",
    "compute_linear_probe_transfer_function",
    "compute_flrw_cl_tt",
    "compute_flrw_d_ell",
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
    random_seed: int = 42
    unit_amplitude_normalization: bool = True
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
    """V5 step-4b-(a) primordial amplitude squared ``|B_K|²`` for the
    Lowell §13.2 seed. Default 1.0 gives unit-B_K transfer functions;
    ``A_s × (k_pivot_ref / k_pivot)^(n_s-1)`` (≈ 2.1e-9) gives
    ζ-normalized physical amplitude. Exact B_K → ζ calibration is a
    pending convention audit (V5 follow-up Round-7)."""
    primordial_b_k_sq_fn: Callable[[float], float] | None = None
    """V5 step-4b-(a) Round-7 k-dependent override. When set to a
    callable ``k → b_k_sq``, overrides the scalar ``primordial_b_k_sq``
    field per k. Standard usage: set to the Planck-2018 P_ζ:

        ``primordial_b_k_sq_fn=lambda k: 2.1e-9 * (k/0.05)**(0.9649-1.0)``

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

    def _z_of_eta(eta: np.ndarray) -> np.ndarray:
        a = np.asarray(bg_table.interp_a(eta), dtype=np.float64)
        return 1.0 / np.maximum(a, 1.0e-30) - 1.0

    def g_of_eta(eta: np.ndarray) -> np.ndarray:
        z = _z_of_eta(np.asarray(eta, dtype=np.float64))
        # Clip to recomb table range to avoid the range-check raise at
        # η-grid endpoints that graze the table boundary by < 1e-9.
        z_clipped = np.clip(z, float(recomb.table.z_min), float(recomb.table.z_max))
        return np.asarray(recomb.query_visibility(z_clipped), dtype=np.float64)

    def kappa_of_eta(eta: np.ndarray) -> np.ndarray:
        z = _z_of_eta(np.asarray(eta, dtype=np.float64))
        z_clipped = np.clip(z, float(recomb.table.z_min), float(recomb.table.z_max))
        return np.asarray(recomb.query_kappa(z_clipped), dtype=np.float64)

    return g_of_eta, kappa_of_eta


def _los_and_wrap(
    integration_result: Any,
    species: "SpeciesBackgroundRegistry",
    k_mpc: float,
    cfg: FLRWPipelineConfig,
    seed_amp_for_norm: float | None,
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
    )
    g_of_eta, kappa_of_eta = build_visibility_and_kappa_callables(species)

    eta_grid = np.asarray(integration_result.eta, dtype=np.float64)
    eta_0_mpc = float(species.bg_table.eta_today)
    eta_for_los = np.clip(eta_grid, 0.0, eta_0_mpc)

    bessel_config = FLRWBesselConfig(
        ell_max=cfg.ell_max_transfer,
        eta_0_mpc=eta_0_mpc,
        quadrature=cfg.quadrature,
    )
    source_T = build_temperature_source(eta_for_los, sources, g_of_eta, kappa_of_eta)
    source_E = build_polarization_source(eta_for_los, sources, g_of_eta)

    delta_T = project_temperature_transfer(
        float(k_mpc), source_T, eta_for_los, bessel_config
    )
    delta_E = project_polarization_transfer(
        float(k_mpc), source_E, eta_for_los, bessel_config
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

    integrator_config = build_cosmological_integrator_config(
        species,
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
    """Low-level k-loop that shares background_monitor + visibility_source
    + backend + canonical_decision + runtime_decision across all k's in
    ``k_values``. Only the integrator (via ``seed_k_comoving``) is
    rebuilt per-k.

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

    if len(k_values) == 0:
        return []

    rc = _pipeline_runtime_controls(cfg)
    ff = _pipeline_feature_flags()

    # k-independent shared build — done ONCE per chunk, reused across k.
    template_integrator_config = build_cosmological_integrator_config(
        species,
        L_max=cfg.L_max_tower,
        n_output=cfg.n_output,
        rtol=cfg.rtol,
        atol=cfg.atol,
        bianchi_cosmo=BianchiCosmology(structure=get_type(bianchi_type), beta=0.0),
        gamma_T_over_H_threshold=cfg.gamma_T_over_H_threshold,
        adiabatic_mode_seed=cfg.adiabatic_mode_seed,
        primordial_b_k_sq=cfg.primordial_b_k_sq,
    )
    template_request = _build_tier_b_runtime_request(
        manifest=_pipeline_manifest("chunked"),
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=template_integrator_config,
        runtime_controls=rc,
        feature_flags=ff,
        release=_pipeline_release("chunked", cfg.random_seed),
        k_grid_mpc=np.array([float(k_values[0]), 2.0 * float(k_values[0])]),
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

    # Per-k: only rebuild the integrator (with this k's seed_k_comoving
    # and its per-k resolved primordial_b_k_sq) and re-run the IMEX
    # integration. Background_monitor + visibility_source + backend +
    # canonical_decision + runtime_decision + execution_plan are reused.
    out: list[BianchiTransferFunctions] = []
    for k_mpc in k_values:
        k_grid_pair = np.array([float(k_mpc), 2.0 * float(k_mpc)], dtype=np.float64)
        seed_k_comoving = float(k_mpc)
        # Resolve per-k b_k_sq in the PARENT process for ProcessPoolExecutor
        # safety. Callable overrides pass through unchanged.
        per_k_b_k_sq = _resolve_primordial_b_k_sq(cfg, float(k_mpc))
        per_k_runtime_config = _dc_replace(
            runtime_config, primordial_b_k_sq=per_k_b_k_sq
        )
        integrator = Ver2TierBIntegrator(
            per_k_runtime_config,
            species,
            backend=backend_instance,
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
            backend=backend_instance,
            reionization_amplitude=reionization_amp,
            integrator=integrator,
            runtime_decision=runtime_decision,
            execution_plan=execution_plan,
            checkpoint_callback=None,
            checkpoint_paths=[],
            metadata={"owner": "flrw_pipeline._run_chunk_shared_bg"},
        )
        # Per-k request carries the k_grid_pair + a fresh manifest/release
        # so downstream artefact identifiers stay distinct per k.
        per_k_request = _dc_replace(
            template_request,
            manifest=_pipeline_manifest(f"chunked-k{k_mpc:.6e}"),
            release=_pipeline_release(f"chunked-k{k_mpc:.6e}", cfg.random_seed),
            k_grid_mpc=k_grid_pair,
        )
        result = integrator.run(
            checkpoint_every_n_steps=None,
            checkpoint_callback=None,
            restart_state=None,
        )
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
        out.append(
            _los_and_wrap(
                run.integration_result,
                species,
                float(k_mpc),
                cfg,
                seed_amp_for_norm=seed_amp,
            )
        )
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
    The returned "α" transfer function has units "per unit B_K_sq",
    not "per unit ζ". The exact B_K ↔ ζ convention is a pending audit;
    if B_K_sq = ζ², then α(k) is the transfer function per unit ζ² and
    pairs directly with P_ζ(k) in C_ℓ assembly. If B_K_sq = ζ, an
    additional √ζ rescaling is needed at assembly time.
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
        if chunked and k_array.size >= 2:
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
    use_chunking = bool(chunked) and (int(k_array.size) > int(effective))

    try:
        if use_chunking:
            # Split k-grid into ~even chunks across workers.
            chunks = [
                chunk.tolist() for chunk in np.array_split(k_array, effective)
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

    # Build the (k, b_k_sq) task pairs. Per-k b_k_sq is resolved in the
    # parent process (handles callable primordial_b_k_sq_fn correctly
    # under ProcessPoolExecutor; workers only see floats).
    tasks: list[tuple[float, float]] = []
    for k_mpc in k_array:
        per_k_target = _resolve_primordial_b_k_sq(cfg, float(k_mpc))
        tasks.append((float(k_mpc), 0.0))  # bias — seed-independent
        tasks.append((float(k_mpc), per_k_target))

    _WORKER_SPECIES = species
    _WORKER_CONFIG = cfg
    _WORKER_BIANCHI_TYPE = bianchi_type

    try:
        if effective == 1:
            raw_results = [_worker_task_bias_pair(task) for task in tasks]
        else:
            import multiprocessing as _mp

            ctx = _mp.get_context("fork")
            with _cf.ProcessPoolExecutor(
                max_workers=effective,
                mp_context=ctx,
                initializer=_worker_init,
            ) as exe:
                raw_results = list(exe.map(_worker_task_bias_pair, tasks))
    finally:
        _WORKER_SPECIES = None
        _WORKER_CONFIG = None
        _WORKER_BIANCHI_TYPE = "I"

    # Pair up the results: (bias_k, target_k) per k in order.
    out: list[BianchiTransferFunctions] = []
    for i in range(len(k_array)):
        bias_tf = raw_results[2 * i]
        target_tf = raw_results[2 * i + 1]
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
    """Compute C_ℓ^TT and C_ℓ^EE from a k-sweep of Tier-B transfer functions.

    Returns a dict::

        {
            "k_grid_mpc": k_array,
            "transfer_functions": list[BianchiTransferFunctions],
            "cl_tt": np.ndarray,
            "cl_ee": np.ndarray,
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
    transfer_fn = _transfer_fn_from_grid(k_array, results)
    cl_tt = assemble_cl_TT_isotropic(transfer_fn, assembly_config)
    cl_ee = assemble_cl_EE_isotropic(transfer_fn, assembly_config)
    return {
        "k_grid_mpc": k_array,
        "transfer_functions": results,
        "cl_tt": cl_tt,
        "cl_ee": cl_ee,
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
    return bundle
