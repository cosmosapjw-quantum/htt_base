from __future__ import annotations

import pytest

from bass.los import (
    PropagatorMode,
    SourcePropagatorConfig,
    build_source_propagator_stub,
)
from bass.runtime import FeatureStatus


def test_flrw_validation_mode_requires_explicit_validation_flag() -> None:
    with pytest.raises(ValueError, match="flrw_validation_only"):
        SourcePropagatorConfig(
            mode=PropagatorMode.FLRW_VALIDATION,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="flrw_scalar_validation",
        )


def test_production_modes_forbid_flrw_validation_kernel() -> None:
    with pytest.raises(ValueError, match="FLRW scalar kernels"):
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.APPROXIMATE,
            polarization_rotation=FeatureStatus.APPROXIMATE,
            flrw_validation_only=True,
        )


def test_propagator_stub_is_observer_neutral_and_mode_coupled() -> None:
    stub = build_source_propagator_stub(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.APPROXIMATE,
            polarization_rotation=FeatureStatus.APPROXIMATE,
        )
    )
    assert stub.ready is False
    assert stub.observer_neutral is True
    assert stub.mode_coupling_expected is True
