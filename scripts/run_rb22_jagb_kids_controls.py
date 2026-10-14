#!/usr/bin/env python3
"""RB22 descriptive controls for CCHP-JAGB photometry and KiDS-1000 SOM n(z).

No likelihood, uncertainty model, significance test, distance conversion, or
physical interpretation is produced. See the report metadata for source limits.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DEFAULT_CCHP = Path("workdir/raw/jwst_sn/cchp_jagb_zenodo_14502265/CCHP-JAGB-v1.zip")
DEFAULT_KIDS = Path("workdir/raw/hsc_kids/kids/KiDS1000_SOM_N_of_Z.tar.gz")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def finite_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _midranks(values: Sequence[float]) -> np.ndarray:
    """Average ranks for ties, with rank 1 assigned to the smallest value."""
    x = np.asarray(values, dtype=float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    i = 0
    while i < len(x):
        j = i + 1
        while j < len(x) and x[order[j]] == x[order[i]]:
            j += 1
        ranks[order[i:j]] = ((i + 1) + j) / 2.0
        i = j
    return ranks


def spearman_rho(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Descriptive Spearman coefficient only; no p-value or significance."""
    if len(x) != len(y) or len(x) < 2:
        return None
    rx, ry = _midranks(x), _midranks(y)
    if np.ptp(rx) == 0 or np.ptp(ry) == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def _quartile_profile(radius: Sequence[float], color: Sequence[float]) -> dict:
    r = np.asarray(radius, dtype=float)
    c = np.asarray(color, dtype=float)
    if len(r) != len(c) or not len(r):
        return {"edges": [], "spearman_rho": None, "bins": []}
    edges = np.quantile(r, [0.0, 0.25, 0.5, 0.75, 1.0], method="linear")
    labels = np.searchsorted(edges[1:-1], r, side="right")
    bins = []
    for index in range(4):
        use = labels == index
        if not np.any(use):
            bins.append({"quartile": index + 1, "n": 0, "median": None,
                         "q25": None, "q75": None, "iqr": None})
            continue
        q25, median, q75 = np.quantile(c[use], [0.25, 0.5, 0.75], method="linear")
        bins.append({"quartile": index + 1, "n": int(np.sum(use)),
                     "radius_min": float(np.min(r[use])),
                     "radius_max": float(np.max(r[use])),
                     "median": float(median), "q25": float(q25),
                     "q75": float(q75), "iqr": float(q75 - q25)})
    return {"edges": [float(v) for v in edges],
            "spearman_rho": spearman_rho(r.tolist(), c.tolist()), "bins": bins}


def analyze_cchp(path: Path) -> dict:
    results = []
    with zipfile.ZipFile(path) as archive:
        names = sorted(n for n in archive.namelist() if n.lower().endswith(".csv"))
        if len(names) != 11:
            raise ValueError(f"Expected 11 host CSVs, found {len(names)}")
        for member in names:
            raw = archive.read(member)
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="strict")))
            fields = reader.fieldnames or []
            color_bands = [band for band in ("F356W", "F444W") if band in fields]
            required = {"RA", "DEC", "RGC", "F115W"}
            if not color_bands or not required.issubset(fields):
                raise ValueError(f"Unexpected CCHP schema in {member}: {fields}")
            rows = list(reader)
            for color_band in color_bands:
                n_rows = n_pairs = n_missing_color_pair = n_missing_rgc = n_radial = 0
                radii: list[float] = []
                colors: list[float] = []
                for row in rows:
                    n_rows += 1
                    f115, other, rgc = (finite_float(row.get(k)) for k in ("F115W", color_band, "RGC"))
                    if f115 is not None and other is not None:
                        n_pairs += 1
                        if rgc is not None:
                            n_radial += 1
                            radii.append(rgc)
                            colors.append(f115 - other)
                    else:
                        n_missing_color_pair += 1
                    if rgc is None:
                        n_missing_rgc += 1
                results.append({
                    "host": Path(member).stem,
                    "source_member": member,
                    "source_member_sha256": sha256_bytes(raw),
                    "color_pair": f"F115W-{color_band}",
                    "rows": n_rows,
                    "finite_color_pairs": n_pairs,
                    "missing_color_pairs": n_missing_color_pair,
                    "missing_rgc": n_missing_rgc,
                    "finite_color_and_rgc": n_radial,
                    "radial_axis": "RGC released coordinate; unit unresolved; no conversion",
                    "profile": _quartile_profile(radii, colors),
                })
    return {"source": "Lee et al. (2024) CCHP-JAGB v1; Zenodo 10.5281/zenodo.14502265",
            "hosts": results,
            "summary": {"host_csv_count": len(names),
                        "host_filter_profile_count": len(results),
                        "row_count": sum({h["source_member"]: h["rows"] for h in results}.values()),
                        "filter_groups": {
                            pair: [h["host"] for h in results if h["color_pair"] == pair]
                            for pair in sorted({h["color_pair"] for h in results})}}}


