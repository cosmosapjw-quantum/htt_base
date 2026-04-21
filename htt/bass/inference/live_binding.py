"""Live BF-06 inference bindings over the completed BASS physics path."""
from __future__ import annotations

from dataclasses import dataclass
from math import atanh
from typing import Any

import numpy as np

from common.contracts import ArtifactManifest, ObservableVector, SkySupport, SolverCoreOutput

from bass.background.bianchi_types import get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.forward.ver2_solver_output import BassReleaseMetadata
from bass.hierarchy.integrator import IntegratorConfig
from bass.inference.drivers.emcee_driver import PosteriorSample, run_posterior
from bass.inference.priors import Prior, prior_observer_boost
from bass.likelihood.live_binding import (
    build_observer_frame_likelihood_from_solver_output,
)
from bass.observational import build_observable_vector_from_solver_output
from bass.observer.observer_boost import ObserverBoost
from bass.runtime import (
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
    execute_tier_b_solver,
)
from bass.spectrum import CutoffCampaignSpec
from bass.species.registry import SpeciesBackgroundRegistry

__all__ = [
    "LiveObserverBoostProblem",
    "build_live_observer_boost_problem",
    "build_type_i_native_validation_problem",
    "run_type_i_native_validation_posterior",
]


@dataclass(frozen=True)
class LiveObserverBoostProblem:
    """Bounded live posterior problem over the observer-boost vector."""

    solver_output: SolverCoreOutput
    observable_vector: ObservableVector
    priors: dict[str, Prior]
    likelihood: object
    dataset_kind: str

    def log_likelihood(self, theta: np.ndarray) -> float:
        vector = np.asarray(theta, dtype=float).reshape(-1)
        if vector.size != 3 or not np.all(np.isfinite(vector)):
            return float("-inf")
        beta = float(np.linalg.norm(vector))
        if beta >= 1.0:
            return float("-inf")
        if beta <= 1.0e-30:
            boost = ObserverBoost(rapidity=0.0)
        else:
            boost = ObserverBoost(
                rapidity=float(atanh(beta)),
                v_hat=tuple((vector / beta).tolist()),
            )
        return float(self.likelihood.log_prob({"observer_boost": boost}))


def _manifest(seed: int) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=f"bass.inference.type_i_native_validation.seed{int(seed)}",
        artifact_path="artifacts/bass/inference/type_i_native_validation.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="diagnostic_only",
        created_by="bass.inference.live_binding",
        git_commit="working-tree",
        config_hash=f"type-i-native-validation:{int(seed)}",
        input_hashes=[f"seed:{int(seed)}"],
        code_version="ver2-bf06",
        schema_version="ver2-v1",
        caveats=[
            "bounded_live_bass_inference_binding",
            "diagnostic_observer_boost_posterior_only",
            "not_model_selection_or_ht_owner_path",
        ],
    )


def _release(seed: int) -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="research_candidate",
        run_label=f"bf06-type-i-native-seed{int(seed)}",
        config_hash=f"type-i-native-validation:{int(seed)}",
        code_version="ver2-bf06",
        schema_version="ver2-v1",
        git_commit="working-tree",
        random_seed=int(seed),
    )


def _runtime_controls(seed: int) -> RuntimeControlBlock:
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
        random_seed=int(seed),
    )


def _feature_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.EXACT,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def _integrator_config() -> IntegratorConfig:
    return IntegratorConfig(
        L_max=4,
        eta_initial_mpc=0.5,
        eta_final_mpc=1.0,
        n_output=12,
        rtol=1.0e-6,
        atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(
            structure=get_type("I"),
            beta=0.0,
        ),
        gamma_T_over_H_threshold=100.0,
        gamma_T_override=lambda eta: 1.0e15,
    )


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="mock_calibrated",
        sky_support_hash="sky.type_i.native.inference.v1",
        mask_hash="mask.type_i.native.inference.v1",
        mock_coverage_status="adequate",
        scan_volume_hash="scan.type_i.native.inference.v1",
    )


def build_type_i_native_validation_problem(seed: int) -> LiveObserverBoostProblem:
    """Build the bounded BF-06 live inference problem from a native Type-I run."""
    species = SpeciesBackgroundRegistry.from_planck2018()
    run = execute_tier_b_solver(
        manifest=_manifest(seed),
        bianchi_type="I",
        species=species,
        integrator_config=_integrator_config(),
        runtime_controls=_runtime_controls(seed),
        feature_flags=_feature_flags(),
        release=_release(seed),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
        cutoff_spec=CutoffCampaignSpec(
            cutoffs=(4, 6),
            closure_name="tier_b_tca",
            baseline_cutoff=4,
        ),
    )
    observable = build_observable_vector_from_solver_output(
        run.solver_output,
        sky_support=_sky_support(),
    )
    likelihood = build_observer_frame_likelihood_from_solver_output(
        run.solver_output,
        tier="low_ell",
    )
    return LiveObserverBoostProblem(
        solver_output=run.solver_output,
        observable_vector=observable,
        priors={"observer_boost": prior_observer_boost()},
        likelihood=likelihood,
        dataset_kind="type_i_native_validation",
    )


def build_live_observer_boost_problem(
    *,
    solver_output: SolverCoreOutput,
    observable_vector: ObservableVector | None = None,
) -> LiveObserverBoostProblem:
    """Wrap an existing live BASS solver output as a posterior problem."""
    observable = (
        observable_vector
        if observable_vector is not None
        else build_observable_vector_from_solver_output(
            solver_output,
            sky_support=_sky_support(),
        )
    )
    return LiveObserverBoostProblem(
        solver_output=solver_output,
        observable_vector=observable,
        priors={"observer_boost": prior_observer_boost()},
        likelihood=build_observer_frame_likelihood_from_solver_output(solver_output),
        dataset_kind="solver_core_output_live",
    )


def run_type_i_native_validation_posterior(
    *,
    seed: int,
    n_walkers: int,
    n_steps: int,
    burnin: int,
    parallel: bool = False,
) -> tuple[LiveObserverBoostProblem, PosteriorSample]:
    """Run the bounded BF-06 live observer-boost posterior."""
    problem = build_type_i_native_validation_problem(int(seed))
    posterior = run_posterior(
        problem.log_likelihood,
        problem.priors,
        seed=int(seed),
        n_walkers=int(n_walkers),
        n_steps=int(n_steps),
        burnin=int(burnin),
        parallel=bool(parallel),
    )
    return problem, posterior
