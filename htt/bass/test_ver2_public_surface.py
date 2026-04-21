from __future__ import annotations

import bass.collision as collision
import bass.hierarchy as hierarchy
import bass.los as los
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
