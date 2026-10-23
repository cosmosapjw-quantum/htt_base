"""R23: selected-cohort distance-factor contract; no fitted physical law supplied.

The released modulus error is recorded, not automatically promoted to a
source-qualified independent or total joint covariance.  A caller must provide
one positive-definite *total* covariance for the released moduli.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import csv
import hashlib
import json
import math
import re

import numpy as np
from scipy.linalg import solve_triangular


ROOT = Path("/mnt/extdrive/workdir/htt_open_data/cf4")
LEDGER = ROOT / "D02_HI_CF4_20261018/TARGET_JOIN_AND_OOF.csv"
UP = ROOT / "upstream_20261018"
SOURCE_SHA256 = {
    LEDGER: "c32885cd2f081ec1bcedfcb98ef18c8c53245c12ac4a5fabb64d68b27a75f48d",
    UP / "ReadMe": "45fa3cca5346aff29bcf9785e7b08e8ab34b1d67e80b359c0d28bdbd18e42581",
    UP / "table1.dat": "ac679ab4548484b02dc17a1cc09bbe8f0a68f45bd5c44efc7302fcabc32d8926",
    UP / "table4.dat": "f4aa0ba0efe7d7a14f044a76ef37f5a033e2788923d586c2d15ed248939455f2",
}
OUTCOMES = ("accepted", "other_quality", "confused", "nondetection")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for part in iter(lambda: handle.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def _schema(readme: str, filename: str) -> dict[str, slice]:
    block = readme.split("Byte-by-byte Description of file: " + filename + "\n", 1)[1]
    block = block.split("Byte-by-byte Description of file:", 1)[0].split("Note (", 1)[0]
    fields = {}
    for line in block.splitlines():
        match = re.match(r"^\s*(\d+)(?:-\s*(\d+))?\s+[AIF]\d+(?:\.\d+)?\s+\S+\s+(\S+)\s+", line)
        if match:
            start, end, name = match.groups()
            fields[name] = slice(int(start) - 1, int(end or start))
    return fields


def _table(path: Path, fields: dict[str, slice]) -> dict[int, str]:
    result = {}
    for line in path.read_text().splitlines():
        pgc = int(line[fields["PGC"]])
        if pgc in result:
            raise ValueError("duplicate PGC in " + path.name)
        result[pgc] = line
    return result


def extract_selected_rows() -> tuple[list[dict], dict]:
    """Return all 628 target marks and only the 274 released distance fields."""
    for path, expected in SOURCE_SHA256.items():
        if _sha256(path) != expected:
            raise ValueError("immutable source identity changed: " + str(path))
    readme = (UP / "ReadMe").read_text()
    width_fields = _schema(readme, "table1.dat")
    distance_fields = _schema(readme, "table4.dat")
    widths = _table(UP / "table1.dat", width_fields)
    distances = _table(UP / "table4.dat", distance_fields)
    ledger = list(csv.DictReader(LEDGER.open(newline="")))
    if len(ledger) != 628 or len({row["pgc"] for row in ledger}) != 628:
        raise ValueError("selected cohort membership changed")
    rows = []
    marks = Counter()
    for row in ledger:
        pgc = int(row["pgc"])
        outcome = row["outcome"]
        if outcome not in OUTCOMES:
            raise ValueError("unknown outcome")
        line = distances.get(pgc)
        dm = line[distance_fields["DMbest"]].strip() if line else ""
        present = bool(dm and dm not in ("--", "---"))
        marks[(outcome, present)] += 1
        if not present:
            continue
        width_line = widths.get(pgc)
        if width_line is None:
            raise ValueError("released distance without source width")
        field = lambda name: width_line[width_fields[name]].strip()
        dfield = lambda name: line[distance_fields[name]].strip()
        distance_error = float(dfield("e_DMbest"))
        width_error = float(field("e_logWmxi"))
        if not (math.isfinite(distance_error) and distance_error > 0 and
                math.isfinite(width_error) and width_error > 0):
            raise ValueError("released source error invalid")
        rows.append({
            "pgc": pgc, "outcome": outcome,
            "group_label": row["CF4_group"] or "UNASSIGNED",
            "vcmb_km_s": int(dfield("Vcmb")),
            "logWmxi": float(field("logWmxi")),
            "e_logWmxi": width_error,
            "DMbest_mag": float(dm), "e_DMbest_mag": distance_error,
        })
    counts = [[marks[(outcome, False)], marks[(outcome, True)]] for outcome in OUTCOMES]
    if counts != [[116, 269], [21, 1], [26, 3], [191, 1]] or len(rows) != 274:
        raise ValueError("A22 selected mark fixture changed")
    return rows, {"outcomes": OUTCOMES, "columns": ("missing", "present"),
                  "counts": counts, "total": 628, "released": 274, "undefined": 354,
                  "undefined_mass": 354 / 628}


def marked_log_probability(counts: np.ndarray, probabilities: np.ndarray) -> float:
    """Categorical mass for all selected outcome/availability marks."""
    counts = np.asarray(counts)
    probabilities = np.asarray(probabilities, dtype=float)
    if (counts.shape != (4, 2) or probabilities.shape != (4, 2) or
        not np.all(np.isfinite(probabilities)) or np.any(probabilities < 0) or
        np.any(counts < 0) or not np.issubdtype(counts.dtype, np.integer) or
        not np.isclose(probabilities.sum(), 1, rtol=0, atol=1e-12)):
        raise ValueError("normalized 4x2 selected mark law required")
    if np.any((counts > 0) & (probabilities == 0)):
        return -math.inf
    return float(np.sum(counts[counts > 0] * np.log(probabilities[counts > 0])))


def gaussian_distance_logpdf(observed: np.ndarray, mean: np.ndarray,
                             total_covariance: np.ndarray) -> float:
    """One joint F_or distance factor, conditional on the selected marks.

    `total_covariance` must already contain its source-qualified released-error,
    shared-calibration and peculiar-velocity terms exactly once.  This function
    neither supplies those terms nor treats e_DMbest as their decomposition.
    """
    observed = np.asarray(observed, dtype=float)
    mean = np.asarray(mean, dtype=float)
    covariance = np.asarray(total_covariance, dtype=float)
    n = len(observed)
    if (observed.ndim != 1 or mean.shape != (n,) or covariance.shape != (n, n) or
        not np.all(np.isfinite(observed)) or not np.all(np.isfinite(mean)) or
        not np.all(np.isfinite(covariance)) or
        not np.allclose(covariance, covariance.T, rtol=1e-13, atol=0)):
        raise ValueError("finite aligned distance law and symmetric total covariance required")
    chol = np.linalg.cholesky(covariance)
    residual = solve_triangular(chol, observed - mean, lower=True, check_finite=False)
    return float(-0.5 * (n * math.log(2 * math.pi) +
                         2 * np.log(np.diag(chol)).sum() + residual @ residual))


def selected_joint_loglik(mark_counts: np.ndarray, mark_probabilities: np.ndarray,
                          observed: np.ndarray, mean: np.ndarray,
                          total_covariance: np.ndarray) -> float:
    """p(marks, released DM | target=1); missing DM are integrated out."""
    if int(np.asarray(mark_counts)[:, 1].sum()) != len(observed):
        raise ValueError("released mark count and distance vector disagree")
    return marked_log_probability(mark_counts, mark_probabilities) + gaussian_distance_logpdf(
        observed, mean, total_covariance)


def main() -> None:
    here = Path(__file__).resolve().parent
    rows, marks = extract_selected_rows()
    with (here / "RELEASED_ROWS.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {"source_sha256": {str(path): digest for path, digest in SOURCE_SHA256.items()},
               "marks": marks, "group_labels_released": len({r["group_label"] for r in rows}),
               "unassigned_group_released": sum(r["group_label"] == "UNASSIGNED" for r in rows),
               "repeated_group_labels_released": sum(n > 1 for label, n in Counter(
                   r["group_label"] for r in rows if r["group_label"] != "UNASSIGNED").items()),
               "DMbest_range_mag": [min(r["DMbest_mag"] for r in rows),
                                    max(r["DMbest_mag"] for r in rows)],
               "e_DMbest_range_mag": [min(r["e_DMbest_mag"] for r in rows),
                                      max(r["e_DMbest_mag"] for r in rows)],
               "logWmxi_range": [min(r["logWmxi"] for r in rows),
                                  max(r["logWmxi"] for r in rows)],
               "mark_only_working_loglik": marked_log_probability(
                   np.asarray(marks["counts"], dtype=int),
                   np.asarray(marks["counts"], dtype=float) / 628),
               "distance_factor_status": "IMPLEMENTED_REQUIRES_SOURCE_QUALIFIED_MEAN_AND_TOTAL_COVARIANCE",
               "actual_distance_fit": "NOT_EVALUABLE"}
    (here / "EXTRACTION.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"marks": marks, "distance_factor_status": summary["distance_factor_status"]}))


if __name__ == "__main__":
    main()
