"""Sparse exact dyadic within-channel contrast factor for the frozen CF4 carrier.

This module defines K_fact = L D_diff; it never materializes rounded reference
coefficients. All exact-value arithmetic operates on binary64-as-rationals.
"""

from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np


EXPECTED_CHANNELS = ("SNIa", "FP", "TFR", "SBFm", "SBFir", "SNII", "DirectCal")
EXPECTED_COUNT = 35970
EXPECTED_IDS_SHA = "f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def exact(value):
    """The exact rational represented by a finite numpy/Python binary64."""
    x = float(value)
    if not np.isfinite(x):
        raise ValueError("NONFINITE_BINARY64")
    return Fraction(*x.as_integer_ratio())


def ratio(value):
    return [str(value.numerator), str(value.denominator)]


def ratios(values):
    return [ratio(x) for x in values]


def validate_carrier(z, require_actual=True):
    ids = z["group_id"]
    support = z["selected_support_7"]
    singleton = z["active_singleton_mask"]
    mixed = z["mixed_zero_leverage_mask"]
    extra = z["extra_zero_leverage_mask"]
    names = tuple(str(s) for s in z["channel_names"])
    k, y, d, b, n = (z[name] for name in ("K", "y", "d", "B", "N"))
    basis = z["STF_basis_5x3x3"]
    size = len(ids)
    if require_actual and size != EXPECTED_COUNT:
        raise ValueError("ACTUAL_ROW_COUNT_MISMATCH")
    if ids.dtype != np.int64 or ids.shape != (size,) or len(np.unique(ids)) != size:
        raise ValueError("INVALID_GROUP_IDS")
    if require_actual and hashlib.sha256(ids.astype("<i8", copy=False).tobytes()).hexdigest() != EXPECTED_IDS_SHA:
        raise ValueError("ACTUAL_ID_ORDER_MISMATCH")
    if names != EXPECTED_CHANNELS or support.shape != (size, 7) or support.dtype != np.bool_:
        raise ValueError("INVALID_SEVEN_CHANNEL_SUPPORT")
    if any(a.shape != (size,) or a.dtype != np.bool_ for a in (singleton, mixed, extra)):
        raise ValueError("INVALID_ROW_MASK")
    counts = support.sum(axis=1)
    if not np.array_equal(singleton, counts == 1) or not np.array_equal(mixed, counts > 1):
        raise ValueError("MASK_SUPPORT_INCONSISTENCY")
    if np.any(counts == 0) or np.any(singleton & mixed) or np.any(extra):
        raise ValueError("UNEXPECTED_SUPPORT_OR_ADDITIONAL_ZERO_ROWS")
    if k.shape != (5, size) or y.shape != (size,) or d.shape != (size,) or b.shape != (size, 5) or n.shape != (size, 14) or basis.shape != (5, 3, 3):
        raise ValueError("INVALID_CARRIER_SHAPES")
    if any(a.dtype != np.float64 or not np.isfinite(a).all() for a in (k, y, d, b, n, basis)):
        raise ValueError("INVALID_CARRIER_BINARY64")
    if not np.all(d > 0) or not np.all(k[:, mixed] == 0):
        raise ValueError("INVALID_WEIGHT_OR_MIXED_ZERO")
    if z["C"].shape != (size, 7) or not np.array_equal(z["C"][singleton], support[singleton].astype(np.float64)):
        raise ValueError("SINGLETON_CALIBRATION_RESPONSE_MISMATCH")
    if require_actual and (int(singleton.sum()), int(mixed.sum())) != (35026, 944):
        raise ValueError("ACTUAL_MASK_COUNTS_MISMATCH")
    return ids, support, singleton, mixed, k, y, d, b, n, basis


