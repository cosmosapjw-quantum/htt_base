from __future__ import annotations

import pytest


def test_normal_frame_identity_forbids_vorticity_term():
    from bass.hierarchy.frame_contracts import FrameIdentityScope

    normal = FrameIdentityScope.normal_frame_slicing()
    assert normal.vorticity_term_allowed is False
    assert normal.geometry_ricci_substitution_allowed is True


def test_threading_identity_blocks_without_full_boost_terms():
    from bass.hierarchy.frame_contracts import FrameIdentityScope

    threading = FrameIdentityScope.threading_candidate(full_boost_terms_bound=False)
    assert threading.claim_tier == "blocked"
    assert "full_boost_terms_missing" in threading.blocked_reasons


def test_threading_identity_unblocks_only_when_all_terms_bound():
    from bass.hierarchy.frame_contracts import FrameIdentityScope

    threading = FrameIdentityScope.threading_candidate(
        full_boost_terms_bound=True,
        flux_terms_bound=True,
        anisotropic_stress_terms_bound=True,
        constraint_terms_bound=True,
    )
    assert threading.claim_tier == "conditional"
    assert threading.vorticity_term_allowed is True
    assert threading.blocked_reasons == ()


def test_constraints_reject_vorticity_in_normal_frame():
    from bass.background.constraints import assert_vorticity_consistent_with_frame
    from bass.hierarchy.frame_contracts import FrameIdentityScope

    normal = FrameIdentityScope.normal_frame_slicing()
    # zero vorticity is admissible under hypersurface-normal slicing
    assert_vorticity_consistent_with_frame(normal, vorticity_norm=0.0)
    with pytest.raises(ValueError, match="W_std=0"):
        assert_vorticity_consistent_with_frame(normal, vorticity_norm=1.0e-3)
