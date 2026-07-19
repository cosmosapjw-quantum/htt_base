#!/usr/bin/env python3
"""PR-151 producer: official DESI DR1 EZmock-calibrated dipole result.

The frozen estimand is the weighted BGS_BRIGHT-21.5 (0.1 <= z <= 0.4)
number-count dipole.  The observation uses its own DR1 NGC/SGC random window;
every FFA mock uses the NSIDE=64 compact window derived from that mock's
authenticated random-realisation-0 pair.  The same pixelization, redshift cut,
weights, per-cap alpha refit, and nuisance refit are applied to the observation,
1000 EZmocks, and (separately) 25 AbacusSummit FFA validation mocks.  EZmock and
Abacus are never pooled.  Random-realisation-1 windows on a preregistered subset
quantify Monte-Carlo integration sensitivity to the single-random policy.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt", REPO / "htt" / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.desi_exact_selection_mock import per_mock_refit  # noqa: E402

OUT = REPO / "docs/generated/desi_official_mock_card.json"
NSIDE = 64
ZMIN = 0.1
ZMAX = 0.4
CHUNK_ROWS = 1_000_000
CMB_DIPOLE_GALACTIC_DEG = (264.021, 48.253)


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _canonical_sha(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _stable_generation_environment(acquisition_sha256: str) -> dict:
    if OUT.is_file():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
            provenance = old.get("provenance") or {}
            environment = provenance.get("generation_environment")
            if (provenance.get("acquisition_manifest_sha256")
                    == acquisition_sha256 and isinstance(environment, dict)):
                return environment
        except (OSError, ValueError, TypeError):
            pass
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
        text=True, check=True).stdout.strip()
    dirty = bool(subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO,
        capture_output=True, text=True, check=True).stdout.strip())
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "git_commit": head,
        "worktree_state": "dirty" if dirty else "clean",
    }


def _column(table, name: str, sl: slice, default: float = 1.0) -> np.ndarray:
    if name not in table.columns.names:
        return np.full(sl.stop - sl.start, default, dtype=np.float64)
    return np.asarray(table[name][sl], dtype=np.float64)


def pixel_counts(path: Path, *, nside: int = NSIDE) -> dict:
    """Read one DESI clustering table in bounded chunks and return a weighted map."""
    import healpy as hp
    from astropy.io import fits

    npix = hp.nside2npix(nside)
    counts = np.zeros(npix, dtype=np.float64)
    selected = 0
    weight_sum = 0.0
    with fits.open(path, memmap=True, lazy_load_hdus=True) as hdus:
        table = hdus[1].data
        n_rows = len(table)
        names = set(table.columns.names)
        required = {"RA", "DEC", "Z", "WEIGHT"}
        if not required.issubset(names):
            raise ValueError(
                f"{path} lacks required columns {sorted(required - names)}"
            )
        for start in range(0, n_rows, CHUNK_ROWS):
            stop = min(start + CHUNK_ROWS, n_rows)
            sl = slice(start, stop)
            ra = _column(table, "RA", sl)
            dec = _column(table, "DEC", sl)
            z = _column(table, "Z", sl)
            weight = _column(table, "WEIGHT", sl)
            keep = ((z >= ZMIN) & (z <= ZMAX) & np.isfinite(ra)
                    & np.isfinite(dec) & np.isfinite(weight) & (weight > 0))
            if not np.any(keep):
                continue
            pix = hp.ang2pix(nside, ra[keep], dec[keep], lonlat=True)
            counts += np.bincount(pix, weights=weight[keep], minlength=npix)
            selected += int(np.count_nonzero(keep))
            weight_sum += float(np.sum(weight[keep]))
    if selected == 0 or weight_sum <= 0:
        raise ValueError(f"no rows survive the frozen z/weight cut in {path}")
    return {"counts": counts, "n_rows": n_rows, "n_selected": selected,
            "weight_sum": weight_sum}


def _selection_template(vec: np.ndarray, mask: np.ndarray) -> np.ndarray:
    z = vec[2]
    template = np.zeros(vec.shape[1])
    template[mask] = z[mask] + 0.25 * (3.0 * z[mask] ** 2 - 1.0)
    template[mask] -= template[mask].mean()
    return template


def _finite_rank(observed: float, values: list[float]) -> dict:
    null = np.asarray(values, dtype=float)
    n = int(null.size)
    if n < 1 or not np.all(np.isfinite(null)):
        raise ValueError("finite-rank ensemble is empty or non-finite")
    b_upper = int(np.count_nonzero(null >= observed))
    b_lower = int(np.count_nonzero(null <= observed))
    ties = int(np.count_nonzero(null == observed))
    p_upper = (1 + b_upper) / (n + 1)
    p_lower = (1 + b_lower) / (n + 1)
    p_two = min(1.0, 2.0 * min(p_upper, p_lower))
    rank_strict = 1 + int(np.count_nonzero(null < observed))
    k = int(math.floor(0.025 * (n + 1)))
    tolerance = None
    if k >= 1:
        ordered = np.sort(null)
        tolerance = {
            "lower_order_1_based": k,
            "upper_order_1_based": n - k + 1,
            "lower": float(ordered[k - 1]),
            "upper": float(ordered[n - k]),
            "finite_predictive_coverage": float(1.0 - 2.0 * k / (n + 1)),
        }
    return {
        "n_mock": n,
        "observed": float(observed),
        "upper_exceedance_count": b_upper,
        "lower_exceedance_count": b_lower,
        "tie_count": ties,
        "observation_inclusive_strict_rank": rank_strict,
        "right_tail_p": float(p_upper),
        "left_tail_p": float(p_lower),
        "central_two_sided_p": float(p_two),
        "support_resolution": float(1.0 / (n + 1)),
        "central_95pct_finite_predictive_interval": tolerance,
        "tail_rule": "inclusive finite rank: p=(1 + count mock at least as extreme)/(N+1)",
    }


def _direction(vector: np.ndarray) -> dict:
    import healpy as hp
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    amplitude = float(np.linalg.norm(vector))
    unit = vector / amplitude
    ra, dec = hp.vec2ang(np.asarray([unit]), lonlat=True)
    sky = SkyCoord(ra=float(ra[0]) * u.deg, dec=float(dec[0]) * u.deg,
                   frame="icrs")
    cmb = SkyCoord(l=CMB_DIPOLE_GALACTIC_DEG[0] * u.deg,
                   b=CMB_DIPOLE_GALACTIC_DEG[1] * u.deg, frame="galactic")
    return {
        "amplitude": amplitude,
        "vector_equatorial_cartesian": [float(v) for v in vector],
        "ra_dec_deg": [float(sky.ra.deg), float(sky.dec.deg)],
        "galactic_l_b_deg": [float(sky.galactic.l.deg),
                              float(sky.galactic.b.deg)],
        "separation_from_cmb_dipole_deg": float(sky.separation(cmb).deg),
    }


def _load_window(window: dict) -> tuple[dict[str, np.ndarray], dict]:
    path = Path(window["path"])
    actual = _sha(path)
    if actual != window["sha256"]:
        raise ValueError(f"compact random-window hash mismatch: {path}")
    with np.load(path) as data:
        if int(data["nside"]) != NSIDE:
            raise ValueError(f"random-window NSIDE mismatch: {path}")
        rp = {cap: np.asarray(data[cap], dtype=np.float64)
              for cap in ("NGC", "SGC")}
    if any(arr.shape != (12 * NSIDE * NSIDE,) for arr in rp.values()):
        raise ValueError(f"random-window shape mismatch: {path}")
    return rp, {
        "path": str(path), "sha256": actual,
        "random_index": int(window["random_index"]),
        "source_sha256": dict(window["source_sha256"]),
        "caps": dict(window["caps"]),
    }


def _measure_pair(files: list[dict], window: dict, vec: np.ndarray) -> dict:
    paths = {"NGC": Path(files[0]["path"]), "SGC": Path(files[1]["path"])}
    for record in files:
        path = Path(record["path"])
        if (not path.is_file() or path.stat().st_size != record["size_bytes"]
                or _sha(path) != record["sha256"]):
            raise ValueError(f"authenticated clustering-data hash mismatch: {path}")
    rp, window_meta = _load_window(window)
    template = {cap: _selection_template(vec, rp[cap] > 0) for cap in rp}
    loaded = {cap: pixel_counts(path) for cap, path in paths.items()}
    fit = per_mock_refit({cap: loaded[cap]["counts"] for cap in loaded},
                         rp, vec, selection_template_per_cap=template)
    return {
        "dipole_amplitude": float(fit["dipole_amplitude"]),
        "dipole": [float(v) for v in fit["dipole"]],
        "cleaned_dipole_amplitude": float(fit["cleaned_dipole_amplitude"]),
        "alpha_hat_per_cap": {k: float(v) for k, v in fit["alpha_hat_per_cap"].items()},
        "beta_hat": float(fit["beta_hat"]),
        "n_selected_per_cap": {cap: loaded[cap]["n_selected"] for cap in loaded},
        "weight_sum_per_cap": {cap: loaded[cap]["weight_sum"] for cap in loaded},
        "random_window": window_meta,
    }


def _paths(record: dict) -> list[dict]:
    rows = sorted(record["data_files"],
                  key=lambda row: ("SGC" in row["path"], row["path"]))
    if len(rows) != 2 or "NGC" not in rows[0]["path"] or "SGC" not in rows[1]["path"]:
        raise ValueError(f"record does not contain one NGC and one SGC file: {record}")
    return rows


def _audit_row(primary: dict, alternate: dict, family: str,
               realization: int) -> dict:
    pvec = np.asarray(primary["dipole"], dtype=float)
    avec = np.asarray(alternate["dipole"], dtype=float)
    pnorm = float(np.linalg.norm(pvec))
    anorm = float(np.linalg.norm(avec))
    if pnorm > 0 and anorm > 0:
        cosine = float(np.clip(np.dot(pvec, avec) / (pnorm * anorm), -1.0, 1.0))
        angle = float(np.degrees(np.arccos(cosine)))
    else:
        angle = None
    return {
        "family": family, "realization": realization,
        "random_indices": [0, 1],
        "amplitude_r0": pnorm, "amplitude_r1": anorm,
        "absolute_amplitude_difference": abs(anorm - pnorm),
        "relative_amplitude_difference": (abs(anorm - pnorm) / pnorm
                                          if pnorm > 0 else None),
        "dipole_direction_difference_deg": angle,
    }


def _audit_summary(rows: list[dict]) -> dict:
    if not rows:
        return {"n_audited": 0, "rows": []}
    absolute = np.asarray([row["absolute_amplitude_difference"] for row in rows])
    relative = np.asarray([row["relative_amplitude_difference"] for row in rows
                           if row["relative_amplitude_difference"] is not None])
    angles = np.asarray([row["dipole_direction_difference_deg"] for row in rows
                         if row["dipole_direction_difference_deg"] is not None])
    return {
        "n_audited": len(rows),
        "families": {family: sum(row["family"] == family for row in rows)
                     for family in ("ezmock", "abacus")},
        "absolute_amplitude_difference": {
            "median": float(np.median(absolute)), "max": float(np.max(absolute)),
            "q95": float(np.quantile(absolute, 0.95)),
        },
        "relative_amplitude_difference": {
            "median": float(np.median(relative)), "max": float(np.max(relative)),
            "q95": float(np.quantile(relative, 0.95)),
        },
        "dipole_direction_difference_deg": {
            "median": float(np.median(angles)), "max": float(np.max(angles)),
            "q95": float(np.quantile(angles, 0.95)),
        },
        "interpretation": "empirical random-catalogue Monte-Carlo integration sensitivity; not an additional cosmological null ensemble",
        "rows": rows,
    }


def measure(acquisition_manifest: Path, jobs: int = 8) -> dict:
    import healpy as hp
    from scipy.stats import ks_2samp

    acquisition = json.loads(acquisition_manifest.read_text(encoding="utf-8"))
    if acquisition.get("status") != "complete":
        raise ValueError("DESI acquisition manifest is not complete")
    if acquisition.get("authenticated_counts") != {"abacus": 25, "ezmock": 1000}:
        raise ValueError("expected exactly 1000 authenticated EZmocks and 25 Abacus mocks")
    observed_record = acquisition["observed"]
    data_paths = sorted(
        observed_record["data_files"],
        key=lambda row: ("SGC" in row["path"], row["path"]))

    npix = hp.nside2npix(NSIDE)
    vec = np.asarray(hp.pix2vec(NSIDE, np.arange(npix)))
    observed = _measure_pair(data_paths, observed_record["random_window"], vec)
    observed["direction"] = _direction(np.asarray(observed.pop("dipole"), float))

    records = acquisition["records"]
    tasks = [(row["family"], int(row["realization"]), _paths(row),
              row["random_windows"]["0"], row["random_windows"].get("1"))
             for row in records]
    results = {"ezmock": [], "abacus": []}
    random_audit: list[dict] = []

    def evaluate(files, window0, window1):
        primary = _measure_pair(files, window0, vec)
        alternate = (_measure_pair(files, window1, vec)
                     if window1 is not None else None)
        return primary, alternate

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        future_map = {pool.submit(evaluate, files, window0, window1):
                      (family, realization)
                      for family, realization, files, window0, window1 in tasks}
        for done, future in enumerate(concurrent.futures.as_completed(future_map), 1):
            family, realization = future_map[future]
            row, alternate = future.result()
            row["realization"] = realization
            results[family].append(row)
            if alternate is not None:
                random_audit.append(_audit_row(row, alternate, family, realization))
            if done % 25 == 0 or done == len(tasks):
                print(f"processed {done}/{len(tasks)} official mocks", flush=True)
    for family in results:
        results[family].sort(key=lambda row: row["realization"])
    random_audit.sort(key=lambda row: (row["family"], row["realization"]))

    ez_amp = [row["dipole_amplitude"] for row in results["ezmock"]]
    ab_amp = [row["dipole_amplitude"] for row in results["abacus"]]
    ez_rank = _finite_rank(observed["dipole_amplitude"], ez_amp)
    ab_rank = _finite_rank(observed["dipole_amplitude"], ab_amp)
    ks = ks_2samp(ez_amp, ab_amp, alternative="two-sided", method="exact")
    source_hash = _sha(acquisition_manifest)
    config = {"nside": NSIDE, "z_min_inclusive": ZMIN,
              "z_max_inclusive": ZMAX, "weight_column": "WEIGHT",
              "sample": "BGS_BRIGHT-21.5", "ezmock_flavour": "FFA",
              "abacus_flavour": "FFA"}
    return {
        "schema": "htt.desi_official_mock_card.v2",
        "status": "OFFICIAL_MOCK_CONDITIONAL_RESULT",
        "owner": "OBSSTAT",
        "implementation_scope": ["obsstat", "dl_pipeline"],
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C3"},
        "artifact_mode": "desi_dr1_bgs_official_mock_conditioned_null_result",
        "transfer_source": "none",
        "config": config,
        "config_hash": f"sha256:{_canonical_sha(config)}",
        "observed": observed,
        "observed_random_window": observed["random_window"],
        "ezmock": {
            "rank": ez_rank,
            "amplitude_summary": {
                "mean": float(np.mean(ez_amp)), "std": float(np.std(ez_amp, ddof=1)),
                "median": float(np.median(ez_amp)),
                "q025_q975": [float(np.quantile(ez_amp, 0.025)),
                               float(np.quantile(ez_amp, 0.975))],
            },
            "realizations": results["ezmock"],
        },
        "abacus_validation": {
            "rank": ab_rank,
            "amplitude_summary": {
                "mean": float(np.mean(ab_amp)), "std": float(np.std(ab_amp, ddof=1)),
                "median": float(np.median(ab_amp)),
                "q025_q975": [float(np.quantile(ab_amp, 0.025)),
                               float(np.quantile(ab_amp, 0.975))],
            },
            "realizations": results["abacus"],
            "pooled_with_ezmock": False,
        },
        "ezmock_abacus_transport_check": {
            "two_sample_ks_statistic": float(ks.statistic),
            "two_sample_ks_p": float(ks.pvalue),
            "interpretation": "separate finite validation-tier comparison; not pooled rank support",
        },
        "random_replication_sensitivity": _audit_summary(random_audit),
        "provenance": {
            "acquisition_manifest": str(acquisition_manifest),
            "acquisition_manifest_sha256": source_hash,
            "aggregate_input_hash": acquisition["aggregate_input_hash"],
            "official_reference": acquisition["source_url"],
            "input_hashes": [
                {"path": str(acquisition_manifest),
                 "sha256": f"sha256:{source_hash}"},
                {"path": "aggregate_authenticated_DESI_inputs",
                 "sha256": f"sha256:{acquisition['aggregate_input_hash']}"},
            ],
            "generation_environment":
                _stable_generation_environment(source_hash),
        },
        "sky_support_status": "observed data window plus authenticated mock-specific FFA random-0 NGC+SGC windows at NSIDE64",
        "mask_status": "selection support is carried by authenticated random windows; no substitute binary mask",
        "covariance_status": "empirical finite ranks from 1000 EZmocks with 25 Abacus validation mocks kept separate",
        "null_mock_status": "1000 authenticated EZmocks with mock-specific windows; 25 authenticated Abacus FFA validation mocks reported separately; random-1 replication audit on 15 preregistered mocks",
        "caveats": [
            "one authenticated random realisation per mock defines the primary selection window; the registered random-1 subset reports Monte-Carlo integration sensitivity, while all 18 random realisations are not averaged",
            "the result is conditional on official FFA mock fidelity, each mock-specific random window, BGS_BRIGHT-21.5 selection, weights, redshift cut, pixelization, and nuisance-refit contract",
            "failure to reject is not proof that the null is true and does not identify clustering, kinematic, or selection causation",
            "no anisotropy detection, geometry, Bianchi-family, or native-solver claim",
        ],
        "claim_boundary": "concrete survey-and-official-mock-conditioned empirical null comparison; not causal attribution or family identification",
        "generating_command": f"venv/bin/python scripts/desi_official_mock_card.py --acquisition-manifest {acquisition_manifest} --jobs {jobs}",
        "git_worktree_state": "recorded by the PR-151 artifact manifest runner",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition-manifest", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    # Keep binary64 values intact in the scientific card.  Display rounding
    # belongs in captions only; finite-rank support and paired sensitivity
    # receipts must remain independently recomputable from serialized values.
    payload = measure(args.acquisition_manifest.resolve(), args.jobs)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text() != rendered:
            print(f"stale {args.output}")
            return 1
        print(f"{args.output} up to date")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(args.output.suffix + ".tmp")
    temp.write_text(rendered)
    temp.replace(args.output)
    rank = payload["ezmock"]["rank"]
    print(f"wrote {args.output} N={rank['n_mock']} "
          f"p_right={rank['right_tail_p']} p_two={rank['central_two_sided_p']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
