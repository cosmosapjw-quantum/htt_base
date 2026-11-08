import importlib.util
import math
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("hubble", Path(__file__).with_name("compute_hubble.py"))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

def test_full_signed_tensor_and_reference():
    x, z = [1,0,0], [0,0,1]
    f = h.contrast(x,z)
    assert np.linalg.norm(f[3:]) > 0
    assert np.allclose(h.tensor([0,0,0,1,0,0,0,0]), h.E[0])
    assert abs(np.trace(h.tensor([0,0,0,1,2,3,4,5]))) < 1e-14
    assert np.allclose(h.contrast(z,z),0)

def test_joint_covariance_cross_bin_falsifier():
    import json
    d=json.loads(h.SN_PATH.read_text())["primary"]
    C=np.asarray(d["full_16x16_covariance_mag2"])
    f=h.contrast([1,0,0],[0,0,1])
    L=np.r_[-f,f]
    actual=float(L@C@L)
    wrong=float(f@C[:8,:8]@f+f@C[8:,8:]@f)
    assert abs(actual-wrong)>1e-7
    assert abs(actual-float(f@np.asarray(d["high_minus_low_8x8_covariance_mag2"])@f))<1e-12

def test_opacity_sign_and_exact_control():
    rows, summary=h.cbl_control()
    assert len(rows)==4
    assert summary["spread_at_generating_opacity_invMpc2"]<1e-12
    assert all(r["naive_kappa_invMpc2"]>0 for r in rows)
    assert all(r["compatible_min_invMpc2"]<=0<=r["compatible_max_invMpc2"] for r in rows)
    m,s,w=h.support(np.array([.1]),np.array([[.04]]),np.array([1.]),q=4)
    assert (m,s,w)==(.1,.2,.4)
    assert math.isclose(math.exp(m+.01+.02/2),math.exp(m+.02))