def factor_indices(ids, support, singleton, d):
    refs = np.full(support.shape[1], -1, dtype=np.int64)
    channel_of_row = np.full(len(ids), -1, dtype=np.int8)
    for c in range(support.shape[1]):
        rows = np.flatnonzero(singleton & support[:, c])
        if len(rows):
            refs[c] = int(min(rows, key=lambda i: (float(d[i]), int(ids[i]))))
            channel_of_row[rows] = c
    nonrefs = np.flatnonzero(singleton & ~np.isin(np.arange(len(ids)), refs[refs >= 0])).astype(np.int64)
    if np.any(channel_of_row[singleton] < 0):
        raise ValueError("SINGLETON_CHANNEL_MAPPING_FAILED")
    return refs, nonrefs, channel_of_row


def exact_evaluation(k, y, d, refs, nonrefs, channel_of_row):
    """Author path: old exact contraction and channel sums, then correction."""
    sums = [[Fraction(0) for _ in range(5)] for _ in range(7)]
    old = [Fraction(0) for _ in range(5)]
    for i in range(k.shape[1]):
        c = int(channel_of_row[i])
        yi = exact(y[i])
        for a in range(5):
            ka = exact(k[a, i])
            old[a] += ka * yi
            if c >= 0:
                sums[c][a] += ka
    correction = [Fraction(0) for _ in range(5)]
    price = Fraction(0)
    for c, r in enumerate(refs):
        if r < 0:
            continue
        yr, dr = exact(y[r]), exact(d[r])
        correction = [correction[a] - sums[c][a] * yr for a in range(5)]
        price += dr * sum((s * s for s in sums[c]), Fraction(0))
    fact = [old[a] + correction[a] for a in range(5)]
    return old, sums, correction, fact, price


def direct_exact_contrasts(l, y, refs, nonrefs, channel_of_row):
    result = [Fraction(0) for _ in range(5)]
    for column, i in enumerate(nonrefs):
        r = refs[int(channel_of_row[i])]
        contrast = exact(y[i]) - exact(y[r])
        for a in range(5):
            result[a] += exact(l[a, column]) * contrast
    return result


def numerical_response(l, nonrefs, refs, channel_of_row, b, n):
    channels = channel_of_row[nonrefs]
    ref_rows = refs[channels]
    kb = l @ (b[nonrefs] - b[ref_rows])
    kn = l @ (n[nonrefs] - n[ref_rows])
    s = np.linalg.svd(kb, compute_uv=False)
    sn = np.linalg.svd(kn, compute_uv=False)
    scale = float(s[0]) if len(s) else 0.0
    ranks = {f"{tol:.0e}": int(np.count_nonzero(s > tol * scale)) for tol in (1e-12, 1e-10, 1e-8)}
    scale_n = float(sn[0]) if len(sn) else 0.0
    ranks_n = {f"{tol:.0e}": int(np.count_nonzero(sn > tol * scale_n)) for tol in (1e-12, 1e-10, 1e-8)}
    return {
        "KB": kb.tolist(), "KN": kn.tolist(),
        "KB_minus_I_fro": float(np.linalg.norm(kb - np.eye(5))),
        "KN_fro": float(np.linalg.norm(kn)),
        "KB_singular_values": s.tolist(), "KB_rank_relative_tolerance": ranks,
        "KN_singular_values": sn.tolist(), "KN_rank_relative_tolerance": ranks_n,
        "scope": "floating numerical diagnostics only; KN=0 and KB=I are not exact claims",
    }


