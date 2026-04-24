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
    "compute_flrw_cl_tt",
    "compute_flrw_d_ell",
    "build_visibility_and_kappa_callables",
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
    random_seed: int = 42

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

    sources = extract_flrw_sources_from_tier_b(
        run.integration_result,
        species,
        k=float(k_mpc),
        anisotropic_stress=cfg.anisotropic_stress,
    )

    g_of_eta, kappa_of_eta = build_visibility_and_kappa_callables(species)

    eta_grid = np.asarray(run.integration_result.eta, dtype=np.float64)
    eta_0_mpc = float(species.bg_table.eta_today)
    # Clip stored eta to within (0, eta_today] for the LoS projector.
    # The solver may report eta slightly beyond eta_today at the final
    # sample due to quadrature step overrun; clip defensively.
    eta_for_los = np.clip(eta_grid, 0.0, eta_0_mpc)

    bessel_config = FLRWBesselConfig(
        ell_max=cfg.ell_max_transfer,
        eta_0_mpc=eta_0_mpc,
        quadrature=cfg.quadrature,
    )

    source_T = build_temperature_source(
        eta_for_los, sources, g_of_eta, kappa_of_eta
    )
    source_E = build_polarization_source(eta_for_los, sources, g_of_eta)

    delta_T = project_temperature_transfer(
        float(k_mpc), source_T, eta_for_los, bessel_config
    )
    delta_E = project_polarization_transfer(
        float(k_mpc), source_E, eta_for_los, bessel_config
    )

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
    """Worker-side entry point for the parallel k-sweep.

    Executed in each child process; reads the fork-inherited module
    globals set by ``compute_transfer_function_grid``.
    """
    assert _WORKER_SPECIES is not None, "worker globals not initialized"
    return compute_transfer_function_at_k(
        _WORKER_SPECIES,
        float(k_mpc),
        config=_WORKER_CONFIG,
        bianchi_type=_WORKER_BIANCHI_TYPE,
    )


def compute_transfer_function_grid(
    species: "SpeciesBackgroundRegistry",
    k_grid_mpc: Sequence[float] | np.ndarray,
    *,
    config: FLRWPipelineConfig | None = None,
    bianchi_type: str = "I",
    n_workers: int | None = None,
) -> list[BianchiTransferFunctions]:
    """Parallel k-sweep: one Tier-B run per k, pooled via fork workers.

    Parameters
    ----------
    species
        Planck-2018 species registry (inherited to workers via fork).
    k_grid_mpc
        Array of comoving wavenumbers (Mpc⁻¹). Each entry triggers one
        ``execute_tier_b_solver`` run.
    config
        ``FLRWPipelineConfig``; defaults chosen for Planck-2018 FLRW.
    bianchi_type
        Defaults to "I" (FLRW). Non-Type-I families require the
        Round-3/4 kernel-pack wiring (not yet in the assembly path).
    n_workers
        Process count; default = ``os.cpu_count()`` capped at the
        k-grid length.

    Returns
    -------
    List of ``BianchiTransferFunctions``, one per k in order.

    Notes
    -----
    Falls back to sequential execution if ``n_workers == 1`` or if the
    k-grid has only one entry. Uses the default ``fork`` start method
    on Linux so species is inherited as COW memory; on other platforms
    a spawn fallback would need to rebuild species inside each worker
    (not implemented — Linux-only in the current runtime).
    """

    global _WORKER_SPECIES, _WORKER_CONFIG, _WORKER_BIANCHI_TYPE

    k_array = np.asarray(k_grid_mpc, dtype=np.float64).ravel()
    if k_array.size == 0:
        raise ValueError("k_grid_mpc must be non-empty")
    if np.any(k_array <= 0.0):
        raise ValueError("k_grid_mpc entries must all be positive")
    cfg = config or FLRWPipelineConfig()

    max_parallel = n_workers if n_workers is not None else os.cpu_count() or 1
    effective = max(1, min(int(max_parallel), int(k_array.size)))

    if effective == 1 or k_array.size == 1:
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
    with _cf.ProcessPoolExecutor(
        max_workers=effective,
        mp_context=ctx,
        initializer=_worker_init,
    ) as exe:
        results = list(exe.map(_worker_task, k_array.tolist()))

    # Clear worker globals after pool exits so parent memory doesn't
    # hold lingering references (small hygiene, no behaviour impact).
    _WORKER_SPECIES = None
    _WORKER_CONFIG = None
    _WORKER_BIANCHI_TYPE = "I"

    return results


# ------------------------------------------------------------------------
# C_ℓ / D_ℓ assembly wrappers
# ------------------------------------------------------------------------


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
