"""S3 registry tests.

Every Bianchi family must have a kernel registered in
``KNOWN_FAMILIES``. Today only Type I carries real numerics; the other
ten raise ``FamilyBackendNotImplemented`` when invoked. Metadata must
match the frozen v5 registries in ``bass.los.family_backend_protocol``.
"""
from __future__ import annotations

import pytest
import numpy as np

from bass.background.bianchi_types import (
    flrw_constants,
    type_i_constants,
)
from bass.los.families import (
    IMPLEMENTED_FAMILIES,
    KNOWN_FAMILIES,
    LegacyDelegationKernel,
    NotImplementedKernel,
    SKELETON_FAMILIES,
    get_family_kernel,
    is_skeleton,
    register_all_defaults,
    unregister_all_defaults,
)
from bass.los.family_backend_protocol import (
    _CHART_DEFAULTS,
    _FAMILY_RESIDUALS,
    _MUST_NOT_DO,
)
from bass.transport.exact_transport import (
    ExactTransportBundle,
    FamilyBackendNotImplemented,
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    list_registered_families,
)

_EXPECTED_FAMILIES = (
    "I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX",
)


@pytest.fixture(autouse=True)
def _clean_dispatch():
    snapshot = dict(_TRANSPORT_DISPATCH)
    _TRANSPORT_DISPATCH.clear()
    yield
    _TRANSPORT_DISPATCH.clear()
    _TRANSPORT_DISPATCH.update(snapshot)


def test_known_families_covers_all_eleven():
    assert tuple(sorted(KNOWN_FAMILIES)) == tuple(sorted(_EXPECTED_FAMILIES))


def test_flrw_is_not_in_known_families():
    """FLRW is handled by the facade's early-return, not via a kernel."""
    assert "FLRW" not in KNOWN_FAMILIES


def test_known_families_metadata_matches_registry():
    for family, kernel in KNOWN_FAMILIES.items():
        assert kernel.family == family
        md = kernel.metadata
        assert md.family == family
        assert md.chart == _CHART_DEFAULTS[family]
        assert md.required_residuals == tuple(_FAMILY_RESIDUALS[family])
        assert md.forbidden_shortcuts == tuple(_MUST_NOT_DO[family])


def test_get_family_kernel_returns_singleton():
    a = get_family_kernel("I")
    b = get_family_kernel("I")
    assert a is b
    assert isinstance(a, LegacyDelegationKernel)


def test_get_family_kernel_rejects_unknown():
    with pytest.raises(KeyError, match="Unknown Bianchi family"):
        get_family_kernel("BOGUS")


# ---------------------------------------------------------------------------
# Skeleton behavior: 10 families raise FamilyBackendNotImplemented.
# ---------------------------------------------------------------------------


def test_skeleton_kernel_raises_when_invoked():
    """Contract check on ``NotImplementedKernel.build_transport_bundle``.

    Post-S5 there are no skeleton families left in ``KNOWN_FAMILIES``;
    exercise the base behavior via a synthetic subclass so the contract
    stays covered."""
    class _DummySkeleton(NotImplementedKernel):
        family = "II"
        deferred_to = "test-fixture"

    with pytest.raises(FamilyBackendNotImplemented, match="Family 'II'"):
        _DummySkeleton().build_transport_bundle()


@pytest.mark.parametrize("family", SKELETON_FAMILIES if SKELETON_FAMILIES else ["<no skeletons>"])
def test_skeleton_families_cover_their_label_sets(family):
    """Parametrized across any remaining skeleton families. Safe to run
    with a single placeholder when the list is empty."""
    if family == "<no skeletons>":
        pytest.skip("no skeleton families remain — all landed in S4/S5")
    kernel = get_family_kernel(family)
    assert is_skeleton(family)
    assert isinstance(kernel, NotImplementedKernel)
    with pytest.raises(FamilyBackendNotImplemented, match=f"Family '{family}'"):
        kernel.build_transport_bundle()