def parse_nz_table(text: str) -> tuple[np.ndarray, np.ndarray]:
    rows = []
    for line_no, line in enumerate(text.splitlines(), 1):
        content = line.split("#", 1)[0].strip()
        if not content:
            continue
        parts = content.split()
        if len(parts) != 2:
            raise ValueError(f"Line {line_no}: expected two columns")
        pair = [finite_float(part) for part in parts]
        if any(v is None for v in pair):
            raise ValueError(f"Line {line_no}: non-finite or invalid number")
        rows.append(pair)
    if len(rows) < 2:
        raise ValueError("Need at least two tabulated bins")
    table = np.asarray(rows, dtype=float)
    starts, values = table[:, 0], table[:, 1]
    if np.any(values < 0):
        raise ValueError("n(z) table contains negative values")
    widths = np.diff(starts)
    if np.any(widths <= 0) or not np.allclose(widths, widths[0], rtol=0, atol=1e-10):
        raise ValueError("binstart values must be strictly increasing and uniform")
    if np.sum(values) <= 0:
        raise ValueError("n(z) table has zero total mass")
    return starts, values


def _weighted_quantile_bins(starts: np.ndarray, masses: np.ndarray, q: float) -> float:
    width = float(starts[1] - starts[0])
    total = float(np.sum(masses))
    target = q * total
    cumulative = 0.0
    for start, mass in zip(starts, masses):
        if mass > 0 and cumulative + mass >= target:
            fraction = min(1.0, max(0.0, (target - cumulative) / mass))
            return float(start + fraction * width)
        cumulative += float(mass)
    return float(starts[-1] + width)


def summarize_nz(starts: np.ndarray, raw_density: np.ndarray) -> dict:
    width = float(starts[1] - starts[0])
    # Local table says binstart,density and values sum to 1.0 for each tomo.
    # Uniform bin widths make normalizing values or density*width equivalent.
    bin_mass = raw_density * width
    bin_mass = bin_mass / float(np.sum(bin_mass))
    centers = starts + width / 2.0
    return {"bin_count": int(len(starts)), "z_min": float(starts[0]),
            "z_max": float(starts[-1] + width), "bin_width": width,
            "input_density_sum": float(np.sum(raw_density)),
            "normalized_bin_mass_sum": float(np.sum(bin_mass)),
            "mean_z": float(np.sum(centers * bin_mass)),
            "quantiles": {str(q): _weighted_quantile_bins(starts, bin_mass, q)
                          for q in (0.16, 0.5, 0.84)},
            "normalized_bin_mass": [float(v) for v in bin_mass]}


def overlap_coefficient(left: Sequence[float], right: Sequence[float]) -> float:
    """Discrete overlap of normalized bin masses on an identical grid."""
    a, b = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if a.shape != b.shape or a.ndim != 1 or not len(a):
        raise ValueError("overlap inputs must be nonempty vectors on the same grid")
    if np.any(~np.isfinite(a)) or np.any(~np.isfinite(b)) or np.any(a < 0) or np.any(b < 0):
        raise ValueError("overlap inputs must be finite nonnegative masses")
    if np.sum(a) <= 0 or np.sum(b) <= 0:
        raise ValueError("overlap inputs must have positive mass")
    a, b = a / np.sum(a), b / np.sum(b)
    return float(np.sum(np.minimum(a, b)))


