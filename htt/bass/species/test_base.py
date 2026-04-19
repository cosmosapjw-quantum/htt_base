"""Tests for bass/species/base.py (LB-1) — SpeciesSnapshot, ABC contract.

Focuses on the ABC-level guarantees (canonical ordering, snapshot
container) and the shape-broadcasting contract (§3.2 of the spec).
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.species.background_table import build_flrw_background_table
from bass.species.base import (
    CANONICAL_ORDER, SpeciesLabel, SpeciesSnapshot,
)
from bass.species.constants import default_constants
from bass.species.photon import PhotonBackground


@pytest.fixture(scope="module")
def bg():
    return build_flrw_background_table()


@pytest.fixture(scope="module")
def photon(bg):
    c = default_constants()
    return PhotonBackground(bg, c.Omega_gamma_0)


def test_canonical_order_length_and_members():
    """CANONICAL_ORDER has exactly the five LB-1 species in spec order."""
    assert len(CANONICAL_ORDER) == 5
    assert CANONICAL_ORDER == (
        SpeciesLabel.PHOTON,
        SpeciesLabel.NEUTRINO,
        SpeciesLabel.BARYON,
        SpeciesLabel.CDM,
        SpeciesLabel.LAMBDA,
    )


def test_species_label_values():
    """Label values match the Unicode symbols in 00_conventions.md §6."""
    assert SpeciesLabel.PHOTON.value == "γ"
    assert SpeciesLabel.NEUTRINO.value == "ν"
    assert SpeciesLabel.BARYON.value == "b"
    assert SpeciesLabel.CDM.value == "c"
    assert SpeciesLabel.LAMBDA.value == "Λ"


def test_species_snapshot_is_frozen():
    """SpeciesSnapshot is immutable (frozen dataclass)."""
    s = SpeciesSnapshot(eta=0.0, a=1.0, rho=5e-5, p=0.0, T=None, w=0.0)
    with pytest.raises((AttributeError, Exception)):
        s.rho = 1.0  # type: ignore[misc]


def test_snapshot_returns_valid_state(bg, photon):
    """snapshot() yields a coherent dataclass for one η."""
    eta_today = bg.eta_today
    snap = photon.snapshot(eta_today)
    assert isinstance(snap, SpeciesSnapshot)
    assert snap.eta == pytest.approx(eta_today, rel=1e-12)
    assert snap.a == pytest.approx(1.0, abs=1e-12)
    c = default_constants()
    assert snap.rho == pytest.approx(c.Omega_gamma_0, rel=1e-10)
    assert snap.p == pytest.approx(c.Omega_gamma_0 / 3.0, rel=1e-10)
    assert snap.T == pytest.approx(c.T_gamma_0_K, rel=1e-10)
    assert snap.w == pytest.approx(1.0 / 3.0, rel=1e-12)


def test_scalar_vs_array_broadcasting_contract(bg, photon):
    """Scalar in → scalar out; array in → array out with matching shape."""
    # Scalar input → Python float (where interp produces one).
    r = photon.rho_rest(float(bg.eta_today))
    assert isinstance(r, float)

    # 1-D array input → ndarray with same shape.
    eta_arr = np.linspace(bg.eta_min, bg.eta_today, 5)[1:]
    r_arr = photon.rho_rest(eta_arr)
    assert isinstance(r_arr, np.ndarray)
    assert r_arr.shape == eta_arr.shape
    assert r_arr.dtype == np.float64


def test_w_handles_zero_rho_gracefully(bg):
    """``w`` defined as 0 where ρ=0 — no 0/0 NaN.

    The photon fluid is always positive on our η-grid, so construct a
    minimal custom species that can be queried at ρ=0 to exercise the
    branch.
    """
    from bass.species.base import SpeciesBackground

    class ZeroSpecies(SpeciesBackground):
        label = SpeciesLabel.CDM  # arbitrary

        def __init__(self, bg):
            self._bg = bg

        def _a_of_eta(self, eta):
            return self._bg.interp_a(eta)

        def rho_rest(self, eta):
            return np.zeros_like(np.atleast_1d(np.asarray(eta, float)))

        def p_rest(self, eta):
            return np.zeros_like(np.atleast_1d(np.asarray(eta, float)))

        def dot_rho(self, eta):
            return np.zeros_like(np.atleast_1d(np.asarray(eta, float)))

    s = ZeroSpecies(bg)
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 10)[1:]
    w = s.w(eta_sample)
    assert np.all(w == 0.0)
    assert not np.any(np.isnan(w))
