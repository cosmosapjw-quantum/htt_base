"""R98 finite, group-disjoint Planck low-ell diagnostics. Run from the repo root."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import healpy as hp
import numpy as np
import scipy
from astropy.io import fits
from scipy.linalg import solve_triangular

from scripts.r93 import smica_ffp999_biposh as r93
from scripts.r94 import gaunt_fast as gaunt
from scripts.r95.planck_fullres_teb_analysis import _all_six_spectra
from scripts.r96 import cmb_crossfit_null as r96
from scripts.r97.cmb_injection_and_eb_leakage import _match_nside2048_ols_monopole_dipole as project_ols

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/research_program/observational_publication_20261015"
OUT = DOCS / "R98_FOURTH_RESEARCH_CYCLE_20261123"
RAW = Path("/mnt/extdrive/workdir/raw")
LMAX = 48
BANDS = ((2, 8), (9, 16), (17, 32), (33, 48))
SRC = Path(__file__).resolve()
CHANNELS = ("T", "E", "B")


def environment():
    return {"base_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "script_sha256": gaunt.sha(SRC), "python": sys.version, "numpy": np.__version__,
            "scipy": scipy.__version__, "healpy": hp.__version__, "system": platform.platform(),
            "OMP_NUM_THREADS": os.getenv("OMP_NUM_THREADS"), "OPENBLAS_NUM_THREADS": os.getenv("OPENBLAS_NUM_THREADS"),
            "command": [sys.executable, "-m", "scripts.r98.cmb_full", *sys.argv[1:]]}


def output(name, obj):
    path = OUT / name
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1, allow_nan=False) + "\n")
    tmp.replace(path)


def split_paths():
    common = RAW / "planck_data"
    hm = RAW / "planck_pr3_smica_hm_20261015"
    extras = RAW / "planck_pr3_targeted_inputs_20261015"
    masks = {
        "common_I": common / "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits",
        "common_P": common / "COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits",
        "hm_I": hm / "COM_Mask_CMB-HM-Misspix-Mask-Int_2048_R3.00.fits",
        "hm_P": extras / "COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits",
        "oe_I": extras / "COM_Mask_CMB-OE-Misspix-Mask-Int_2048_R3.00.fits",
        "oe_P": extras / "COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits"}
    maps = {}
    for pipe, split, directory in (("smica", "hm", hm), ("smica", "oe", extras), ("nilc", "hm", extras)):
        for half in (1, 2):
            tag = f"{pipe}_{split}{half}"
            maps[tag] = directory / f"COM_CMB_IQU-{pipe}_2048_R3.00_{split}{half}.fits"
    for pipe in ("smica", "commander", "nilc", "sevem"):
        version = "3.01" if pipe == "sevem" else "3.00"
        directory = common if pipe in ("smica", "commander") else RAW / "planck_pr3_component_controls"
        maps[pipe + "_full"] = directory / f"COM_CMB_IQU-{pipe}_2048_R{version}_full.fits"
    return masks, maps


def nested_field(ext, name):
    if ext.header.get("NSIDE") != 2048 or ext.header.get("ORDERING") != "NESTED":
        raise ValueError("Unexpected observed FITS coordinates")
    return ext.data[name].reshape(-1)


def split_support(masks):
    support = []
    for chan in ("I", "P"):
        w = None
        for key in ("common", "hm", "oe"):
            with fits.open(masks[f"{key}_{chan}"], memmap=True) as hdul:
                field = nested_field(hdul[1], "TMASK" if chan == "I" else "PMASK")
                # PR3 binary common and coverage flags; reject polarity/encoding drift.
                if not np.all((field == 1) | (field == 0)):
                    raise ValueError("Expected binary PR3 coverage mask")
                if w is None:
                    w = field.astype(bool)
                else:
                    w &= field.astype(bool)
        support.append(w)
    return support


def support_basis(intensity):
    w = hp.reorder(intensity.astype(np.float64), n2r=True)
    basis = [hp.map2alm(w, lmax=LMAX, iter=0, pol=False)]
    n = len(w)
    for axis in range(3):
        b = np.empty_like(w)
        for start in range(0, n, 1_000_000):
            stop = min(start + 1_000_000, n)
            xyz = hp.pix2vec(2048, np.arange(start, stop))
            b[start:stop] = w[start:stop] * xyz[axis]
        basis.append(hp.map2alm(b, lmax=LMAX, iter=0, pol=False))
    return np.stack(basis)


def observed_alm(path, support, basis):
    def stokes(ext, index):
        name = ("I_STOKES", "Q_STOKES", "U_STOKES")[index]
        if ext.columns[name].unit != "K_CMB":
            raise ValueError("Unexpected thermodynamic units")
        field = nested_field(ext, name)
        w = support[int(index > 0)]
        masked = np.zeros(len(w), dtype=np.float64)
        np.multiply(field, 1e6, where=w, out=masked, dtype=np.float64)
        if not np.all(np.isfinite(masked)) or np.max(np.abs(masked)) > 1e8:
            raise ValueError(f"Invalid data inside common analysis support: {path.name}/{name}")
        return hp.reorder(masked, n2r=True)
    with fits.open(path, memmap=True) as h:
        t = hp.map2alm(stokes(h[1], 0), lmax=LMAX, iter=0, pol=False)
        e, b = hp.map2alm_spin([stokes(h[1], 1), stokes(h[1], 2)], spin=2, lmax=LMAX)
    return project_ols(np.stack([t, e, b]), basis, LMAX)


def split_power(a1, a2):
    """Mode-count-weighted pseudo powers on the same sky support."""
    spectra = [hp.alm2cl(a1), hp.alm2cl(a2), hp.alm2cl(a1, a2),
               hp.alm2cl((a1 + a2) / 2), hp.alm2cl((a1 - a2) / 2)]
    aa, bb, ab, positive, negative = spectra
    error = max(np.max(abs(positive - negative - ab)),
                np.max(abs(positive + negative - (aa + bb) / 2)))
    if error > 2e-12 * max(1.0, np.max(aa), np.max(bb)):
        raise ArithmeticError("Split power identity failed")
    rec = {}
    for lo, hi in ((2, 48), *BANDS):
        w = np.arange(2 * lo + 1, 2 * hi + 2, 2)
        aa_b, bb_b, ab_b, pos, neg = (float(np.average(x[lo:hi+1], weights=w)) for x in spectra)
        rec[f"{lo}-{hi}"] = {"coadd_uK2": pos, "half_difference_uK2": neg,
                               "cross_uK2": ab_b, "half_difference_over_coadd": neg / pos,
                               "cross_correlation": ab_b / np.sqrt(aa_b * bb_b)}
    return rec, float(error)


def run_splits():
    start = time.monotonic()
    masks, maps = split_paths()
    identity = {}
    support = split_support(masks)
    basis = support_basis(support[0])
    for key, path in masks.items():
        identity[key] = {"path": str(path), "sha256": gaunt.sha(path), "size": path.stat().st_size}
    alms = {}
    for key, path in maps.items():
        print(f"observed harmonic transform {key}", flush=True)
        identity[key] = {"path": str(path), "sha256": gaunt.sha(path), "size": path.stat().st_size}
        alms[key] = observed_alm(path, support, basis)
    cmp_pairs = [(p+"1", p+"2") for p in ("smica_hm", "smica_oe", "nilc_hm")]
    for p in ("smica_hm", "smica_oe", "nilc_hm"):
        alms[p + "_mean"] = (alms[p+"1"] + alms[p+"2"]) / 2
    cmp_pairs.extend([("smica_hm_mean", "smica_oe_mean"), ("smica_hm_mean", "nilc_hm_mean"),
                      ("smica_full", "smica_hm_mean"), ("smica_full", "smica_oe_mean"),
                      ("nilc_full", "nilc_hm_mean"), ("smica_full", "nilc_full"),
                      ("smica_full", "sevem_full"), ("smica_full", "commander_full")])
    rows = {}
    worst = 0.0
    for key1, key2 in cmp_pairs:
        row = {}
        for j, name in enumerate(CHANNELS):
            row[name], err = split_power(alms[key1][j], alms[key2][j])
            worst = max(worst, err)
        rows[f"{key1}__{key2}"] = row
    sums = [int(np.count_nonzero(w)) for w in support]
    return {"scope": "same-sky observational split and component-separation consistency",
            "owner": "HTT/obsstat/P2", "claim_tier": "conditional_diagnostic", "environment": environment(),
            "nside": 2048, "lmax": LMAX, "input_units": "K_CMB", "output_spectra_units": "uK_CMB^2",
            "support": "intersection of PR3 common, half-mission and odd-even coverage separately in intensity and polarization; positive=1",
            "retained_pixels_I_P": sums, "sky_fraction_I_P": [x/len(support[0]) for x in sums],
            "input_identities": identity, "split_and_method_comparisons": rows,
            "max_split_algebra_err_uK2": worst, "elapsed_s": time.monotonic()-start,
            "commander_null_qualified": False, "null_status": "shared observed sky; no split-matched simulation ranking",
            "instrument_transfer": "supplied PR3 maps, their native transfer; no extra beam smoothing or deconvolution"}

def group_weights(groups):
    _, inverse, counts = np.unique(groups, return_inverse=True, return_counts=True)
    return 1.0 / (len(counts) * counts[inverse])


def fit_gaussian(x, w, shrink):
    mu = w @ x
    z = x - mu
    cov = z.T @ (w[:, None] * z)
    sd = np.sqrt(np.diag(cov))
    if np.any(sd <= 0) or not np.isfinite(sd).all():
        raise ValueError("Degenerate feature")
    corr = cov / np.outer(sd, sd)
    shrunk = (1-shrink) * corr + shrink * np.eye(x.shape[1])
    chol = np.linalg.cholesky(shrunk)
    logdet = 2 * np.sum(np.log(sd) + np.log(np.diag(chol)))
    return mu, sd, chol, float(logdet)


def scores(model, x):
    mu, sd, chol, logdet = model
    z = solve_triangular(chol, ((x-mu)/sd).T, lower=True)
    q = np.sum(z*z, axis=0)
    return q, 0.5 * (q + logdet + len(mu)*np.log(2*np.pi))


def fit_shear(train, w):
    u, b = train[:, :40], train[:, 40:]
    mu, bmu = w @ u, w @ b
    sd = np.sqrt(w @ ((u - mu)**2))
    z = (u-mu)/sd
    beta = np.linalg.solve(z.T @ (w[:, None]*z) + 10*np.eye(40), z.T @ (w[:, None]*(b-bmu)))
    return mu, sd, bmu, beta


def apply_shear(x, coeff):
    mu, sd, bmu, beta = coeff
    return np.column_stack([x[:, :40], x[:, 40:] - bmu - ((x[:, :40]-mu)/sd) @ beta])


def project_features(a, terms, backend="native"):
    return np.column_stack([gaunt.project(a[:, j], terms[j], backend=backend).reshape(len(a), 20)
                            for j in range(3)])


def train_terms(paired, w):
    auto = _all_six_spectra(paired, LMAX)
    c = np.zeros((3, LMAX+1))
    c[0] = r93.iso_theory_cl()
    for j, label in enumerate(("EE", "BB"), start=1):
        c[j, 2:] = np.maximum(w @ auto[label][:, 2:], 1e-12)
    return [gaunt.build_terms(row, LMAX) for row in c], c


def digest_array(a):
    import hashlib
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def matched_source():
    ids, pair, signal, noise, smica, man = r96.load()
    stream = r96.STREAM
    files = [r96.MANIFEST, stream/"alm_basis_lmax48.npz", r93.THEORY,
             stream/"noise_300_TEB_alm.npz", stream/"observed_smica_commander_TEB_alm.npz"]
    digests = {str(f): gaunt.sha(f) for f in files}
    if digests[str(files[3])] != man["noise_master_sha256"] or digests[str(files[4])] != man["observed_info"]["sha256"]:
        raise ValueError("Observation/noise cache drift")
    if len(man["cmb_chunks"]) != 40 or len(man["noise_chunks"]) != 6:
        raise ValueError("Source chunk coverage drift")
    for rec in man["cmb_chunks"]:
        f = stream / rec["chunk"]
        with np.load(f, allow_pickle=False) as d:
            np.testing.assert_array_equal(d["cmb_ids"], rec["ids"])
            np.testing.assert_array_equal(d["noise_ids"], d["cmb_ids"] % 300)
        # r96.load() checked this exact digest before decoding its harmonic arrays.
        digests[str(f)] = rec["sha256"]
    unique_noise = []
    for rec in man["noise_chunks"]:
        f = stream / rec["chunk"]
        if gaunt.sha(f) != rec["sha256"]:
            raise ValueError("Per-chunk noise digest drift")
        with np.load(f, allow_pickle=False) as d:
            np.testing.assert_array_equal(d["TEB_alm"], noise[d["noise_ids"]])
            unique_noise.extend(d["noise_ids"].tolist())
        digests[str(f)] = rec["sha256"]
    np.testing.assert_array_equal(sorted(unique_noise), np.arange(300))
    with np.load(files[1], allow_pickle=False) as f:
        basis = f["basis_T_alm"]
        if any(str(f[k]) != man["basis_meta"][k] for k in ("maskI_sha256", "maskP_sha256")):
            raise ValueError("OLS mask binding drift")
    with np.load(files[4], allow_pickle=False) as d:
        commander = d["commander_TEB_n2048sub"]
        smica64 = d["smica_TEB_n64sub"]
    obs_err = float(np.max(abs(project_ols(smica64, basis, LMAX) - smica)))
    if obs_err > 1e-12:
        raise ValueError("Cannot recover observed NSIDE2048 OLS")
    clean = [project_ols(x, basis, LMAX) for x in (pair, signal, noise)]
    delta = clean[0] - clean[1] - clean[2][ids % 300]
    rel = np.linalg.norm(delta, axis=2) / np.maximum(np.linalg.norm(clean[0], axis=2), 1e-15)
    if np.max(rel) > 1e-6:
        raise ValueError("Signal/noise cache or ID mismatch beyond complex64 precision")
    sources = [ROOT/"scripts/r94/gaunt_fast.py", gaunt.CPP, gaunt._native_so(compile_if_needed=False)[1],
               ROOT/"scripts/r93/smica_ffp999_biposh.py", ROOT/"scripts/r95/stream_fullres_fast.py",
               ROOT/"scripts/r95/planck_fullres_teb_analysis.py", ROOT/"scripts/r96/cmb_crossfit_null.py",
               ROOT/"scripts/r97/cmb_injection_and_eb_leakage.py", r96.R95,
               DOCS/"R97_SCIENCE_EXECUTION_20261122/CMB_INJECTION_AND_EB_LEAKAGE.json"]
    digests.update({str(f): gaunt.sha(f) for f in sources})
    checks = {"observed_ols_recovery_max_uK": obs_err, "linear_pair_sum_max_relative_T_E_B": rel.max(axis=0).tolist(),
              "cache_fits_source_warnings": man["warnings_log"], "new_raw_mc_fits_rehash": False,
              "mask_shas_from_basis_and_manifest": man["basis_meta"], "per_chunk_noise_and_master_byte_values_match": True}
    return ids, *clean, np.stack([smica, commander]), digests, checks


def variance_budget(pair, sig, noise, sd, groups):
    """Gram of standardized components. Sum of all nine entries equals total variance."""
    parts = np.stack([sig, noise, pair-sig-noise], axis=1) / sd
    w = group_weights(groups)
    parts -= np.einsum("n,nkd->kd", w, parts)
    z = (pair - w @ pair) / sd
    cov = np.einsum("n,nid,njd->ij", w, parts, parts)
    total = w @ np.sum(z*z, axis=1)
    np.testing.assert_allclose(cov.sum(), total, rtol=2e-12)
    return (cov / total).tolist()


def finite_summary(scores_te, qobs, ids, groups):
    exceed = scores_te >= qobs
    first = ids == groups
    if first.sum() != len(np.unique(groups)):
        raise ValueError("First realization unavailable")
    count_first = int(exceed[first].sum())
    return {"smica_score": float(qobs), "all_paired_exceed": int(exceed.sum()),
            "group_balanced_tail": float(group_weights(groups) @ exceed),
            "first_rep_exceed": count_first, "first_rep_N": int(first.sum()),
            "first_rep_add_one_rank": (1+count_first)/(1+int(first.sum())),
            "heldout_q50_q95_q99": np.quantile(scores_te, [.5,.95,.99]).tolist()}


def run_cache():
    start = time.monotonic()
    ids, pair, sig, noi, obs, source_hashes, checks = matched_source()
    noise_id = ids % 300
    fold_id = noise_id % 5
    folds, oof = [], {}
    max_parity = max_shear = 0.0
    for fold in range(5):
        print(f"fitting fold {fold}", flush=True)
        test = fold_id == fold
        train = ~test
        groups = noise_id[test]
        if set(groups) & set(noise_id[train]):
            raise ValueError("Training noise held out incorrectly")
        w = group_weights(noise_id[train])
        wt = group_weights(groups)
        terms, cw = train_terms(pair[train], w)
        x = project_features(pair, terms)
        xt, xv = x[train], x[test]
        yo = project_features(obs, terms)
        # A separate vectorized backend on a test sky and both observations.
        audit = np.concatenate([pair[np.flatnonzero(test)[:1]], obs])
        reference = project_features(audit, terms, "numpy")
        native = np.vstack([xv[0], yo])
        np.testing.assert_allclose(native, reference, atol=1e-12, rtol=1e-12)
        max_parity = max(max_parity, float(abs(native-reference).max()))
        gs, which = np.unique(groups, return_inverse=True)
        ns = project_features(noi[gs], terms)[which]
        ss = project_features(sig[test], terms)
        shear = fit_shear(xt, w)
        dt, dv, dy = [apply_shear(arr, shear) for arr in (xt, xv, yo)]
        rec = {"fold": fold, "test_pair_N": len(xv), "train_pair_N": len(xt), "test_group_N": len(gs),
               "train_group_N": int(len(np.unique(noise_id[train]))), "train_weights_spectra_sha256": digest_array(cw),
               "scaled_B_prediction_mse_ratio": float((wt @ np.sum(dv[:,40:]**2, axis=1)) /
                                                        (wt @ np.sum((xv[:,40:]-shear[2])**2, axis=1)))}
        models, values, costs = {}, {}, {}
        raw = fit_gaussian(xt, w, .2)
        for name, tr, va, ob, lam in [("raw", xt, xv, yo, .2), ("ridge", dt, dv, dy, .2),
                                      ("diagonal", xt, xv, yo, 1.)]:
            model = raw if name == "raw" else fit_gaussian(tr, w, lam)
            qs, costs[name] = scores(model, va)
            qo, _ = scores(model, ob)
            values[name] = qs
            models[name] = {**finite_summary(qs, qo[0], ids[test], groups),
                            "commander_score_diagnostic_only": float(qo[1]),
                            "group_balanced_mean_nll": float(wt @ costs[name])}
        channel_q = []
        for j in range(3):
            sl = slice(20*j, 20*j+20)
            m = fit_gaussian(xt[:,sl], w, .2)
            y = np.vstack([xv[:,sl], yo[:,sl]])
            q, _ = scores(m, y)
            channel_q.append(q)
        qc = np.max(channel_q, axis=0)
        models["max_T_E_B"] = {**finite_summary(qc[:-2], qc[-2], ids[test], groups),
                                "commander_score_diagnostic_only": float(qc[-1])}
        values["max_T_E_B"] = qc[:-2]
        zr = np.vstack([xv,yo])
        zc = np.vstack([dv,dy])
        baseline = scores(fit_gaussian(xt,w,0), zr)
        transformed = scores(fit_gaussian(dt,w,0), zc)
        err = float(np.max(np.abs(np.asarray(baseline)-np.asarray(transformed))))
        max_shear = max(max_shear, err)
        if err > 1e-8:
            raise ArithmeticError("Unregularized metric violates affine invariance")
        rec.update({"models": models, "standardized_covariance_budget_signal_noise_cross_3x3":
                    variance_budget(xv,ss,ns,raw[1],groups), "unregularized_shear_error": err})
        folds.append(rec)
        for i, cid in enumerate(ids[test]):
            oof[int(cid)] = [int(groups[i]), fold, *[float(values[m][i]) for m in
                            ("raw", "ridge", "diagonal", "max_T_E_B")],
                            float(costs["ridge"][i]-costs["raw"][i]),
                            float(costs["diagonal"][i]-costs["raw"][i])]
    if sorted(oof) != ids.tolist():
        raise ArithmeticError("Out-of-fold coverage mismatch")
    summary = {}
    rows = np.array([oof[i] for i in ids])
    for j, method in enumerate(("raw","ridge","diagonal","max_T_E_B")):
        thresholds = np.array([folds[f]["models"][method]["smica_score"] for f in fold_id])
        indicator = rows[:,2+j] >= thresholds
        valid = ids != 818
        summary[method] = {"pair_exceed": int(indicator.sum()), "pair_fraction": float(indicator.mean()),
                            "group_balanced_tail": float(group_weights(noise_id) @ indicator),
                            "exclude_818_fixed_fit_group_balanced_tail": float(group_weights(noise_id[valid]) @ indicator[valid]),
                            "primary_fold0_one_per_noise_rank": folds[0]["models"][method]["first_rep_add_one_rank"]}
    checks.update({"max_Gaunt_native_numpy_abs": max_parity, "max_unshrunk_shear_q_and_nll_abs": max_shear,
                   "all_train_test_group_intersections_empty": True})
    for name,col in [("ridge",6),("diagonal",7)]:
        summary[name]["group_balanced_nll_difference_to_raw_nats"] = float(group_weights(noise_id) @ rows[:,col])
    return {"schema":"htt.r98.planck_group_disjoint_full_cache/1", "owner":"HTT/obsstat/P2",
            "claim_tier":"source_conditional_diagnostic", "sky_support_status":"PR3 common intensity/polarization full-resolution masks",
            "null_mock_status":"SMICA FFP10 with recycled noise clustered by original realization",
            "transfer_source":"masked derivative TEB cache R95, 2048 OLS R97, native R94 Gaunt; no cosmological transfer likelihood",
            "environment":environment(), "source_hashes":source_hashes, "finite_assertion":"all available cached skies evaluated on unseen noise groups",
            "coverage":{"eligible_CMB":999,"evaluated_paired":len(oof),"evaluated_cmb_only":len(ids),
                        "evaluated_distinct_noise":len(set(noise_id)),"missing_CMB_ID":970,
                        "group_size_histogram":dict(Counter(Counter(noise_id.tolist()).values()))},
            "fold_rule":"(CMB_ID % 300) % 5; all members of a noise group held out together",
            "primary":"fold 0, raw alpha=.20, CMB ID equals noise ID for the 60 calibration representatives",
            "null_interpretation":"conditional on exchangeability of SMICA and simulation; overlapping-fold ranks descriptive",
            "source_variance_terms":["signal only","noise only","paired minus signal minus noise"],
            "checks":checks, "folds":folds,"summary":summary,
            "oof_columns":["noise_id","fold","raw_score","ridge_score","diagonal_score","max_T_E_B_score",
                           "ridge_minus_raw_nll_nats","diagonal_minus_raw_nll_nats"],
            "oof_by_cmb_id":{str(i):oof[i] for i in sorted(oof)},
            "commander_null_qualified":False,"Bianchi_family_attribution":None,"physical_Q":None,"physical_Pi":None,
            "physical_F":None,"physical_GF":None,"elapsed_s":time.monotonic()-start}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("cache","splits"))
    mode = parser.parse_args().mode
    if mode == "cache":
        result = run_cache()
        output("CMB_GROUPED_FULL_CACHE.json",result)
        print(json.dumps(result["summary"]))
    else:
        result = run_splits()
        output("CMB_OBSERVED_SPLITS.json",result)
        print("complete", result["elapsed_s"], result["sky_fraction_I_P"])