def test_skeleton_residual_pack_always_fails():
    """Guards ``NotImplementedKernel.residual_pack`` behavior.

    Once every family lands real numerics (post-S5) there is no skeleton
    kernel left in ``KNOWN_FAMILIES``. Instantiate a synthetic one so the
    behavior contract stays covered even at full-stack completion."""
    from bass.los.families import NotImplementedKernel

    class _DummySkeleton(NotImplementedKernel):
        family = "II"  # any real family — we only exercise the base class
        deferred_to = "test-fixture"

    pack = _DummySkeleton().residual_pack()
    assert pack.passed is False
    assert pack.metadata["status"] == "skeleton"


def test_implemented_and_skeleton_cover_all_families():
    assert set(IMPLEMENTED_FAMILIES) | set(SKELETON_FAMILIES) == set(KNOWN_FAMILIES)
    assert set(IMPLEMENTED_FAMILIES) & set(SKELETON_FAMILIES) == set()


# ---------------------------------------------------------------------------
# Type I reference numerics: bit-identical via dispatch.
# ---------------------------------------------------------------------------


def _build_bundle(structure):
    eta = np.linspace(40.0, 420.0, 65)
    k = np.array([0.05, 0.08, 0.12])
    def vis(eta_val):
        return float(np.exp(-0.5 * ((eta_val - 220.0) / 35.0) ** 2))
    def source(eta_val, k_val):
        env = float(np.exp(-0.5 * ((eta_val - 210.0) / 40.0) ** 2))
        return {
            "temperature": env * (1.0 + 0.1 * k_val),
            "temperature_anisotropy": 0.2 * env,
            "polarization": 0.35 * env,
            "b_mode": 0.0,
        }
    return build_exact_transport(
        structure,
        eta_grid_mpc=eta,
        k_grid_mpc=k,
        ell_max=6,
        visibility_fn=vis,
        source_builder=source,
    )


def test_type_i_kernel_matches_legacy_when_registered():
    structure = type_i_constants()
    legacy_bundle = _build_bundle(structure)
    assert legacy_bundle.dispatch_route == "lowell_los_legacy"

    register_all_defaults()
    routed_bundle = _build_bundle(structure)
    assert routed_bundle.dispatch_route == "family_kernel_legacy_delegation"

    # Type I via the kernel must be bit-identical to the legacy fallback.
    assert np.array_equal(routed_bundle.transfer_T, legacy_bundle.transfer_T)
    assert np.array_equal(routed_bundle.transfer_E, legacy_bundle.transfer_E)
    assert np.array_equal(routed_bundle.transfer_B, legacy_bundle.transfer_B)
    assert np.array_equal(
        routed_bundle.propagator_matrix, legacy_bundle.propagator_matrix
    )


def test_flrw_still_uses_legacy_even_with_all_defaults_registered():
    register_all_defaults()
    bundle = _build_bundle(flrw_constants())
    assert bundle.dispatch_route == "lowell_los_legacy"
    assert bundle.metadata["fallback_reason"] == "flrw_direct_legacy"


# ---------------------------------------------------------------------------
# Registration lifecycle
# ---------------------------------------------------------------------------


def test_register_all_defaults_then_unregister():
    assert list_registered_families() == ()
    registered = register_all_defaults()
    assert set(registered) == set(_EXPECTED_FAMILIES)
    assert set(list_registered_families()) == set(_EXPECTED_FAMILIES)

    unregister_all_defaults()
    assert list_registered_families() == ()


def test_register_all_defaults_is_idempotent():
    register_all_defaults()
    # second call must not raise
    register_all_defaults()
    assert set(list_registered_families()) == set(_EXPECTED_FAMILIES)


def test_bundle_is_correct_type_for_type_i():
    register_all_defaults()
    structure = type_i_constants()
    bundle = _build_bundle(structure)
    assert isinstance(bundle, ExactTransportBundle)
