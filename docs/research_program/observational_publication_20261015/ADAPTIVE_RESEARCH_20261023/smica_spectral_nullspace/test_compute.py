"""Falsifiers for the released-weight linear information audit."""

from fractions import Fraction
import importlib.util
from pathlib import Path

import numpy as np
import pytest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("smica_spectral_compute", HERE / "compute.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_release_source_and_all_targets():
    result = mod.compute()
    assert result["tensor"]["rank"] == 24
    assert result["tensor"]["nullity"] == 144
    assert len(result["tensor"]["nonzero_entries"]) == 168
    for key, row in result["operators"].items():
        assert row["target_count"] == 28
        assert row["row_rank"] == 1
        assert row["kernel_dimension"] == 6
        assert row["controls"]["projector_symmetry_max_abs"] < 1e-14
        assert row["controls"]["projector_idempotence_max_abs"] < 1e-14
        assert row["controls"]["projector_annihilation_norm"] < 1e-14
        assert abs(row["controls"]["projector_trace"]-6) < 1e-13
        assert row["controls"]["projection_vs_lstsq_max_abs"] < 1e-14
        assert [t["target"] for t in row["targets"]] == [n for n,_ in mod.targets()]
        for t in row["targets"]:
            assert abs(t["retained_squared_fraction"] + t["lost_squared_fraction"] - 1) < 1e-14
            assert abs(t["witness_compressed_difference"]) < 1e-14
            assert t["witness_target_difference"] > 0
        exact = row["exact_witness"]
        assert exact["w_dot_h_exact"] == "0"
        assert exact["a_dot_h_minus_h_dot_h_exact"] == "0"
        assert Fraction(exact["a_dot_h_exact"]) > 0
        assert abs(float(exact["decimal_w_dot_h_residual"])) < 1e-75
        assert abs(float(exact["decimal_a_dot_h_minus_h_dot_h_residual"])) < 1e-75


def test_full_tensor_basis_and_field_separation():
    result = mod.compute()
    rows = {key: np.asarray(v["weights"]) for key,v in result["operators"].items()}
    M, blocks = mod.tensor_operator(rows)
    assert M.shape == (24,168)
    for b in blocks:
        w = rows[b["key"]]; p = b["pivot_frequency_index"]
        n = len(b["harmonic_coordinates"])
        assert np.count_nonzero(M[b["output_start"]:b["output_start"]+n,
                                     b["input_start"]:b["input_start"]+7*n]) == 7*n
        for m in range(n):
            for j in range(7):
                if j == p: continue
                x = np.zeros(168)
                x[b["input_start"]+j*n+m] = 1
                x[b["input_start"]+p*n+m] = -w[j]/w[p]
                assert np.linalg.norm(M@x) < 1e-14
        other = [c for c in blocks if c["key"][0] != b["key"][0]]
        for c in other:
            assert not np.any(M[b["output_start"]:b["output_start"]+n,
                                c["input_start"]:c["input_start"]+7*len(c["harmonic_coordinates"])])


@pytest.mark.parametrize("w,a", [([0]*7,[1,0,0,0,0,0,0]),
                                    ([1,2,3,4,5,6,7],[1,2,3,4,5,6,7])])
def test_zero_and_aligned_identification_fixtures(w,a):
    w = np.asarray(w,dtype=float); a = np.asarray(a,dtype=float)
    parallel,h = mod.projection(w,a)
    assert np.allclose(a,parallel+h)
    if np.any(w):
        assert np.linalg.norm(h) < 1e-14  # L = K M, identified
    else:
        assert np.allclose(h,a)  # M=0, all nonzero targets lost


def test_frequency_permutation_invariance():
    rng = np.random.default_rng(247)
    w = np.asarray([0.2,-0.8,0.5,1.1,-0.3,0.7,0.4]); a = np.asarray([1,-1,0,0,0,0,0])
    perm = rng.permutation(7)
    p0,h0 = mod.projection(w,a); p1,h1 = mod.projection(w[perm],a[perm])
    assert np.allclose(p1,p0[perm])
    assert np.allclose(h1,h0[perm])
    assert np.isclose(w@h0,w[perm]@h1)
