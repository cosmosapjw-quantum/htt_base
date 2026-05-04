"""Live BF-06 inference bindings over the completed BASS physics path."""
from __future__ import annotations

from dataclasses import dataclass
from math import atanh
from typing import Any, Mapping

import numpy as np

from common.contracts import ArtifactManifest, ObservableVector, SkySupport, SolverCoreOutput

from bass.background.bianchi_types import get_type
from bass.forward.ver3_output_archive import resolve_output_gate_registry
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
from bass.validation import GateDecision, hard_gate_before_fitting

__all__ = [
    "FittingBlockedError",
    "LiveObserverBoostProblem",
    "StatisticsReadinessDecision",
    "build_live_observer_boost_problem",
    "build_type_i_native_validation_problem",
    "run_type_i_native_validation_posterior",
    "statistics_readiness_decision",
]


class FittingBlockedError(RuntimeError):
    """Raised when a live posterior path is attempted without fitting readiness."""

    def __init__(
        self,
        *,
        gate_decision: GateDecision,
        covariance_readiness: str,
    ) -> None:
        self.gate_decision = gate_decision
        self.covariance_readiness = str(covariance_readiness)
        super().__init__(
            "live observer-boost posterior blocked: "
            f"covariance_readiness={self.covariance_readiness}, "
            f"missing_gates={list(self.gate_decision.missing_gates)}"
        )


@dataclass(frozen=True)
class StatisticsReadinessDecision:
    """Hard-gated decision for promoting live inference to fitting-ready."""

    allowed: bool
    gate_decision: GateDecision
    covariance_readiness: str
    observable_production_status: str
    checks: dict[str, bool]
    blockers: tuple[str, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "allowed": bool(self.allowed),
            "fitting_allowed": bool(self.allowed),
            "diagnostic_only": not bool(self.allowed),
            "covariance_readiness": self.covariance_readiness,
            "observable_production_status": self.observable_production_status,
            "checks": dict(self.checks),
            "blockers": list(self.blockers),
            "gate_decision": self.gate_decision.as_payload(),
        }


@dataclass(frozen=True)
class LiveObserverBoostProblem:
    """Bounded live posterior problem over the observer-boost vector."""

    solver_output: SolverCoreOutput
    observable_vector: ObservableVector
    priors: dict[str, Prior]
    likelihood: object
    dataset_kind: str
    gate_decision: GateDecision
    covariance_readiness: str
    fitting_ready: bool
    statistics_decision: StatisticsReadinessDecision

    def log_likelihood(self, theta: np.ndarray) -> float:
        if not self.fitting_ready:
            raise FittingBlockedError(
                gate_decision=self.gate_decision,
                covariance_readiness=self.covariance_readiness,
            )
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


def _covariance_readiness(observable_vector: ObservableVector) -> str:
    if observable_vector.covariance_features is None:
        return "missing"
    readiness = observable_vector.alm_features.get("covariance_readiness")
    if readiness is not None:
        return str(readiness)
    if bool(observable_vector.covariance_features.get("supports_full_biposh", False)):
        return "full"
    if bool(
        observable_vector.covariance_features.get(
            "supports_basis_reduced_morphology",
            False,
        )
    ):
        return "reduced"
    return "proxy"


def _gate_registry(
    solver_output: SolverCoreOutput,
    *,
    stochastic_alm_T: object | None = None,
    stochastic_alm_E: object | None = None,
    stochastic_alm_B: object | None = None,
    boost_alm_T: object | None = None,
    boost_alm_E: object | None = None,
    boost_alm_B: object | None = None,
) -> dict[str, object]:
    return resolve_output_gate_registry(
        solver_output,
        stochastic_alm_T=stochastic_alm_T,
        stochastic_alm_E=stochastic_alm_E,
        stochastic_alm_B=stochastic_alm_B,
        boost_alm_T=boost_alm_T,
        boost_alm_E=boost_alm_E,
        boost_alm_B=boost_alm_B,
    )


