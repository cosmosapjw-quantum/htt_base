from __future__ import annotations

import pytest

from bass.collision import (
    ElectronFrameThomsonContext,
    electron_frame_rate_factor,
    project_thomson_source_stub,
)
from bass.hierarchy import PhotonDirectionConvention


def test_electron_frame_rate_factor_uses_propagation_convention() -> None:
    rate = electron_frame_rate_factor(
        gamma_e=1.25,
        v_dot_direction=0.2,
        convention=PhotonDirectionConvention.PROPAGATION,
    )
    assert rate.factor == pytest.approx(1.25 * 0.8)


def test_electron_frame_rate_factor_uses_sky_convention() -> None:
    rate = electron_frame_rate_factor(
        gamma_e=1.25,
        v_dot_direction=0.2,
        convention=PhotonDirectionConvention.SKY,
    )
    assert rate.factor == pytest.approx(1.25 * 1.2)


def test_context_blocks_non_linear_scope() -> None:
    with pytest.raises(ValueError, match="classical linear Thomson"):
        ElectronFrameThomsonContext(operator_scope="nonlinear")


def test_projection_stub_stays_non_executable() -> None:
    result = project_thomson_source_stub(ElectronFrameThomsonContext())
    assert result.source_ready is False
    assert result.isotropic_null_mode_required is True
