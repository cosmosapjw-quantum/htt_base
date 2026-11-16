"""Focused source/cache integrity tests plus opt-in execution on committed data."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


def runner():
    path = Path(__file__).resolve().parents[2] / "scripts/r58/run_r58_owned_tensor.py"
    spec = importlib.util.spec_from_file_location("r58_owned_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_changed_frozen_input_stops_before_data_analysis(tmp_path, monkeypatch):
    run = runner()
    p = tmp_path / "source.bin"
    p.write_bytes(b"old")
    monkeypatch.setattr(run, "PINS", {"source.bin": hashlib.sha256(b"old").hexdigest()})
    monkeypatch.setattr(run, "import_modules", lambda *a: (None, None, None, None))
    p.write_bytes(b"changed")
    with pytest.raises(ValueError, match="frozen dependency changed: source.bin"):
        run.compute(tmp_path, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def cache_fixture(tmp_path, *, labels=("probe:0", "probe:1"), model_key="fixed"):
    p = tmp_path / "body.npz"
    np.savez(p, labels=np.array(labels), n_rows=2, cosmic_linear=np.eye(2),
             operator_fingerprint=np.array("historical-floating-bytes"), model_key=np.array(model_key))
    return p


def fake_cf(tmp_path):
    return SimpleNamespace(ROOT=tmp_path, model_key=lambda *a: "fixed", operator_fingerprint=lambda *a: "current-floating-bytes")


def test_label_permutation_cannot_rebind_cached_covariance(tmp_path):
    run = runner()
    p = cache_fixture(tmp_path, labels=("probe:1", "probe:0"))
    before = p.read_bytes()
    with pytest.raises(ValueError, match="labels or row count differ"):
        run.cached_rows(p, {"probe": np.eye(2)}, np.ones(2), fake_cf(tmp_path), np.zeros((2, 3)), np.ones(2))
    assert p.read_bytes() == before


def test_changed_cosmic_model_cannot_use_roundoff_exception(tmp_path):
    run = runner()
    p = cache_fixture(tmp_path, model_key="other-physics")
    before = p.read_bytes()
    with pytest.raises(ValueError, match="model key differs"):
        run.cached_rows(p, {"probe": np.eye(2)}, np.ones(2), fake_cf(tmp_path), np.zeros((2, 3)), np.ones(2))
    assert p.read_bytes() == before


def test_byte_mismatch_is_explicit_numerical_reuse_never_cache_rewrite(tmp_path):
    run = runner()
    p = cache_fixture(tmp_path)
    before = p.read_bytes()
    body, layout, receipt = run.cached_rows(p, {"probe": np.eye(2)}, np.ones(2), fake_cf(tmp_path), np.zeros((2, 3)), np.ones(2))
    assert receipt["exact_operator_bytes"] is False
    assert receipt["model_key_equal"] is True
    assert "mandatory seven-model numerical parity" in receipt["reuse_policy"]
    np.testing.assert_array_equal(body, np.eye(2))
    assert layout["probe"] == slice(0, 2)
    assert p.read_bytes() == before


@pytest.mark.skipif(os.environ.get("R58_OWNED_DATA") != "1", reason="opt-in committed 35970-group numerical reproduction")
def test_existing_data_reanalysis_reproduces_frozen_marginals_and_mixed_covariance(tmp_path):
    run = runner()
    root = Path(__file__).resolve().parents[2]
    res = run.compute(root, tmp_path)
    assert res["n_groups"] == 35970
    assert res["n_models"] == 7
    assert max(max(x.values()) for x in res["reproduction"].values()) < 2e-7
    assert all(v["fit"]["rank"] == 11 for v in res["variants"].values())
    assert all(v["canonical_correlations"][0] > 0.79 for v in res["variants"].values())
    # Fixed-design inference separates a joint target from arbitrary component
    # thresholds, while the observational interpretation remains conditional.
    assert 0.01 < res["robust"]["max_wald_p_common_theta_zero"] < 0.03
    assert res["robust"]["max_null_p"] > 0.1
    assert all(v["lower"] < 0 < v["upper"] for v in res["robust"]["coordinate_support_hull"].values())