def produce(carrier_path, result_path, output_dir):
    result = json.loads(Path(result_path).read_text())
    if result.get("status") != "FULL5_APPARENT_STF_ESTIMATOR":
        raise ValueError("NO_NONTRIVIAL_USABLE_SOURCE_FUNCTIONAL")
    with np.load(carrier_path, allow_pickle=False) as z:
        ids, support, singleton, mixed, k, y, d, b, n, basis = validate_carrier(z)
        refs, nonrefs, channels = factor_indices(ids, support, singleton, d)
        l = k[:, nonrefs].copy()
        old, sums, correction, fact, price = exact_evaluation(k, y, d, refs, nonrefs, channels)
        if fact != direct_exact_contrasts(l, y, refs, nonrefs, channels):
            raise ValueError("ACTUAL_DIRECT_CORRECTION_PARITY_FAILURE")
        if not np.array_equal(l.view(np.uint64), k[:, nonrefs].view(np.uint64)):
            raise ValueError("NONREFERENCE_BITS_CHANGED")
        response = numerical_response(l, nonrefs, refs, channels, b, n)
        display = np.array([float(v) for v in fact], dtype=np.float64)
        if not np.isfinite(display).all():
            raise ValueError("NONFINITE_DISPLAY")
        display_error = [exact(display[a]) - fact[a] for a in range(5)]
        tensor = np.einsum("a,aij->ij", display, basis)
        parent_b = z["b_min"]
        parent_difference = [exact(parent_b[a]) - old[a] for a in range(5)]
        product = Path(output_dir) / "FACTOR.npz"
        np.savez_compressed(
            product, group_id=ids, selected_support_7=support,
            active_singleton_mask=singleton, mixed_zero_leverage_mask=mixed,
            extra_zero_leverage_mask=z["extra_zero_leverage_mask"],
            channel_names=z["channel_names"], reference_row_by_channel=refs,
            nonreference_row_index=nonrefs, nonreference_channel=channels[nonrefs],
            difference_reference_row_index=refs[channels[nonrefs]],
            L_binary64=l, y_binary64=y, d_binary64=d,
            STF_basis_5x3x3=basis,
        )
    payload = {
        "schema": "htt.cf4_exact_factored_calibration_observable/1",
        "status": "EXACT_FINITE_INPUT_FACTOR_AND_VALUE_PENDING_INDEPENDENT_REVIEW",
        "source": {"carrier_path": str(carrier_path), "carrier_sha256": sha256(carrier_path),
                   "result_path": str(result_path), "result_sha256": sha256(result_path)},
        "factor_product_sha256": sha256(product),
        "factor_product_bytes": product.stat().st_size,
        "factor": "K_fact=L D_diff; D_diff columns e_i-e_reference(channel(i)); reference coefficient is unevaluated negative exact channel sum; mixed columns zero",
        "index_base": 0,
        "reference_row_by_channel": refs.tolist(),
        "reference_group_id_by_channel": [None if r < 0 else int(ids[r]) for r in refs],
        "channel_row_counts": [int(np.count_nonzero(singleton & support[:, c])) for c in range(7)],
        "nonreference_count": int(len(nonrefs)),
        "exact_old_Khat_y": ratios(old),
        "exact_channel_sums_7x5": [ratios(v) for v in sums],
        "exact_change_b_fact_minus_old": ratios(correction),
        "exact_b_fact": ratios(fact),
        "actual_direct_correction_exact_parity": True,
        "exact_delta_D_sq": ratio(price),
        "display_b_fact": display.tolist(),
        "exact_display_minus_b_fact": ratios(display_error),
        "parent_b_min_binary64": parent_b.tolist(),
        "exact_parent_b_min_minus_old": ratios(parent_difference),
        "complete_3x3_tensor_display_in_saved_basis": tensor.tolist(),
        "response_numerical": response,
        "claim_ceiling": "exact on serialized binary64 input and fixed seven-channel support-simplex additive calibration family only; physical response, residual covariance, unrestricted nuisance, selection/PV/null and H02/H03 remain UNKNOWN/HOLD",
    }
    result_out = Path(output_dir) / "RESULT.json"
    result_out.write_text(json.dumps(payload, indent=2) + "\n")
    (Path(output_dir) / "REPORT.md").write_text(
        "# Exact factored calibration observable\n\n"
        "The stored binary64 L and sparse integer differences define an exact rational "
        "five-component functional on the retained 35,970 rows. For each singleton "
        "channel, the reference is the minimum (d, group ID); mixed leverage is zero. "
        "The saved-input five-vector, exact correction, channel sums and D-weighted "
        "squared change are in RESULT.json. The displayed tensor uses the retained "
        "floating STF basis. KB/KN are numerical diagnostics. Exact protection is "
        "limited to the fixed released-support additive calibration family; unrestricted "
        "nuisance, physical/source effects and covariance remain unresolved.\n"
    )
    return payload
