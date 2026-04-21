from __future__ import annotations

import bass.collision as collision
import bass.hierarchy as hierarchy
import bass.likelihood as likelihood
import bass.los as los
import bass.observer as observer
import bass.recombination as recombination
import bass.transport as transport


def test_public_packages_do_not_reexport_stub_aliases() -> None:
    assert not hasattr(transport, "photon_geodesic_rhs_stub")
    assert not hasattr(collision, "project_thomson_source_stub")
    assert not hasattr(recombination, "build_tilted_visibility_source_stub")
    assert not hasattr(hierarchy, "build_constraint_projection_stub")
    assert not hasattr(hierarchy, "build_flrw_regular_seed_stub")
    assert not hasattr(hierarchy, "promote_tilted_seed_stub")
    assert not hasattr(hierarchy, "project_from_angular_samples_stub")
    assert not hasattr(hierarchy, "reconstruct_on_sphere_stub")
    assert not hasattr(los, "build_source_propagator_stub")


def test_public_packages_export_live_ver2_radiation_projection_helpers() -> None:
    assert hasattr(hierarchy, "project_from_angular_samples")
    assert hasattr(hierarchy, "reconstruct_on_sphere")


def test_observer_root_surface_is_production_only() -> None:
    assert hasattr(observer, "ObserverBoost")
    assert hasattr(observer, "apply_observer_boost")
    assert not hasattr(observer, "ObservedSpectrumDataset")
    assert not hasattr(observer, "likelihood_ratio")
    assert not hasattr(observer, "coverage_report")
    assert not hasattr(observer, "GlobalTiltState")
    assert not hasattr(observer, "compose_tilts")


def test_likelihood_root_surface_prefers_live_solver_output_bindings() -> None:
    assert hasattr(likelihood, "build_live_htt_decomposition_from_solver_output")
    assert hasattr(likelihood, "build_cosmological_frame_likelihood_from_solver_output")
    assert hasattr(likelihood, "build_observer_frame_likelihood_from_solver_output")
    assert not hasattr(likelihood, "build_htt_decomposition")
    assert not hasattr(likelihood, "CosmologicalFrameLikelihood")
    assert not hasattr(likelihood, "ObserverFrameLikelihood")
