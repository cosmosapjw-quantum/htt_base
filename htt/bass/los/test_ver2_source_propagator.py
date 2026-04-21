from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import get_type
from bass.los import (
    PropagatorMode,
    SourcePropagator,
    SourcePropagatorConfig,
    build_source_propagator,
)
from bass.los.ver2_source_propagator import build_source_propagator_stub
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


def test_live_propagator_builder_returns_ready_covariance_bundle() -> None:
    propagator = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.APPROXIMATE,
            polarization_rotation=FeatureStatus.APPROXIMATE,
        ),
        structure=get_type("VII_h"),
        eta_grid_mpc=np.linspace(0.0, 6.0, 7),
        k_grid_mpc=np.geomspace(1.0e-3, 5.0e-2, 6),
        ell_max=4,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=lambda eta, k: {
            "theta_0": float(np.cos(0.1 * k) * np.exp(-0.25 * (eta - 2.0) ** 2)),
            "pi_m0": float(np.sin(0.05 * k) * np.exp(-0.25 * (eta - 3.0) ** 2)),
            "pi_m_plus2": float(0.2 * np.exp(-0.5 * (eta - 3.5) ** 2)),
            "pi_m_minus2": float(-0.15 * np.exp(-0.5 * (eta - 3.5) ** 2)),
        },
    )
    assert isinstance(propagator, SourcePropagator)
    assert propagator.ready is True
    assert propagator.observer_neutral is True
    assert propagator.transfer_bundle["transfer_T"].shape == (6, 5, 3)
    assert propagator.covariance_bundle["off_diagonal_strategy"] == "m_decoupled_blocks"


def test_flrw_validation_builder_disables_mode_coupling_expectation() -> None:
    propagator = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.FLRW_VALIDATION,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            flrw_validation_only=True,
            kernel_family="flrw_scalar_validation",
        ),
        structure=get_type("I"),
        eta_grid_mpc=np.linspace(0.0, 4.0, 5),
        k_grid_mpc=np.geomspace(1.0e-3, 1.0e-2, 4),
        ell_max=3,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 2.0) ** 2)),
        source_builder=lambda eta, k: {
            "theta_0": float(np.exp(-0.25 * (eta - 2.0) ** 2)),
            "pi_m0": float(0.1 * np.cos(0.1 * k)),
        },
    )
    assert propagator.mode_coupling_expected is False
