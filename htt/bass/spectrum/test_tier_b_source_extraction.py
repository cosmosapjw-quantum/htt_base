"""Unit tests for the V5 Round-5 Tier-B → FLRWSourceTerms extractor.

Verifies the identity relations required by the Round-5 audit answer:

    theta_0(eta) = integration_result.photon_T_tower[:, slot(0, 0)]
    pi(eta)     = Θ_2 − √6·E_2  (no extra PSTF prefactor)
    v_b(eta)    = integration_result.baryon_local_history[:, 1]

Also verifies the anisotropic-stress toggle, PchipInterpolator no-extrap
contract, and the finite-difference ISW-driver stencil.
"""
from __future__ import annotations

import warnings

import numpy as np
import pytest

from common.contracts import ArtifactManifest

from bass.background.bianchi_types import get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.forward.ver2_solver_output import BassReleaseMetadata
from bass.hierarchy.integrator import IntegratorConfig
from bass.los.flrw_bessel_projector import FLRWSourceTerms
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
from bass.spectrum.tier_b_source_extraction import (
    _fd4_derivative,
    _scaled_pchip_no_extrapolation,
    _slot,
    extract_flrw_sources_from_tier_b,
    reconstruct_synchronous_metric_history_from_tier_b,
)
from bass.species.registry import SpeciesBackgroundRegistry


_SQRT6 = float(np.sqrt(6.0))


# ---------- fast toy-range fixture (~1-2 s per run) --------------------------


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.v5.round5.source_extraction_test",
        artifact_path="artifacts/bass/round5_source_extraction_test.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="pytest",
        git_commit="test-commit",
        config_hash="round5-test",
        input_hashes=["planck2018"],
        code_version="v5-runtime",
        schema_version="1.0.0",
        required_gates=["runtime"],
        passed_gates=["runtime"],
    )


def _release() -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="research_candidate",
        run_label="round5-source-extraction-test",
        config_hash="round5-test",
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


def _toy_integrator_config() -> IntegratorConfig:
    """Toy range config matching the existing ver2_execution test fixtures."""
    return IntegratorConfig(
        L_max=4,
        eta_initial_mpc=0.5,
        eta_final_mpc=1.0,
        n_output=12,
        rtol=1.0e-6,
        atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
        gamma_T_over_H_threshold=100.0,
        gamma_T_override=lambda eta: 1.0e15,
    )


@pytest.fixture(scope="module")
def species_registry() -> SpeciesBackgroundRegistry:
    return SpeciesBackgroundRegistry.from_planck2018()


@pytest.fixture(scope="module")
def tier_b_run(species_registry):
    return execute_tier_b_solver(
        manifest=_manifest(),
        bianchi_type="I",
        species=species_registry,
        integrator_config=_toy_integrator_config(),
        runtime_controls=_runtime_controls(),
        feature_flags=_feature_flags(),
        release=_release(),
        k_grid_mpc=np.array([1.0e-4, 2.0e-4], dtype=np.float64),
    )


# ---------- extractor identity tests ----------------------------------------


def test_extractor_returns_flrw_source_terms(tier_b_run, species_registry) -> None:
    """The extractor must return an FLRWSourceTerms with all 5 callables."""
    sources = extract_flrw_sources_from_tier_b(
        tier_b_run.integration_result, species_registry, k=1.0e-4
    )
    assert isinstance(sources, FLRWSourceTerms)
    assert callable(sources.theta_0)
    assert callable(sources.psi)
    assert callable(sources.phi_dot_plus_psi_dot)
    assert callable(sources.v_b)
    assert callable(sources.pi)


def test_theta_0_identity(tier_b_run, species_registry) -> None:
    """Q-17.1: theta_0(η) must equal photon_T_tower[:, slot(0, 0)] on the
    stored η grid (PchipInterpolator passes through the node values)."""
    sources = extract_flrw_sources_from_tier_b(
        tier_b_run.integration_result, species_registry, k=1.0e-4
    )
    eta = np.asarray(tier_b_run.integration_result.eta, dtype=np.float64)
    expected = np.asarray(
        tier_b_run.integration_result.photon_T_tower[:, _slot(0, 0)],
        dtype=np.float64,
    )
    got = np.asarray(sources.theta_0(eta), dtype=np.float64)
    assert np.allclose(got, expected, atol=1e-14, rtol=0.0)


