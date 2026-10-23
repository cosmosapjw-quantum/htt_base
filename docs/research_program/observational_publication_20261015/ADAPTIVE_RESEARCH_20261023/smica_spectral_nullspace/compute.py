"""Source-bound linear information audit of the PR3 SMICA polarization weights.

The seven coordinates are already unit-converted frequency-map E/B harmonics.
This module never executes the archive's Python 2 producer or reads sky maps.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import tarfile

import numpy as np


ARCHIVE = Path("/mnt/extdrive/workdir/htt_open_data/planck/PR3/weights/COM_Code_SMICA-weights-propagation_R3.00.tar.gz")
ARCHIVE_SHA = "044ec9bed746ae745ad35a8b6ccf6e603f546083fec328e9c64d866ac9221f93"
WEIGHTS_SHA = "541378f6c9ab37574aae909519b0f1fe020714a6cea2b8dd1c7fcedb5ffd87df"
PRODUCER_SHA = "dd1f9c2435cae456b4cc0445b7257b360d01a73754455d11ea409252d3788160"
README_SHA = "de52811701de2ef4c1c37aff05f317e264fd9cd3ad867cab6289dd3a8e4aaf27"
CHANNELS = (30, 44, 70, 100, 143, 217, 353)
BLOCKS = (("E", 2), ("E", 3), ("B", 2), ("B", 3))
MEMBER_HASHES = {"weights_EB_smica_R3.00.txt": WEIGHTS_SHA,
                 "smica_coadd.py": PRODUCER_SHA, "README": README_SHA}


def sha256(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read_release() -> tuple[list[list[list[str]]], dict]:
    if ARCHIVE.stat().st_size != 74625775 or sha256(ARCHIVE) != ARCHIVE_SHA:
        raise ValueError("immutable PR3 archive size/SHA mismatch")
    contents = {}
    with tarfile.open(ARCHIVE, "r:gz") as tf:
        for member in tf:
            name = member.name.rsplit("/", 1)[-1]
            if name in MEMBER_HASHES:
                if not member.isfile() or name in contents:
                    raise ValueError("unexpected or duplicate source member")
                contents[name] = tf.extractfile(member).read()
    if set(contents) != set(MEMBER_HASHES):
        raise ValueError("missing source member")
    for name, expected in MEMBER_HASHES.items():
        if hashlib.sha256(contents[name]).hexdigest() != expected:
            raise ValueError(f"source member SHA mismatch: {name}")
    producer = contents["smica_coadd.py"].decode("utf-8")
    required = ('reshape(2,7,4001)', 'names[:-2]', 'W_pol[iz,m,:]',
                'hp.almxfl(combalm, hp.pixwin(nside)[0:lmax])')
    if not all(term in producer for term in required):
        raise ValueError("producer interpretation changed")
    rows = [line.split() for line in contents["weights_EB_smica_R3.00.txt"].decode("ascii").splitlines()]
    if len(rows) != 14 or any(len(row) != 4001 for row in rows):
        raise ValueError("unexpected 2x7x4001 source shape")
    weights = [[rows[p * 7 + j] for j in range(7)] for p in range(2)]
    return weights, {"archive_sha256": ARCHIVE_SHA, "member_sha256": MEMBER_HASHES,
                     "shape": [2, 7, 4001], "producer_checks": list(required)}


def targets() -> list[tuple[str, np.ndarray]]:
    out = []
    for j, channel in enumerate(CHANNELS):
        a = np.zeros(7); a[j] = 1
        out.append((f"unit_{channel}", a))
    for j, k in combinations(range(7), 2):
        a = np.zeros(7); a[j] = 1; a[k] = -1
        out.append((f"contrast_{CHANNELS[j]}_{CHANNELS[k]}", a))
    assert len(out) == 28
    return out


def projection(w: np.ndarray, a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d = float(w @ w)
    if d == 0:
        return np.zeros_like(a), a.copy()
    parallel = (float(a @ w) / d) * w
    return parallel, a - parallel


def exact_witness(decimal_weights: list[str], j: int = 0, k: int = 1) -> dict:
    w = [Fraction(s) for s in decimal_weights]
    a = [Fraction(int(i == j) - int(i == k)) for i in range(7)]
    d = sum(v * v for v in w)
    if d == 0:
        raise ValueError("contracted source row is zero")
    c = sum(x * y for x, y in zip(a, w)) / d
    h = [x - c * y for x, y in zip(a, w)]
    wh = sum(x * y for x, y in zip(w, h))
    ah = sum(x * y for x, y in zip(a, h))
    hh = sum(x * x for x in h)
    assert wh == 0 and ah == hh and hh > 0
    with localcontext() as ctx:
        ctx.prec = 80
        dec = lambda q: Decimal(q.numerator) / Decimal(q.denominator)
        wd, hd, ad = [dec(q) for q in w], [dec(q) for q in h], [dec(q) for q in a]
        decimal_wh = sum((x * y for x, y in zip(wd, hd)), Decimal(0))
        decimal_ah_hh = sum((x * y for x, y in zip(ad, hd)), Decimal(0)) - sum((x * x for x in hd), Decimal(0))
    return {"target": f"contrast_{CHANNELS[j]}_{CHANNELS[k]}",
            "source_decimal_weights": decimal_weights, "s0": ["0"] * 7,
            "s1_h_exact": [str(q) for q in h], "projection_coefficient_exact": str(c),
            "w_dot_h_exact": str(wh), "a_dot_h_exact": str(ah),
            "h_dot_h_exact": str(hh), "a_dot_h_minus_h_dot_h_exact": str(ah - hh),
            "decimal_precision": 80, "decimal_w_dot_h_residual": str(decimal_wh),
            "decimal_a_dot_h_minus_h_dot_h_residual": str(decimal_ah_hh)}


def tensor_operator(rows: dict[str, np.ndarray]) -> tuple[np.ndarray, list[dict]]:
    """Real harmonic coordinate layout: block, frequency, m=-ell..ell."""
    mat = np.zeros((24, 168))
    blocks = []
    input_base = output_base = 0
    for pol, ell in BLOCKS:
        n = 2 * ell + 1
        key = f"{pol}{ell}"
        w = rows[key]
        for freq in range(7):
            for t in range(n):
                mat[output_base + t, input_base + freq * n + t] = w[freq]
        pivot = int(np.argmax(np.abs(w)))
        blocks.append({"key": key, "input_start": input_base, "output_start": output_base,
                       "harmonic_coordinates": [f"m={m}" for m in range(-ell, ell + 1)],
                       "operator": f"kron(w_{key}^T,I_{n})", "input_shape": [7, n],
                       "output_shape": [n], "pivot_frequency_index": pivot,
                       "kernel_basis_rule": f"for each m and j != {pivot}: e_(j,m) - (w_j/w_{pivot}) e_({pivot},m)"})
        input_base += 7 * n; output_base += n
    assert input_base == 168 and output_base == 24
    return mat, blocks


def compute() -> dict:
    source, source_meta = read_release()
    rows = {f"{pol}{ell}": np.asarray([float(source[p][j][ell]) for j in range(7)])
            for p, pol in enumerate(("E", "B")) for ell in (2, 3)}
    analyses = {}
    for p, pol in enumerate(("E", "B")):
        for ell in (2, 3):
            key = f"{pol}{ell}"; w = rows[key]; d = float(w @ w)
            if d == 0:
                raise ValueError(f"source row {key} is zero; rank-zero branch required")
            P = np.eye(7) - np.outer(w, w) / d
            details = []
            for name, a in targets():
                parallel, h = projection(w, a)
                fit = np.linalg.lstsq(w[:, None], a, rcond=None)[0]
                ls_residual = float(np.linalg.norm(a - w * fit[0]))
                norm = float(np.linalg.norm(a))
                details.append({"target": name, "target_vector": a.tolist(),
                    "projection_coefficient": float((a @ w) / d),
                    "retained_projection_norm": float(np.linalg.norm(parallel)),
                    "lost_norm": float(np.linalg.norm(h)),
                    "retained_fraction": float(np.linalg.norm(parallel) / norm),
                    "lost_fraction": float(np.linalg.norm(h) / norm),
                    "retained_squared_fraction": float((parallel @ parallel) / (norm * norm)),
                    "lost_squared_fraction": float((h @ h) / (norm * norm)),
                    "witness_s0": [0.0] * 7, "witness_s1": h.tolist(),
                    "witness_compressed_difference": float(w @ h),
                    "witness_target_difference": float(a @ h),
                    "least_squares_residual": ls_residual})
            analyses[key] = {"weights": w.tolist(), "source_decimal_weights": [source[p][j][ell] for j in range(7)],
                "weight_sum": float(w.sum()), "weight_norm": float(np.sqrt(d)),
                "row_rank": int(np.linalg.matrix_rank(w[None, :])), "kernel_dimension": 6,
                "target_count": len(details), "targets": details,
                "exact_witness": exact_witness([source[p][j][ell] for j in range(7)]),
                "controls": {"projector_symmetry_max_abs": float(np.max(np.abs(P-P.T))),
                    "projector_idempotence_max_abs": float(np.max(np.abs(P@P-P))),
                    "projector_annihilation_norm": float(np.linalg.norm(P@w)),
                    "projector_trace": float(np.trace(P)),
                    "projection_vs_lstsq_max_abs": max(abs(t["lost_norm"]-t["least_squares_residual"]) for t in details)}}
    M, blocks = tensor_operator(rows)
    rank = int(np.linalg.matrix_rank(M))
    sparse = [{"output": int(i), "input": int(j), "weight": float(M[i,j])}
              for i,j in zip(*np.nonzero(M))]
    assert len(sparse) == 168
    return {"source": source_meta, "channels_GHz": list(CHANNELS),
        "coordinate_metric": "Euclidean on seven processed frequency coordinates; computational, not physical amplitude",
        "input_coordinate_order": "(E2,E3,B2,B3); within block frequency order 30..353 GHz; within frequency m=-ell..ell",
        "output_coordinate_order": "(E2,E3,B2,B3); within block m=-ell..ell",
        "tensor": {"input_dimension": 168, "output_dimension": 24, "rank": rank,
                   "nullity": 168-rank, "blocks": blocks, "nonzero_entries": sparse},
        "operators": analyses}


def figure(result: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels = list(result["operators"])
    contrasts = [t for t in result["operators"][labels[0]]["targets"] if t["target"].startswith("contrast_")]
    names = [t["target"].replace("contrast_", "") for t in contrasts]
    values = np.asarray([[t["lost_fraction"] for t in result["operators"][key]["targets"][7:]] for key in labels])
    fig, ax = plt.subplots(figsize=(13, 3.8))
    im = ax.imshow(values, vmin=0, vmax=1, aspect="auto", cmap="viridis")
    ax.set_yticks(range(4), labels)
    ax.set_xticks(range(21), names, rotation=60, ha="right", fontsize=7)
    ax.set_title("Lost Euclidean fraction of PR3 frequency contrasts (computational)")
    fig.colorbar(im, ax=ax, label="||Pker a|| / ||a||")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    result = compute()
    (here / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    figure(result, here / "figure.png")
    print(json.dumps({"rank": result["tensor"]["rank"], "nullity": result["tensor"]["nullity"],
                      "target_counts": {key: val["target_count"] for key,val in result["operators"].items()}}))
