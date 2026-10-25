#!/usr/bin/env python3
"""R33 finite signed WMAP F2 extension; invoked once by supervise.py after GO."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import mpmath as mp

HERE = Path(__file__).resolve().parent
FRAME = Path("/mnt/extdrive/workdir/htt_open_data/r33_cmb_additional_frequency_framing")
OLD = Path("/mnt/extdrive/workdir/htt_open_data/r30_cmb_spectral_response_numeric/attempt_38cdf6b948a41ee9/RESULT.json")
DA = ("K1", "Ka1", "Q1", "Q2", "V1", "V2", "W1", "W2", "W3", "W4")
BANDS = (("K", ("K1",)), ("Ka", ("Ka1",)), ("Q", ("Q1", "Q2")),
         ("V", ("V1", "V2")), ("W", ("W1", "W2", "W3", "W4")))
DRIFT = {"K": .0013, "Ka": .0012, "Q": .0011, "V": .0006, "W": 0.0}
H, KB, C = 6.62607015e-34, 1.380649e-23, 299792458.0
TC, TD, NS, ND = 2.7255, 20.0, 30e9, 353e9
ORDER = "frequency-major E2,E3,B2,B3 each (m0,sqrt2 Re,-sqrt2 Im)"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spectra(nu):
    """Return CMB derivative then inherited nine intensity functions."""
    def planck(n, t):
        return 2 * H * n**3 / C**2 / np.expm1(H*n/(KB*t))
    def g(x):
        return x / -np.expm1(-x)
    def gp(x):
        q = -np.expm1(-x)
        return 1/q - x*np.exp(-x)/q**2
    x, xd, xc = H*nu/(KB*TD), H*ND/(KB*TD), H*nu/(KB*TC)
    b = planck(nu, TC)*g(xc)/TC
    bs = planck(NS, TC)*g(H*NS/(KB*TC))/TC
    bd = planck(ND, TC)*g(H*ND/(KB*TC))/TC
    s = bs*(nu/NS)**(-1)
    dust = bd*(nu/ND)**1.5*planck(nu, TD)/planck(ND, TD)
    ls, ld = np.log(nu/NS), np.log(nu/ND)
    d = g(x)-g(xd)
    e = x*gp(x)-xd*gp(xd)
    return np.stack((b, s, s*ls, dust, dust*ld, dust*d,
                     s*ls**2, dust*ld**2, dust*d*ld,
                     dust*(d**2-d-e)), axis=-1)


def read_curves():
    metadata = json.loads((FRAME/"BANDPASS_SOURCE_METADATA.json").read_text())
    expected = {e["file"]: e for e in metadata["entries"]}
    assert len(expected) == 20
    curves = {}
    for file, entry in expected.items():
        path = FRAME/"sources"/"bandpasses"/file
        assert sha(path) == entry["sha256"], ("source hash", file)
        rows = []
        for line in path.read_text("ascii").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                tokens = line.split()
                assert len(tokens) == 3, file
                rows.append(tuple(float(t) for t in tokens))
        arr = np.array(rows, dtype=np.float64)
        assert arr.shape == (201, 3) and np.isfinite(arr).all()
        assert np.all(np.diff(arr[:, 0]) > 0) and np.all(arr[:, 0] > 0)
        curves[file] = arr
    return curves


def response(curve, drift):
    nu = curve[:, 0]*1e9/(1+drift)
    spec = spectra(nu)
    out = []
    denoms = []
    cancellation = []
    unity = []
    for j in (1, 2):
        g = curve[:, j]
        term = g*spec[:, 0]/nu**2
        den = np.trapezoid(term, nu)
        assert np.isfinite(den) and den > 0
        ints = np.trapezoid(g[:, None]*spec/nu[:, None]**2, nu, axis=0)
        assert np.isfinite(ints).all()
        rj_tau = g*(NS/nu)**2
        rj_ints = np.trapezoid(rj_tau[:, None]*spec,nu,axis=0)
        rj_comparison = np.linalg.norm(ints[1:]/den-rj_ints[1:]/rj_ints[0])
        assert rj_comparison <= 1e-12
        denoms.append(float(den))
        cancellation.append(float(np.trapezoid(abs(g)*spec[:, 0]/nu**2, nu)/abs(den)))
        unity.append(float(ints[0]/den))
        out.append(ints[1:]/den)
    assert max(abs(x-1) for x in unity) <= 1e-12
    return np.array(out), denoms, cancellation, unity


def mp_derivative_control():
    """Independent differentiation of the dust t and t^2 functions."""
    mp.mp.dps = 120
    h, k, c = map(mp.mpf, ("6.62607015e-34", "1.380649e-23", "299792458"))
    tc, td, ns, nd = map(mp.mpf, ("2.7255", "20", "30000000000", "353000000000"))
    def B(n, t):
        return 2*h*n**3/c**2/mp.expm1(h*n/(k*t))
    def gg(x):
        return x/(-mp.expm1(-x))
    def gprime(x):
        q = -mp.expm1(-x)
        return 1/q-x*mp.exp(-x)/q**2
    bnd = B(nd, tc)*gg(h*nd/(k*tc))/tc
    def dust(beta, t, n):
        temp = td*(1+t)
        return bnd*(n/nd)**beta*B(n, temp)/B(nd, temp)
    errors, zeros = {}, {}
    for ghz in (20, 30, 70, 100, 217, 353, 600):
        n = mp.mpf(ghz)*10**9
        x, xd = h*n/(k*td), h*nd/(k*td)
        d = gg(x)-gg(xd)
        e = x*gprime(x)-xd*gprime(xd)
        analytic = (dust(mp.mpf("1.5"), 0, n)*d,
                    dust(mp.mpf("1.5"), 0, n)*(d*d-d-e))
        direct = (mp.diff(lambda t: dust(mp.mpf("1.5"), t, n), 0),
                  mp.diff(lambda t: dust(mp.mpf("1.5"), t, n), 0, 2))
        errors[str(ghz)] = [float(abs(a-b)/max(1, abs(b))) for a,b in zip(analytic,direct)]
        assert max(errors[str(ghz)]) <= 1e-30
        if ghz == 353:
            zeros["dust_t_at_reference"] = float(abs(analytic[0]))
            zeros["dust_beta_at_reference"] = float(abs(dust(mp.mpf("1.5"),0,n)*mp.log(n/nd)))
            assert max(zeros.values()) <= 1e-30
        if ghz == 30:
            bs = B(ns,tc)*gg(h*ns/(k*tc))/tc
            zeros["synch_beta_at_reference"] = float(abs(bs*(n/ns)**(-1)*mp.log(n/ns)))
            assert zeros["synch_beta_at_reference"] <= 1e-30
    return {"relative_scaled_errors": errors, "reference_zeros": zeros}


def ranks(s):
    return int(np.sum(s >= 1e-10)), int(np.sum((s > 1e-12) & (s < 1e-10)))


def assess(F):
    n = F.shape[0]
    assert F.shape == (n, 9) and n in (12, 17) and np.isfinite(F).all()
    a = np.ones(n)
    scales = np.linalg.norm(F, axis=0)
    assert np.all(scales > 0)
    G = F/scales
    U, s, _ = np.linalg.svd(G, full_matrices=True)
    sa = np.linalg.svd(np.column_stack((G, a/np.linalg.norm(a))), compute_uv=False)
    rank, ambiguous = ranks(s)
    augmented, ambiguous_aug = ranks(sa)
    p = a-U[:, :rank]@(U[:, :rank].T@a)
    d = float(np.linalg.norm(p)/np.linalg.norm(a))
    answer = {
        "raw_matrix": F.tolist(), "column_scales": scales.tolist(),
        "normalized_singular_values": s.tolist(),
        "normalized_augmented_singular_values": sa.tolist(),
        "resolved_nuisance_rank": rank, "resolved_augmented_rank": augmented,
        "rank_increments_from_accepted_7": [rank-7, augmented-7],
        "ambiguous_nuisance_count": ambiguous, "ambiguous_augmented_count": ambiguous_aug,
        "principal_angle_sine": d, "principal_angle_rad": float(np.arcsin(min(1., d))),
        "resolved_condition": float(s[0]/s[rank-1]) if rank else None,
        "tensor_dimensions": {"A": [24*n, 24], "B": [24*n, 216]},
        "coordinate_order": ORDER, "status": "NUMERIC_RANK_HOLD"
    }
    # Explicit full24 basis action arrays; these are synthetic operator controls.
    A = np.kron(a[:, None], np.eye(24))
    B = np.kron(F, np.eye(24))
    if rank == 9 and augmented == 10 and not (ambiguous or ambiguous_aug) and d >= 1e-10:
        w = p/(a@p)
        H = np.kron(w[None, :], np.eye(24))
        ha = H@A-np.eye(24)
        hb = H@B
        wa, wf = float(w@a), (w@G).tolist()
        ares, bres = np.linalg.norm(ha, axis=0), np.linalg.norm(hb, axis=0)
        assert abs(wa-1) <= 1e-9 and np.linalg.norm(w@G) <= 1e-9
        assert max(ares) <= 1e-9 and max(bres) <= 1e-9
        answer.update(status="RESOLVED_FINITE_F2_QUOTIENT", w=w.tolist(),
            wTa=wa, wTF_normalized=wf, w_norm2=float(np.linalg.norm(w)),
            w_norm1=float(np.linalg.norm(w,1)), w_norminf=float(np.linalg.norm(w,np.inf)),
            full24_HA_column_residuals=ares.tolist(), full24_HB_column_residuals=bres.tolist(),
            full24_identified_target_rank=24)
    elif rank == 9 and augmented == rank and d <= 1e-12 and not (ambiguous or ambiguous_aug):
        coeff = np.linalg.lstsq(F, a, rcond=1e-12)[0]
        rel = float(np.linalg.norm(F@coeff-a)/np.linalg.norm(a))
        action = A-B@np.kron(coeff[:,None], np.eye(24))
        residual = np.linalg.norm(action, axis=0)/np.linalg.norm(A, axis=0)
        assert rel <= 1e-10 and max(residual) <= 1e-9
        answer.update(status="NUMERICAL_F2_CONFOUNDING", c=coeff.tolist(),
            reconstruction_relative_residual=rel,
            full24_degeneracy_relative_residuals=residual.tolist(),
            full24_identified_target_rank=0)
    return answer


def synthetic_controls(F, result):
    n = len(F)
    a = np.ones(n)
    G = F/np.linalg.norm(F, axis=0)
    s = np.linalg.svd(G, compute_uv=False)
    rank, _ = ranks(s)
    dup = G.copy()
    dup[:, 1] = dup[:, 0]
    dup_rank, _ = ranks(np.linalg.svd(dup, compute_uv=False))
    assert dup_rank < rank
    injected = np.column_stack((G, a/np.linalg.norm(a)))
    confounded = np.linalg.norm(a-injected@np.linalg.lstsq(injected,a,rcond=1e-12)[0])/np.linalg.norm(a)
    assert confounded <= 1e-12
    injected_raw = np.column_stack((F,a))
    synthetic_coefficients = np.r_[np.zeros(9),1.]
    full24 = (np.kron(a[:,None], np.eye(24))-
              np.kron(injected_raw,np.eye(24))@
              np.kron(synthetic_coefficients[:,None],np.eye(24)))
    blackbody_basis_residuals = (np.linalg.norm(full24,axis=0)/np.sqrt(n)).tolist()
    assert max(blackbody_basis_residuals) <= 1e-12
    factors = np.array([1., 3., .1, 7., .3, 5., 2., .2, 11.])
    resc = G*factors
    r2, _ = ranks(np.linalg.svd(resc/np.linalg.norm(resc,axis=0), compute_uv=False))
    assert r2 == rank
    return {"duplicate_nuisance_rank": dup_rank, "original_rank": rank,
            "injected_blackbody_relative_residual": float(confounded),
            "injected_blackbody_full24_basis_residuals": blackbody_basis_residuals,
            "rescaled_rank": r2, "synthetic_only": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    curves = read_curves()
    old = json.loads(OLD.read_text())["branches"]
    assert len(old) == 6
    result = {"task_id": "R33-CMB-WMAP-PLANCK-F2-EXTENSION",
              "status": "PRODUCER_COMPUTED_PENDING_INDEPENDENT_CHECK",
              "claim_tier": "C0", "sky_data": "NOT_CONSUMED",
              "old_planck_sha256": sha(OLD), "old_planck_reintegration": False,
              "derivative_controls": mp_derivative_control(),
              "branches": {}, "diagnostic_bundle": {
                  "x": "NOT_MEASURED", "observed_quotient_tensor": "NOT_MEASURED",
                  "Q": "NOT_EVALUATED", "F_physical": "NOT_EVALUABLE",
                  "Pi": "NOT_CALIBRATED", "G_F": "NOT_APPLICABLE_FREQUENCY_IS_NOT_DEPTH"}}
    for wbranch in ("W0_LITERAL", "W1_CENTER_DRIFT_PROXY"):
        detectors, denoms, cancellation, unity = [], [], [], []
        radiometers = {}
        for da in DA:
            band = "Ka" if da.startswith("Ka") else da[0]
            drift = DRIFT[band] if wbranch.startswith("W1") else 0.
            for r in (1, 2):
                name = f"wmap_bandpass_{da}{r}_v5.cbp"
                resp, ds, cs, us = response(curves[name], drift)
                detectors.extend(resp.tolist())
                denoms.extend(ds)
                cancellation.extend(cs)
                unity.extend(us)
                radiometers[f"{da}{r}"] = resp.mean(axis=0)
        det = np.asarray(detectors)
        assert det.shape == (40,9) and max(abs(u-1) for u in unity) <= 1e-12
        da_rows = np.array([(radiometers[f"{d}1"]+radiometers[f"{d}2"])/2 for d in DA])
        assert np.allclose(da_rows,det.reshape(10,4,9).mean(axis=1),rtol=0,atol=1e-13)
        band_rows = np.array([da_rows[[DA.index(d) for d in members]].mean(axis=0)
                              for _, members in BANDS])
        Cmat = np.zeros((12,17))
        Cmat[:7,:7] = np.eye(7)
        for i, (_, members) in enumerate(BANDS):
            Cmat[7+i,[7+DA.index(d) for d in members]] = 1/len(members)
        assert np.array_equal(Cmat@np.ones(17), np.ones(12))
        for pbranch, payload in old.items():
            P = np.asarray(payload["F2"]["matrix_7xk"], dtype=np.float64)
            assert P.shape == (7,9) and np.isfinite(P).all()
            assert np.array_equal(P[:,:5], np.asarray(payload["F1"]["matrix_7xk"], dtype=np.float64))
            F17 = np.vstack((P, da_rows))
            F12 = np.vstack((P, band_rows))
            compression_error = np.linalg.norm(F12-Cmat@F17)/max(1,np.linalg.norm(F12))
            assert compression_error <= 1e-13 and np.array_equal(F17[:7],P)
            a17, a12 = np.ones(17), np.ones(12)
            r17, r12 = assess(F17), assess(F12)
            lifted = None
            if r12["status"] == "RESOLVED_FINITE_F2_QUOTIENT":
                lift = Cmat.T@np.array(r12["w"])
                H12 = np.kron(np.asarray(r12["w"])[None,:],np.eye(24))
                HC = H12@np.kron(Cmat,np.eye(24))
                Hl = np.kron(lift[None,:],np.eye(24))
                lift_basis_error = np.linalg.norm(HC-Hl,axis=0)
                lifted = {"w17": lift.tolist(), "Ctw_a": float(lift@a17),
                          "Ctw_F17_norm": float(np.linalg.norm(lift@F17)),
                          "response_error": float(abs(lift@a17-r12["wTa"])),
                          "full24_lift_column_residuals": lift_basis_error.tolist()}
                assert abs(lifted["Ctw_a"]-1) <= 1e-9 and lifted["Ctw_F17_norm"] <= 1e-9
                assert max(lift_basis_error) <= 1e-9
            result["branches"][f"{pbranch}__{wbranch}"] = {
                "Planck_branch": pbranch, "WMAP_branch": wbranch,
                "detector_matrix_40x9": det.tolist(), "DA_matrix_10x9": da_rows.tolist(),
                "band_matrix_5x9": band_rows.tolist(), "detector_denominators": denoms,
                "denominator_cancellation_factors": cancellation, "detector_CMB_unity": unity,
                "compression_C_12x17": Cmat.tolist(), "compression_relative_error": float(compression_error),
                "F17": r17, "F12": r12, "lifted_compressed_weight": lifted,
                "synthetic_controls_17": synthetic_controls(F17,r17),
                "synthetic_controls_12": synthetic_controls(F12,r12)}
    pairs = {}
    for key, item in result["branches"].items():
        pairs[key] = [item["F12"]["status"], item["F17"]["status"]]
    result["classification_pairs"] = pairs
    result["branch_independent_classification"] = len({tuple(v) for v in pairs.values()}) == 1
    out = Path(args.output)
    assert not out.exists()
    out.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
