"""Cached-statistics formatter for the source-bound manuscript candidate.

Cached-statistics formatter. Run only in an authorized, acknowledged
publication execution after the controller selects an exact qualified upstream
bounded_moment_frontier directory. Hash matching and local checks do not establish
qualification: the caller must bind the actual independent decision externally.
No matrix operations, source reintegration, fitting, plotting or NPZ loading.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

BRANCHES = tuple(f"{c}_BT_{t}" for c in ("A", "B")
                 for t in ("1e-07", "1e-08", "1e-06"))
FREQUENCIES = ["030", "044", "070", "100", "143", "217", "353PSB"]
MOMENTS = ["s", "s_beta", "d", "d_beta", "d_t", "s_betabeta",
           "d_betabeta", "d_beta_t", "d_tt"]
COORDINATES = []
for field, ell in (("E", 2), ("E", 3), ("B", 2), ("B", 3)):
    COORDINATES.append(f"{field}{ell}:m0")
    for m in range(1, ell + 1):
        COORDINATES.extend((f"{field}{ell}:sqrt2Re_m{m}",
                            f"{field}{ell}:-sqrt2Im_m{m}"))


def finite_positive(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label}: expected a finite positive stored number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label}: expected a finite positive stored number")
    return value


def read_bound_result(qualified_dir, expected_result_sha256):
    """Read only RESULT.json in the explicitly selected directory."""
    if (len(expected_result_sha256) != 64 or
            any(c not in "0123456789abcdef" for c in expected_result_sha256)):
        raise ValueError("expected RESULT SHA-256 must be explicit lowercase hex")
    source = Path(qualified_dir) / "RESULT.json"
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_result_sha256:
        raise ValueError("selected RESULT byte identity mismatch")
    return json.loads(raw)


def validate_selection(data, expected_r31_sha256):
    """Validate the stored six-branch model, without adjudicating qualification."""
    if data.get("task_id") != "R32-04-BANDPASS-BOUNDS":
        raise ValueError("unexpected upstream task")
    if data.get("checks_status") != "PASS":
        raise ValueError("stored upstream checks did not pass")
    if data.get("source_sha256") != expected_r31_sha256:
        raise ValueError("unexpected retained R31 source identity")
    if data.get("frequencies") != FREQUENCIES:
        raise ValueError("frequency order mismatch")
    if data.get("moment_order") != MOMENTS:
        raise ValueError("moment order mismatch")
    if data.get("full24_coordinate_order") != COORDINATES:
        raise ValueError("signed full24 coordinate order mismatch")
    scales = data.get("common_reference_column_scales", [])
    if len(scales) != 9:
        raise ValueError("expected nine common metric scales")
    for i, scale in enumerate(scales):
        finite_positive(scale, f"common scale {i}")
    if set(data.get("branches", {})) != set(BRANCHES):
        raise ValueError("expected exactly the six retained response branches")
    rows = []
    for name in BRANCHES:
        branch = data["branches"][name]
        if (branch.get("finite_rank_F2") != 7 or
                branch.get("free_target_quotient_rank") != 0):
            raise ValueError(f"{name}: unexpected finite rank scope")
        row = {"branch": name}
        for metric in ("common_reference", "raw_identity"):
            stored = branch[metric]
            row[metric] = {
                key: finite_positive(stored[key], f"{name}/{metric}/{key}")
                for key in ("minimum_budget_ell",
                            "one_compensator_radius_per_unit_rho",
                            "pairwise_max_separation_per_unit_rho")}
        rows.append(row)
    return rows


def render_table(rows):
    """Format stored values only; no reconstructed slopes or inferred bounds."""
    out = [r"\begin{tabular}{lrrrr}", r"\toprule",
           r"Branch & $\ell_M$ & $1/\ell_M$ & $2/\ell_M$ & $\ell_I$ \\",
           r"\midrule"]
    for row in rows:
        c = row["common_reference"]
        i = row["raw_identity"]
        name = row["branch"].replace("_", r"\_")
        out.append(f"{name} & {c['minimum_budget_ell']:.6f} & "
                   f"{c['one_compensator_radius_per_unit_rho']:.6f} & "
                   f"{c['pairwise_max_separation_per_unit_rho']:.6f} & "
                   f"{i['minimum_budget_ell']:.6f}" + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualified-dir", type=Path, required=True)
    parser.add_argument("--expected-result-sha256", required=True)
    parser.add_argument("--expected-r31-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    data = read_bound_result(args.qualified_dir, args.expected_result_sha256)
    rows = validate_selection(data, args.expected_r31_sha256)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "budgets.tex").write_text(render_table(rows))
    # This records formatter input selection, never upstream scientific admission.
    provenance = {
        "status": "CACHED_VALUES_FORMATTED",
        "qualification": "EXTERNAL_DECISION_REQUIRED_NOT_ADJUDICATED_HERE",
        "selected_directory": str(args.qualified_dir.resolve()),
        "result_sha256": args.expected_result_sha256,
        "retained_r31_sha256": args.expected_r31_sha256,
        "numerical_recomputation": False,
        "rows": rows,
    }
    (args.output_dir / "selection.json").write_text(
        json.dumps(provenance, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
