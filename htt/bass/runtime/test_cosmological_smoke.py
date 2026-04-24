"""End-to-end cosmological Tier-B smoke test (opt-in via pytest -m slow).

Chains the three closed V5 runtime blockers in a single CI-gated test:

- Blocker 1 (commit bce0eb9): multipole_cutoff accepts L_max ∈ {4,6,8,12,16,...}.
- Blocker 2 (commit bce0eb9): residual-joint IMEX stable over the cosmological
  η-range after eight operator patches (Rounds 1+2 algebraic audit).
- Blocker 3 (commit e78e012): build_cosmological_integrator_config supplies
  real-physics eta_initial = η(z_*) − 20 Mpc from the species registry.

The standalone script version is kept at ``scripts/v5_tier_b_cosmological_smoke.py``
for manual reproducibility; this test calls the same ``execute_tier_b_solver``
with the same construction and asserts the same success conditions.

Marked ``slow`` (takes ~45 s at L_max=4); deselected by default pytest runs
to preserve the 1378 fast-baseline timing. Run with::

    venv/bin/python -m pytest -m slow htt/bass/runtime/test_cosmological_smoke.py

Rationale: the fast 1378 baseline uses ``eta_initial_mpc = 0.5`` toy fixtures;
this test is the only CI-resident path that exercises the full cosmological
η-range post-Round-2 operator patches.
"""
from __future__ import annotations

import time

import numpy as np
import pytest

from common.contracts import ArtifactManifest

from bass.background.bianchi_types import get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.forward.ver2_solver_output import BassReleaseMetadata
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
from bass.species.registry import SpeciesBackgroundRegistry


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.v5.blocker_1_2_3.cosmological_smoke",
        artifact_path="artifacts/bass/v5_cosmological_smoke.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="pytest",
        git_commit="test-commit",
        config_hash="v5-cosmological-smoke",
        input_hashes=["planck2018-species"],
        code_version="v5-runtime",
        schema_version="1.0.0",
        required_gates=["runtime"],
        passed_gates=["runtime"],
    )


def _release() -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="research_candidate",
        run_label="v5-cosmological-smoke",
        config_hash="v5-cosmological-smoke",
        code_version="v5-runtime",
        schema_version="1.0.0",
        git_commit="test-commit",
        random_seed=42,
    )


def _runtime_controls() -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=SolverTier.TIER_B_PSTF,
        integrator_family=IntegratorFamily.IMEX_SPLIT,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=4,
        rtol=1.0e-6,
        atol=1.0e-9,
        checkpoint=CheckpointPolicy(enabled=False),
        constraint_projection=ConstraintProjectionPolicy(
            enabled=True,
            every_n_steps=4,
            status=FeatureStatus.APPROXIMATE,
        ),
        random_seed=42,
    )


def _feature_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.APPROXIMATE,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


@pytest.mark.slow
def test_cosmological_smoke_chains_blocker_1_2_3() -> None:
    """Full Type-I cosmological run: η ≈ 260 → 14147 Mpc, L_max=4.

    Asserts:
      1. Blocker 3: eta_initial comes from real Planck-2018 recombination
         (260 ≤ eta_initial ≤ 270 Mpc, i.e. η_* ≈ 281 Mpc minus 20 Mpc margin).
      2. Blocker 3: eta_final is the canonical η_today (~14147 Mpc).
      3. Blocker 1: L_max=4 is accepted without diagnostic override.
      4. Blocker 2: IMEX completes over the full cosmological η-range,
         reaches eta_final to within float precision.
      5. Final tower state is finite and physically bounded.
      6. Runtime stays below 180 s budget (typical 43 s at L_max=4).
    """

    species = SpeciesBackgroundRegistry.from_planck2018()
    integrator_config = build_cosmological_integrator_config(
        species,
        L_max=4,
        n_output=64,
        rtol=1.0e-6,
        atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
        gamma_T_over_H_threshold=100.0,
    )

    assert 260.0 <= integrator_config.eta_initial_mpc <= 270.0, (
        f"Blocker 3: eta_initial={integrator_config.eta_initial_mpc:.3f} Mpc "
        f"outside the 260-270 Mpc band (expected η_* - 20 Mpc, "
        f"η_* ∈ [270, 290])"
    )
    assert 14000.0 <= integrator_config.eta_final_mpc <= 14300.0, (
        f"Blocker 3: eta_final={integrator_config.eta_final_mpc:.3f} Mpc "
        f"outside the Planck-2018 eta_today band"
    )

    t0 = time.monotonic()
    run = execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type="I",
        species=species,
        integrator_config=integrator_config,
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )
    dt = time.monotonic() - t0

    eta_array = np.asarray(run.integration_result.eta, dtype=np.float64)
    eta_reached = float(eta_array[-1])
    T_last = np.asarray(
        run.integration_result.photon_T_tower[-1], dtype=np.float64
    )
    E_last = np.asarray(
        run.integration_result.photon_E_tower[-1], dtype=np.float64
    )

    assert eta_reached == pytest.approx(integrator_config.eta_final_mpc, rel=1.0e-9), (
        f"Blocker 2: IMEX did not reach eta_final; reached "
        f"{eta_reached:.4f} Mpc, target {integrator_config.eta_final_mpc:.4f} Mpc"
    )
    assert np.all(np.isfinite(T_last)), (
        "Final photon_T_tower contains non-finite entries"
    )
    assert np.all(np.isfinite(E_last)), (
        "Final photon_E_tower contains non-finite entries"
    )
    assert float(np.max(np.abs(T_last))) > 0.0, (
        "Final photon_T_tower is identically zero (no physics)"
    )
    assert float(np.max(np.abs(T_last))) < 1.0e6, (
        f"Final photon_T_tower blow-up: "
        f"|T|_∞ = {float(np.max(np.abs(T_last))):.3e}"
    )
    assert dt < 180.0, (
        f"Cosmological smoke took {dt:.1f} s (expected ~45 s at L_max=4); "
        f"runtime regression suspected"
    )