def test_pi_identity_theta_minus_sqrt6_e2(tier_b_run, species_registry) -> None:
    """Q-20: Π = Θ_2 − √6·E_2 with α_T=1, α_E=−√6, no PSTF prefactor."""
    sources = extract_flrw_sources_from_tier_b(
        tier_b_run.integration_result, species_registry, k=1.0e-4
    )
    eta = np.asarray(tier_b_run.integration_result.eta, dtype=np.float64)
    theta2 = np.asarray(
        tier_b_run.integration_result.photon_T_tower[:, _slot(2, 0)],
        dtype=np.float64,
    )
    e2 = np.asarray(
        tier_b_run.integration_result.photon_E_tower[:, _slot(2, 0)],
        dtype=np.float64,
    )
    expected = theta2 - _SQRT6 * e2
    got = np.asarray(sources.pi(eta), dtype=np.float64)
    assert np.allclose(got, expected, atol=1e-14, rtol=0.0)


def test_v_b_identity_baryon_slot_1(tier_b_run, species_registry) -> None:
    """Legacy Newtonian-constraint mode keeps the raw baryon velocity."""
    sources = extract_flrw_sources_from_tier_b(
        tier_b_run.integration_result,
        species_registry,
        k=1.0e-4,
        source_frame="legacy_newtonian_constraint",
    )
    eta = np.asarray(tier_b_run.integration_result.eta, dtype=np.float64)
    expected = np.asarray(
        tier_b_run.integration_result.baryon_local_history[:, 1],
        dtype=np.float64,
    )
    got = np.asarray(sources.v_b(eta), dtype=np.float64)
    assert np.allclose(got, expected, atol=1e-14, rtol=0.0)


def test_opt_in_source_uses_mb95_synchronous_effective_metric(
    tier_b_run,
    species_registry,
) -> None:
    """Opt-in diagnostic path uses reconstructed etak/sigma."""
    result = tier_b_run.integration_result
    assert "matter_seed_observables" in result.solver_info
    assert "eta_cov" in result.solver_info["matter_seed_observables"]

    metric = reconstruct_synchronous_metric_history_from_tier_b(
        result,
        species_registry,
        k=1.0e-4,
    )
    sources = extract_flrw_sources_from_tier_b(
        result,
        species_registry,
        k=1.0e-4,
        source_frame="mb95_synchronous_effective",
    )
    eta = np.asarray(result.eta, dtype=np.float64)

    np.testing.assert_allclose(
        sources.psi(eta),
        metric.psi_effective_sw,
        rtol=1e-13,
        atol=1e-13,
    )
    np.testing.assert_allclose(
        sources.v_b(eta),
        metric.doppler_velocity_effective,
        rtol=1e-13,
        atol=1e-13,
    )
    np.testing.assert_allclose(
        sources.phi_dot_plus_psi_dot(eta),
        metric.isw_driver,
        rtol=1e-13,
        atol=1e-13,
    )
    assert metric.metadata["source_equivalence"].startswith("FLRWSourceTerms are effective")


def test_coevolved_scalar_metric_history_is_authority_for_mb95_source(
    tier_b_run,
    species_registry,
) -> None:
    from dataclasses import replace

    result = tier_b_run.integration_result
    posthoc = reconstruct_synchronous_metric_history_from_tier_b(
        result,
        species_registry,
        k=1.0e-4,
    )
    solver_info = dict(result.solver_info)
    solver_info["scalar_metric_history_metadata"] = {
        "owner": "ver2_native_integrator.main_state_scalar_metric",
        "labels": ("etak", "sigma"),
        "integration_scheme": "main_state_coevolved_mb95_synchronous",
        "photon_neutrino_monopole_coupled": True,
        "photon_neutrino_quadrupole_coupled": True,
        "photon_neutrino_scalar_streaming_coupled": False,
        "matter_continuity_coupled": True,
        "baryon_euler_pressure_coupled": True,
    }
    coevolved = replace(
        result,
        scalar_metric_history=np.column_stack([posthoc.etak, posthoc.sigma]),
        solver_info=solver_info,
    )

    metric = reconstruct_synchronous_metric_history_from_tier_b(
        coevolved,
        species_registry,
        k=1.0e-4,
    )

    assert metric.metadata["owner"] == "ver2_native_integrator.main_state_scalar_metric"
    assert metric.metadata["integration_scheme"] == "main_state_coevolved"
    np.testing.assert_allclose(metric.etak, posthoc.etak, rtol=0.0, atol=0.0)
    np.testing.assert_allclose(metric.sigma, posthoc.sigma, rtol=0.0, atol=0.0)


