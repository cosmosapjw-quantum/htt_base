"""Numerical controls for the frozen, conditional depth-bias calculation."""

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
module_spec = importlib.util.spec_from_file_location("depth_bias_compute", HERE / "compute.py")
mod = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(mod)


def test_frozen_sources_and_grid():
    spec, src, mu, C, A, G, S = mod.load()
    d = json.loads((HERE / "RESULT.json").read_text())
    assert d["input_identity"] == "sha256:" + mod.sha(mod.INPUT)
    assert len(d["independent_controls"]) == 18
    assert all(x["objective_agreement"] for x in d["independent_controls"])
    assert np.linalg.matrix_rank(A) == 12 and np.linalg.matrix_rank(A @ S) == 6
    assert d["full24_zero_residual"]["relative_Ab_minus_d"] < 1e-10
    for tau in spec["tau_uasyr"]:
        y,W,_,_=mod.whitening(mu,C,A,np.eye(24),tau)
        assert mod.solve(y,W,d["full24_zero_residual"]["radius"])["T"] < 1e-10
    assert np.allclose(G @ C @ G.T, src["G_F"]["cov18_at_tau0_uasyr2"], atol=1e-10)
    for name, scope in (("full24", np.eye(24)), ("slope6", S)):
        rows = d["scopes"][name]["grid"]
        assert len(rows) == 6 and all(len(r["cells"]) == 6 for r in rows)
        table = np.array([[c["T"] for c in r["cells"]] for r in rows])
        assert np.max(np.diff(table, axis=0)) < 1e-9
        assert np.max(np.diff(table, axis=1)) < 1e-9
        for row in rows:
            for cell in row["cells"]:
                assert cell["feasibility_excess"] <= 1e-9
                if cell["branch"] == "zero_radius":
                    assert cell["kkt_stationarity_abs"] is None
                else:
                    assert cell["kkt_stationarity_abs"] <= 1e-9
                    assert cell["kkt_stationarity_scaled"] <= 1e-9
                assert np.isclose(np.linalg.norm(cell["bias_witness24"]), cell["witness_norm"],atol=1e-9)
                y,W,_,_=mod.whitening(mu,C,A,scope,row["tau"])
                assert np.isclose(np.linalg.norm(y-W@cell["bias_witness"])**2,cell["T"],atol=1e-8)
        for item in d["scopes"][name]["frontiers"]:
            for key, f in item["thresholds"].items():
                if f["status"] == "crossed":
                    assert np.isclose(f["T"], d["thresholds"][key],rtol=1e-9,atol=1e-8)
                if f["status"] == "never_reached":
                    assert f["least_squares_floor"] > d["thresholds"][key]


def test_compact_rank_and_orthogonal_residual():
    y = np.array([2.,3.,4.])
    zero = mod.solve(y,np.zeros((3,2)),1.)
    assert zero["rank"] == 0 and zero["T"] == 29 and zero["orthogonal_residual_norm2"] == 29
    W = np.array([[2.,0.,0.],[0.,0.,0.],[0.,0.,0.]])
    fit = mod.solve(y,W,10)
    assert fit["rank"] == 1 and np.allclose(fit["b"],[1,0,0])
    assert np.isclose(fit["orthogonal_residual_norm2"],25)
    boundary = mod.solve(y,W,.5)
    assert np.isclose(boundary["T"],26)
    assert np.isclose(boundary["norm"],.5)


def test_common_mode_and_o3_equivariance():
    _,_,mu,C,A,_,S = mod.load()
    # Identical shifts in the three level blocks cancel in both contrasts.
    common = np.kron(np.array([1.,1.,1.,0.])[:,None],np.eye(6))
    assert np.max(np.abs(A@common)) == 0
    R = np.array([[0.,1.,0.],[1.,0.,0.],[0.,0.,1.]])
    for base in (R, -R):
        D6 = np.block([[base,np.zeros((3,3))],[np.zeros((3,3)),np.linalg.det(base)*base]])
        B = np.kron(np.eye(4),D6)
        D12 = np.kron(np.eye(2),D6)
        assert np.allclose(A@B,D12@A,atol=1e-12)
        for scope in (np.eye(24),S):
            transformed_scope = B@scope
            y,W,_,_=mod.whitening(mu,C,A,scope,.3)
            yt,Wt,_,_=mod.whitening(B@mu,B@C@B.T,A,transformed_scope,.3)
            assert np.isclose(mod.solve(y,W,1)["T"],mod.solve(yt,Wt,1)["T"],atol=1e-9)


def test_support_witnesses_and_full_covariance():
    _,_,mu,C,_,G,S=mod.load()
    d=json.loads((HERE/"RESULT.json").read_text())
    for name,scope in (("full24",np.eye(24)),("slope6",S)):
        for label, map18 in (("full24",None),("G_F18",G)):
            saved=d["support_examples"][name][label]
            u=np.asarray(saved["direction"])
            fresh=mod.support(mu,C+.3**2*np.eye(24),map18,scope,1,1,u)
            assert np.isclose(saved["value"],saved["attained"],atol=1e-10)
            assert np.isclose(saved["value"],fresh["value"],atol=1e-10)
            assert np.isclose(u @ (G @ mu), (G.T@u)@mu,atol=1e-12) if map18 is not None else True
    assert d["source_science"]["Pi"]["retained_rows"] == 4096
    assert d["source_science"]["Q"]["physical_status"] == "UNAVAILABLE"
    assert d["source_science"]["F"]["physical_occupancy"] == "UNAVAILABLE"
