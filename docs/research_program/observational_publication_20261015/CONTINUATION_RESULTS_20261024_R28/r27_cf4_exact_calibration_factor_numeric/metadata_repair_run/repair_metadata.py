"""Copy-on-write exact zero-leverage metadata repair; no estimator replay."""

import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np


HERE = Path(__file__).resolve().parent
EXPECTED_ROWS = 35970
DENOMINATOR_EXPONENT = 1074  # Every finite binary64 is an integer / 2**1074.


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def scaled_dyadic_integer(value):
    x = float(value)
    if not np.isfinite(x):
        raise ValueError("NONFINITE_L_COEFFICIENT")
    numerator, denominator = x.as_integer_ratio()
    exponent = denominator.bit_length() - 1
    if denominator != 1 << exponent or exponent > DENOMINATOR_EXPONENT:
        raise ValueError("NON_DYADIC_BINARY64")
    return numerator << (DENOMINATOR_EXPONENT - exponent)


def exact_zero_mask(data):
    ids = data["group_id"]
    singleton = data["active_singleton_mask"]
    mixed = data["mixed_zero_leverage_mask"]
    inherited = data["extra_zero_leverage_mask"]
    refs = data["reference_row_by_channel"]
    nonrefs = data["nonreference_row_index"]
    channels = data["nonreference_channel"]
    refrows = data["difference_reference_row_index"]
    l = data["L_binary64"]
    support = data["selected_support_7"]
    if ids.shape != (EXPECTED_ROWS,) or ids.dtype != np.int64:
        raise ValueError("SOURCE_ID_SHAPE_OR_DTYPE_CHANGED")
    if singleton.shape != mixed.shape or singleton.shape != inherited.shape or singleton.shape != (EXPECTED_ROWS,):
        raise ValueError("SOURCE_MASK_SHAPE_CHANGED")
    if any(x.dtype != np.bool_ for x in (singleton, mixed, inherited)):
        raise ValueError("SOURCE_MASK_DTYPE_CHANGED")
    if refs.shape != (7,) or nonrefs.ndim != 1 or channels.shape != nonrefs.shape or refrows.shape != nonrefs.shape:
        raise ValueError("SOURCE_SPARSE_FACTOR_SHAPE_CHANGED")
    if l.shape != (5, len(nonrefs)) or l.dtype != np.float64 or not np.isfinite(l).all():
        raise ValueError("SOURCE_L_SHAPE_OR_FINITE_CHANGED")
    if support.shape != (EXPECTED_ROWS, 7) or support.dtype != np.bool_:
        raise ValueError("SOURCE_SUPPORT_INVALID")
    if not np.all((refs >= -1) & (refs < EXPECTED_ROWS)):
        raise ValueError("SOURCE_REFERENCE_ROW_INVALID")
    if not np.all((nonrefs >= 0) & (nonrefs < EXPECTED_ROWS)) or len(np.unique(nonrefs)) != len(nonrefs):
        raise ValueError("SOURCE_NONREFERENCE_ROWS_INVALID")
    if not np.all((channels >= 0) & (channels < 7)) or not np.array_equal(refrows, refs[channels]):
        raise ValueError("SOURCE_DIFFERENCE_INDEX_INVALID")
    valid_refs = refs[refs >= 0]
    if len(np.unique(valid_refs)) != len(valid_refs):
        raise ValueError("DUPLICATE_REFERENCE_ROWS")
    if not np.all(singleton[valid_refs]) or not np.all(singleton[nonrefs]) or np.any(mixed[valid_refs]) or np.any(mixed[nonrefs]):
        raise ValueError("SOURCE_FACTOR_SUPPORT_INVALID")
    if not np.array_equal(singleton, support.sum(axis=1) == 1) or not np.array_equal(mixed, support.sum(axis=1) > 1):
        raise ValueError("SOURCE_SUPPORT_MASK_MISMATCH")
    if not np.all(support[nonrefs, channels]) or not np.all(support[valid_refs, np.flatnonzero(refs >= 0)]):
        raise ValueError("SOURCE_FACTOR_CHANNEL_SUPPORT_MISMATCH")
    if not np.all(refs[channels] >= 0):
        raise ValueError("NONREFERENCE_EMPTY_CHANNEL")
    covered = np.zeros(EXPECTED_ROWS, dtype=np.bool_)
    covered[valid_refs] = True
    covered[nonrefs] = True
    if not np.array_equal(covered | mixed, np.ones(EXPECTED_ROWS, dtype=np.bool_)) or np.any(covered & mixed):
        raise ValueError("SOURCE_FULL_PARTITION_INVALID")
    if not np.array_equal(covered, singleton) or int(mixed.sum()) != 944:
        raise ValueError("SOURCE_SINGLETON_PARTITION_INVALID")

    # The nonreference coefficients are their stored binary64 bits, interpreted
    # exactly. Reference coefficients are negative exact within-channel sums.
    current_zero = mixed.copy()
    current_zero[nonrefs] = np.all(l == 0, axis=0)
    exact_channel_sum_integer = [[0] * 5 for _ in range(7)]
    for column, channel in enumerate(channels):
        c = int(channel)
        for a in range(5):
            exact_channel_sum_integer[c][a] += scaled_dyadic_integer(l[a, column])
    for c, row in enumerate(refs):
        if row >= 0:
            current_zero[row] = all(value == 0 for value in exact_channel_sum_integer[c])
        elif any(value != 0 for value in exact_channel_sum_integer[c]):
            raise ValueError("EMPTY_CHANNEL_NONZERO_SUM")
    extra_current = current_zero & ~mixed
    if not extra_current[1484] or int(ids[1484]) != 11274:
        raise ValueError("REVIEW_FIRST_FAILURE_WITNESS_NOT_REPAIRED")
    return current_zero, extra_current, inherited