def _observable_harmonic_gaussian_ready(observable_vector: ObservableVector) -> bool:
    if bool(observable_vector.alm_features.get("harmonic_gaussian_ready", False)):
        return True
    features = observable_vector.covariance_features
    return bool(
        features is not None
        and features.get("supports_harmonic_gaussian", False)
        and isinstance(features.get("harmonic_gaussian_covariance"), Mapping)
    )


def statistics_readiness_decision(
    *,
    solver_output: SolverCoreOutput,
    observable_vector: ObservableVector,
    gate_registry: Mapping[str, object] | None = None,
    stochastic_alm_T: object | None = None,
    stochastic_alm_E: object | None = None,
    stochastic_alm_B: object | None = None,
    boost_alm_T: object | None = None,
    boost_alm_E: object | None = None,
    boost_alm_B: object | None = None,
) -> StatisticsReadinessDecision:
    """Return the live-inference fitting decision with all blocking evidence."""

    covariance_readiness = _covariance_readiness(observable_vector)
    resolved_gate_registry = (
        dict(gate_registry)
        if gate_registry is not None
        else _gate_registry(
            solver_output,
            stochastic_alm_T=stochastic_alm_T,
            stochastic_alm_E=stochastic_alm_E,
            stochastic_alm_B=stochastic_alm_B,
            boost_alm_T=boost_alm_T,
            boost_alm_E=boost_alm_E,
            boost_alm_B=boost_alm_B,
        )
    )
    gate_decision = hard_gate_before_fitting(
        resolved_gate_registry,
        residuals={
            "offdiag_strength": None
            if observable_vector.covariance_features is None
            else observable_vector.covariance_features.get("offdiag_strength"),
            "rotation_strength": None
            if observable_vector.covariance_features is None
            else observable_vector.covariance_features.get("rotation_strength"),
        },
        metadata={
            "solver_output_ref": solver_output.manifest.artifact_id,
            "observable_vector_ref": observable_vector.manifest.artifact_id,
            "covariance_readiness": covariance_readiness,
            "observable_production_status": observable_vector.manifest.production_status,
        },
    )
    sky_support = observable_vector.sky_support
    checks = {
        "gate_allowed": bool(gate_decision.allowed),
        "covariance_full": covariance_readiness == "full",
        "observable_production_candidate": (
            observable_vector.manifest.production_status == "production_candidate"
        ),
        "observable_declares_fitting_ready": bool(
            observable_vector.alm_features.get("fitting_ready", False)
        ),
        "harmonic_gaussian_ready": _observable_harmonic_gaussian_ready(
            observable_vector
        ),
        "sky_support_mock_calibrated": (
            sky_support.selection_mode == "mock_calibrated"
            and sky_support.mock_coverage_status == "adequate"
        ),
        "local_boost_is_output_only": (
            observable_vector.alm_features.get("local_boost_contract")
            == "observer_side_only_not_applied_in_bass_output"
        ),
        "tilt_boost_separated": (
            observable_vector.alm_features.get("tilt_boost_separation")
            == "explicit_nonmerged"
        ),
        "inference_owner_wraps_diagnostic_likelihood": True,
    }
    blockers = tuple(key for key, passed in checks.items() if not passed)
    return StatisticsReadinessDecision(
        allowed=not blockers,
        gate_decision=gate_decision,
        covariance_readiness=covariance_readiness,
        observable_production_status=observable_vector.manifest.production_status,
        checks=checks,
        blockers=blockers,
    )