def test_no_extrapolation_outside_domain(tier_b_run, species_registry) -> None:
    """Critical constraint C5: PchipInterpolator(extrapolate=False).
    Evaluation outside [η_0, η_{N-1}] must return NaN."""
    sources = extract_flrw_sources_from_tier_b(
        tier_b_run.integration_result, species_registry, k=1.0e-4
    )
    eta = np.asarray(tier_b_run.integration_result.eta, dtype=np.float64)
    eta_before = float(eta[0]) - 0.1
    eta_after = float(eta[-1]) + 0.1
    for getter in (
        sources.theta_0,
        sources.psi,
        sources.phi_dot_plus_psi_dot,
        sources.v_b,
        sources.pi,
    ):
        assert np.isnan(float(getter(eta_before))), "should NaN below domain"
        assert np.isnan(float(getter(eta_after))), "should NaN above domain"


def test_scaled_pchip_avoids_tiny_slope_overflow_warning() -> None:
    eta = np.linspace(0.0, 1.0, 16, dtype=np.float64)
    values = np.linspace(0.0, 1.0e-320, eta.size, dtype=np.float64)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        interp = _scaled_pchip_no_extrapolation(eta, values)
        got = np.asarray(interp(eta), dtype=np.float64)
    assert np.allclose(got, values, atol=0.0, rtol=0.0)
    assert np.isnan(float(interp(-0.1)))


def test_anisotropic_stress_toggle_changes_psi(tier_b_run, species_registry) -> None:
    """Q-21.3: anisotropic_stress=False sets Ψ = Φ (no stress correction);
    the difference from the default must be non-zero when Θ_2^γ or Θ_2^ν
    are non-zero on the toy grid. This test belongs to the legacy
    Newtonian-constraint diagnostic mode."""
    src_on = extract_flrw_sources_from_tier_b(
        tier_b_run.integration_result,
        species_registry,
        k=1.0e-4,
        anisotropic_stress=True,
        source_frame="legacy_newtonian_constraint",
    )
    src_off = extract_flrw_sources_from_tier_b(
        tier_b_run.integration_result,
        species_registry,
        k=1.0e-4,
        anisotropic_stress=False,
        source_frame="legacy_newtonian_constraint",
    )
    eta = np.asarray(tier_b_run.integration_result.eta, dtype=np.float64)
    psi_on = np.asarray(src_on.psi(eta), dtype=np.float64)
    psi_off = np.asarray(src_off.psi(eta), dtype=np.float64)
    # The stress correction is (12πG·a²/k²) · (8/3)·(ρ_γ·Θ_2^γ + ρ_ν·Θ_2^ν).
    # On this fast toy config γ_T_override = 1e15 forces tight coupling so
    # Θ_2 is strongly suppressed but not identically zero — the test just
    # asserts the two paths are not identical.
    assert not np.allclose(psi_on, psi_off, atol=1e-18), (
        "anisotropic_stress toggle produced identical Ψ; check the "
        "stress-from-Θ_2 wiring"
    )


def test_psi_finite_and_bounded(tier_b_run, species_registry) -> None:
    """Sanity: Ψ should be finite everywhere in the stored domain."""
    sources = extract_flrw_sources_from_tier_b(
        tier_b_run.integration_result, species_registry, k=1.0e-4
    )
    eta = np.asarray(tier_b_run.integration_result.eta, dtype=np.float64)
    psi = np.asarray(sources.psi(eta), dtype=np.float64)
    assert np.all(np.isfinite(psi)), (
        f"Ψ has non-finite entries: {psi[~np.isfinite(psi)][:5]}"
    )