def analyze_kids(path: Path) -> dict:
    bins = {}
    with tarfile.open(path, mode="r:gz") as archive:
        members = [m for m in archive.getmembers() if m.isfile() and m.name.endswith(".asc")]
        if len(members) != 5:
            raise ValueError(f"Expected 5 KiDS TOMO files, found {len(members)}")
        for member in sorted(members, key=lambda item: item.name):
            match = __import__("re").search(r"TOMO([1-5])_Nz\.asc$", member.name)
            if not match:
                raise ValueError(f"Unexpected KiDS file name: {member.name}")
            payload = archive.extractfile(member)
            if payload is None:
                raise ValueError(f"Cannot read {member.name}")
            raw = payload.read()
            starts, vals = parse_nz_table(raw.decode("ascii"))
            bins[f"TOMO{match.group(1)}"] = {
                "source_member": member.name,
                "source_member_sha256": sha256_bytes(raw),
                **summarize_nz(starts, vals),
            }
    names = [f"TOMO{i}" for i in range(1, 6)]
    reference = bins[names[0]]
    for name in names[1:]:
        if bins[name]["bin_count"] != reference["bin_count"] or bins[name]["bin_width"] != reference["bin_width"] or bins[name]["z_min"] != reference["z_min"]:
            raise ValueError("KiDS TOMO grids do not align; overlap is undefined")
    overlap = {}
    for i, left in enumerate(names):
        for right in names[i:]:
            a = np.asarray(bins[left]["normalized_bin_mass"])
            b = np.asarray(bins[right]["normalized_bin_mass"])
            value = overlap_coefficient(a, b)
            overlap[f"{left}:{right}"] = value
            overlap[f"{right}:{left}"] = value
    return {"source": "KiDS-1000 official DR4 SOM-gold n(z) product; five tomographic distributions",
            "interpretation": "two-column binstart,density table; normalized discrete bin masses; piecewise-uniform within-bin quantiles; descriptive only",
            "bins": bins, "pairwise_overlap_coefficient": overlap}


