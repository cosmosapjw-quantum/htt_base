"""End-to-end cosmological Tier-B smoke — chains Blockers 1+2+3.

Reproduces the commit ``bce0eb9`` manual validation:

    execute_tier_b_solver(FLRW, β=0, L_max=4, η=261 → 14147 Mpc,
                          Planck-2018 species)
    → SUCCESS in ~130 s, reaches η=14147 Mpc, finite state.

Uses the Blocker-3 ``build_cosmological_integrator_config`` helper so the
real-physics η anchors (``η(z_*) - 20 Mpc ≈ 261 Mpc``, ``η_today
≈ 14147 Mpc``) are extracted directly from the species registry rather
than hard-coded.

Purpose
-------
This script is a REPRODUCIBLE DIAGNOSTIC, not a unit test. The full
130 s cosmological IMEX run is too slow for CI; keeping it as a script
preserves the `bce0eb9` validation path for manual verification
(e.g. after kernel-pack wiring patches or closure-policy changes) while
not bloating the default `pytest` runtime.

Run
---
    venv/bin/python scripts/v5_tier_b_cosmological_smoke.py

Output
------
Timing, reached η_final, final-state sup-norms per channel, and a
PASS/FAIL summary. Exits with non-zero status on failure.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "htt" / "src"))
sys.path.insert(0, str(_REPO / "htt"))

import numpy as np


def build_bundle() -> dict[str, Any]:
    """Assemble all the Tier-B plumbing around the Blocker-3 config."""

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
    )
    from bass.species.registry import SpeciesBackgroundRegistry

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

    runtime_controls = RuntimeControlBlock(
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

    feature_flags = SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.APPROXIMATE,
        checkpoint_restart=FeatureStatus.DISABLED,
    )

    manifest = ArtifactManifest(
        artifact_id="bass.v5.blocker3.cosmological_smoke",
        artifact_path="artifacts/bass/v5_blocker3_cosmological_smoke.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="v5_tier_b_cosmological_smoke.py",
        git_commit="unknown",
        config_hash="v5-blocker3-smoke",
        input_hashes=["planck2018"],
        code_version="v5-runtime",
        schema_version="1.0.0",
        required_gates=["runtime"],
        passed_gates=["runtime"],
    )

    release = BassReleaseMetadata(
        release_stage="research_candidate",
        run_label="v5-blocker3-cosmological-smoke",
        config_hash="v5-blocker3-smoke",
        code_version="v5-runtime",
        schema_version="1.0.0",
        git_commit="unknown",
        random_seed=42,
    )

    return {
        "species": species,
        "integrator_config": integrator_config,
        "runtime_controls": runtime_controls,
        "feature_flags": feature_flags,
        "manifest": manifest,
        "release": release,
    }


def main() -> int:
    from bass.runtime import execute_tier_b_solver

    bundle = build_bundle()
    cfg = bundle["integrator_config"]

    print("V5 Blocker-1+2+3 end-to-end cosmological Tier-B smoke")
    print("=" * 68)
    print(
        f"η_initial = {cfg.eta_initial_mpc:.4f} Mpc  "
        f"(Blocker 3 from_recombination: η(z_*) − 20 Mpc)"
    )
    print(
        f"η_final   = {cfg.eta_final_mpc:.4f} Mpc  "
        f"(Blocker 3 from_recombination: η_today)"
    )
    print(
        f"L_max     = {cfg.L_max}  "
        f"(Blocker 1 multipole_cutoff validation)"
    )
    print(
        f"IMEX      = imex_split  "
        f"(Blocker 2 residual-joint operator stability)"
    )
    print(f"Bianchi   = FLRW (I), β = 0")
    print()

    t0 = time.monotonic()
    run = execute_tier_b_solver(
        manifest=bundle["manifest"],
        bianchi_type="I",
        species=bundle["species"],
        integrator_config=cfg,
        runtime_controls=bundle["runtime_controls"],
        feature_flags=bundle["feature_flags"],
        release=bundle["release"],
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )
    dt = time.monotonic() - t0

    eta_array = np.asarray(run.integration_result.eta, dtype=np.float64)
    eta_reached = float(eta_array[-1])
    eta_steps = len(eta_array)

    T_last = np.asarray(run.integration_result.photon_T_tower[-1], dtype=np.float64)
    E_last = np.asarray(run.integration_result.photon_E_tower[-1], dtype=np.float64)
    nu_last = np.asarray(run.integration_result.neutrino_tower[-1], dtype=np.float64)

    def sup_norm(a: np.ndarray) -> float:
        return float(np.max(np.abs(a))) if a.size else 0.0

    print("─" * 68)
    print("RESULT")
    print("─" * 68)
    print(f"  Integration time      : {dt:.2f} s")
    print(f"  η reached             : {eta_reached:.4f} Mpc")
    print(f"  η_final target        : {cfg.eta_final_mpc:.4f} Mpc")
    print(f"  Integration points    : {eta_steps}")
    print(f"  |T_tower(η_final)|_∞  : {sup_norm(T_last):.6e}")
    print(f"  |E_tower(η_final)|_∞  : {sup_norm(E_last):.6e}")
    print(f"  |ν_tower(η_final)|_∞  : {sup_norm(nu_last):.6e}")
    print()

    ok = True
    if not np.isclose(eta_reached, cfg.eta_final_mpc, rtol=1e-3):
        print(
            f"  ✗ FAIL: did not reach η_final "
            f"(reached {eta_reached:.3f}, target {cfg.eta_final_mpc:.3f})"
        )
        ok = False
    if not (np.all(np.isfinite(T_last)) and np.all(np.isfinite(E_last))):
        print("  ✗ FAIL: non-finite final state in T or E tower")
        ok = False
    if sup_norm(T_last) == 0.0:
        print("  ✗ FAIL: T_tower identically zero at η_final (no physics)")
        ok = False
    if sup_norm(T_last) > 1.0e6:
        print("  ✗ FAIL: T_tower sup-norm > 1e6 (numerical blow-up)")
        ok = False

    if ok:
        print("  ✓ PASS: Blocker-1+2+3 integration chain is operational.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
