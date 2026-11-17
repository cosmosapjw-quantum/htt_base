"""Focused source/cache integrity tests plus default execution on the committed (pinned) data."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
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


ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117"


def comparator():
    path = ROOT / "scripts/r58/compare_r59_native_replay.py"
    spec = importlib.util.spec_from_file_location("r59_compare", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def skip_unless_pinned_inputs(run):
    """Every pinned input is committed; a missing one is an explicit skip that names the file, never a silent pass."""
    missing = [rel for rel in run.PINS if not (ROOT / rel).is_file()]
    if missing:
        pytest.skip("pinned input missing: " + ", ".join(missing))


def test_existing_data_reanalysis_reproduces_frozen_marginals_and_mixed_covariance(tmp_path):
    run = runner()
    skip_unless_pinned_inputs(run)
    root = ROOT
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
    # every numeric leaf of the committed result, with the comparator and tolerances of R59-A (rtol 1e-7, atol 1e-9)
    cmp = comparator()
    ref = json.loads((PKG / "RESULTS/OWNED_TENSOR_RESULT.json").read_text())
    rep = json.loads((tmp_path / "OWNED_TENSOR_RESULT.json").read_text())
    out = cmp.compare_json(ref, rep)
    assert out["numeric_leaves"] > 1000
    assert not out["numeric_outside_tolerance"], out["numeric_outside_tolerance"][:5]
    assert not out["only_reference"] and not out["only_replay"]
    # R59-A cache policy (LOCAL_AGENT_CONTRACT.json): the operator byte fingerprint may differ between BLAS builds or thread
    # counts only with equal model keys, equal row labels and the numeric parity asserted above; nothing else may differ
    byte_flags = {k for k in out["nonnumeric_differences"] if re.fullmatch(r"/cache_reuse\[\d\]/exact_operator_bytes", k)}
    assert set(out["nonnumeric_differences"]) == byte_flags, out["nonnumeric_differences"]
    assert all(c["model_key_equal"] and c["row_labels_equal"] for c in rep["cache_reuse"])
    za = np.load(PKG / "RESULTS/OWNED_TENSOR_CARRIERS.npz", allow_pickle=False)
    zb = np.load(tmp_path / "OWNED_TENSOR_CARRIERS.npz", allow_pickle=False)
    assert set(za.files) == set(zb.files)
    for key in za.files:
        if za[key].dtype.kind in "fc":
            np.testing.assert_allclose(zb[key], za[key], rtol=cmp.RTOL, atol=cmp.ATOL, err_msg=key)
        else:
            np.testing.assert_array_equal(zb[key], za[key], err_msg=key)


def test_rank_deficient_common_target_fails_closed_before_any_output(tmp_path):
    """A fit that does not identify all 11 apparent coefficients stops the runner before any result file is written."""
    run = runner()
    skip_unless_pinned_inputs(run)
    module = tmp_path / "rank10_fit.py"
    module.write_text("from htt.htt.infer.r58_mixed_tensor_likelihood import *\n"
                      "from htt.htt.infer import r58_mixed_tensor_likelihood as _m\n"
                      "def fit_linear(*a, **k):\n    f = _m.fit_linear(*a, **k)\n    f['rank'] = 10\n    return f\n")
    with pytest.raises(ValueError, match="full common target is not identified"):
        run.compute(ROOT, tmp_path / "out", module)
    assert not (tmp_path / "out").exists()