def _readme_summary(cchp: dict, kids: dict, cchp_sha: str, kids_sha: str) -> str:
    lines = [
        "# RB22 CCHP-JAGB and KiDS-1000 source controls",
        "",
        "## Scope",
        "",
        "Descriptive source-bound summaries only. No uncertainty propagation, significance testing, cosmological likelihood, distance estimate, or physical-law claim is made.",
        "CCHP RGC is preserved as the released coordinate; its unit is unresolved here and no conversion is applied.",
        "KiDS values are the supplied five tomographic SOM n(z) tables. The source table labels columns `binstart, density`; this run treats each equally spaced row as nonnegative bin weight, normalizes those weights, and assumes uniform density within each bin only for quantile interpolation. The equal spacing means normalizing density×binwidth and normalizing row weights give the same bin probabilities.",
        "",
        "## Sources",
        "",
        f"- CCHP ZIP SHA-256: `{cchp_sha}`. Zenodo DOI 10.5281/zenodo.14502265; README identifies JWST NIRCam photometry for Lee et al. (2024).",
        f"- KiDS tarball SHA-256: `{kids_sha}`. Official KiDS DR4 page calls this a SOM-calibrated n(z) tarball for the five tomographic bins; see https://kids.strw.leidenuniv.nl/DR4/KiDS-1000_shearcatalogue.php and Hildebrandt et al. 2021 https://arxiv.org/abs/2007.15635.",
        "- CCHP release source URL: https://zenodo.org/api/records/14502265/files/abiglee7/CCHP-JAGB-v1.zip/content",
        "",
        "## CCHP-JAGB",
        "",
        f"Rows: {cchp['summary']['row_count']} across {cchp['summary']['host_csv_count']} host tables.",
        "Each filter group is summarized separately. Within-host radial quartiles use empirical 25/50/75 percentiles of released RGC; color statistics are median and IQR. Spearman rho is descriptive only and has no p-value.",
        "",
        "| Host | Color | Rows | Finite color pairs | Missing color pairs | Missing RGC | Finite color and RGC | Spearman rho |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for host in cchp["hosts"]:
        rho = host["profile"]["spearman_rho"]
        lines.append(f"| {host['host']} | {host['color_pair']} | {host['rows']} | {host['finite_color_pairs']} | {host['missing_color_pairs']} | {host['missing_rgc']} | {host['finite_color_and_rgc']} | {rho if rho is not None else 'NA'} |")
    lines += ["", "## KiDS SOM n(z)", "", "| Tomographic bin | Mean z | q16 | q50 | q84 |", "|---|---:|---:|---:|---:|"]
    for name, item in kids["bins"].items():
        q = item["quantiles"]
        lines.append(f"| {name} | {item['mean_z']:.6f} | {q['0.16']:.6f} | {q['0.5']:.6f} | {q['0.84']:.6f} |")
    lines += ["", "Pairwise overlap is the descriptive discrete coefficient `sum_i min(p_i, q_i)` on the shared redshift grid. It is not an independence or covariance statement.", ""]
    return "\n".join(lines)


def run(cchp_path: Path, kids_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output directory: {output}")
    output.mkdir(parents=True)
    cchp_path, kids_path = cchp_path.resolve(), kids_path.resolve()
    cchp = analyze_cchp(cchp_path)
    kids = analyze_kids(kids_path)
    cchp_hash, kids_hash = sha256_file(cchp_path), sha256_file(kids_path)
    result = {"schema": "htt.rb22.jagb_kids_controls.v1",
              "claim_tier": "DESCRIPTIVE_ONLY", "scientific_admission": "HOLD",
              "cchp": cchp, "kids": kids,
              "inputs": [{"path": str(cchp_path), "sha256": cchp_hash,
                          "size_bytes": cchp_path.stat().st_size},
                         {"path": str(kids_path), "sha256": kids_hash,
                          "size_bytes": kids_path.stat().st_size}],
              "source_conventions": {
                  "cchp": "release README says JWST NIRCam photometry; CSV fields are literal; RGC unit unresolved",
                  "kids": "official DR4 product page identifies the tarball as five SOM-calibrated tomographic n(z) distributions; tabulated binstart,density values normalized as equal-width bin weights",
              },
              "limitations": ["no significance claims", "no distances or SN fit",
                              "no CCHP measurement covariance/uncertainties/completeness or masks",
                              "no RGC unit conversion", "KiDS overlap is a table-shape descriptor, not covariance"]}
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "report.md").write_text(_readme_summary(cchp, kids, cchp_hash, kids_hash), encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    colors = {"F115W-F356W": "#1f77b4", "F115W-F444W": "#d95f02"}
    for host in cchp["hosts"]:
        profile = host["profile"]["bins"]
        valid = [b for b in profile if b["n"]]
        if valid:
            axes[0].plot([b["quartile"] for b in valid], [b["median"] for b in valid],
                         marker="o", alpha=0.65, linewidth=1,
                         color=colors[host["color_pair"]], label=host["color_pair"])
    axes[0].set_xticks([1, 2, 3, 4], ["Q1", "Q2", "Q3", "Q4"])
    axes[0].set_xlabel("Within-host RGC quartile (released coordinate)")
    axes[0].set_ylabel("Median color (mag; F115W − other band)")
    axes[0].set_title("CCHP-JAGB within-host color profiles")
    handles, labels = axes[0].get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    axes[0].legend(unique.values(), unique.keys(), frameon=False)
    for name, item in kids["bins"].items():
        starts = np.linspace(item["z_min"], item["z_max"] - item["bin_width"], item["bin_count"])
        axes[1].step(starts + item["bin_width"] / 2,
                     item["normalized_bin_mass"], where="mid", label=name)
    axes[1].set_xlabel("Redshift z")
    axes[1].set_ylabel("Normalized tabulated bin weight")
    axes[1].set_title("KiDS-1000 SOM-gold n(z) shapes")
    axes[1].legend(frameon=False, ncol=2)
    fig.savefig(output / "diagnostic.png", dpi=160)
    fig.savefig(output / "diagnostic.pdf")
    plt.close(fig)

    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = "UNKNOWN"
    receipt = {"status": "COMPLETED_DESCRIPTIVE_EXECUTION",
               "created_utc": datetime.now(timezone.utc).isoformat(),
               "git_head": head,
               "command": "python scripts/run_rb22_jagb_kids_controls.py --output <new-directory>",
               "source_script_sha256": sha256_file(Path(__file__).resolve()),
               "inputs": result["inputs"],
               "outputs": {p.name: {"size_bytes": p.stat().st_size,
                                    "sha256": sha256_file(p)}
                           for p in sorted(output.iterdir()) if p.is_file() and p.name != "execution_receipt.json"},
               "claim_tier": "DESCRIPTIVE_ONLY", "scientific_admission": "HOLD"}
    (output / "execution_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cchp-zip", type=Path, default=DEFAULT_CCHP)
    parser.add_argument("--kids-nz-tar", type=Path, default=DEFAULT_KIDS)
    parser.add_argument("--output", type=Path, required=True, help="new output directory; must not exist")
    args = parser.parse_args()
    run(args.cchp_zip, args.kids_nz_tar, args.output)


if __name__ == "__main__":
    main()
