"""CONTRACTS-01 — AtlasEntry schema tests (INDEPENDENT_TRACKS_PLAN v1.2 §11.1)."""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from workspace.contracts.atlas_entry import AtlasEntry


def _entry(**overrides):
    ell = np.arange(2, 11)
    base = dict(
        atlas_name="K_ell_v1",
        bianchi_type="I",
        parameter_point={"Sigma2": 1.2e-8, "beta": 1.334e-3},
        ell=ell,
        kernel_values=np.ones_like(ell, dtype=float),
        kernel_name="K_ell",
        generated_by="bass.atlas.builder v0.3",
        git_commit="abc123",
        config_hash="cfg1",
        entry_hash="h_0001",
        domain_caveats=("valid_below_ell_30",),
    )
    base.update(overrides)
    return AtlasEntry(**base)


def test_atlas_entry_readonly():
    e = _entry()
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.atlas_name = "K_ell_v2"  # type: ignore[misc]


def test_atlas_entry_shape_check():
    with pytest.raises(ValueError, match="kernel_values shape"):
        _entry(kernel_values=np.ones(3))


def test_atlas_entry_empty_hash_rejected():
    with pytest.raises(ValueError, match="entry_hash"):
        _entry(entry_hash="")


def test_atlas_entry_has_no_posterior_field():
    for f in dataclasses.fields(AtlasEntry):
        assert "posterior" not in f.name.lower(), (
            f"AtlasEntry must not expose a 'posterior' field "
            f"(found '{f.name}') — atlas lookup is interpolation, not inference."
        )
