"""Tests for ``bass.transport.exact_transport`` (S2 skeleton).

Two invariants are protected here:

1. **Legacy-path bit-identity.** For any StructureConstants whose
   ``label`` is not in ``_TRANSPORT_DISPATCH``, calling
   ``build_exact_transport`` must produce the same transfer/propagator
   arrays as calling ``build_lowell_line_of_sight_propagator`` directly.
   This is the D_2 regression-anchor protection required by the S2 plan.

2. **Dispatch is registerable and error-safe.** A toy ``FamilyTransportKernel``
   can be registered, replaced-by-itself without error, refused when
   replaced by a different object, and reached through
   ``build_exact_transport``.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping

import numpy as np
import pytest

from bass.background.bianchi_types import (
    flrw_constants,
    type_i_constants,
    type_iv_constants,
    type_v_constants,
    type_vii0_constants,
    type_viih_constants,
    type_ix_constants,
)
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator
from bass.transport.exact_transport import (
    ExactTransportBundle,
    FamilyBackendNotImplemented,
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    list_registered_families,
    register_family_kernel,
)


ETA_GRID = np.linspace(40.0, 420.0, 65)
K_GRID = np.array([0.05, 0.08, 0.12], dtype=float)
ELL_MAX = 6


def _visibility(eta: float) -> float:
    return float(np.exp(-0.5 * ((eta - 220.0) / 35.0) ** 2))


def _source_builder(eta: float, k: float) -> dict[str, float]:
    envelope = float(np.exp(-0.5 * ((eta - 210.0) / 40.0) ** 2))
    return {
        "temperature": envelope * (1.0 + 0.1 * k),
        "temperature_anisotropy": 0.2 * envelope,
        "polarization": 0.35 * envelope,
        "b_mode": 0.0,
    }


def _call_facade(structure) -> ExactTransportBundle:
    return build_exact_transport(
        structure,
        eta_grid_mpc=ETA_GRID,
        k_grid_mpc=K_GRID,
        ell_max=ELL_MAX,
        visibility_fn=_visibility,
        source_builder=_source_builder,
    )


def _call_legacy(structure) -> dict:
    return build_lowell_line_of_sight_propagator(
        structure,
        eta_grid_mpc=ETA_GRID,
        k_grid_mpc=K_GRID,
        ell_max=ELL_MAX,
        visibility_fn=_visibility,
        source_builder=_source_builder,
    )


@pytest.fixture(autouse=True)
def _clean_dispatch():
    """Reset the dispatch registry around every test."""
    snapshot = dict(_TRANSPORT_DISPATCH)
    _TRANSPORT_DISPATCH.clear()
    yield
    _TRANSPORT_DISPATCH.clear()
    _TRANSPORT_DISPATCH.update(snapshot)


# ---------------------------------------------------------------------------
# Legacy-path bit-identity (the D_2 regression protection)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "factory",
    [
        flrw_constants,
        type_i_constants,
        type_iv_constants,
        type_v_constants,
        type_vii0_constants,
        type_viih_constants,
        type_ix_constants,
    ],
    ids=["FLRW", "I", "IV", "V", "VII_0", "VII_h", "IX"],
)
def test_legacy_path_bit_identical(factory):
    """Every unregistered family must produce the same arrays as the
    legacy direct call. Transfer arrays are compared with
    ``np.array_equal`` — bit-identity, not ``allclose``."""
    structure = factory()
    legacy = _call_legacy(structure)
    bundle = _call_facade(structure)

    assert bundle.dispatch_route == "lowell_los_legacy"
    assert bundle.family == structure.label
    assert np.array_equal(bundle.transfer_T, legacy["transfer_T"])
    assert np.array_equal(bundle.transfer_E, legacy["transfer_E"])
    assert np.array_equal(bundle.transfer_B, legacy["transfer_B"])
    assert np.array_equal(bundle.propagator_matrix, legacy["propagator_matrix"])


def test_legacy_as_payload_preserves_legacy_keys():
    structure = type_i_constants()
    legacy = _call_legacy(structure)
    bundle = _call_facade(structure)
    payload = bundle.as_payload()
    # Every legacy key must still be reachable.
    for legacy_key in legacy.keys():
        assert legacy_key in payload, f"legacy key '{legacy_key}' dropped by facade"
    # Array keys must be bit-identical.
    for key in ("transfer_T", "transfer_E", "transfer_B", "propagator_matrix"):
        assert np.array_equal(
            np.asarray(payload[key]), np.asarray(legacy[key])
        )


# ---------------------------------------------------------------------------
# FLRW early-return path
# ---------------------------------------------------------------------------


def test_flrw_never_consults_dispatch_table(monkeypatch):
    """Registering anything under FLRW must not divert the legacy path —
    FLRW is handled by the early-return clause in build_exact_transport."""
    called = {"fired": False}

    class _Fake:
        family = "FLRW"

        def build_transport_bundle(self, **_kwargs):
            called["fired"] = True
            raise AssertionError("FLRW should not reach dispatch")

    _TRANSPORT_DISPATCH["FLRW"] = _Fake()  # deliberately bypass register_family_kernel guard
    bundle = _call_facade(flrw_constants())
    assert called["fired"] is False
    assert bundle.dispatch_route == "lowell_los_legacy"
    assert bundle.metadata["fallback_reason"] == "flrw_direct_legacy"


# ---------------------------------------------------------------------------
# Registry behavior
# ---------------------------------------------------------------------------


class _TypeIIdentityKernel:
    """Reference-style kernel: delegates back to the legacy builder."""

    family = "I"

    def __init__(self):
        self.call_count = 0

    def build_transport_bundle(
        self,
        *,
        structure,
        eta_grid_mpc: np.ndarray,
        k_grid_mpc: np.ndarray,
        ell_max: int,
        visibility_fn: Callable[[float], float],
        source_builder: Callable[[float, float], Mapping[str, object]],
    ) -> ExactTransportBundle:
        self.call_count += 1
        legacy = build_lowell_line_of_sight_propagator(
            structure,
            eta_grid_mpc=eta_grid_mpc,
            k_grid_mpc=k_grid_mpc,
            ell_max=ell_max,
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
        return ExactTransportBundle(
            family="I",
            tier="A",
            dispatch_route="family_kernel",
            transfer_T=np.asarray(legacy["transfer_T"]),
            transfer_E=np.asarray(legacy["transfer_E"]),
            transfer_B=np.asarray(legacy["transfer_B"]),
            propagator_matrix=np.asarray(legacy["propagator_matrix"]),
            ell=np.arange(int(ell_max) + 1, dtype=int),
            k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
            eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
            metadata={"tier": "A", "dispatch_route": "family_kernel", "family_registered": True},
            raw_payload=legacy,
        )


def test_registered_kernel_is_invoked():
    kernel = _TypeIIdentityKernel()
    register_family_kernel(kernel)
    bundle = _call_facade(type_i_constants())
    assert kernel.call_count == 1
    assert bundle.dispatch_route == "family_kernel"


def test_registered_kernel_matches_legacy_numerics():
    """Sanity: the Type I reference kernel (wrapping the legacy builder)
    must produce the same transfer arrays."""
    legacy = _call_legacy(type_i_constants())
    register_family_kernel(_TypeIIdentityKernel())
    bundle = _call_facade(type_i_constants())
    assert np.array_equal(bundle.transfer_T, legacy["transfer_T"])
    assert np.array_equal(bundle.transfer_E, legacy["transfer_E"])
    assert np.array_equal(bundle.propagator_matrix, legacy["propagator_matrix"])


def test_register_rejects_replacement_with_different_object():
    a = _TypeIIdentityKernel()
    b = _TypeIIdentityKernel()
    register_family_kernel(a)
    with pytest.raises(RuntimeError, match="already registered for 'I'"):
        register_family_kernel(b)


def test_register_idempotent_for_same_object():
    kernel = _TypeIIdentityKernel()
    register_family_kernel(kernel)
    register_family_kernel(kernel)  # should not raise
    assert list_registered_families() == ("I",)


def test_register_requires_family_attribute():
    class _NoFamily:
        pass

    with pytest.raises(TypeError, match="non-empty 'family'"):
        register_family_kernel(_NoFamily())


def test_kernel_returning_wrong_type_raises():
    class _BadKernel:
        family = "I"

        def build_transport_bundle(self, **_kw):
            return {"not": "a bundle"}

    register_family_kernel(_BadKernel())
    with pytest.raises(TypeError, match="ExactTransportBundle"):
        _call_facade(type_i_constants())


# ---------------------------------------------------------------------------
# Error surface
# ---------------------------------------------------------------------------


def test_non_structure_input_rejected():
    with pytest.raises(TypeError, match="StructureConstants"):
        build_exact_transport(
            "not a structure",  # type: ignore[arg-type]
            eta_grid_mpc=ETA_GRID,
            k_grid_mpc=K_GRID,
            ell_max=ELL_MAX,
            visibility_fn=_visibility,
            source_builder=_source_builder,
        )


def test_family_backend_not_implemented_is_notimplementederror():
    assert issubclass(FamilyBackendNotImplemented, NotImplementedError)
