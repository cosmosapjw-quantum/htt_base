#!/usr/bin/env python3
"""RB17/20/21 cache-only descriptive and released-Gaussian scenarios.

No calibrated p-values from estimated covariance, native solver admission,
physical response reinterpretation, or catalogue regeneration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import time

import numpy as np
from scipy.linalg import cho_factor, cho_solve


Q_GRID = (0.0, 0.25, 0.5, 0.75, 0.9)


def finite(value, name="array"):
    value = np.asarray(value, dtype=float)
    if not np.isfinite(value).all():
        raise ValueError(f"nonfinite {name}")
    return value


def spd_solve(covariance, rhs):
    c = finite(covariance, "covariance")
    if c.ndim != 2 or c.shape[0] != c.shape[1]:
        raise ValueError("square covariance required")
    if not np.allclose(c, c.T, rtol=1e-11, atol=0):
        raise ValueError("asymmetric covariance")
    return cho_solve(cho_factor(c, lower=True), finite(rhs))


def amplitude_fit(data, reference, covariance, precision_scale=1.0):
    y, t = finite(data), finite(reference)
    if y.ndim != 1 or y.shape != t.shape or covariance.shape != (len(y), len(y)):
        raise ValueError("aligned amplitude inputs required")
    if not np.isfinite(precision_scale) or precision_scale <= 0:
        raise ValueError("positive precision scale required")
    information = float(t @ spd_solve(covariance, t))
    if information <= 0:
        raise ValueError("reference amplitude unidentified")
    amp = float(t @ spd_solve(covariance, y) / information)
    residual = y - amp * t
    return {"amplitude": amp,
            "conditional_se": float((precision_scale * information)**-.5),
            "residual_quadratic": float(precision_scale * residual @ spd_solve(covariance, residual)),
            "precision_scale": precision_scale, "data": y,
            "reference": t, "residual": residual,
            "covariance_status": "RELEASED_ESTIMATED_COVARIANCE",
            "calibrated_chi2_p": None}


def offset_profile(data, model, precision):
    residual = finite(data) - finite(model)
    p = finite(precision)
    one = np.ones(len(residual))
    information = float(one @ p @ one)
    if information <= 0:
        raise ValueError("offset unidentified")
    offset = float(one @ p @ residual / information)
    centered = residual - offset
    return offset, float(centered @ p @ centered)


def marginal_precision(precision, keep):
    """Delete nodes by marginalization, not by conditioning on discarded nodes."""
    p = finite(precision)
    keep = np.asarray(keep, dtype=int)
    if len(np.unique(keep)) != len(keep) or len(keep) == 0:
        raise ValueError("unique nonempty retained node indices required")
    c = spd_solve(p, np.eye(len(p)))
    ck = c[np.ix_(keep, keep)]
    return spd_solve(ck, np.eye(len(keep)))


def mean_covariances_by_box(y, box):
    """Return covariance of feature rows and two covariance-of-mean scenarios."""
    y = finite(y)
    box = np.asarray(box)
    if y.ndim != 2 or box.shape != (len(y),) or not np.issubdtype(box.dtype, np.integer):
        raise ValueError("aligned feature matrix and integer boxes required")
    ids = np.unique(box)
    if len(ids) < 2 or len(y) < 2:
        raise ValueError("at least two boxes required")
    centered = y - y.mean(0)
    sums = np.stack([centered[box == b].sum(0) for b in ids])
    covariance = np.atleast_2d(np.cov(y, rowvar=False, ddof=1))
    cluster_mean = len(ids) / (len(ids) - 1) * sums.T @ sums / len(y)**2
    return covariance, covariance / len(y), cluster_mean


def covariance_shape(covariance):
    c = finite(covariance)
    sd = np.sqrt(np.diag(c))
    if np.any(sd <= 0):
        raise ValueError("zero or negative feature variance")
    correlation = c / np.outer(sd, sd)
    eigenvalues = np.linalg.eigvalsh(correlation)
    if eigenvalues.min() < -1e-10:
        raise ValueError("negative covariance eigenvalue")
    eigenvalues = np.maximum(eigenvalues, 0)
    return {"correlation_eigenvalues": eigenvalues,
            "participation_rank": float(eigenvalues.sum()**2 / (eigenvalues @ eigenvalues))}


def json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def source_receipt(path, root):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    try:
        name = str(path.relative_to(root))
    except ValueError:
        name = str(path)
    return {"path": name, "sha256": digest.hexdigest(), "size_bytes": path.stat().st_size}


def lensing(root):
    base = root / "workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2"
    files = [base / f for f in ("clkk_bandpowers_act.txt", "clkk_bandpowers_planck.txt",
             "binning_matrix_act.txt", "binning_matrix_planck.txt", "covmat_act_cmbmarg.txt",
             "covmat_actplanck_cmbmarg.txt", "README",
             "like_corrs/cosmo2017_10K_acc3_lenspotentialCls.dat")]
    y = finite(np.loadtxt(files[0])); yp = finite(np.loadtxt(files[1]))
    wa = finite(np.loadtxt(files[2])); wp = finite(np.loadtxt(files[3]))
    ca = finite(np.loadtxt(files[4])); cj = finite(np.loadtxt(files[5]))
    if (y.shape != (18,) or yp.shape != (9,) or wa.shape != (18, 3000)
            or wp.shape != (9, 3000) or ca.shape != (18, 18) or cj.shape != (27, 27)):
        raise ValueError("ACT v1.2 release shape mismatch")
    fid = finite(np.loadtxt(files[-1]))
    ell = fid[:, 0].astype(int)
    if np.any(fid[:, 0] != ell) or not np.array_equal(ell, np.arange(2, 2 + len(ell))):
        raise ValueError("released fiducial ell ordering mismatch")
    if ell[-1] < 2999:
        raise ValueError("fiducial does not cover released window")
    kk = np.zeros(3000)
    available = ell < 3000
    kk[ell[available]] = fid[available, 5] * np.pi / 2
    scenarios = []
    for extended in (False, True):
        sel = np.arange(18)[2:-3 if extended else -6]
        for joint in (False, True):
            idx = np.r_[sel, np.arange(18, 27)] if joint else sel
            data = np.r_[y[sel], yp] if joint else y[sel]
            theory = np.r_[(wa @ kk)[sel], wp @ kk] if joint else (wa @ kk)[sel]
            covariance = (cj if joint else ca)[np.ix_(idx, idx)]
            nsims = 400 if joint else 792
            hartlap = (nsims - len(data) - 2) / (nsims - 1)
            fit = amplitude_fit(data, theory, covariance, hartlap)
            fit.update({"name": ("act_planck" if joint else "act") +
                        ("_extended" if extended else "_baseline"),
                        "release_indices": idx, "nsims": nsims,
                        "se_without_hartlap": amplitude_fit(data, theory, covariance)["conditional_se"],
                        "ell_effective": np.r_[(wa @ np.arange(3000))[sel], wp @ np.arange(3000)]
                        if joint else (wa @ np.arange(3000))[sel]})
            if not joint:
                h796 = (796 - len(data) - 2) / 795
                fit["se_helper_default_796_sensitivity"] = amplitude_fit(data, theory, covariance, h796)["conditional_se"]
            scenarios.append(fit)
    return {"owner": "HTT", "scope": "RELEASED_FIDUCIAL_LENS_ONLY_AMPLITUDE_SCENARIOS",
            "release": "ACT DR6 lensing likelihood v1.2", "scenarios": scenarios,
            "method_source": "https://github.com/ACTCollaboration/act_dr6_lenslike/blob/main/act_dr6_lenslike/act_dr6_lenslike.py",
            "method_source_access_date": "2026-10-14",
            "conventions": ["Ckk dimensionless; released fiducial column 5 times pi/2",
                            "ACT baseline [2:-6], extended [2:-3]; ACT then all Planck bins",
                            "CMB-marginalized covariance; primary-CMB likelihood corrections disabled",
                            "ACT nsims pinned to Cobaya-class 792; helper-default 796 sensitivity supplied"],
            "caveats": ["Fixed reference shape, not a cosmological posterior",
                        "Scenarios overlap and are not independent measurements",
                        "Hartlap is a release convention, not an exact finite-sample calibration",
                        "No raw-QE or native Bianchi solver result"]}, files


def uniform_amplitude_posterior(amplitude, conditional_se, lower=0.0, upper=2.0):
    """Exact bounded-normal posterior for a uniform scalar-amplitude prior."""
    from scipy.special import ndtr, ndtri
    from scipy.stats import norm
    if not (np.isfinite(amplitude) and np.isfinite(conditional_se) and
            conditional_se > 0 and np.isfinite(lower) and np.isfinite(upper) and lower < upper):
        raise ValueError("finite amplitude, positive scale, and proper bounds required")
    a, b = (lower-amplitude)/conditional_se, (upper-amplitude)/conditional_se
    cdf_a, cdf_b = ndtr(a), ndtr(b)
    mass = float(cdf_b-cdf_a)
    if not np.isfinite(mass) or mass <= 0:
        raise FloatingPointError("truncated-normal mass unresolved")
    phi_a, phi_b = norm.pdf(a), norm.pdf(b)
    shift = (phi_a-phi_b)/mass
    mean = amplitude+conditional_se*shift
    variance = conditional_se**2*(1+(a*phi_a-b*phi_b)/mass-shift**2)
    if variance < 0 and variance > -1e-14*conditional_se**2:
        variance = 0.0
    if variance < 0:
        raise FloatingPointError("truncated-normal variance unresolved")
    quantiles = {str(p): float(amplitude+conditional_se*ndtri(cdf_a+p*mass))
                 for p in (0.025, 0.5, 0.975)}
    if upper <= 1:
        prob_above_one = 0.0
    elif lower >= 1:
        prob_above_one = 1.0
    else:
        prob_above_one = float((cdf_b-ndtr((1.0-amplitude)/conditional_se))/mass)
    return {"prior": "Uniform[0,2]" if (lower,upper)==(0.0,2.0) else "uniform_bounded",
            "prior_bounds": [lower,upper], "normalizing_gaussian_mass": mass,
            "mean": float(mean), "variance": float(variance), "sd": float(np.sqrt(variance)),
            "quantiles": quantiles, "probability_above_one": prob_above_one,
            "posterior_family": "Gaussian amplitude proxy truncated to proper uniform prior"}


def planck_marginal_amplitude(root):
    """Planck nine-bin marginal of the released ACT+Planck covariance proxy."""
    base = root / "workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2"
    files = [base / name for name in ("clkk_bandpowers_planck.txt", "binning_matrix_planck.txt",
             "covmat_actplanck_cmbmarg.txt", "README",
             "like_corrs/cosmo2017_10K_acc3_lenspotentialCls.dat")]
    old = root / "docs/observational_reboot_20261014/results/cache_lensing_v1/result.json"
    y, window, joint_cov = (finite(np.loadtxt(path), path.name) for path in files[:3])
    if y.shape != (9,) or window.shape != (9,3000) or joint_cov.shape != (27,27):
        raise ValueError("released nine-bin Planck and 27-bin joint source shapes required")
    fid = finite(np.loadtxt(files[-1]), "fiducial lensing reference")
    if fid.ndim != 2 or fid.shape[1] <= 5:
        raise ValueError("explicit fiducial ell/column-five reference mismatch")
    ell = fid[:,0].astype(int)
    if (np.any(fid[:,0] != ell) or
            not np.array_equal(ell, np.arange(2,2+len(ell))) or ell[-1] < 2999):
        raise ValueError("explicit fiducial ell/column-five reference mismatch")
    ckk = np.zeros(3000)
    selected = ell < 3000
    ckk[ell[selected]] = fid[selected,5] * np.pi/2
    theory = window @ ckk
    prior = json.loads(old.read_text())
    if prior.get("release") != "ACT DR6 lensing likelihood v1.2":
        raise ValueError("retained ACT+Planck release identity mismatch")
    joint = next((row for row in prior.get("scenarios", [])
                  if row.get("name") == "act_planck_baseline"), None)
    if (joint is None or joint.get("release_indices", [])[-9:] != list(range(18,27)) or
            len(joint.get("data", [])) != 19 or len(joint.get("reference", [])) != 19 or
            not np.allclose(y, joint["data"][-9:], rtol=1e-12, atol=0) or
            not np.allclose(theory, joint["reference"][-9:], rtol=1e-12, atol=0)):
        raise ValueError("retained joint Planck bins/reference differ from released inputs")
    covariance = joint_cov[18:,18:].copy()  # marginal covariance, then invert in amplitude_fit
    alpha19 = (400-19-2)/399
    alpha9 = (400-9-2)/399
    primary = amplitude_fit(y,theory,covariance,alpha19)
    sensitivity = amplitude_fit(y,theory,covariance,alpha9)
    residual_fixed = y-theory
    chi2_fixed = float(alpha19 * residual_fixed @ spd_solve(covariance,residual_fixed))
    posterior = uniform_amplitude_posterior(primary["amplitude"],primary["conditional_se"])
    predictive_covariance = covariance/alpha19 + posterior["variance"]*np.outer(theory,theory)
    result = {"owner":"HTT", "scope":"PLANCK_NINE_BIN_MARGINAL_FIXED_REFERENCE_AMPLITUDE",
              "release":"ACT DR6 lensing likelihood v1.2",
              "provider":"ACTCollaboration/act_dr6_lenslike v1.2 release Planck block",
              "method_source":"https://github.com/ACTCollaboration/act_dr6_lenslike/blob/main/act_dr6_lenslike/act_dr6_lenslike.py",
              "source_relation":"exact nine Planck bins of retained act_planck_baseline; marginal covariance block, not independent product",
              "retained_joint_result":str(old.relative_to(root)),
              "release_indices":list(range(18,27)), "data":y, "reference":theory,
              "ell_effective":window@np.arange(3000),
              "covariance":covariance,"covariance_status":"RELEASED_CMB_MARGINALIZED_ESTIMATE",
              "covariance_operation":"subset 27x27 covariance [18:,18:] before inversion; nine-bin marginal",
              "nsims":400,"primary_precision_scale":alpha19,
              "primary_precision_policy":"exact marginal of baseline 19-bin Gaussian proxy, alpha=(400-19-2)/399",
              "amplitude":primary["amplitude"],"conditional_se":primary["conditional_se"],
              "residual":primary["residual"],
              "chi_square_descriptor_fixed_A1":chi2_fixed,
              "chi_square_descriptor_optimized_A":primary["residual_quadratic"],
              "calibrated_chi2_p":None,
              "proper_uniform_amplitude_posterior":posterior,
              "posterior_predictive_conditional_covariance":{
                  "mean":posterior["mean"]*theory,
                  "covariance":predictive_covariance,
                  "measurement_covariance":covariance/alpha19,
                  "status":"ANALYTIC_GAUSSIAN_PROXY_MOMENTS_NO_CALIBRATED_P_VALUE"},
              "alpha9_covariance_estimate_sensitivity":{
                  "precision_scale":alpha9,"amplitude":sensitivity["amplitude"],
                  "conditional_se":sensitivity["conditional_se"],
                  "optimized_chi_square_descriptor":sensitivity["residual_quadratic"],
                  "role":"separate covariance-estimate proxy sensitivity"},
              "caveats":["Fixed released reference shape and estimated CMB-marginalized covariance",
                         "Posterior is for scalar amplitude under Uniform[0,2], not cosmological parameters or evidence",
                         "Nine bins overlap the retained ACT+Planck joint product; never multiply as independent likelihoods",
                         "Hartlap scales are declared Gaussian proxies, not exact finite-simulation calibration",
                         "Chi-square values are descriptors with no calibrated tail probabilities",
                         "No native Bianchi solver or physical lensing mechanism admission"]}
    return result,files+[old]


def feature_ranks(root):
    base = root / "workdir/pr177_act_dr6_inband/5cf582e12b7982d30fe6e30b8c9ca4a8127009c07b0463b5f66cba166322c27b/units"
    files = [base / "data.json"] + [base / f"sim-{i:04d}.json" for i in range(1, 401)]
    rows = [json.loads(path.read_text()) for path in files]
    if len({r["cache_key"] for r in rows}) != 1:
        raise ValueError("mixed feature cache identities")
    if rows[0]["unit_id"] != "data" or rows[0]["unit_kind"] != "observed":
        raise ValueError("observed feature unit missing")
    if len({r["unit_id"] for r in rows}) != 401:
        raise ValueError("duplicate retained feature unit")
    fixed_pipeline = {k: rows[0]["identical_pipeline_receipt"][k] for k in
                      ("feature_callable", "integer_min", "integer_max", "mask_threshold", "nside")}
    if fixed_pipeline["integer_min"] != 41 or fixed_pipeline["integer_max"] != 762:
        raise ValueError("observed strict in-band support changed")
    for i, row in enumerate(rows[1:], 1):
        if row["unit_id"] != f"sim-{i:04d}":
            raise ValueError("simulation identity ordering changed")
        receipt = row["identical_pipeline_receipt"]
        if row["unit_kind"] != "release_simulation" or any(receipt[k] != v for k, v in fixed_pipeline.items()):
            raise ValueError("identical feature pipeline/support changed")
    outputs = []
    for name in ("q_raw", "q_controlled"):
        x = finite([r["feature"][name] for r in rows], name)
        if x.shape != (401, 5):
            raise ValueError("retained modulation five-vector required")
        training, calibration, observed = x[1:201], x[201:], x[0]
        mean = training.mean(0); covariance = np.cov(training, rowvar=False, ddof=1)
        residual = np.vstack([observed, calibration]) - mean
        scores = np.einsum("ij,ji->i", residual, spd_solve(covariance, residual.T))
        exceed = int(np.sum(scores[1:] >= scores[0]))
        outputs.append({"feature": name, "observed_vector": observed,
                        "training_mean": mean, "training_covariance": covariance,
                        "observed_score": float(scores[0]), "calibration_scores": scores[1:],
                        "upper_rank": exceed + 1, "rank_fraction": (exceed + 1) / 201,
                        "ties_counted_in_upper_tail": True})
    return {"owner": "OBSSTAT", "scope": "DELIVERED_RECONSTRUCTED_KAPPA_FEATURE_RANK",
            "training_units": [r["unit_id"] for r in rows[1:201]],
            "calibration_units": [r["unit_id"] for r in rows[201:]],
            "unit_semantic_digests": {r["unit_id"]: r["semantic_digest"] for r in rows},
            "pipeline": fixed_pipeline, "features": outputs,
            "caveats": ["Fixed 200 training and 200 calibration units; no post-score split choice",
                        "Raw and controlled ranks are dependent comparisons; no minimum-rank selection",
                        "Rank interpretation is conditional on delivered-unit exchangeability",
                        "Cache receipt reuse; raw map/QE processing was not rerun"]}, files


def union3(root):
    from astropy.io import fits
    from scipy.optimize import minimize_scalar
    from scripts.observed_runs.r8_product_intake import decode_union3, flat_distance_modulus
    source = root / "workdir/rrss_observational_inputs/union3_release-main/mu_mat_union3_cosmo=2_mu.fits"
    summary = root / "docs/generated/tensor_joint_r8/law_followup/products.json"
    with fits.open(source) as h:
        z, mu, precision = decode_union3(h[0].data)
    stored = json.loads(summary.read_text())["products"]["union3"]
    if not np.array_equal(z, stored["redshift"]) or not np.array_equal(mu, stored["modulus"]):
        raise ValueError("recovered Union3 source differs from retained result rows")
    blocks = [(f"node_{i}", np.array([i])) for i in range(len(z))]
    blocks += [("z_lt_0p1", np.flatnonzero(z < .1)),
               ("z_0p1_to_0p5", np.flatnonzero((z >= .1) & (z < .5))),
               ("z_ge_0p5", np.flatnonzero(z >= .5))]
    covariance = spd_solve(precision, np.eye(len(z)))
    outputs = []
    for name, deleted in blocks:
        if len(deleted) == 0:
            continue
        keep = np.setdiff1d(np.arange(len(z)), deleted)
        if len(keep) < 3:
            raise ValueError("deletion leaves too few distance nodes")
        pk = spd_solve(covariance[np.ix_(keep, keep)], np.eye(len(keep)))
        objective = lambda omega: offset_profile(mu[keep], flat_distance_modulus(z[keep], omega), pk)[1]
        fit = minimize_scalar(objective, bounds=(.01, .99), method="bounded", options={"xatol": 1e-11})
        if not fit.success:
            raise RuntimeError(fit.message)
        offset, quadratic = offset_profile(mu[keep], flat_distance_modulus(z[keep], fit.x), pk)
        outputs.append({"deletion": name, "deleted_indices": deleted, "deleted_redshift": z[deleted],
                        "retained_indices": keep, "omega_m": float(fit.x),
                        "delta_omega_m": float(fit.x - stored["omega_m"]),
                        "offset_mag": offset, "delta_offset_mag": offset - stored["profile_offset_mag"],
                        "profile_quadratic": quadratic})
    return {"owner": "HTT", "scope": "UNION3_RELEASE_COMPRESSED_MARGINAL_DELETION_SCENARIOS",
            "baseline": {k: stored[k] for k in ("omega_m", "profile_offset_mag", "chi2")},
            "baseline_execution": "REUSED_STORED_RESULT", "redshift": z, "modulus": mu,
            "deletions": outputs,
            "caveats": ["Released approximate Gaussian compression, not an exact coverage law",
                        "Deletion marginalizes covariance; does not condition on removed nodes",
                        "Fixed node and redshift-block deletions; no significance search",
                        "Flat LCDM/free offset and historical numerical bounds (0.01,0.99)",
                        "No angular information or Bianchi geometry identification"]}, [source, summary,
                root / "docs/generated/tensor_joint_r8/law_followup/union3_README.md",
                root / "docs/generated/tensor_joint_r8/law_followup/union3_source.json",
                root / "scripts/observed_runs/r8_product_intake.py"]


def jwst(root):
    from htt.infer.jwst_host_hierarchy import (HostPair, validate_pairs,
        method_cell_covariance, contrast_covariance)
    base = root / "workdir/raw/jwst_anchors"
    manifest_path = base / "jwst_anchors_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    files = [manifest_path]; datasets = []
    for receipt in manifest["transcription_receipts"]:
        cells = receipt["exact_cells"]
        if not cells or "host" not in cells[0]:
            continue
        src = next(s for s in manifest["fetched"] if s["label"] == receipt["source_label"])
        path = base / src["path"]
        with tarfile.open(path) as archive:
            member = archive.extractfile(receipt["source_member"])
            if member is None:
                raise ValueError("table-bearing JWST source member missing")
            raw = member.read()
        if "sha256:" + hashlib.sha256(raw).hexdigest() != receipt["source_member_sha256"]:
            raise ValueError("immutable JWST table member changed")
        files.append(path)
        pairs = validate_pairs([HostPair(**{k: (float(c[k]) if k.endswith("_mag") else c[k])
                     for k in HostPair.__dataclass_fields__}) for c in cells], receipt["dataset"])
        delta = np.array([p.delta_mag for p in pairs]); scenarios = []
        for mode in ("global_all_cell_factor", "method_block_factor"):
            for q in Q_GRID:
                covariance = contrast_covariance(method_cell_covariance(pairs, q, mode))
                fit = amplitude_fit(delta, np.ones(len(delta)), covariance)
                loo = []
                for i, p in enumerate(pairs):
                    keep = np.delete(np.arange(len(pairs)), i)
                    removed = amplitude_fit(delta[keep], np.ones(len(keep)), covariance[np.ix_(keep, keep)])
                    loo.append({"host": p.host, "offset_without_host_mag": removed["amplitude"],
                                "shift_mag": removed["amplitude"] - fit["amplitude"]})
                scenarios.append({"mode": mode, "q": q, "offset_mag": fit["amplitude"],
                                  "conditional_se_mag": fit["conditional_se"], "host_influence": loo})
        datasets.append({"dataset": receipt["dataset"], "hosts": [p.host for p in pairs],
                         "source_arxiv": receipt["source_arxiv"], "source_member": receipt["source_member"],
                         "source_member_sha256": receipt["source_member_sha256"],
                         "delta_definition": "method_a_minus_method_b_mag", "delta_mag": delta,
                         "scenarios": scenarios})
    if len(datasets) != 2:
        raise ValueError("exactly two authenticated host families required")
    return {"owner": "HTT", "scope": "JWST_SAME_HOST_COVARIANCE_AND_INFLUENCE_SENSITIVITY",
            "q_grid": Q_GRID, "datasets": datasets,
            "caveats": ["PSD covariance modes are declared sensitivity scenarios, not observed shared covariance",
                        "Same-host shared geometry cancels exactly; no tilt or H0 measurement",
                        "Source families remain separate; calibration/host overlap does not create independent anchors",
                        "No calibrated p-value or total uncertainty from these modes"]}, files + [
            root / "htt/htt/htt/infer/jwst_host_hierarchy.py"]


def sdss(root, draws=64, seed=1729):
    if not 2 <= draws <= 512:
        raise ValueError("bootstrap draws must be in [2,512]")
    base = root / "docs/research_program/tensor_joint_r9/revision2/multidepth/final"
    features = base / "mock_features.npz"; moments = base / "moments.npz"; obs = base / "observed.json"
    with np.load(features, allow_pickle=False) as a:
        y = finite(a["Y"]); truth = finite(a["truth"]); response = finite(a["response"])
        box, observer = a["box"], a["observer"]
    with np.load(moments, allow_pickle=False) as a:
        training = a["training_mask"]
    observed = json.loads(obs.read_text()); h = finite(observed["H"])
    if (y.shape != (2048, 36) or truth.shape != y.shape or response.shape != (2048, 36, 36)
            or box.shape != (2048,) or observer.shape != box.shape or training.dtype.kind != "b"
            or not np.array_equal(training, box % 2 == 0) or h.shape != (27, 36)):
        raise ValueError("preserved SDSS release dimensions/box split changed")
    pairs = np.column_stack((box, observer))
    if len(np.unique(pairs, axis=0)) != len(y) or len(np.unique(box)) != 256:
        raise ValueError("SDSS complete box/observer identities required")
    for b in np.unique(box):
        if not np.array_equal(np.sort(observer[box == b]), np.arange(8)):
            raise ValueError("eight preserved observer IDs per box required")
    x, tags = y[training], box[training]
    covariance, mean_iid, mean_cluster = mean_covariances_by_box(x, tags)
    ratio = np.diag(mean_cluster) / np.diag(mean_iid)
    ids = np.unique(tags); grouped = [np.flatnonzero(tags == b) for b in ids]
    rng = np.random.default_rng(seed); bootstrap = []
    for draw in range(draws):
        chosen = rng.integers(0, len(ids), len(ids))
        idx = np.concatenate([grouped[i] for i in chosen])
        c = np.cov(x[idx], rowvar=False, ddof=1)
        bootstrap.append({"draw": draw, "selected_box_ids": ids[chosen],
                          "covariance_shape": covariance_shape(c),
                          "contrast_covariance_shape": covariance_shape(h @ c @ h.T),
                          "relative_covariance_frobenius_change": float(np.linalg.norm(c-covariance) / np.linalg.norm(covariance))})
    observer_slices = []
    for o in range(8):
        c = np.cov(y[training & (observer == o)], rowvar=False, ddof=1)
        observer_slices.append({"observer_id": o, **covariance_shape(c)})
    error = y - truth
    return {"owner": "HTT", "scope": "SDSS_RELEASED_MOCK_BOX_DEPENDENCE_DIAGNOSTIC",
            "training_boxes": ids, "evaluation_boxes": np.unique(box[~training]),
            "feature_ids": observed["feature_ids"], "training_mean": x.mean(0),
            "feature_covariance": covariance, "feature_covariance_shape": covariance_shape(covariance),
            "iid_mean_covariance_sensitivity": mean_iid, "cluster_mean_covariance": mean_cluster,
            "mean_variance_ratio_cluster_over_iid": ratio,
            "error_mean_training": error[training].mean(0),
            "error_mean_evaluation": error[~training].mean(0),
            "mean_response_training": response[training].mean(0),
            "mean_response_evaluation": response[~training].mean(0),
            "bootstrap_seed": seed, "bootstrap_draws": draws, "bootstrap": bootstrap,
            "observer_covariance_slices": observer_slices,
            "caveats": ["256 boxes x8 observers; frozen even/odd box split preserved",
                        "Cluster sandwich concerns ensemble mean, not one observed feature-vector covariance",
                        "Box bootstrap is an empirical stability diagnostic, not exact coverage",
                        "Released additive log-distance response is not a physical boost/global-tilt response",
                        "No calibrated chi-square p-value, 2048-IID claim, or catalogue re-extraction"]}, [features, moments, obs,
             root / "htt/obsstat/sdss_pv_depth.py"]


def join_coverage(root):
    path = root / "docs/research_program/tensor_joint_r9/revision2/selected_law/tempel_sdss_rows.npz"
    with np.load(path, allow_pickle=False) as a:
        rows = a["sdss_row_indices"]; objid = a["objid"]
        tg, rg = a["tempel_group_id"], a["release_group_id"]
        tr, rr = a["tempel_richness"], a["release_richness"]
        unmatched = a["unmatched_sdss_objid"]
    if any(v.shape != rows.shape for v in (objid, tg, rg, tr, rr)) or len(np.unique(rows)) != len(rows):
        raise ValueError("join rows/identities are not aligned and unique")
    groups = []
    for name, ids, richness in (("tempel", tg, tr), ("release", rg, rr)):
        positive = ids > 0
        keys, counts = np.unique(ids[positive], return_counts=True)
        groups.append({"catalogue": name, "positive_id_rows": int(positive.sum()),
                       "nonpositive_id_rows": int((~positive).sum()),
                       "positive_group_ids": keys, "retained_rows_per_group": counts,
                       "reported_richness_min": int(richness.min()),
                       "reported_richness_max": int(richness.max()),
                       "single_retained_member_groups": int(np.sum(counts == 1))})
    return {"owner": "HTT", "scope": "SDSS_TEMPEL_STORED_JOIN_COVERAGE_DESCRIPTIVES",
            "joined_rows": len(rows), "unique_objids": len(np.unique(objid)),
            "unmatched_objids": len(unmatched), "group_summaries": groups,
            "both_positive_id_rows": int(np.sum((tg > 0) & (rg > 0))),
            "same_reported_richness_rows": int(np.sum(tr == rr)),
            "caveats": ["Positive-ID classification is descriptive; no official sentinel/selection-law admission",
                        "Group IDs are different catalogue namespaces; equality is not cross-catalogue identity",
                        "Retained members are selected overlap, not complete source group populations",
                        "No fresh SDSS-CF3 calibration; raw rows/CF3 covariance remain required"]}, [path]


def plot_result(result, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.8))
    scope = result["scope"]
    if scope.startswith("PLANCK_NINE_BIN_MARGINAL"):
        x = result["ell_effective"]
        sd = np.sqrt(np.diag(result["covariance"]))
        ax.errorbar(x,result["data"],yerr=sd,fmt="o",label="Released Planck bins")
        ax.plot(x,np.asarray(result["reference"])*result["amplitude"],"-",label="Fitted fixed reference")
        ax.set_xlabel("Effective lensing multipole L")
        ax.set_ylabel("Ckk bandpower")
        ax.legend()
    elif scope.startswith("RELEASED_FIDUCIAL"):
        rows = result["scenarios"]; x = np.arange(len(rows))
        ax.errorbar(x, [r["amplitude"] for r in rows], yerr=[r["conditional_se"] for r in rows], fmt="o")
        ax.set_xticks(x, [r["name"] for r in rows], rotation=15); ax.axhline(1, color="gray", ls="--")
        ax.set_ylabel("Fixed-reference amplitude (conditional SE)")
    elif scope.startswith("DELIVERED_RECONSTRUCTED"):
        for r,color in zip(result["features"],("#0072B2","#D55E00")):
            ax.hist(r["calibration_scores"], bins=20, histtype="step", color=color,label=r["feature"])
            ax.axvline(r["observed_score"], ls="--",color=color,label=r["feature"]+" observed")
        ax.set_xlabel("Training-whitened five-vector score"); ax.set_ylabel("Calibration units"); ax.legend()
    elif scope.startswith("UNION3"):
        rows = result["deletions"]
        ax.bar(np.arange(len(rows)), [r["delta_omega_m"] for r in rows]); ax.axhline(0, color="gray")
        ax.set_xlabel("Fixed individual-node then redshift-block deletion"); ax.set_ylabel("Shift in profiled matter density")
    elif scope.startswith("JWST"):
        for d in result["datasets"]:
            for mode in ("global_all_cell_factor", "method_block_factor"):
                rows = [r for r in d["scenarios"] if r["mode"] == mode]
                ax.errorbar([r["q"] for r in rows], [r["offset_mag"] for r in rows],
                            yerr=[r["conditional_se_mag"] for r in rows], marker="o", label=d["dataset"]+" / "+mode)
        ax.set_xlabel("Declared covariance q sensitivity"); ax.set_ylabel("Method contrast (mag), conditional SE"); ax.legend(fontsize=6)
    elif scope.startswith("SDSS_RELEASED"):
        ax.plot(result["mean_variance_ratio_cluster_over_iid"], "o-"); ax.axhline(1, color="gray", ls="--")
        ax.set_xlabel("Preserved depth-feature index"); ax.set_ylabel("Cluster / IID mean variance sensitivity")
    else:
        for d in result["group_summaries"]:
            ax.hist(d["retained_rows_per_group"], bins=np.arange(1, 52), histtype="step", label=d["catalogue"])
        ax.set_xlabel("Retained joined members per positive-ID group (1–50)")
        ax.set_ylabel("Groups"); ax.legend()
    ax.set_title("Cache-only " + scope.replace("_", " ").lower(), fontsize=9)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(output / ("diagnostic." + suffix), dpi=160)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lane", choices=("lensing", "planck-marginal", "feature-ranks", "union3", "jwst", "sdss", "join-coverage"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-draws", type=int, default=64)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve(); output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for path in (root, root / "htt", root / "htt/src", root / "htt/htt"):
        sys.path.insert(0, str(path))
    started = time.monotonic()
    receipt = {"schema": "htt.reboot.cache_execution.v1", "lane": args.lane,
               "command": sys.argv, "repo_root": str(root), "output": str(output),
               "python": sys.version, "numpy": np.__version__, "platform": platform.platform(),
               "requested_author_runtime": "gpt-6.1-sol/high", "observed_author_runtime": "UNKNOWN",
               "observed_executor_runtime": "UNKNOWN"}
    for field, cmd in (("git_head", ["rev-parse", "HEAD"]), ("git_branch", ["branch", "--show-current"]),
                       ("git_status", ["status", "--porcelain=v1"])):
        run = subprocess.run(["git", "-C", str(root), *cmd], capture_output=True, text=True)
        receipt[field] = run.stdout.strip() if run.returncode == 0 else "UNAVAILABLE"
    try:
        if args.lane == "sdss":
            result, files = sdss(root, args.bootstrap_draws, args.seed)
        else:
            runner = {"lensing": lensing, "planck-marginal": planck_marginal_amplitude,
                      "feature-ranks": feature_ranks,
                      "union3": union3, "jwst": jwst, "join-coverage": join_coverage}[args.lane]
            result, files = runner(root)
        receipt["sources"] = [source_receipt(p, root) for p in files]
        receipt["code"] = source_receipt(Path(__file__), root)
        result["claim_tier"] = "DIAGNOSTIC_ONLY"
        result["transfer_source"] = "RELEASED_OBSERVATIONAL_PRODUCTS_AND_FIXED_REFERENCE"
        result["scientific_admission"] = "NOT_EVALUATED"
        (output / "result.json").write_text(json.dumps(result, default=json_value, indent=2, allow_nan=False)+"\n")
        plot_result(result, output)
        report = "# " + result["scope"].replace("_", " ").title() + "\n\n"
        report += "Owner: " + result["owner"] + ". Diagnostic-only; scientific admission not evaluated.\n\n"
        report += "Numerical results and retained identities: `result.json`. Figure: `diagnostic.png` / `diagnostic.pdf`.\n\n"
        if args.lane == "lensing":
            for row in result["scenarios"]:
                report += f"- {row['name']}: amplitude {row['amplitude']:.6g}, conditional SE {row['conditional_se']:.6g}.\n"
        elif args.lane == "planck-marginal":
            report += f"- Nine-bin marginal of the retained 19-bin Gaussian proxy: A = {result['amplitude']:.6g}, conditional SE = {result['conditional_se']:.6g}.\n"
            report += f"- Fixed A=1 chi-square descriptor = {result['chi_square_descriptor_fixed_A1']:.6g}; optimized descriptor = {result['chi_square_descriptor_optimized_A']:.6g}. No calibrated p-value.\n"
            report += f"- Primary precision scale {result['primary_precision_scale']:.9g}; separate nine-bin scale sensitivity {result['alpha9_covariance_estimate_sensitivity']['precision_scale']:.9g}.\n"
            report += "- Uniform[0,2] scalar-amplitude posterior and analytic Gaussian-proxy predictive moments are in result.json.\n"
        elif args.lane == "feature-ranks":
            for row in result["features"]:
                report += f"- {row['feature']}: upper rank {row['upper_rank']}/201, rank fraction {row['rank_fraction']:.6g}.\n"
        elif args.lane == "union3":
            shifts = [row["delta_omega_m"] for row in result["deletions"]]
            report += f"- Fixed deletion matter-density shifts: {min(shifts):.6g} to {max(shifts):.6g}; {len(shifts)} scenarios.\n"
        elif args.lane == "jwst":
            for data in result["datasets"]:
                offsets = [row["offset_mag"] for row in data["scenarios"]]
                report += f"- {data['dataset']}: {len(data['hosts'])} hosts; covariance-mode offsets {min(offsets):.6g} to {max(offsets):.6g} mag.\n"
        elif args.lane == "sdss":
            ratios = result["mean_variance_ratio_cluster_over_iid"]
            report += f"- {len(result['training_boxes'])} training boxes; {result['bootstrap_draws']} complete-box bootstrap draws.\n"
            report += f"- Cluster/IID mean-variance ratio: {min(ratios):.6g} to {max(ratios):.6g}.\n"
        else:
            report += f"- {result['joined_rows']} joined rows; {result['unmatched_objids']} unmatched IDs.\n"
        report += "\n"
        report += "\n".join("- " + c for c in result["caveats"]) + "\n"
        (output / "report.md").write_text(report)
        receipt["exit_code"] = 0
    except Exception as error:
        import traceback
        receipt["exit_code"] = 1; receipt["error"] = type(error).__name__ + ": " + str(error)
        (output / "failure.log").write_text(traceback.format_exc())
    receipt["elapsed_seconds"] = time.monotonic() - started
    (output / "execution_receipt.json").write_text(json.dumps(receipt, default=json_value, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"lane": args.lane, "output": str(output), "exit_code": receipt["exit_code"],
                      "elapsed_seconds": receipt["elapsed_seconds"]}))
    return receipt["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