def same_json_bits(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same_json_bits(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same_json_bits(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return struct.pack(">d", a) == struct.pack(">d", b)
    return a == b


def unchanged_array_bytes(original, revised):
    return (original.dtype == revised.dtype and original.shape == revised.shape
            and original.tobytes(order="C") == revised.tobytes(order="C"))


def main():
    inp = json.loads((HERE / "INPUT.json").read_text())
    if inp["state"] != "FROZEN_REPAIR_SCIENCE_INPUT":
        raise RuntimeError("REPAIR_INPUT_NOT_FROZEN")
    for role in ("original_factor", "original_result", "failed_review", "repair_contract"):
        obj = inp[role]
        if sha256(obj["path"]) != obj["sha256"]:
            raise RuntimeError(f"{role.upper()}_SHA_MISMATCH")
    source_factor = Path(inp["original_factor"]["path"])
    source_result = Path(inp["original_result"]["path"])
    output = HERE / "actual_run" / "products"
    output.mkdir(exist_ok=False)
    with np.load(source_factor, allow_pickle=False) as z:
        arrays = {key: z[key] for key in z.files}
    current_zero, extra_current, inherited = exact_zero_mask(arrays)
    arrays["extra_zero_leverage_mask"] = extra_current
    arrays["exact_zero_leverage_mask"] = current_zero
    arrays["legacy_parent_extra_zero_leverage_mask"] = inherited
    factor_path = output / "FACTOR.npz"
    np.savez_compressed(factor_path, **arrays)
    with np.load(source_factor, allow_pickle=False) as old_z, np.load(factor_path, allow_pickle=False) as new_z:
        if set(new_z.files) != set(old_z.files) | {"exact_zero_leverage_mask", "legacy_parent_extra_zero_leverage_mask"}:
            raise ValueError("UNEXPECTED_FACTOR_ARRAY_KEYS")
        for key in old_z.files:
            if key != "extra_zero_leverage_mask" and not unchanged_array_bytes(old_z[key], new_z[key]):
                raise ValueError(f"UNCHANGED_ARRAY_BYTES_DIFFER_{key}")
        if not unchanged_array_bytes(old_z["extra_zero_leverage_mask"], new_z["legacy_parent_extra_zero_leverage_mask"]):
            raise ValueError("LEGACY_PARENT_MASK_BYTES_DIFFER")
        if not np.array_equal(new_z["extra_zero_leverage_mask"], extra_current) or not np.array_equal(new_z["exact_zero_leverage_mask"], current_zero):
            raise ValueError("NEW_FACTOR_MASK_SERIALIZATION_DIFFERS")

    original = json.loads(source_result.read_text())
    result = dict(original)
    result["factor_product_sha256"] = sha256(factor_path)
    result["factor_product_bytes"] = factor_path.stat().st_size
    indices = np.flatnonzero(extra_current)
    added = np.flatnonzero(extra_current & ~inherited)
    removed = np.flatnonzero(inherited & ~extra_current)
    result["metadata_repair"] = {
        "class": "NEW_ZERO_LEVERAGE_MASK_MISMATCH",
        "original_factor_sha256": inp["original_factor"]["sha256"],
        "original_result_sha256": inp["original_result"]["sha256"],
        "first_failed_review_sha256": inp["failed_review"]["sha256"],
        "repair_contract_sha256": inp["repair_contract"]["sha256"],
        "definition": "Current K_fact exact rational coefficients: mixed absent, all-zero stored L nonreferences, exact dyadic zero-sum references",
        "current_total_count": int(current_zero.sum()),
        "current_additional_outside_mixed_count": int(len(indices)),
        "current_additional_row_indices": indices.tolist(),
        "current_additional_group_ids": arrays["group_id"][indices].astype(int).tolist(),
        "legacy_parent_extra_count": int(inherited.sum()),
        "added_vs_legacy_row_indices": added.tolist(),
        "added_vs_legacy_group_ids": arrays["group_id"][added].astype(int).tolist(),
        "removed_vs_legacy_row_indices": removed.tolist(),
        "removed_vs_legacy_group_ids": arrays["group_id"][removed].astype(int).tolist(),
        "sbfm_witness_row_1484_group_11274_zero": bool(extra_current[1484]),
        "exact_integer_dyadic_scale": "2^1074 for reference zero tests only",
        "factor_array_unchanged_bytes_comparison": "PASS_ALL_KEYS_EXCEPT_REPLACED_AND_ADDED_MASKS",
        "unchanged_json_fields_bit_comparison": "PASS_ALL_ORIGINAL_FIELDS_EXCEPT_FACTOR_SHA_AND_BYTES",
        "old_producer_controls_y_contraction_response_replayed": False,
    }
    for key in original:
        if key not in ("factor_product_sha256", "factor_product_bytes") and not same_json_bits(original[key], result[key]):
            raise ValueError(f"UNCHANGED_RESULT_FIELD_DIFFERS_{key}")
    if set(result) != set(original) | {"metadata_repair"}:
        raise ValueError("UNEXPECTED_RESULT_FIELDS")
    result_path = output / "RESULT.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n")
    serialized = json.loads(result_path.read_text())
    for key in original:
        if key not in ("factor_product_sha256", "factor_product_bytes") and not same_json_bits(original[key], serialized[key]):
            raise ValueError(f"UNCHANGED_RESULT_FIELD_DIFFERS_{key}")
    if set(serialized) != set(original) | {"metadata_repair"}:
        raise ValueError("UNEXPECTED_RESULT_FIELDS")
    (output / "REPORT.md").write_text(
        "# Exact factor metadata repair\n\n"
        "This candidate copies the original saved factor and exactly derives the "
        "current zero-leverage masks from its stored L and sparse contrast indices. "
        "The parent K_hat extra mask is retained under a legacy name. The "
        "original exact five-vector, correction price, and B/N numerical response "
        "fields are unchanged. The first failed review and original artifacts "
        "remain intact. Scientific claim scope and review status are unchanged; "
        "this candidate awaits fresh independent actual-result review.\n"
    )
    print(json.dumps({"status": "REPAIRED_METADATA_CANDIDATE_PENDING_INDEPENDENT_REVIEW",
                      "current_extra_zero_count": int(len(indices)),
                      "factor_sha256": sha256(factor_path),
                      "result_sha256": sha256(result_path)}), flush=True)


if __name__ == "__main__":
    sys.exit(main())
