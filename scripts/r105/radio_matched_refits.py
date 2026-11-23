"""Paired spatial deletions of the actual R65 ring-conditioned NVSS common dipole fits."""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import healpy as hp
import numpy as np
import pandas as pd
from scipy.linalg import eigh

from htt.htt.infer.r65_count_quotient import RingLikelihood, fit_joint, shared_maps
from scripts.r104.radio_block_jackknife import RAW, SHA


BASE = Path("docs/research_program/observational_publication_20261015")
R65 = BASE / "R65_DIPOLE_ANOMALY_20261117/RESULTS"
OUT = BASE / "R105_RESEARCH_20261124/RADIO_MATCHED_REFITS.json"
CARRIER_SHA = "a51da9a98c3d0563446eb61f21aceff69fbfeed5446ec74471177170b8664e89"


def raw_migration(raw_path, pixels):
    """Reconstruct both selections at the actual R65 pixel centres and flux boundaries."""
    with open(raw_path, "rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != SHA:
            raise ValueError("incorrect paired NVSS source")
    tab = pd.read_csv(raw_path, sep=r"\s+", quotechar='"',
                      usecols=["ra", "dec", "peak_flux", "integrated_flux"])
    a, d, p, t = (tab[k].to_numpy(float) for k in ["ra","dec","peak_flux","integrated_flux"])
    keep = (np.isfinite(a) & np.isfinite(d) & np.isfinite(p) & np.isfinite(t) &
            (a >= 0) & (a < 360) & (np.abs(d) <= 90) & (p > 0) & (t > 0))
    k = hp.ang2pix(64, a[keep], d[keep], lonlat=True)
    bp = np.searchsorted([20,40,80], p[keep], side="right")
    bt = np.searchsorted([20,40,80], t[keep], side="right")
    bins = hp.nside2npix(64)
    joint = np.bincount((4*bp+bt)*bins+k, minlength=16*bins).reshape(4,4,bins)
    return len(tab), joint[:, :, pixels]


def selection_fit(counts, features, rings, p, start=None):
    # For pure dipoles all three flux bins share both coefficients, all pixel
    # partitions and exposures. Summing their counts is an exact reduction.
    f = np.ascontiguousarray(features[:, :p])
    if p == 2:
        e = RingLikelihood(counts.sum(axis=0), f, rings)
        return fit_joint([e], start=start)["estimate"]
    ex = [RingLikelihood(y, f, rings) for y in counts]
    maps, offsets = shared_maps(len(ex), p)
    return fit_joint(ex, maps, offsets, start=start)["estimate"]


def _worker_init(inputs):
    global _INPUTS
    _INPUTS = inputs


def _delete(task):
    nside, block_id = task
    counts, features, rings, labels, starts = _INPUTS
    keep = labels[nside] != block_id
    output = {}
    for p in (2, 6):
        fit = [selection_fit(y[:, keep], features[keep], rings[keep], p, init)[:2]
               for y, init in zip(counts, starts[p])]
        output[p] = np.concatenate(fit)
    return nside, int(block_id), output


def paired_covariance(replicates):
    r = np.asarray(replicates, dtype=float)
    if r.ndim != 2 or r.shape[1] != 4 or len(r) < 5 or not np.isfinite(r).all():
        raise ValueError("need finite shared replicate matrix (blocks,4)")
    a = r-r.mean(axis=0)
    joint = ((len(a)-1)/len(a)) * (a.T @ a)
    contrast = np.column_stack((-np.eye(2), np.eye(2)))
    return joint, contrast @ joint @ contrast.T


def run(nsides, workers, raw=RAW):
    if not nsides or any(n not in (2,4,8) for n in nsides) or len(set(nsides)) != len(nsides):
        raise ValueError("one or more unique nested patch resolutions 2,4,8 required")
    with (R65 / "PROVIDER_NVSS_CARRIERS.npz").open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != CARRIER_SHA:
            raise ValueError("R65 carrier digest mismatch")
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as src:
            pix, f, rings = (src[x] for x in ["pixel_indices", "features", "groups"])
            nsrc, joint = raw_migration(raw, pix)
            if not np.array_equal(joint, src["joint_bin_pixel_counts"]):
                raise ValueError("raw counts differ from R65 joint carrier")
            counts = [joint[1:, :, :].sum(axis=1), joint[:, 1:, :].sum(axis=0)]
            for rows, key in zip(counts, ["provider_peak_counts","provider_integrated_counts"]):
                if not np.array_equal(rows, src[key]):
                    raise ValueError("R65 marginal counts mismatch")
    r65 = json.loads((R65/"PROVIDER_NVSS_RESULT.json").read_text())
    if r65["carrier_sha256"] != CARRIER_SHA:
        raise ValueError("unmatched R65 reference")
    labels = {n: hp.nest2ring(n, hp.ring2nest(64, pix)//((64//n)**2)) for n in nsides}
    starts, ref_delta, prefit = {}, {}, {}
    for p, model in ((2,"dipole"),(6,"dipole_stf")):
        starts[p] = [selection_fit(y, f, rings, p) for y in counts]
        ref_delta[p] = starts[p][1][:2] - starts[p][0][:2]
        old = r65["paired_comparisons"][model]
        err = float(np.max(np.abs(ref_delta[p]-old["integrated_minus_peak"])))
        if err > 2e-9:
            raise ValueError("full R65 fit failed to replay")
        prefit[model] = {"actual_delta_xy": ref_delta[p].tolist(),
                         "full_fit_replay_error": err, "R65_source_Poisson_Wald": old["poisson_source_linearized_wald"]}
    tasks = [(n,b) for n in nsides for b in np.unique(labels[n])]
    samples = {}
    inputs = (counts, f, rings, labels, starts)
    if workers < 1:
        raise ValueError("positive worker count required")
    with ProcessPoolExecutor(max_workers=workers, initializer=_worker_init, initargs=(inputs,)) as pool:
        for n, b, result in pool.map(_delete, tasks, chunksize=4):
            for p, obs in result.items():
                samples.setdefault((n,p), []).append(obs)
    output = {}
    for n in nsides:
        row = {}
        for p, model in ((2,"dipole"),(6,"dipole_stf")):
            joint_cov, cov = paired_covariance(samples[n,p])
            points = np.array(samples[n,p])
            empirical = np.cov((points[:,2:] - points[:,:2]).T) * ((len(points)-1)**2 / len(points))
            if not np.allclose(empirical, cov, atol=1e-15, rtol=2e-10):
                raise ValueError("paired covariance identity failed")
            delta = ref_delta[p]
            old = r65["paired_comparisons"][model]
            cpois = np.array(old["covariance"]["covariance_contrast"])
            wald = float(delta @ np.linalg.solve(cov, delta))
            vals = eigh(cov, cpois, eigvals_only=True)
            row[model] = {"paired_replicates": len(points), "joint_covariance_peak_xy_integrated_xy": joint_cov.tolist(),
                          "contrast_covariance_xy": cov.tolist(), "generalized_eigenvalues_vs_R65_poisson": vals.tolist(),
                          "direct_matched_Wald": wald, "covariance_xy_correlation": float(cov[0,1]/np.sqrt(cov[0,0]*cov[1,1])),
                          "ignoring_shared_peak_integrated_crosscov_Wald": float(delta @ np.linalg.solve(joint_cov[:2,:2]+joint_cov[2:,2:],delta)),
                          "naive_scalar_trace_Wald": float(old["poisson_source_linearized_wald"] * np.trace(cpois)/np.trace(cov))}
        output[str(n)] = row
    return {"schema":"htt.r105.radio_matched_refits/1", "raw_sha256":SHA, "raw_rows_reread":nsrc, "carrier_sha256":CARRIER_SHA,
            "fit_definition":"R65 ring-conditioned multinomial on its identical NSIDE=64 mask, three source flux bins, common transverse dipole, optional four independent STF coefficients per bin",
            "n_pixels":len(pix), "counts_by_flux_bin_peak_integrated":[x.sum(axis=1).tolist() for x in counts],
            "full_refits":prefit, "spatial_deletions":output, "physical_Pi":None, "calibrated_p":None,
            "scope":"Same-source and same-patch deletions refit all nuisance coefficients and omit the deleted patch from the conditional exposure. Uneven boundary block coverage and one underlying sky limit the jackknife. Independent physical LSS and flux-response calibration absent."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--nsides", nargs="+", type=int, default=[4,8])
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--raw", type=Path, default=RAW)
    p.add_argument("--output", type=Path, default=OUT)
    a = p.parse_args()
    obj = run(a.nsides, a.workers, a.raw)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(obj, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