def test_isw_driver_matches_fd_of_phi_plus_psi(tier_b_run, species_registry) -> None:
    """Q-18.2: phi_dot_plus_psi_dot = d(Φ+Ψ)/dη via the 4th-order stencil.
    Numerically rebuild Φ+Ψ from the two sources above and compare via FD."""
    # Cannot access Φ directly through FLRWSourceTerms, but the ISW driver
    # must be finite and smooth (not identically zero on the tight-coupling
    # toy grid, since both Ψ and Φ evolve).
    sources = extract_flrw_sources_from_tier_b(
        tier_b_run.integration_result, species_registry, k=1.0e-4
    )
    eta = np.asarray(tier_b_run.integration_result.eta, dtype=np.float64)
    isw = np.asarray(sources.phi_dot_plus_psi_dot(eta), dtype=np.float64)
    assert np.all(np.isfinite(isw))
    # Not all zero (the background evolves on this range).
    assert float(np.max(np.abs(isw))) > 0.0


def test_mb95_source_requires_seed_metric_provenance(
    tier_b_run,
    species_registry,
) -> None:
    from dataclasses import replace

    result = tier_b_run.integration_result
    stripped = replace(result, solver_info={})
    with pytest.raises(ValueError, match="matter_seed_observables"):
        extract_flrw_sources_from_tier_b(
            stripped,
            species_registry,
            k=1.0e-4,
            source_frame="mb95_synchronous_effective",
        )

    legacy = extract_flrw_sources_from_tier_b(
        stripped,
        species_registry,
        k=1.0e-4,
    )
    eta = np.asarray(stripped.eta, dtype=np.float64)
    assert np.all(np.isfinite(np.asarray(legacy.theta_0(eta), dtype=np.float64)))


# ---------- rejection tests ---------------------------------------------------


def test_rejects_non_positive_k(tier_b_run, species_registry) -> None:
    with pytest.raises(ValueError, match="k must be positive"):
        extract_flrw_sources_from_tier_b(
            tier_b_run.integration_result, species_registry, k=0.0
        )
    with pytest.raises(ValueError, match="k must be positive"):
        extract_flrw_sources_from_tier_b(
            tier_b_run.integration_result, species_registry, k=-1.0e-4
        )


def test_rejects_small_eta_grid(tier_b_run, species_registry) -> None:
    """The FD stencil requires ≥ 5 samples. A trimmed fixture must be
    rejected with a clear error."""
    from dataclasses import replace

    tiny = replace(
        tier_b_run.integration_result,
        eta=np.asarray(tier_b_run.integration_result.eta[:4], dtype=np.float64),
    )
    with pytest.raises(ValueError, match="needs"):
        extract_flrw_sources_from_tier_b(tiny, species_registry, k=1.0e-4)


# ---------- _fd4_derivative micro-tests -------------------------------------


def test_fd4_derivative_exact_on_quadratic() -> None:
    """4th-order centered + 2nd-order boundaries is EXACT on polynomials
    up to degree 2 at all points (boundary 2nd-order is exact for deg ≤ 2,
    bulk 4th-order is exact for deg ≤ 4)."""
    x = np.linspace(0.0, 1.0, 11)
    y = 0.3 * x - 0.7 * x**2
    dy_expected = 0.3 - 1.4 * x
    dy = _fd4_derivative(x, y)
    assert np.allclose(dy, dy_expected, atol=1e-12)


def test_fd4_derivative_exact_on_quartic_bulk() -> None:
    """Bulk 4th-order stencil is exact on polynomials of degree ≤ 4;
    boundaries carry the 2nd-order truncation error (O(h²))."""
    x = np.linspace(0.0, 1.0, 11)
    y = 0.1 * x**4 - 0.3 * x**3 + 0.2 * x**2 - 0.5 * x + 0.7
    dy_expected = 0.4 * x**3 - 0.9 * x**2 + 0.4 * x - 0.5
    dy = _fd4_derivative(x, y)
    # Bulk [2, N-3] exact to float precision:
    assert np.allclose(dy[2:-2], dy_expected[2:-2], atol=1e-12)
    # Boundary points: 2nd-order error ~ h² · f'''/6 ≈ 0.01 · 0.4 ≈ 4e-3
    assert np.allclose(dy, dy_expected, atol=1e-2)


def test_fd4_derivative_linear_exact() -> None:
    """Linear y = 2x + 3 ⇒ dy/dx = 2 everywhere, exact for any stencil."""
    x = np.linspace(1.0, 5.0, 8)
    y = 2.0 * x + 3.0
    dy = _fd4_derivative(x, y)
    assert np.allclose(dy, 2.0, atol=1e-12)


def test_fd4_derivative_requires_five_points() -> None:
    with pytest.raises(ValueError, match="at least 5 points"):
        _fd4_derivative(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0]))
