from __future__ import annotations

import math

import pytest

from bass.closure import (
    TightCouplingStartupMetadata,
    quadrupole_startup_from_sources,
)


def test_startup_metadata_blocks_hidden_promotion() -> None:
    with pytest.raises(ValueError, match="closure promotion"):
        TightCouplingStartupMetadata(hidden_promotion_forbidden=False)


def test_quadrupole_startup_matches_subleading_se_limit() -> None:
    state = quadrupole_startup_from_sources(S_T=3.0, S_E=0.0, gamma_T=9.0)
    assert state.E_2 == pytest.approx(-(math.sqrt(6.0) / 4.0) * state.theta_2)
    assert state.combined_source_pi == pytest.approx(2.5 * state.theta_2)
    assert state.metadata.startup_scope == "approximate_startup_manifold_only"


def test_quadrupole_startup_requires_positive_gamma() -> None:
    with pytest.raises(ValueError, match="positive finite"):
        quadrupole_startup_from_sources(S_T=1.0, S_E=0.0, gamma_T=0.0)
