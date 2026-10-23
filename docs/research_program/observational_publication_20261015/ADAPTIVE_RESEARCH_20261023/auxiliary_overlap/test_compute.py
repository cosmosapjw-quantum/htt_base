"""Independent checks of saved R25 finite-frame and joint-tensor artifacts."""
import csv
import json
from collections import Counter

import numpy as np

from compute import HERE, LEDGER, OOF, cell


def test_exact_support_and_missing_scope():
    with LEDGER.open(newline="") as f:
        target = list(csv.DictReader(f))
    result = json.loads((HERE/"RESULT.json").read_text())
    counts = Counter(cell(r) for r in target)
    observed = {int(k) for k in np.load(HERE/"joint_tensor_atomic.npz")["pgc"]}
    assert len(target) == 628 and len(observed) == 274
    assert result["cohort"]["quality_observed_only"] == {
        "accepted": 269, "other_quality": 1, "confused": 3, "nondetection": 1}
    assert result["cohort"]["quality_undefined"] == "UNKNOWN"
    for witness in result["full628"]["witnesses"]:
        c = tuple(witness["cell"])
        target_ids = {int(r["pgc"]) for r in target if cell(r) == c}
        assert counts[c] == 1 and target_ids == set(witness["target_pgc"])
        assert not target_ids & observed
        assert witness["target_dot_rational"] == "-1/628"
    assert sum(r["undefined"] for r in result["cohort"]["cells"]) == 354
    assert result["supported625"]["undefined"] == 351


def test_joint_atomic_tensors_and_window_means():
    result = json.loads((HERE/"RESULT.json").read_text())
    with np.load(HERE/"joint_tensor_atomic.npz") as d:
        pgc, p, n, r = d["pgc"], d["weights"], d["direction_J2000"], d["residual_mag"]
        v, t, coords = d["vector_mag"], d["stf_tensor_mag"], d["full_coordinates_mag"]
        assert len(set(pgc)) == 274 and r.shape == (274, 12)
        assert coords.shape == (274, 12, 13)
        assert np.isfinite(coords).all() and np.min(p) > 0
        assert abs(np.sum(p)-1) < 1e-12
        assert np.max(np.abs(v-r[:, :, None]*n[:, None])) < 1e-12
        assert np.max(np.abs(t-r[:, :, None, None]*(np.einsum("ni,nj->nij", n, n)[:, None]-np.eye(3)/3))) < 1e-12
        assert np.max(np.abs(np.trace(t, axis1=2, axis2=3))) < 1e-12
        assert np.max(np.abs(np.mean(coords, axis=0)-result["joint_carrier"]["windows"]["global"]["uniform_mean_full13"])) < 1e-12
        assert np.max(np.abs(np.einsum("n,nmk->mk", p, coords)-result["joint_carrier"]["windows"]["global"]["weighted_mean_full13"])) < 1e-12
        with OOF.open(newline="") as f:
            source = {(row["scenario"], row["model"], int(row["pgc"])):
                      float(row["OOF_signed_residual_mag"]) for row in csv.DictReader(f)}
        assert len(source) == 12*274
        for j, pair in enumerate(zip(d["scenario"], d["model"])):
            for i, k in enumerate(pgc):
                assert abs(r[i, j]-source[(str(pair[0]), str(pair[1]), int(k))]) < 1e-12
