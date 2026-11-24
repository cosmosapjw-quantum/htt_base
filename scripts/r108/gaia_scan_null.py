"""R108 gaia lane: scan-law null of the R106 Gaia/Quaia VSH curvature statistic.

Purpose
  Mock proper-motion fields for the 634,233 qualified Quaia sources whose anisotropy follows the
  Gaia EDR3 commanded scanning law (scripts/r108/gaia_scanlaw.py products) are pushed through the
  identical R106 estimator (scripts/r108/gaia_estimator.py: all 48 patches and the per-draw R104
  rule-selected exclusion, jk1 and jk2 quadratic forms). Null kinds:
    noise_catalogue   Gaussian noise with each source's catalogue covariance (whitened iid N(0,1)).
    noise_scanshape   Gaussian noise whose 2x2 shape is the scan-law PM covariance of the source's
                      NSIDE-64 pixel, scaled to the trace of the catalogue covariance.
    sys_<c>_tau<T>    noise_catalogue plus a scan-coherent systematic: along-scan errors e_k that are
                      constant over blocks of T seconds of one FOV stream (T = 10 s: independent per
                      10 s sample; 600 s: 10 deg of scan; 21600 s: one 6 h great circle), N(0,1)
                      per block, propagated per NSIDE-64 pixel through the 5-parameter along-scan
                      least squares, PM block of N^-1 sum a_k e_k. Coupling c: blind (all sources),
                      colour ((BP-RP - median)/IQR of Quaia) or gmag ((G - median)/IQR of Quaia).
  Amplitude calibration (calibrate): NSIDE-16 pixel-mean proper-motion power (blind), or power of the
  red-minus-blue (colour) / faint-minus-bright (gmag) half difference, measured three ways: the
  noise-subtracted auto power of the disjoint R106 CRF3 complement (G-matched), and the cross power of
  two disjoint random halves of the complement and of the Quaia sample. For each, the amplitude that
  makes the same estimator on the noise-free mock reproduce the 97.5% one-sided upper value is
  computed, and the largest is used (conservative: the whole measured power is attributed to the
  scan-law systematic). Calibration v1 (auto power only) was superseded because that estimator is
  biased by catalogue-error mis-scaling; it is kept in the log.
  For each systematic draw the noise-free systematic curvature is also kept, giving the amplitude
  that the systematic alone would need to reach the observed spin6 quadratic form (observed jk1 cov).
Inputs: scan-law products (SHA-256 in SCANLAW_PIXEL_STATISTICS.json), R106 pinned inputs through
  scripts.r108.gaia_estimator; complement via scripts/r106 complement_sample.
Units: fields mas/yr; curvature microarcsec/yr per z^2; Q dimensionless; amplitudes in units of the
  calibrated amplitude.
Usage:
  python -m scripts.r108.gaia_scan_null validate --scan-dir D --out J
  python -m scripts.r108.gaia_scan_null calibrate --scan-dir D --out J [--cal-draws 16 --seed 108300]
  python -m scripts.r108.gaia_scan_null run --kind K --draws N --seed S --scan-dir D --calibration J --out-dir O
  python -m scripts.r108.gaia_scan_null summarize --out-dir O --calibration J --out J [--replay-dir R]
    (--replay-dir: short reruns of the stored runs, run --draws n with the same kind/seed/calibration/amplitude; the
    summary then checks the first n draws of every stored array bit for bit and names the script SHA-256 of the rerun)
Provenance: every receipt records the SHA-256 of the __main__ script (gaia_estimator.provenance, main_script) from the
  R108 review fix on; the summary groups earlier receipts by script version (script_versions).
Seeds: fixed per kind (see the run commands in the summary); deterministic given the seed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import healpy as hp
import numpy as np

from scripts.r106 import gaia_null_refit as r106
from scripts.r108 import gaia_estimator as est
from scripts.r108.common import maxrss_mb, sha256_file, write_json

MOCK_NSIDE = 64
CAL_NSIDE = 16
TAUS = {"tau10": 1, "tau600": 60, "tau21600": 2160}  # block lengths in 10 s samples
COUPLINGS = ("blind", "colour", "gmag")
KINDS = ("noise_catalogue", "noise_scanshape") + tuple(f"sys_{c}_{t}" for c in COUPLINGS for t in TAUS)
STATS_KEEP = ("spin6", "magnetic16", "joint32", "glide6", "E2_10", "B2_10", "electric16")
SPIN6 = r106.STAT_SETS["spin6"]
MIRRORED_CONTROL_NOTE = ("not computed (R108 review GAIA-3): the former 'pearson_if_east_axis_mirrored' was corr(-pred, cat) = "
                         "-corr(pred, cat) identically and recomputed no mirrored design (which would also change the "
                         "parallax column); the scan-angle convention test is scan_angle_convention_check in "
                         "SCANLAW_PIXEL_STATISTICS.json (FOV-centre position angle versus the scan-law angle)")


def load_scan(scan_dir):
    scan_dir = Path(scan_dir)
    summ = scan_dir / "scanlaw_pixel_statistics.npz"
    with np.load(summ) as d:
        N = d[f"N{MOCK_NSIDE}"]
        shape = d[f"pmcov_shape{MOCK_NSIDE}"]
        shape32 = d["pmcov_shape32"]
    streams = []
    for fov in ("fov1", "fov2"):
        streams.append({k: np.load(scan_dir / f"mock_{fov}_{k}.npy", mmap_mode="r") for k in ("pix", "a", "segment_start")})
    return {"N": N, "shape": shape, "shape32": shape32, "streams": streams,
            "sha256": {p.name: sha256_file(p) for p in sorted(scan_dir.iterdir()) if p.is_file()}}


def pixel_solver(Nflat):
    """Inverse of the per-pixel 5x5 information; zero rows where singular."""
    from scripts.r108.gaia_scanlaw import unpack

    N = unpack(Nflat)
    ok = np.linalg.matrix_rank(N) == 5
    inv = np.zeros_like(N)
    inv[ok] = np.linalg.inv(N[ok])
    return inv, ok


def block_ids(segment_start, block):
    """Block index per sample: new block at every segment start and every `block` samples inside a segment."""
    seg = np.cumsum(segment_start) - 1
    start_idx = np.flatnonzero(segment_start)
    pos = np.arange(len(segment_start)) - start_idx[seg]
    key = seg.astype(np.int64) * (1 << 31) + pos // block
    _, ids = np.unique(key, return_inverse=True)
    return ids.astype(np.int64)


class SysField:
    """Scan-coherent systematic PM field per NSIDE-64 pixel for one block length.

    Because e is constant inside a block, sum_k a_k e_k over a pixel equals sum_b e_b A[p, b] with
    A[p, b] = sum of a_k over the samples of block b in pixel p; A is stored as one sparse matrix
    (5 * npix x nblocks) per FOV stream. draw() consumes the random stream exactly as the direct
    per-sample sum (one standard_normal(nblocks) per stream, in stream order)."""

    def __init__(self, scan, block):
        from scipy import sparse

        self.inv, self.ok = pixel_solver(scan["N"])
        self.npix = len(scan["N"])
        self.block_len = block
        self.parts = []
        for st in scan["streams"]:
            ids = block_ids(np.asarray(st["segment_start"]), block)
            pix = np.asarray(st["pix"], dtype=np.int64)
            a = np.asarray(st["a"], dtype=np.float64)
            nb = int(ids.max()) + 1
            key = ids * self.npix + pix
            uk, inv = np.unique(key, return_inverse=True)
            rows_p, cols_b = uk % self.npix, uk // self.npix
            mats = []
            for j in range(5):
                vals = np.bincount(inv, weights=a[:, j], minlength=len(uk))
                mats.append(sparse.csr_matrix((vals, (rows_p, cols_b)), shape=(self.npix, nb)))
            self.parts.append({"A": sparse.vstack(mats, format="csr"), "nblocks": nb, "nnz_pairs": int(len(uk))})
            del ids, pix, a, key, uk, inv

    def draw(self, rng):
        b = np.zeros((5, self.npix))
        for p in self.parts:
            b += (p["A"] @ rng.standard_normal(p["nblocks"])).reshape(5, self.npix)
        theta = np.einsum("pij,jp->pi", self.inv, b)
        return theta[:, 3:5]  # (mu_alpha*, mu_delta) per pixel, units [e]/yr

    def draw_direct(self, rng, scan):
        """Reference per-sample sum (tests / verification only)."""
        b = np.zeros((self.npix, 5))
        for st, p in zip(scan["streams"], self.parts):
            ids = block_ids(np.asarray(st["segment_start"]), self.block_len)
            e = rng.standard_normal(p["nblocks"])[ids]
            pix = np.asarray(st["pix"], dtype=np.int64)
            a = np.asarray(st["a"], dtype=np.float64)
            for j in range(5):
                b[:, j] += np.bincount(pix, weights=a[:, j] * e, minlength=self.npix)
        return np.einsum("pij,pj->pi", self.inv, b)[:, 3:5]


def coupling(kind, G, c, ref):
    if kind == "blind":
        return np.ones(len(G))
    if kind == "colour":
        return (c - ref["c_med"]) / ref["c_iqr"]
    return (G - ref["G_med"]) / ref["G_iqr"]


def coupling_reference(q_G, q_c):
    return {"G_med": float(np.median(q_G)), "G_iqr": float(np.subtract(*np.quantile(q_G, [.75, .25]))),
            "c_med": float(np.median(q_c)), "c_iqr": float(np.subtract(*np.quantile(q_c, [.75, .25])))}


def pixel_excess(pix, y, e1, e2, split=None):
    """NSIDE-16 pixel-mean excess power over noise; split=None (blind) or boolean 'upper half' mask."""
    npix = hp.nside2npix(CAL_NSIDE)
    terms = np.zeros(npix)
    used = np.zeros(npix, bool)
    for comp, err in ((0, e1), (1, e2)):
        wgt = 1.0 / err ** 2
        if split is None:
            W = np.bincount(pix, weights=wgt, minlength=npix)
            M = np.bincount(pix, weights=wgt * y[:, comp], minlength=npix)
            ok = W > 0
            terms[ok] += (M[ok] / W[ok]) ** 2 - 1.0 / W[ok]
            used |= ok
        else:
            Wu = np.bincount(pix[split], weights=wgt[split], minlength=npix)
            Wl = np.bincount(pix[~split], weights=wgt[~split], minlength=npix)
            Mu = np.bincount(pix[split], weights=(wgt * y[:, comp])[split], minlength=npix)
            Ml = np.bincount(pix[~split], weights=(wgt * y[:, comp])[~split], minlength=npix)
            ok = (Wu > 0) & (Wl > 0)
            terms[ok] += (Mu[ok] / Wu[ok] - Ml[ok] / Wl[ok]) ** 2 - 1.0 / Wu[ok] - 1.0 / Wl[ok]
            used |= ok
    t = terms[used]
    return float(t.mean()), float(t.std(ddof=1) / np.sqrt(len(t))), int(used.sum())


def pixel_power_noise_free(pix, y, e1, e2, split=None):
    """Same statistic for a noise-free field (no noise subtraction)."""
    npix = hp.nside2npix(CAL_NSIDE)
    terms = np.zeros(npix)
    used = np.zeros(npix, bool)
    for comp, err in ((0, e1), (1, e2)):
        wgt = 1.0 / err ** 2
        if split is None:
            W = np.bincount(pix, weights=wgt, minlength=npix)
            M = np.bincount(pix, weights=wgt * y[:, comp], minlength=npix)
            ok = W > 0
            terms[ok] += (M[ok] / W[ok]) ** 2
        else:
            Wu = np.bincount(pix[split], weights=wgt[split], minlength=npix)
            Wl = np.bincount(pix[~split], weights=wgt[~split], minlength=npix)
            Mu = np.bincount(pix[split], weights=(wgt * y[:, comp])[split], minlength=npix)
            Ml = np.bincount(pix[~split], weights=(wgt * y[:, comp])[~split], minlength=npix)
            ok = (Wu > 0) & (Wl > 0)
            terms[ok] += (Mu[ok] / Wu[ok] - Ml[ok] / Wl[ok]) ** 2
        used |= ok
    return float(terms[used].mean())


def complement_for_calibration(ctx):
    q, crf3 = ctx["q"], ctx["crf3"]
    _, _, (g4, c4) = r106.build_strata(q, crf3)
    comp, census = r106.complement_sample(q, crf3, g4, c4, match_g=True)
    order = np.argsort(crf3["source_id"])
    G, _ = r106.lookup(crf3["source_id"][order], crf3["phot_g_mean_mag"][order], comp["source_id"])
    c, _ = r106.lookup(crf3["source_id"][order], crf3["bp_rp"][order], comp["source_id"])
    ok = np.isfinite(G) & np.isfinite(c)
    out = {k: v[ok] for k, v in comp.items() if isinstance(v, np.ndarray) and len(v) == len(ok)}
    out["G"], out["c"] = G[ok], c[ok]
    census["calibration_rows_with_G_and_bp_rp"] = int(ok.sum())
    return out, census


def validate(a):
    """Scan-law PM covariance shape versus the catalogue covariance of the qualified Quaia sources."""
    t0 = time.monotonic()
    scan = load_scan(a.scan_dir)
    ctx = est.load_context(with_colour=False)
    q = ctx["q"]
    pix = hp.ang2pix(MOCK_NSIDE, np.pi / 2 - q["dec"], q["ra"])
    S = scan["shape"][pix]
    fin = np.isfinite(S).all(axis=(1, 2))
    pred_rho = S[:, 0, 1] / np.sqrt(S[:, 0, 0] * S[:, 1, 1])
    pred_lr = 0.5 * np.log(S[:, 0, 0] / S[:, 1, 1])
    cat_lr = np.log(q["e1"] / q["e2"])
    r_rho = float(np.corrcoef(pred_rho[fin], q["rho"][fin])[0, 1])
    r_lr = float(np.corrcoef(pred_lr[fin], cat_lr[fin])[0, 1])
    sign = float(np.mean(np.sign(pred_rho[fin]) == np.sign(q["rho"][fin])))
    bins = np.quantile(pred_rho[fin], np.linspace(0, 1, 11))
    bi = np.clip(np.digitize(pred_rho[fin], bins[1:-1]), 0, 9)
    binned = [{"pred_rho_median": float(np.median(pred_rho[fin][bi == k])),
               "catalogue_rho_median": float(np.median(q["rho"][fin][bi == k])), "n": int((bi == k).sum())}
              for k in range(10)]
    res = {"schema": "htt.r108.gaia_scan_null.validate/2", "scan_inputs_sha256": scan["sha256"],
           "estimator_inputs": ctx["inputs"], "quaia_sources": int(len(fin)), "sources_in_singular_pixels": int((~fin).sum()),
           "pearson_pred_vs_catalogue_pm_corr": r_rho,
           "mirrored_convention_control": MIRRORED_CONTROL_NOTE,
           "sign_agreement_fraction_pm_corr": sign,
           "pearson_pred_vs_catalogue_log_sigma_ratio": r_lr, "binned_pm_corr": binned,
           "scope": "A positive, large correlation means the per-pixel scan-law shape reproduces the orientation of the "
                    "catalogue PM error ellipses (pixel aggregation and shape); the scan-angle convention itself is tested "
                    "in SCANLAW_PIXEL_STATISTICS.json scan_angle_convention_check.",
           "runtime_s": time.monotonic() - t0, "maxrss_mb": maxrss_mb(), "provenance": est.provenance()}
    write_json(a.out, res)
    print(json.dumps({k: res[k] for k in ("pearson_pred_vs_catalogue_pm_corr", "sign_agreement_fraction_pm_corr",
                                          "pearson_pred_vs_catalogue_log_sigma_ratio")}))


def _pixel_means(pix, y, wgt, sel, npix):
    W = np.bincount(pix[sel], weights=wgt[sel], minlength=npix)
    M = np.bincount(pix[sel], weights=(wgt * y)[sel], minlength=npix)
    return W, M


def pixel_cross(pix, y, e1, e2, half, split=None):
    """NSIDE-16 cross-power of two disjoint random halves of the sources (noise-free in expectation, so it is
    insensitive to a mis-scaled catalogue error and to single-source outliers); split as in pixel_excess."""
    npix = hp.nside2npix(CAL_NSIDE)
    terms = np.zeros(npix)
    used = np.ones(npix, bool)
    for comp, err in ((0, e1), (1, e2)):
        wgt = 1.0 / err ** 2
        est_h = []
        for h in (half, ~half):
            if split is None:
                W, M = _pixel_means(pix, y[:, comp], wgt, h, npix)
                ok = W > 0
                v = np.where(ok, M / np.where(ok, W, 1), 0.0)
            else:
                Wu, Mu = _pixel_means(pix, y[:, comp], wgt, h & split, npix)
                Wl, Ml = _pixel_means(pix, y[:, comp], wgt, h & ~split, npix)
                ok = (Wu > 0) & (Wl > 0)
                v = np.where(ok, Mu / np.where(Wu > 0, Wu, 1) - Ml / np.where(Wl > 0, Wl, 1), 0.0)
            used &= ok
            est_h.append(v)
        terms += est_h[0] * est_h[1]
    t = terms[used]
    return float(t.mean()), float(t.std(ddof=1) / np.sqrt(len(t))), int(used.sum())


def calibrate(a):
    """Amplitude of the scan-coherent systematic from three measurements; the largest upper value is used."""
    t0 = time.monotonic()
    scan = load_scan(a.scan_dir)
    ctx = est.load_context(with_colour=True)
    q = ctx["q"]
    ref = coupling_reference(q["G"], ctx["bp_rp"])
    comp, census = complement_for_calibration(ctx)
    samples = {"complement": {"ra": comp["ra"], "dec": comp["dec"], "y": comp["y"], "e1": comp["e1"], "e2": comp["e2"],
                              "G": comp["G"], "c": comp["c"]},
               "quaia": {"ra": q["ra"], "dec": q["dec"], "y": q["y"], "e1": q["e1"], "e2": q["e2"], "G": q["G"],
                         "c": ctx["bp_rp"]}}
    hrng = np.random.default_rng(a.seed + 7)
    for smp in samples.values():
        smp["pix16"] = hp.ang2pix(CAL_NSIDE, np.pi / 2 - smp["dec"], smp["ra"])
        smp["pix64"] = hp.ang2pix(MOCK_NSIDE, np.pi / 2 - smp["dec"], smp["ra"])
        smp["split"] = {"blind": None, "colour": smp["c"] > ref["c_med"], "gmag": smp["G"] > ref["G_med"]}
        smp["half"] = hrng.random(len(smp["ra"])) < 0.5
    obs = {}
    for c in COUPLINGS:
        cm = samples["complement"]
        m, se, npx = pixel_excess(cm["pix16"], cm["y"], cm["e1"], cm["e2"], cm["split"][c])
        obs[f"complement_auto_{c}"] = {"power_mas2_per_yr2": m, "standard_error": se, "pixels": npx, "upper_97p5": m + 1.96 * se}
        for name in ("complement", "quaia"):
            sm = samples[name]
            m, se, npx = pixel_cross(sm["pix16"], sm["y"], sm["e1"], sm["e2"], sm["half"], sm["split"][c])
            obs[f"{name}_cross_{c}"] = {"power_mas2_per_yr2": m, "standard_error": se, "pixels": npx, "upper_97p5": m + 1.96 * se}
    rng = np.random.default_rng(a.seed)
    cal = {}
    for tname, block in TAUS.items():
        field = SysField(scan, block)
        unit = {}
        for _ in range(a.cal_draws):
            d = field.draw(rng)
            for c in COUPLINGS:
                for name in ("complement", "quaia"):
                    sm = samples[name]
                    ys = d[sm["pix64"]] * coupling(c, sm["G"], sm["c"], ref)[:, None]
                    if name == "complement":
                        unit.setdefault(f"complement_auto_{c}", []).append(
                            pixel_power_noise_free(sm["pix16"], ys, sm["e1"], sm["e2"], sm["split"][c]))
                    unit.setdefault(f"{name}_cross_{c}", []).append(
                        pixel_cross(sm["pix16"], ys, sm["e1"], sm["e2"], sm["half"], sm["split"][c])[0])
        for c in COUPLINGS:
            cand = {}
            for meas in (f"complement_auto_{c}", f"complement_cross_{c}", f"quaia_cross_{c}"):
                mu = float(np.mean(unit[meas]))
                cand[meas] = {"unit_amplitude_power_mean": mu, "unit_amplitude_power_sd": float(np.std(unit[meas], ddof=1)),
                              "target_power": max(obs[meas]["upper_97p5"], 0.0),
                              "amplitude": float(np.sqrt(max(obs[meas]["upper_97p5"], 0.0) / mu))}
            used = max(cand, key=lambda k: cand[k]["amplitude"])
            cal[f"sys_{c}_{tname}"] = {"amplitude": cand[used]["amplitude"], "amplitude_from": used, "candidates": cand,
                                       "block_samples": block}
        del field
    res = {"schema": "htt.r108.gaia_scan_null.calibration/2", "coupling_reference_quaia": ref, "complement_census": census,
           "observed_pixel_power": obs, "calibration": cal, "cal_draws": a.cal_draws, "seed": a.seed,
           "scan_inputs_sha256": scan["sha256"], "estimator_inputs": ctx["inputs"],
           "rule": "for each measurement, amplitude^2 = max(observed NSIDE-16 power + 1.96 SE, 0) / mean unit-amplitude mock "
                   "power of the same estimator on the same sources; the largest of the three amplitudes (complement "
                   "noise-subtracted auto power, complement and Quaia random-half cross power) is used. Inverse-variance "
                   "weights per component; colour/gmag use the half difference split at the Quaia median.",
           "auto_power_caveat": "the noise-subtracted auto power is biased upward by any underestimate of the catalogue errors "
                                "and by contaminating single sources; the cross power of disjoint random halves is not",
           "runtime_s": time.monotonic() - t0, "maxrss_mb": maxrss_mb(), "provenance": est.provenance()}
    write_json(a.out, res)
    print(json.dumps({"observed": obs, "amplitudes": {k: [v["amplitude"], v["amplitude_from"]] for k, v in cal.items()}}))


def run(a):
    t0 = time.monotonic()
    ctx = est.load_context(with_colour=True)
    ctx.pop("crf3", None)  # only bp_rp is needed here
    q, f, w = ctx["q"], ctx["f"], ctx["w"]
    n = len(q["ra"])
    rng = np.random.default_rng(a.seed)
    allp = np.arange(est.NPATCH)
    keep_ex = np.setdiff1d(allp, r106.EXCLUDE)
    _, c1_48, _, _, _ = r106.refit_parts(f, ctx["s_obs"], w, allp)
    _, c1_ex, _ = r106.refit(f, ctx["s_obs"], w, keep_ex)
    obs_q = {"all48": r106.qforms(est.stats(f, ctx["s_obs"], w)["all48"]["vec"], c1_48)["spin6"]}
    extra = {}
    field, amp, gfac, pix = None, 0.0, None, None
    if a.kind == "noise_scanshape" or a.kind.startswith("sys_"):
        scan = load_scan(a.scan_dir)
        extra["scan_inputs_sha256"] = scan["sha256"]
        pix = hp.ang2pix(MOCK_NSIDE, np.pi / 2 - q["dec"], q["ra"])
    if a.kind == "noise_scanshape":
        S = scan["shape"][pix]
        bad = ~np.isfinite(S).all(axis=(1, 2))
        S[bad] = scan["shape32"][hp.ang2pix(32, np.pi / 2 - q["dec"][bad], q["ra"][bad])]
        tr_cat = q["e1"] ** 2 + q["e2"] ** 2
        S = S * (tr_cat / (S[:, 0, 0] + S[:, 1, 1]))[:, None, None]
        chol = np.linalg.cholesky(S)
        extra["sources_with_nside32_fallback_shape"] = int(bad.sum())
    if a.kind.startswith("sys_"):
        _, cpl, tname = a.kind.split("_")
        cal = json.loads(Path(a.calibration).read_text())
        extra["calibration_sha256"] = sha256_file(a.calibration)
        amp = cal["calibration"][a.kind]["amplitude"]
        extra["amplitude_from"] = cal["calibration"][a.kind]["amplitude_from"]
        if a.amplitude_from is not None:  # amplitude sensitivity run (reported next to the primary run, never instead)
            amp = cal["calibration"][a.kind]["candidates"][f"{a.amplitude_from}_{cpl}"]["amplitude"]
            extra["amplitude_from"] = f"{a.amplitude_from}_{cpl} (sensitivity)"
        ref = cal["coupling_reference_quaia"]
        gfac = coupling(cpl, q["G"], ctx["bp_rp"], ref)
        field = SysField(scan, TAUS[tname])
        extra["sources_in_singular_pixels"] = int((~field.ok[pix]).sum())
        v_fast = field.draw(np.random.default_rng(a.seed + 999))
        v_direct = field.draw_direct(np.random.default_rng(a.seed + 999), scan)
        extra["sparse_vs_direct_field_max_rel"] = float(np.max(np.abs(v_fast - v_direct)) / np.max(np.abs(v_direct)))
        if extra["sparse_vs_direct_field_max_rel"] > 1e-10:
            raise ArithmeticError(f"sparse block aggregation differs: {extra['sparse_vs_direct_field_max_rel']}")
        extra["block_pixel_pairs"] = [p["nnz_pairs"] for p in field.parts]
        del scan, v_fast, v_direct
    rec = {"all48": {k: np.empty(a.draws) for k in STATS_KEEP}, "all48_jk2": {k: np.empty(a.draws) for k in STATS_KEEP},
           "excl": {k: np.empty(a.draws) for k in STATS_KEEP}, "excl_jk2": {k: np.empty(a.draws) for k in STATS_KEEP}}
    vec48 = np.empty((a.draws, 32))
    pairs = np.empty((a.draws, 2), dtype=np.int64)
    sys_q = {"all48": np.full(a.draws, np.nan), "excl_8_47": np.full(a.draws, np.nan)}
    for t in range(a.draws):
        if a.kind == "noise_scanshape":
            y = np.einsum("nij,nj->ni", chol, rng.standard_normal((n, 2)))
            Yw = est.whiten_field(ctx["L"], y)
        else:
            Yw = rng.standard_normal((n, 2))
        if field is not None:
            ysys = amp * field.draw(rng)[pix] * gfac[:, None]
            Ysys = est.whiten_field(ctx["L"], ysys)
            Yw = Yw + Ysys
            s_sys = est.rhs(ctx["X"], Ysys, ctx["key"])
            for cfg, keep, c1 in (("all48", allp, c1_48), ("excl_8_47", keep_ex, c1_ex)):
                v = r106.curvature(f, s_sys, w, keep)
                sys_q[cfg][t] = float(v[SPIN6] @ np.linalg.solve(c1[np.ix_(SPIN6, SPIN6)], v[SPIN6]))
        st = est.stats(f, est.rhs(ctx["X"], Yw, ctx["key"]), w)
        for k in STATS_KEEP:
            rec["all48"][k][t] = st["all48"]["jk1"][k]
            rec["all48_jk2"][k][t] = st["all48"]["jk2"][k]
            rec["excl"][k][t] = st[f"excl_selected__{est.RULE}"]["jk1"][k]
            rec["excl_jk2"][k][t] = st[f"excl_selected__{est.RULE}"]["jk2"][k]
        vec48[t] = st["all48"]["vec"]
        pairs[t] = st[f"excl_selected__{est.RULE}"]["pair"]
        if (t + 1) % max(1, a.draws // 10) == 0:
            print(json.dumps({"kind": a.kind, "done": t + 1, "elapsed_s": round(time.monotonic() - t0, 1)}), flush=True)
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = a.kind if a.amplitude_from is None else f"{a.kind}__amp_{a.amplitude_from}"
    npz = out_dir / f"scan_null_{tag}.npz"
    if npz.exists():
        raise FileExistsError(f"refusing to overwrite {npz}")
    np.savez_compressed(npz, vec48=vec48, pairs=pairs, sys_q_all48=sys_q["all48"], sys_q_excl=sys_q["excl_8_47"],
                        **{f"{c}__{k}": rec[c][k] for c in rec for k in STATS_KEEP})
    receipt = {"schema": "htt.r108.gaia_scan_null.run/1", "kind": a.kind, "draws": a.draws, "seed": a.seed,
               "amplitude_mas_per_yr_per_unit_e": amp, "npz": str(npz), "npz_sha256": sha256_file(npz),
               "estimator_inputs": ctx["inputs"], "estimator_replay": ctx["replay"], "observed_spin6_jk1_all48": obs_q["all48"],
               **extra, "runtime_s": time.monotonic() - t0, "maxrss_mb": maxrss_mb(), "provenance": est.provenance()}
    write_json(out_dir / f"scan_null_{tag}.json", receipt)
    print(json.dumps({"kind": a.kind, "runtime_s": receipt["runtime_s"], "npz_sha256": receipt["npz_sha256"]}))


def receipt_script_version(kind, r):
    """Which gaia_scan_null.py version wrote a run receipt.

    Receipts written after the R108 review fix carry provenance.main_script (the __main__ script SHA-256). Earlier receipts do
    not (python -m registers the script only as __main__); they are grouped by the one receipt field that changed between
    the earlier versions: whether run() recorded amplitude_from for a primary systematic run."""
    pv = r.get("provenance", {})
    main = pv.get("main_script") or {}
    est_sha = pv.get("module_sha256", {}).get("scripts/r108/gaia_estimator.py")
    if main.get("sha256"):
        return {"group": "identified", "gaia_scan_null_py_sha256": main["sha256"], "gaia_estimator_py_sha256": est_sha}
    if not kind.startswith("sys_"):
        grp = "pre_fix_noise_kind (amplitude_from not applicable; version not separable from the receipt)"
    elif r.get("amplitude_from") is None:
        grp = "pre_fix_A (primary systematic run written before run() recorded amplitude_from)"
    else:
        grp = "pre_fix_B (amplitude_from recorded)"
    return {"group": grp, "gaia_scan_null_py_sha256": None, "gaia_estimator_py_sha256": est_sha}


def replay_check(stored_npz, replay_dir, tag):
    """Bit-identity of the first n draws of a stored run with a short rerun (same kind, seed, amplitude) by the current script."""
    rj = Path(replay_dir) / f"scan_null_{tag}.json"
    if not rj.exists():
        return {"status": "NOT_RUN"}
    rr = json.loads(rj.read_text())
    rnpz = Path(replay_dir) / f"scan_null_{tag}.npz"
    if sha256_file(rnpz) != rr["npz_sha256"]:
        raise ValueError(f"replay npz identity mismatch for {tag}")
    bad, n_arr = [], 0
    with np.load(stored_npz) as d, np.load(rnpz) as e:
        if sorted(d.files) != sorted(e.files):
            raise ValueError(f"replay arrays differ in names for {tag}")
        n = None
        for k in sorted(d.files):
            x, y = d[k], e[k]
            n = len(y)
            same = np.array_equal(x[:n], y, equal_nan=bool(np.issubdtype(x.dtype, np.floating)))
            n_arr += 1
            if not same:
                bad.append(k)
    main = rr.get("provenance", {}).get("main_script") or {}
    return {"status": "BIT_IDENTICAL" if not bad else "MISMATCH", "draws_compared": n, "arrays_compared": n_arr,
            "mismatched_arrays": bad, "replay_receipt": str(rj), "replay_receipt_sha256": sha256_file(rj),
            "replay_seed": rr["seed"], "replay_amplitude_mas_per_yr_per_unit_e": rr["amplitude_mas_per_yr_per_unit_e"],
            "replay_gaia_scan_null_py_sha256": main.get("sha256"),
            "replay_gaia_estimator_py_sha256": rr.get("provenance", {}).get("module_sha256", {}).get("scripts/r108/gaia_estimator.py")}


def summarize(a):
    obs = json.loads(est.R106_OBSERVED.read_text())
    out_dir = Path(a.out_dir)
    cal = json.loads(Path(a.calibration).read_text())
    res = {"schema": "htt.r108.gaia_scan_null/2", "units": "Q dimensionless; amplitudes relative to the calibrated amplitude",
           "calibrated_p": None, "significance_sigma": None, "physical_Pi": None, "physical_GF": None,
           "r106_observed_sha256": sha256_file(est.R106_OBSERVED), "calibration_sha256": sha256_file(a.calibration),
           "calibration": cal["calibration"], "observed_pixel_power": cal["observed_pixel_power"], "kinds": {}}
    tags = list(KINDS) + sorted(p.name[len("scan_null_"):-len(".json")] for p in out_dir.glob("scan_null_*__amp_*.json"))
    for kind in tags:
        jp = out_dir / f"scan_null_{kind}.json"
        if not jp.exists():
            res["kinds"][kind] = {"status": "NOT_RUN"}
            continue
        r = json.loads(jp.read_text())
        npz = out_dir / f"scan_null_{kind}.npz"
        if sha256_file(npz) != r["npz_sha256"]:
            raise ValueError(f"npz identity mismatch for {kind}")
        ent = {"receipt": {k: r.get(k) for k in ("draws", "seed", "amplitude_mas_per_yr_per_unit_e", "amplitude_from",
                                                 "npz_sha256", "runtime_s", "calibration_sha256")},
               "receipt_path": str(jp), "receipt_sha256": sha256_file(jp),
               "command": r["provenance"]["argv"], "script_version": receipt_script_version(kind, r), "tables": {}}
        if a.replay_dir is not None:
            ent["replay_check"] = replay_check(npz, a.replay_dir, kind)
            if ent["replay_check"]["status"] == "MISMATCH":
                raise ValueError(f"replay of {kind} by the current script is not bit-identical: {ent['replay_check']}")
        with np.load(npz) as d:
            for cfg, ocfg, jk in (("all48", "all48", "jk1"), ("all48_jk2", "all48", "jk2"), ("excl", "excl_8_47", "jk1"),
                                  ("excl_jk2", "excl_8_47", "jk2")):
                for k in ("spin6", "magnetic16", "joint32"):
                    x = d[f"{cfg}__{k}"]
                    o = obs["configs"][ocfg][jk][k]
                    ent["tables"][f"{cfg}__{k}"] = {"observed": o, "null_q50": float(np.median(x)), "null_q95": float(np.quantile(x, .95)),
                                                    "null_q99": float(np.quantile(x, .99)), "null_max": float(x.max()),
                                                    "draws_ge_observed": int((x >= o).sum()), "draws": int(len(x))}
            if kind.startswith("sys_"):
                for cfg, key, ocfg in (("all48", "sys_q_all48", "all48"), ("excl_8_47", "sys_q_excl", "excl_8_47")):
                    sq = d[key]
                    o = obs["configs"][ocfg]["jk1"]["spin6"]
                    need = np.sqrt(o / sq)
                    ent[f"systematic_only_{cfg}"] = {
                        "spin6_Q_in_observed_jk1_q50_q95_max": [float(np.median(sq)), float(np.quantile(sq, .95)), float(sq.max())],
                        "amplitude_needed_for_observed_spin6_over_calibrated_q01_q50": [float(np.quantile(need, .01)), float(np.median(need))],
                        "min_amplitude_needed_over_calibrated": float(need.min())}
        res["kinds"][kind] = ent
    groups = {}
    for kind, v in res["kinds"].items():
        if "script_version" in v:
            groups.setdefault(v["script_version"]["group"], []).append(kind)
    rep = {k: v["replay_check"]["status"] for k, v in res["kinds"].items() if "replay_check" in v}
    res["script_versions"] = {
        "summarize_script": est.main_script_identity(),
        "receipts_by_version_group": groups,
        "replay_dir": None if a.replay_dir is None else str(a.replay_dir),
        "replay_status_by_kind": rep,
        "note": ("Receipts in the pre_fix groups were written before gaia_estimator.provenance() hashed the __main__ script, "
                 "so they carry no gaia_scan_null.py SHA-256 (their gaia_estimator.py SHA-256 is recorded per kind). The "
                 "pre_fix_A / pre_fix_B split is the only receipt-visible difference between those earlier versions. "
                 "replay_check reruns the first draws of every stored run (same kind, seed, calibration and amplitude) with "
                 "the current script, whose SHA-256 is recorded in the replay receipt; BIT_IDENTICAL means every stored array "
                 "agrees bit for bit on those draws, i.e. the stored run is reproduced by that identified script version "
                 "for the compared draws (later draws of the same loop are not re-executed).")}
    res["assumptions"] = [
        "noise: Gaussian, independent between sources, catalogue covariance (or scan-law shape with catalogue trace)",
        "systematic: along-scan error constant over blocks of 10 s / 600 s / 6 h of one FOV stream, independent between "
        "blocks and FOVs, propagated through a 5-parameter along-scan least squares per NSIDE-64 pixel of the commanded "
        "scan law; source coupling blind, linear in BP-RP or linear in G",
        "amplitude: the largest of three NSIDE-16 pixel-power measurements (upper 97.5%; complement auto power, complement "
        "and Quaia random-half cross power) is attributed to the modelled systematic; real Gaia systematics with other "
        "spatial/temporal structure are not covered",
        "no cosmological signal in the mocks; the observed R106 value is compared with the mock distribution (rank only, "
        "no calibrated p: the systematic model is not a qualified description of the Gaia error budget)"]
    write_json(a.out, res)
    print(json.dumps({k: (v.get("tables", {}).get("all48__spin6") if isinstance(v, dict) else None) for k, v in res["kinds"].items()}))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--scan-dir", type=Path, required=True)
    v.add_argument("--out", type=Path, required=True)
    c = sub.add_parser("calibrate")
    c.add_argument("--scan-dir", type=Path, required=True)
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--cal-draws", type=int, default=16)
    c.add_argument("--seed", type=int, default=108300)
    r = sub.add_parser("run")
    r.add_argument("--kind", choices=KINDS, required=True)
    r.add_argument("--draws", type=int, required=True)
    r.add_argument("--seed", type=int, required=True)
    r.add_argument("--scan-dir", type=Path)
    r.add_argument("--calibration", type=Path)
    r.add_argument("--out-dir", type=Path, required=True)
    r.add_argument("--amplitude-from", choices=("complement_auto", "complement_cross", "quaia_cross"), default=None,
                   help="sensitivity run at another calibration candidate (output tagged __amp_<name>)")
    s = sub.add_parser("summarize")
    s.add_argument("--out-dir", type=Path, required=True)
    s.add_argument("--calibration", type=Path, required=True)
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--replay-dir", type=Path, default=None,
                   help="directory of short reruns (run --draws n, same kind/seed/calibration) for a bit-identity check")
    a = ap.parse_args(argv)
    {"validate": validate, "calibrate": calibrate, "run": run, "summarize": summarize}[a.cmd](a)


if __name__ == "__main__":
    main()