def _fitting_decision(
    *,
    solver_output: SolverCoreOutput,
    observable_vector: ObservableVector,
    stochastic_alm_T: object | None = None,
    stochastic_alm_E: object | None = None,
    stochastic_alm_B: object | None = None,
    boost_alm_T: object | None = None,
    boost_alm_E: object | None = None,
    boost_alm_B: object | None = None,
) -> tuple[GateDecision, str, bool, StatisticsReadinessDecision]:
    resolved_gate_registry = _gate_registry(
        solver_output,
        stochastic_alm_T=stochastic_alm_T,
        stochastic_alm_E=stochastic_alm_E,
        stochastic_alm_B=stochastic_alm_B,
        boost_alm_T=boost_alm_T,
        boost_alm_E=boost_alm_E,
        boost_alm_B=boost_alm_B,
    )
    statistics_decision = statistics_readiness_decision(
        solver_output=solver_output,
        observable_vector=observable_vector,
        gate_registry=resolved_gate_registry,
    )
    gate_decision = statistics_decision.gate_decision
    covariance_readiness = statistics_decision.covariance_readiness
    fitting_ready = bool(statistics_decision.allowed)
    solver_output.metadata["fitting_gate_enforced"] = True
    solver_output.metadata["fitting_gate_allowed"] = fitting_ready
    solver_output.metadata["fitting_allowed"] = fitting_ready
    solver_output.metadata["diagnostic_only"] = not fitting_ready
    solver_output.metadata["fitting_block_reason"] = (
        None
        if fitting_ready
        else (
            ";".join(statistics_decision.blockers)
            if statistics_decision.blockers
            else gate_decision.reason
        )
    )
    solver_output.metadata["missing_gates"] = gate_decision.missing_gates
    solver_output.metadata["covariance_readiness"] = covariance_readiness
    solver_output.metadata["gate_registry"] = resolved_gate_registry
    solver_output.metadata["fitting_gate_decision"] = gate_decision.as_payload()
    solver_output.metadata[
        "statistics_readiness_decision"
    ] = statistics_decision.as_payload()
    solver_output.metadata["statistics_claim_allowed"] = fitting_ready
    solver_output.metadata["statistics_owner"] = "bass.inference.live_binding"
    solver_output.metadata[
        "likelihood_binding_scope"
    ] = "direct_likelihood_is_diagnostic_wrapped_by_inference_gate"
    return gate_decision, covariance_readiness, fitting_ready, statistics_decision


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
    (
        gate_decision,
        covariance_readiness,
        fitting_ready,
        statistics_decision,
    ) = _fitting_decision(
        solver_output=run.solver_output,
        observable_vector=observable,
    )
    return LiveObserverBoostProblem(
        solver_output=run.solver_output,
        observable_vector=observable,
        priors={"observer_boost": prior_observer_boost()},
        likelihood=likelihood,
        dataset_kind="type_i_native_validation",
        gate_decision=gate_decision,
        covariance_readiness=covariance_readiness,
        fitting_ready=fitting_ready,
        statistics_decision=statistics_decision,
    )


def build_live_observer_boost_problem(
    *,
    solver_output: SolverCoreOutput,
    observable_vector: ObservableVector | None = None,
    stochastic_alm_T: object | None = None,
    stochastic_alm_E: object | None = None,
    stochastic_alm_B: object | None = None,
    boost_alm_T: object | None = None,
    boost_alm_E: object | None = None,
    boost_alm_B: object | None = None,
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
    (
        gate_decision,
        covariance_readiness,
        fitting_ready,
        statistics_decision,
    ) = _fitting_decision(
        solver_output=solver_output,
        observable_vector=observable,
        stochastic_alm_T=stochastic_alm_T,
        stochastic_alm_E=stochastic_alm_E,
        stochastic_alm_B=stochastic_alm_B,
        boost_alm_T=boost_alm_T,
        boost_alm_E=boost_alm_E,
        boost_alm_B=boost_alm_B,
    )
    return LiveObserverBoostProblem(
        solver_output=solver_output,
        observable_vector=observable,
        priors={"observer_boost": prior_observer_boost()},
        likelihood=build_observer_frame_likelihood_from_solver_output(solver_output),
        dataset_kind="solver_core_output_live",
        gate_decision=gate_decision,
        covariance_readiness=covariance_readiness,
        fitting_ready=fitting_ready,
        statistics_decision=statistics_decision,
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
    if not problem.fitting_ready:
        raise FittingBlockedError(
            gate_decision=problem.gate_decision,
            covariance_readiness=problem.covariance_readiness,
        )
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
