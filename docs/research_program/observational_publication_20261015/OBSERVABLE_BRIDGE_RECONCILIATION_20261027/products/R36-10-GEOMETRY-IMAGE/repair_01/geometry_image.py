"""Finite instantaneous geometry and deterministic uncertainty image for R36-10.

Run: python geometry_image.py.  All calculations use a right-handed orthonormal
spatial triad and dimensionless variables scaled by the declared u_star.  No
time evolution, sky transfer, likelihood, or Bianchi-family inference occurs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "AGENTS.md").exists())
CONTRACT = Path("/mnt/extdrive/workdir/htt_open_data/r36_geometry_contract_preparation/IMPLEMENTATION_CONTRACT.json")
CSV = REPO / "docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report/joint_image.csv"
U = 1e-26
C = 299792458.0
G = 6.67430e-11
KAPPA = 8 * math.pi * G / C**4
EPS = np.finfo(float).eps
TOL = 4096 * EPS
SQ2 = math.sqrt(2)


def levi(i, j, k):
    if len({i, j, k}) != 3:
        return 0
    return 1 if (j - i) % 3 == 1 else -1


E = np.array([[[levi(i, j, k) for k in range(3)] for j in range(3)] for i in range(3)])
B = np.array([
    np.diag([1, -1, 0]) / SQ2,
    np.diag([1, 1, -2]) / math.sqrt(6),
    (np.outer([1, 0, 0], [0, 1, 0]) + np.outer([0, 1, 0], [1, 0, 0])) / SQ2,
    (np.outer([1, 0, 0], [0, 0, 1]) + np.outer([0, 0, 1], [1, 0, 0])) / SQ2,
    (np.outer([0, 1, 0], [0, 0, 1]) + np.outer([0, 0, 1], [0, 1, 0])) / SQ2,
])
SB = np.array([
    np.diag([1, 0, 0]), np.diag([0, 1, 0]), np.diag([0, 0, 1]),
    B[2], B[3], B[4],
])


def svec(a):
    return np.array([a[0, 0], a[1, 1], a[2, 2], SQ2*a[0, 1], SQ2*a[0, 2], SQ2*a[1, 2]])


def unsvec(v):
    return sum((v[i] * SB[i] for i in range(6)), np.zeros((3, 3), dtype=np.asarray(v).dtype))


def natural(residual, scale, label):
    err = float(np.linalg.norm(np.asarray(residual)))
    if scale == 0:
        assert err == 0, (label, err, "exact zero scale")
        return 0.0
    rel = err / scale
    assert rel <= TOL, (label, err, scale, rel)
    return rel


def frame(n, a, h, s, ebar, qbar, lam=0):
    """Direct Jacobi/Koszul/Riemann/Gauss-Codazzi evaluator, normalized by u²."""
    n = np.asarray(n, dtype=float); a = np.asarray(a, dtype=float)
    s = np.asarray(s, dtype=float); qbar = np.asarray(qbar, dtype=float)
    assert n.shape == (3, 3) and a.shape == (3,) and s.shape == (3, 3)
    assert np.all(np.isfinite(n)) and np.all(np.isfinite(a)) and np.all(np.isfinite(s))
    assert all(math.isfinite(float(x)) for x in (h, ebar, lam, *qbar)) and h > 0
    natural(n-n.T, np.linalg.norm(n), "symmetric n")
    natural(s-s.T, np.linalg.norm(s), "symmetric S")
    natural(np.trace(s), np.linalg.norm(s), "trace-free S")
    j = n @ a
    jscale = np.linalg.norm(n) * np.linalg.norm(a)
    if jscale and np.linalg.norm(j)/jscale > TOL:
        raise ValueError("INVALID_JACOBI")
    natural(j, jscale, "Jacobi")
    cc = np.einsum("ijl,lk->ijk", E, n)
    cc += np.einsum("i,jk->ijk", a, np.eye(3)) - np.einsum("j,ik->ijk", a, np.eye(3))
    gam = (cc - cc.transpose(2, 0, 1) + cc.transpose(1, 2, 0)) / 2
    riem = np.zeros((3, 3, 3, 3))  # [upper l, lower m, i, j]
    for l in range(3):
        for m in range(3):
            for i in range(3):
                for j0 in range(3):
                    riem[l, m, i, j0] = sum(gam[j0, m, p]*gam[i, p, l] -
                                           gam[i, m, p]*gam[j0, p, l] -
                                           cc[i, j0, p]*gam[p, m, l] for p in range(3))
    ric = np.array([[sum(riem[i, j0, i, k] for i in range(3)) for k in range(3)] for j0 in range(3)])
    r = float(np.trace(ric))
    kext = -h*np.eye(3)-s
    hres = 3*h*h - ebar-lam-.5*np.sum(s*s)+.5*r
    adm = r + np.trace(kext)**2 - np.sum(kext*kext)-2*ebar-2*lam
    mom = 3*s@a + np.einsum("ijk,jl,kl->i", E, n, s)
    cod = np.array([-sum(gam[j0, j0, p]*kext[p, i] + gam[j0, i, p]*kext[j0, p]
                         for j0 in range(3) for p in range(3)) for i in range(3)])
    cscale = (np.linalg.norm(n)+np.linalg.norm(a))**2
    natural(ric-ric.T, cscale, "Ricci symmetry")
    natural(cod-mom, 3*np.linalg.norm(a)*np.linalg.norm(s)+2*np.linalg.norm(n)*np.linalg.norm(s), "Codazzi sign")
    natural(adm-2*hres, 3*h*h+abs(ebar)+abs(lam)+.5*np.sum(s*s)+.5*abs(r), "ADM +2rH")
    return {"jacobi": j, "structure": cc, "connection": gam, "riemann": riem,
            "ricci": ric, "ricci_stf": ric-r*np.eye(3)/3, "scalar": r,
            "extrinsic": kext, "hamiltonian_residual": hres,
            "adm_residual": adm, "momentum": mom, "codazzi": cod,
            "momentum_residual": mom-qbar}


def class_a_ric(n):
    t = np.trace(n)
    return 2*n@n-t*n+(.5*t*t-np.trace(n@n))*np.eye(3, dtype=n.dtype)


def unpack(z):
    return unsvec(z[:6]), z[6], sum((z[7+i]*B[i] for i in range(5)),
                                  np.zeros((3, 3), dtype=np.asarray(z).dtype))


def joint(z):
    n, h, s = unpack(z)
    ric = class_a_ric(n)
    ebar = 3*h*h-.5*np.sum(s*s)+.5*np.trace(ric)
    q = np.einsum("ijk,jl,kl->i", E, n, s)
    return np.concatenate((svec(ric), np.atleast_1d(ebar), q))


def derivatives(z):
    # Polarization of an exactly homogeneous quadratic map gives exact analytic
    # first and second derivatives; complex step is an independent numeric check.
    eye = np.eye(12)
    y0 = joint(z)
    je = np.array([joint(z+v)-y0-joint(v) for v in eye]).T
    hh = np.array([[joint(eye[i]+eye[j])-joint(eye[i])-joint(eye[j])
                    for j in range(12)] for i in range(12)]).transpose(2, 0, 1)
    jc = np.array([np.imag(joint(z.astype(complex)+1e-30j*v))/1e-30 for v in eye]).T
    natural(je-jc, np.linalg.norm(je)+np.linalg.norm(jc), "complex step Jacobian")
    return je, hh


def rank_svd(j):
    left, sig, right = np.linalg.svd(j, full_matrices=True)
    tau = 256*EPS*max(j.shape)*(sig[0] if len(sig) else 0)
    near = [i for i, v in enumerate(sig) if tau/16 <= v <= 16*tau] if tau else []
    if near:
        raise ArithmeticError(f"UNRESOLVED_NUMERICAL_RANK {near}")
    rank = int(np.sum(sig > tau)) if tau else 0
    assert np.linalg.norm(j-left[:, :len(sig)]@np.diag(sig)@right[:len(sig), :]) <= TOL*max(np.linalg.norm(j), EPS)
    assert np.linalg.norm(j@right[rank:, :].T) <= TOL*max(np.linalg.norm(j), EPS)
    return {"singular_values": sig.tolist(), "rank": rank, "threshold": float(tau),
            "left_singular_coordinates": left.T.tolist(), "right_singular_coordinates": right.tolist(),
            "null_residual": float(np.linalg.norm(j@right[rank:, :].T))}


def bounds(y0, j, hh, ll, w):
    g = j.T@w
    hw = np.einsum("k,kij->ij", w, hh)
    linear = float(np.linalg.norm(ll.T@g))
    quadratic = float(.5*np.linalg.norm(ll.T@hw@ll, 2))
    roundoff = TOL*(abs(float(w@y0))+linear+quadratic)
    return {"center": float(w@y0), "linear": linear, "quadratic": quadratic,
            "roundoff": roundoff, "radius": linear+quadratic+roundoff}


def probes():
    xis = [np.zeros(12)]
    eye = np.eye(12)
    for radius in (.5, 1.):
        for i in range(12):
            for si in (-1, 1):
                xis.append(radius*si*eye[i])
        for i in range(12):
            for j in range(i+1, 12):
                for si in (-1, 1):
                    for sj in (-1, 1):
                        xis.append(radius*(si*eye[i]+sj*eye[j])/SQ2)
    assert len(xis) == 577
    return np.asarray(xis)


def native(v):
    if isinstance(v, (np.ndarray, np.generic)):
        return v.tolist()
    if isinstance(v, Path):
        return str(v)
    raise TypeError(type(v).__name__)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def center_shear(name):
    """Frozen matched-pair shear and exact zero-shear flat-center inputs."""
    if name in ("I", "flatVII0"):
        return np.zeros((3, 3))
    if name in ("II", "VII0matched", "IX", "V"):
        return np.diag([.1, -.05, -.05])
    raise KeyError(name)


def source_seals(contract):
    actual = []
    for item in contract["source_bindings"]:
        p = Path(item["path"])
        assert p.is_file() and sha(p) == item["sha256"] and p.stat().st_size == item["bytes"], p
        actual.append({"path": str(p), "sha256": item["sha256"], "bytes": item["bytes"]})
    return actual


def main():
    assert sha(CONTRACT) == "76e2c762c4e9fbf4d27ac1af8521c3138edefb138f62e292c776ca83d67bf6b5"
    contract = json.loads(CONTRACT.read_text())
    assert sha(REPO / "docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/EVIDENCE_MANIFEST.json") == contract["input_identity"].split(":")[1]
    seals = source_seals(contract)
    cases = {
        "I": (np.diag([0., 0, 0]), np.zeros(3), np.zeros((3, 3))),
        "II": (np.diag([1., 0, 0]), np.zeros(3), np.diag([.5, -.5, -.5])),
        "IX": (np.eye(3), np.zeros(3), .5*np.eye(3)),
        "V": (np.zeros((3, 3)), np.array([1., 0, 0]), -2*np.eye(3)),
        "flatVII0": (np.diag([0., 1, 1]), np.zeros(3), np.zeros((3, 3))),
        "VII0matched": (np.diag([0., 2, 1]), np.zeros(3), np.diag([-.5, 1.5, -1.5])),
    }
    s0 = center_shear("II"); h0 = 2.
    controls = {}
    rz = np.array([[3/5, -4/5, 0], [4/5, 3/5, 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, 5/13, -12/13], [0, 12/13, 5/13]])
    for name, (n, a, expected) in cases.items():
        sc = center_shear(name)
        ebar = 3*h0*h0-.5*np.sum(sc*sc)+.5*np.trace(expected)
        mm = frame(n, a, h0, sc, ebar, np.zeros(3))
        natural(mm["ricci"]-expected, (np.linalg.norm(n)+np.linalg.norm(a))**2, name+" oracle")
        if not np.any(a):
            natural(mm["ricci"]-class_a_ric(n), np.linalg.norm(n)**2, name+" polynomial")
        for rot in (rz, rx, rx@rz):
            other = frame(rot@n@rot.T, rot@a, h0, rot@sc@rot.T, ebar, rot@mm["momentum"])
            natural(other["connection"]-np.einsum("ip,jq,kr,pqr->ijk",rot,rot,rot,mm["connection"]),
                    np.linalg.norm(n)+np.linalg.norm(a),name+" rotation connection")
            natural(other["riemann"]-np.einsum("lp,mq,ir,js,pqrs->lmij",rot,rot,rot,rot,mm["riemann"]),
                    (np.linalg.norm(n)+np.linalg.norm(a))**2,name+" rotation Riemann")
            natural(other["ricci"]-rot@mm["ricci"]@rot.T,
                    (np.linalg.norm(n)+np.linalg.norm(a))**2, name+" rotation Ricci")
            natural(other["momentum"]-rot@mm["momentum"],
                    3*np.linalg.norm(a)*np.linalg.norm(sc)+2*np.linalg.norm(n)*np.linalg.norm(sc),
                    name+" rotation momentum")
        controls[name] = {"ricci": mm["ricci"], "scalar": mm["scalar"],
                          "n_bar":n,"a_bar":a,"h_bar":h0,"S_bar":sc,
                          "structure":mm["structure"],"connection":mm["connection"],
                          "riemann":mm["riemann"],"ricci_stf":mm["ricci_stf"],
                          "extrinsic":mm["extrinsic"],
                          "sectional_12_13_23": [mm["riemann"][i,j,i,j] for i,j in ((0,1),(0,2),(1,2))],
                          "density_bar": ebar, "mom_bar": mm["momentum"],
                          "hamiltonian_residual": mm["hamiltonian_residual"]}
    # Same scalar, matter, shear and flux; unequal tensor spectra. Flat pair has
    # vanishing full intrinsic Riemann in two different group presentations.
    assert np.isclose(controls["II"]["scalar"], controls["VII0matched"]["scalar"])
    assert controls["II"]["density_bar"] == controls["VII0matched"]["density_bar"] == 4697/400
    assert np.linalg.norm(controls["II"]["ricci"]-controls["VII0matched"]["ricci"]) > 1
    assert np.allclose(controls["I"]["ricci"], controls["flatVII0"]["ricci"])
    for name in ("I", "flatVII0"):
        assert np.array_equal(controls[name]["S_bar"], np.zeros((3,3)))
        assert controls[name]["density_bar"] == 12
        assert np.array_equal(controls[name]["extrinsic"], -2*np.eye(3))
    mixed_n = np.diag([0., .7, 1.1]); mixed_a = np.array([.3, 0, 0])
    mixed_s = np.array([[.1, .02, -.01], [.02, -.05, .03], [-.01, .03, -.05]])
    seed = frame(mixed_n, mixed_a, 2., mixed_s, 0., np.zeros(3))
    mixed_e = 12-.5*np.sum(mixed_s*mixed_s)+.5*seed["scalar"]
    mixed = frame(mixed_n, mixed_a, 2., mixed_s, mixed_e, seed["momentum"])
    assert np.isclose(mixed["ricci"][1,2], -.12)
    invalid_rejected = False
    try:
        frame(np.diag([1., .7, 1.1]), mixed_a, 2., mixed_s, mixed_e, seed["momentum"])
    except ValueError as exc:
        invalid_rejected = str(exc) == "INVALID_JACOBI"
    assert invalid_rejected
    for rot in (rz, rx, rx@rz):
        rr = frame(rot@mixed_n@rot.T, rot@mixed_a, 2., rot@mixed_s@rot.T,
                   mixed_e, rot@mixed["momentum"])
        natural(rr["connection"]-np.einsum("ip,jq,kr,pqr->ijk",rot,rot,rot,mixed["connection"]),
                np.linalg.norm(mixed_n)+np.linalg.norm(mixed_a),"mixed rotated connection")
        natural(rr["riemann"]-np.einsum("lp,mq,ir,js,pqrs->lmij",rot,rot,rot,rot,mixed["riemann"]),
                (np.linalg.norm(mixed_n)+np.linalg.norm(mixed_a))**2,"mixed rotated Riemann")
        natural(rr["ricci"]-rot@mixed["ricci"]@rot.T,
                (np.linalg.norm(mixed_n)+np.linalg.norm(mixed_a))**2, "mixed rotated Ricci")
        natural(rr["momentum"]-rot@mixed["momentum"],
                3*np.linalg.norm(mixed_a)*np.linalg.norm(mixed_s)+2*np.linalg.norm(mixed_n)*np.linalg.norm(mixed_s),
                "mixed rotated momentum")
    scales = []
    for u in (1e-30, 1e-26, 1e-22):
        assert u > 0 and u*u > 0
        scales.append({"u_star_m_inverse": u, "H_s_inverse": C*h0*u,
                       "sigma_s_inverse": C*s0*u, "II_ricci_m_inverse2": controls["II"]["ricci"]*u*u,
                       "II_dimensionless_ricci": controls["II"]["ricci"]})
    ll = np.diag([.05]*7+[.01]*5)
    ll[7,5] = .005
    xi = probes()
    stf_d = np.diag([-1., 2, -1])/math.sqrt(6)
    w_d = np.zeros(10); w_d[:6] = svec(stf_d)
    w_scalar = np.zeros(10); w_scalar[:3] = 1
    images = {}; rows = []; signatures = {}
    for name in ("II", "VII0matched", "I", "flatVII0"):
        n = cases[name][0]
        sc = center_shear(name)
        z = np.r_[svec(n), 2., [float(np.sum(b*sc)) for b in B]]
        y0 = joint(z)
        jj, hh = derivatives(z)
        gj = rank_svd(jj[:6,:6]); jrank = rank_svd(jj)
        bounds10 = [bounds(y0,jj,hh,ll,np.eye(10)[i]) for i in range(10)]
        bd = bounds(y0,jj,hh,ll,w_d); bs = bounds(y0,jj,hh,ll,w_scalar)
        # Whole-ellipsoid positivity follows from the same exact quadratic bound.
        assert z[6]-np.linalg.norm(ll[6]) > 0
        assert bounds10[6]["center"]-bounds10[6]["radius"] > 0
        radius = math.sqrt(sum(bounds10[i]["radius"]**2 for i in range(6)))
        max_recon = max_linear = 0.
        for p, point in enumerate(xi):
            delta = ll@point
            direct = joint(z+delta)
            linear = y0+jj@delta
            exact = linear+.5*np.einsum("k,ikj,j->i", delta, hh, delta)
            diff = np.linalg.norm(direct-exact)
            term = np.linalg.norm(direct)+np.linalg.norm(y0)+np.linalg.norm(jj@delta)+.5*np.linalg.norm(np.einsum("k,ikj,j->i",delta,hh,delta))
            natural(direct-exact, term, name+" exact Taylor")
            for k in range(10):
                assert abs(direct[k]-y0[k]) <= bounds10[k]["radius"] + TOL*term
            assert abs(w_d@direct-bd["center"]) <= bd["radius"] + TOL*term
            assert abs(w_scalar@direct-bs["center"]) <= bs["radius"] + TOL*term
            max_recon = max(max_recon, diff)
            max_linear = max(max_linear, float(np.linalg.norm(direct-linear)))
            rows.append({"center":name,"probe":p,"xi":point.tolist(),"z":(z+delta).tolist(),
                         "directY":direct.tolist(),"linearY":linear.tolist(),"quadraticY":exact.tolist(),
                         "linear_error_norm":float(np.linalg.norm(direct-linear)),
                         "scalar":float(w_scalar@direct),"x_D":float(w_d@direct)})
        images[name] = {"z0":z,"Y0":y0,"center_S_bar":sc,"geometry_J":jj[:6,:6],"geometry_svd":gj,
                        "joint_J":jj,"joint_H":hh,"joint_svd":jrank,"bounds10":bounds10,
                        "x_D_bound":bd,"scalar_bound":bs,"ricci_F_bound":radius,
                        "max_taylor_error":max_recon,"max_linear_error":max_linear,
                        "probe_count":len(xi)}
        signatures[name] = np.sort(np.linalg.eigvalsh(unsvec(y0[:6])))
    assert [images[x]["geometry_svd"]["rank"] for x in images] == [6,6,0,3]
    assert [images[x]["joint_svd"]["rank"] for x in images] == [9,10,1,6]
    only_h = np.zeros((10,12)); only_h[6,6] = 12.
    natural(images["I"]["joint_J"]-only_h, 12., "frozen I center has only dE/dh=12")
    for name in ("I", "flatVII0"):
        assert np.array_equal(images[name]["z0"][7:], np.zeros(5))
        assert images[name]["Y0"][6] == 12
    i_n = cases["II"][0]
    nonlinear_i = [{"t":t,"ricci":class_a_ric(t*i_n),"expected":t*t*class_a_ric(i_n)}
                   for t in (.5,.25,.125)]
    for row in nonlinear_i:
        assert np.linalg.norm(row["ricci"]) > 0 and np.allclose(row["ricci"],row["expected"])
    flat_n = cases["flatVII0"][0]
    curved_flat = []
    for t in (.125,.25,.5):
        rot = np.array([[math.cos(t),-math.sin(t),0],[math.sin(t),math.cos(t),0],[0,0,1]])
        nn = rot@flat_n@rot.T
        curved_flat.append({"t":t,"ricci_norm":float(np.linalg.norm(class_a_ric(nn)))})
        assert curved_flat[-1]["ricci_norm"] <= TOL*np.linalg.norm(nn)**2
    sep = float(np.linalg.norm(signatures["II"]-signatures["VII0matched"]))
    rad_sum = images["II"]["ricci_F_bound"]+images["VII0matched"]["ricci_F_bound"]
    # LRS V bridge consumes retained rows exactly once; never invokes the R32 producer.
    perm = np.array([[0,0,1],[1,0,0],[0,1,0]])
    lrs = []; lrs_max = {"hamiltonian":0.,"momentum":0.,"lambda_negative_roundoff":0.,"speed":0.}
    parity = {}
    with CSV.open(newline="") as fh:
        for index, row in enumerate(csv.DictReader(fh)):
            num = {k:float(v) for k,v in row.items() if v not in ("",None) and k not in
                   ("matter_velocity_status","normal_vorticity_status","matter_vorticity_status")}
            kval = num["K"]; beta = num["beta"]
            assert 0 < kval <= 1 and 0 <= num["w"] <= 1 and 0 <= num["u"] <= 1 and abs(beta) < 1
            shear = np.array([[num[f"shear_{i}{j}"] for j in "xyz"] for i in "xyz"])
            pi = np.array([[num[f"pi_{i}{j}"] for j in "xyz"] for i in "xyz"])
            flux = np.array([num[f"flux_{i}"] for i in "xyz"])
            vb = np.array([num[f"beta_chart_{i}"] for i in "xyz"])
            h = 2.; aa = np.array([h*math.sqrt(kval),0,0]); ss = h*perm@shear@perm.T
            qb = 3*h*h*perm@flux
            eb = 3*h*h*num["Omega_n"]
            lam = 3*h*h*num["Omega_Lambda"]
            mm = frame(np.zeros((3,3)),aa,h,ss,eb,qb,lam)
            hs = 3*h*h+abs(eb)+abs(lam)+.5*np.sum(ss*ss)+.5*abs(mm["scalar"])
            ms = 3*np.linalg.norm(aa)*np.linalg.norm(ss)+np.linalg.norm(qb)
            lrs_max["hamiltonian"] = max(lrs_max["hamiltonian"],abs(mm["hamiltonian_residual"])/hs)
            lrs_max["momentum"] = max(lrs_max["momentum"],np.linalg.norm(mm["momentum_residual"])/ms if ms else 0.)
            lrs_max["lambda_negative_roundoff"] = max(lrs_max["lambda_negative_roundoff"],max(0.,-lam)/hs)
            lrs_max["speed"] = max(lrs_max["speed"],abs(beta))
            assert abs(mm["hamiltonian_residual"])/hs <= 1e-12
            if ms: assert np.linalg.norm(mm["momentum_residual"])/ms <= 1e-12
            assert lam >= -TOL*hs
            assert np.isclose(mm["momentum"][0],6*aa[0]*h*num["z_s"],atol=TOL*ms)
            physical = row["matter_velocity_status"]
            assert physical in ("DEFINED","UNDEFINED_ABSENT_MATTER")
            if physical == "DEFINED": assert np.isclose(float(row["beta_physical"]),beta)
            else: assert row["beta_physical"] == ""
            lrs.append({"row":index,"K":kval,"w":num["w"],"u":num["u"],"beta_speed_v_over_c":beta,
                        "beta_physical":None if physical!="DEFINED" else beta,
                        "matter_velocity_status":physical,"normal_vorticity_status":row["normal_vorticity_status"],
                        "matter_vorticity_status":row["matter_vorticity_status"],
                        "n_bar":np.zeros((3,3)),"a_bar":aa,"h_bar":h,"S_bar":ss,
                        "epsilon_N_J_m3":eb*U*U/KAPPA,"q_J_m3":qb*U*U/KAPPA,
                        "pressure_J_m3":3*h*h*num["pressure"]*U*U/KAPPA,
                        "pi_J_m3":3*h*h*perm@pi@perm.T*U*U/KAPPA,
                        "beta_vector":perm@vb,"Lambda_m_inverse2":lam*U*U,
                        "hamiltonian_residual_bar":mm["hamiltonian_residual"],
                        "momentum_residual_bar":mm["momentum_residual"]})
            parity[(round(kval,12),round(num["w"],12),round(num["u"],12),round(beta,12))] = lrs[-1]
    assert len(lrs) == 280
    assert lrs_max["hamiltonian"] <= 1e-12 and lrs_max["momentum"] <= 1e-12
    parity_max = 0.
    for key, row in parity.items():
        counterpart = parity.get((*key[:3],-key[3]))
        if counterpart is None: continue
        for field in ("S_bar","q_J_m3","beta_vector"):
            ar, br = np.asarray(row[field]), np.asarray(counterpart[field])
            scale = max(np.linalg.norm(ar),np.linalg.norm(br))
            parity_max=max(parity_max,float(np.linalg.norm(ar+br)/scale) if scale else 0.)
        for field in ("epsilon_N_J_m3","pressure_J_m3","pi_J_m3"):
            ar, br = np.asarray(row[field]), np.asarray(counterpart[field])
            scale=max(np.linalg.norm(ar),np.linalg.norm(br))
            parity_max=max(parity_max,float(np.linalg.norm(ar-br)/scale) if scale else 0.)
    assert parity_max <= 1e-12
    with (HERE/"UNCERTAINTY_PROBES.jsonl").open("w") as fh:
        for row in rows: fh.write(json.dumps(row,default=native,allow_nan=False)+"\n")
    with (HERE/"LRS280.jsonl").open("w") as fh:
        for row in lrs: fh.write(json.dumps(row,default=native,allow_nan=False)+"\n")
    fig, axes = plt.subplots(1,3,figsize=(17,5),layout="constrained")
    colors = {"II":"tab:blue","VII0matched":"tab:orange","I":"tab:green","flatVII0":"tab:red"}
    for name in images:
        rr = [r for r in rows if r["center"]==name]
        axes[0].scatter([r["scalar"] for r in rr],[r["x_D"] for r in rr],s=2,alpha=.18,color=colors[name],label=name)
        yy = images[name]["Y0"]; bb=images[name]
        axes[0].errorbar(float(w_scalar@yy),float(w_d@yy),xerr=bb["scalar_bound"]["radius"],
                         yerr=bb["x_D_bound"]["radius"],fmt="o",color=colors[name],capsize=2)
        axs = np.array([float(w_scalar@np.array(r["linearY"])) for r in rr])
        ays = np.array([float(w_d@np.array(r["linearY"])) for r in rr])
        axes[0].scatter(axs,ays,s=1,alpha=.08,color=colors[name])
    axes[0].set(xlabel=r"$^3R/u_*^2$",ylabel=r"$D:^3R/u_*^2$",title="Direct probes, tangent images, whole-set boxes")
    axes[0].legend(fontsize=8)
    for index,name in enumerate(images):
        eig=signatures[name]; radius=images[name]["ricci_F_bound"]
        axes[1].errorbar(np.arange(3)+index*.08,eig,yerr=radius,fmt="o",capsize=2,label=name)
    axes[1].set(xlabel="sorted Ricci eigenvalue index",ylabel=r"$^3R_{ij}/u_*^2$",title="Centers with conservative tensor radii")
    axes[1].set_xticks(range(3)); axes[1].legend(fontsize=8)
    for index,name in enumerate(images):
        sig=images[name]["geometry_svd"]["singular_values"]
        axes[2].plot(range(1,7),sig,marker="o",label=f"{name}: rank {images[name]['geometry_svd']['rank']}")
    axes[2].set(xlabel="singular index",ylabel="normalized geometry singular value",title="Exact-zero I and flat rank branch")
    axes[2].legend(fontsize=8)
    fig.suptitle(r"Synthetic deterministic tensor uncertainty; $u_*=10^{-26}$ m$^{-1}$; flat I/VII$_0$ are locally equivalent")
    fig.savefig(HERE/"GEOMETRY_IMAGE.png",dpi=200); fig.savefig(HERE/"GEOMETRY_IMAGE.pdf")
    plt.close(fig)
    with (HERE/"TABLE.json").open("w") as fh:
        json.dump({"controls":controls,"mixed":{"ricci":mixed["ricci"],"ricci_stf":mixed["ricci_stf"],
                   "structure":mixed["structure"],"connection":mixed["connection"],
                   "riemann":mixed["riemann"],"extrinsic":mixed["extrinsic"],"q_bar":mixed["momentum"],
                   "epsilon_bar":mixed_e,"invalid_jacobi_rejected":invalid_rejected},
                   "scales":scales,"images":images,"nonlinear_I":nonlinear_i,"curved_flat":curved_flat,
                   "matched_orbit_separation":sep,"matched_tensor_radius_sum":rad_sum,
                   "matched_set_separation_status":"PROVED_BY_CONSERVATIVE_BOUND" if sep>rad_sum else "BOUND_INCONCLUSIVE",
                   "lrs280_max_residuals":lrs_max,"lrs280_signed_parity_max_relative":parity_max},fh,indent=2,default=native,allow_nan=False)
    result = {"schema":"R36-10-result-repair-01-v1","task_id":"R36-10-GEOMETRY-IMAGE",
              "packet_id":"8da987a1500dc1afc4b9167e4e46de07bddb4a2bff47268daf108918f3a9e424",
              "base_packet_id":"5a748e12c1d19b5a4e636c7f31a92d772ee083ca84c2e723a98946f0a9c185d9",
              "base_candidate_identity":"sha256:54ae8c59cb6c0d144cb9798079f357bdfba6254694cb416bf5a14f3a59160423",
              "repair_plan_identity":"da72e7c2e926cff9b87f4f7da489d84e7b8e2b597d60a979c9cb9c0476102144",
              "input_identity":contract["input_identity"],"contract_sha256":sha(CONTRACT),
              "source_bindings":seals,"source_count":len(seals),"status":"REPAIR_CANDIDATE_PENDING_TARGETED_INDEPENDENT_CLOSEOUT",
              "owner":"common", "scope":"finite instantaneous presolver geometry compatibility",
              "claim_tier":"diagnostic-only finite algebraic result", "transfer_source":"none",
              "generating_command":"python -B geometry_image.py",
              "caveats":["synthetic uncertainty, no empirical covariance", "no evolution or transfer response",
                         "local geometry and group presentation differ", "no family identification"],
              "frame":"oriented orthonormal triad, epsilon123=+1, proper SO(3), signature (-,+,+,+)",
              "units":{"u_star_m_inverse":U,"c_m_s":C,"G_m3_kg_s2":G,"kappa_m_J_inverse":KAPPA,
                       "n_a_h_S":"m^-1","Ricci_Lambda_kappa_epsilon_kappa_q":"m^-2","epsilon_q":"J/m^3"},
              "matched_pair":{"same_scalar":True,"same_h_S_epsilon_q_Lambda":True,
                              "different_Ricci_spectra":True,"orbit_center_separation":sep,
                              "conservative_tensor_radii_sum":rad_sum,
                              "whole_set_status":"SEPARATED_BY_BOUND" if sep>rad_sum else "BOUND_INCONCLUSIVE"},
              "flat_pair":"same local intrinsic Euclidean geometry in distinct simply transitive presentations",
              "uncertainty":"declared deterministic 12D ellipsoids, 577 probes per center; bounds apply to entire set, probes are visual only",
              "lrs_retained_rows":len(lrs),"beta_definition":"signed physical speed v/c, never rapidity",
              "x":"full same-frame tensor/constraint carrier in TABLE.json and LRS280.jsonl",
              "x_C":"NOT_EVALUATED_NO_FROZEN_COMPARATOR_RESPONSE",
              "Q":"NOT_EVALUATED_NO_PREMISE_ANCHOR_OR_POLICY_DENOMINATOR",
              "F":"NOT_EVALUATED_NO_OCCUPANCY_MEASURE_OR_CEILING",
              "Pi":"NOT_EVALUATED_NO_JOINT_PROBABILITY_LAW",
              "G_F":"NOT_EVALUATED_NO_DEPTH_WINDOWS_OR_JOINT_DEPTH_LAW",
              "artifacts":["TABLE.json","UNCERTAINTY_PROBES.jsonl","LRS280.jsonl","GEOMETRY_IMAGE.png","GEOMETRY_IMAGE.pdf"],
              "qualified_products_proposed":["geometry_compatibility_result"],"acceptance_met":False,
              "original42_promotion":False,"native_solver":False,"independent_review":"PENDING"}
    (HERE/"RESULT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"task_id":result["task_id"],"controls":list(controls),"geometry_ranks":{n:images[n]["geometry_svd"]["rank"] for n in images},
                      "joint_ranks":{n:images[n]["joint_svd"]["rank"] for n in images},"probes":len(rows),
                      "lrs_rows":len(lrs),"matched_set_status":result["matched_pair"]["whole_set_status"],
                      "lrs_max":lrs_max},indent=2))


if __name__ == "__main__":
    main()
