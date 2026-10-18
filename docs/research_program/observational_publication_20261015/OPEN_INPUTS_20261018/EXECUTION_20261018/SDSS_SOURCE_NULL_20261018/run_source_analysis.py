"""One-shot SDSS source diagnostic; actual execution requires Astra field approval.

Preparation of this file is not source execution. Use the existing estimator
unchanged. Archive qualification/extraction precedes the shared science clock;
the controls, 64 fits, summaries and plots all run inside its timed subprocess.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import time
import traceback

HERE = Path(__file__).resolve().parent
CONTRACT_SHA256 = "27d1d9109c4ef9e8784bd0a31cf06d30293052802fe8deff78b456c253678831"
ROOT = Path("/mnt/extdrive/workdir/htt_open_data/sdss_source_null_20261018")
LEDGER = HERE / "SCIENTIFIC_BUDGET.jsonl"
PHASE = "ACTUAL_SOURCE_64Y0_ONCE"
TEST_PHASE = "SOURCE_DRIVER_FINITE_FIXTURES"
CAP = 600.
EXTRACT_CAP = 2 * 1024**3
REQUIRED = ("ID", "RA", "Dec", "z_obs", "cen_flag", "logdist_true", "logdist", "logdist_err")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def jsonable(value):
    if hasattr(value, "tolist"):
        return jsonable(value.tolist())
    if isinstance(value, dict):
        return {key: jsonable(val) for key, val in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(val) for val in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Nonfinite computed output; not silently serialized as null")
    return value


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(jsonable(value), stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def validate_approval(approval, selection_path, header_path, identity):
    """Only consume actual source binding, approved format/map and reference.

    Approval JSON: status=APPROVED_FOR_STAGE2, approval_reference, the four
    *_sha256 bindings below, column_count, field_indices (zero based),
    delimiter (whitespace/comma), and header_lines. No PDF order is assumed.
    """
    if (approval.get("status") != "APPROVED_FOR_STAGE2"
            or not str(approval.get("approval_reference", "")).strip()):
        raise ValueError("HOLD: explicit parent/Astra actual-field approval required")
    bindings = {"contract_sha256": CONTRACT_SHA256,
                "selected_members_sha256": sha256(selection_path),
                "actual_header_sha256": sha256(header_path),
                "archive_sha256": identity["sha256"]}
    if any(approval.get(key) != value for key, value in bindings.items()):
        raise ValueError("HOLD: approval source binding mismatch")
    count, skip = approval.get("column_count"), approval.get("header_lines")
    mapping = approval.get("field_indices", {})
    if type(count) is not int or count != 36 or type(skip) is not int or not 0 <= skip <= 8:
        raise ValueError("HOLD: actual 36-field format/header qualification required")
    if (set(mapping) != set(REQUIRED)
            or any(type(i) is not int or not 0 <= i < count for i in mapping.values())
            or len(set(mapping.values())) != len(REQUIRED)):
        raise ValueError("HOLD: complete distinct required-field column mapping required")
    if approval.get("delimiter") not in ("whitespace", "comma"):
        raise ValueError("HOLD: supported actual delimiter approval required")
    return bindings


def validate_inputs(root, selection_path, header_path, approval_path):
    from acquire_sdss import MD5, TOTAL, URL
    from inspect_archive import selected_entries

    if sha256(HERE / "CONTRACT.md") != CONTRACT_SHA256:
        raise ValueError("Frozen contract identity changed")
    identity = load_json(root / "archive_identity.json")
    archive = root / "mocks.tar.gz"
    if (identity.get("status") != "VALIDATED" or identity.get("bytes") != TOTAL
            or identity.get("md5") != MD5 or identity.get("url") != URL
            or identity.get("source_version") != "v1.1.0"
            or archive.is_symlink() or archive.stat().st_size != TOTAL):
        raise ValueError("HOLD: immutable verified source archive required")
    selection, header, approval = (load_json(path) for path in
                                   (selection_path, header_path, approval_path))
    bindings = validate_approval(approval, selection_path, header_path, identity)
    index = load_json(root / "archive_index.json")
    if index.get("archive_sha256") != identity["sha256"]:
        raise ValueError("Archive index binding mismatch")
    boxes, expected = selected_entries(index["entries"])
    if (selection.get("members") != expected or selection.get("boxes") != boxes[:64]
            or selection.get("archive_sha256") != identity["sha256"]
            or selection.get("archive_md5") != MD5
            or selection.get("frozen_before_scientific_outcome_read") is not True
            or selection.get("selected_size_bytes") != sum(e["size"] for e in expected)):
        raise ValueError("HOLD: frozen lowest-64 distinct-box Y0 selection mismatch")
    if (header.get("member") != expected[0]
            or header.get("status") != "HEADER_INSPECTED_AWAITING_ASTRA"
            or header.get("scientific_execution") != "NOT_STARTED"):
        raise ValueError("Actual-header receipt does not bind designated first member")
    if len(header.get("first_eight_lines", [])) != 8:
        raise ValueError("Actual-header sample missing")
    # Immutable source check is archive qualification, outside science timing.
    before = archive.stat()
    md5, sha = hashlib.md5(), hashlib.sha256()
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b""):
            md5.update(block)
            sha.update(block)
    after = archive.stat()
    if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            or md5.hexdigest() != MD5 or sha.hexdigest() != identity["sha256"]):
        raise ValueError("Immutable archive identity mismatch before extraction")
    return selection, header, approval, bindings, after


def extract_selected(root, selection, header, archive_stat):
    """Stream safe regular members only; reuse the qualified first member."""
    from acquire_sdss import safe_member

    selected = {e["name"]: e for e in selection["members"]}
    if len(selected) != 64 or sum(e["size"] for e in selected.values()) > EXTRACT_CAP:
        raise ValueError("Selected extraction exceeds frozen limits")
    first = Path(header["member_path"])
    expected_first = root / "selected" / PurePosixPath(header["member"]["name"]).name
    if (first != expected_first or first.is_symlink() or not first.is_file()
            or first.stat().st_size != header["member"]["size"]
            or sha256(first) != header["member_sha256"]):
        raise ValueError("Qualified first member identity mismatch")
    target = root / "analysis_selected"
    # Preserve first failures/partials. Recovery needs an explicit later decision.
    if target.exists():
        raise ValueError("HOLD: prior extraction retained; explicit recovery required")
    if shutil.disk_usage(root).free < sum(e["size"] for e in selected.values()) + EXTRACT_CAP:
        raise ValueError("Insufficient extraction storage plus 2 GiB reserve")
    target.mkdir()
    paths, seen, basenames = {}, set(), set()
    try:
        with tarfile.open(root / "mocks.tar.gz", "r|gz") as source:
            for member in source:
                p = PurePosixPath(member.name)
                if p.is_absolute() or ".." in p.parts:
                    raise ValueError("Unsafe archive path")
                if member.isdir():
                    continue
                safe_member(member.name, member.isfile(), member.size, limit=10_643_218_721 * 100)
                if member.name not in selected:
                    continue
                expected = selected[member.name]
                safe_member(member.name, member.isfile(), member.size)
                if member.name in seen or p.name in basenames or member.size != expected["size"]:
                    raise ValueError("Duplicate or size-altered selected member")
                seen.add(member.name)
                basenames.add(p.name)
                if member.name == header["member"]["name"]:
                    paths[member.name] = {"path": str(first), "sha256": header["member_sha256"]}
                    continue
                destination = target / p.name
                count, h = 0, hashlib.sha256()
                with source.extractfile(member) as inp, destination.open("xb") as out:
                    for block in iter(lambda: inp.read(8 * 1024**2), b""):
                        count += len(block)
                        if count > expected["size"]:
                            raise ValueError("Selected extraction exceeds declared size")
                        out.write(block)
                        h.update(block)
                if count != expected["size"]:
                    raise ValueError("Short selected archive member")
                paths[member.name] = {"path": str(destination), "sha256": h.hexdigest()}
        if seen != set(selected):
            raise ValueError("Missing selected archive members")
        now = (root / "mocks.tar.gz").stat()
        if (now.st_dev, now.st_ino, now.st_size, now.st_mtime_ns) != (
                archive_stat.st_dev, archive_stat.st_ino, archive_stat.st_size, archive_stat.st_mtime_ns):
            raise ValueError("Archive mutated during extraction")
        write_json(target / "EXTRACTION.json", paths)
        return paths
    except BaseException:
        with (target / "FIRST_FAILURE.txt").open("x") as stream:
            traceback.print_exc(file=stream)
        raise


def read_mock(path, approval):
    """Parse a single mock. Invalid rows are errors, never implicit deletions."""
    import numpy as np

    indices = approval["field_indices"]
    values = {key: [] for key in REQUIRED if key != "ID"}
    rows = 0
    with Path(path).open(encoding="ascii", newline="") as stream:
        for _ in range(approval["header_lines"]):
            if not stream.readline():
                raise ValueError("Short source header")
        for line_number, line in enumerate(stream, start=approval["header_lines"] + 1):
            tokens = line.split() if approval["delimiter"] == "whitespace" else next(csv.reader([line]))
            if len(tokens) != approval["column_count"]:
                raise ValueError(f"Invalid row field count at line {line_number}; no dropping")
            if not tokens[indices["ID"]].strip():
                raise ValueError(f"Empty lexical ID at line {line_number}")
            try:
                row = {key: float(tokens[indices[key]]) for key in values}
            except ValueError as error:
                raise ValueError(f"Invalid required number at line {line_number}") from error
            if (not all(math.isfinite(v) for v in row.values()) or row["logdist_err"] <= 0
                    or row["cen_flag"] not in (0., 1.) or abs(row["Dec"]) > 90):
                raise ValueError(f"Invalid required value at line {line_number}; no dropping")
            rows += 1
            if .01 <= row["z_obs"] <= .1:
                for key in values:
                    values[key].append(row[key])
    if not rows or not values["RA"]:
        raise ValueError("Empty source or empty frozen redshift selection")
    return {key: np.asarray(value, dtype=float) for key, value in values.items()}, rows


def fit_mock(rows, eta=None):
    from sdss_estimator import fit_source_errors
    return fit_source_errors(rows["RA"], rows["Dec"], rows["z_obs"], rows["logdist_true"],
                             rows["logdist"] if eta is None else eta, rows["logdist_err"])


def first_mock_controls(rows, baseline):
    """Original absolute+relative tolerance; no tuning or replacement mock."""
    import numpy as np
    from sdss_estimator import ATOL_MAG, RTOL, directions, independent_full_intercept_lstsq

    def close(actual, expected):
        np.testing.assert_allclose(actual, expected, atol=ATOL_MAG, rtol=RTOL)

    zero = fit_mock(rows, rows["logdist_true"])
    close(zero["coefficients_mag"], np.zeros(16))
    close(zero["weighted_scalar_mean_errors_mag"], np.zeros(2))
    close(zero["profiled_intercepts_mag"], np.zeros(2))
    del zero
    constant = fit_mock(rows, rows["logdist"] + .01)
    close(constant["coefficients_mag"], baseline["coefficients_mag"])
    close(constant["weighted_scalar_mean_errors_mag"] - baseline["weighted_scalar_mean_errors_mag"], [-.05, -.05])
    close(constant["profiled_intercepts_mag"] - baseline["profiled_intercepts_mag"], [-.05, -.05])
    del constant
    nx = directions(rows["RA"], rows["Dec"])[:, 0]
    dipole = fit_mock(rows, rows["logdist"] + .002 * nx)
    expected = np.zeros(16)
    expected[[0, 8]] = -.01
    close(dipole["coefficients_mag"] - baseline["coefficients_mag"], expected)
    del dipole
    for window, kernel in enumerate(baseline["window_kernels"]):
        full = independent_full_intercept_lstsq(baseline["design"], baseline["error_mag"],
                                               baseline["sigma_mag"], kernel)
        close(full[1:], baseline["coefficients_mag"][8 * window:8 * (window + 1)])
        close(full[0], baseline["profiled_intercepts_mag"][window])
    if not np.any(baseline["working_covariance_mag2"][:8, 8:] != 0):
        raise ValueError("Shared soft-window cross covariance unexpectedly zero")
    # Deliberately singular angular response; original kernel must reject it.
    singular = dict(rows, RA=np.zeros_like(rows["RA"]), Dec=np.zeros_like(rows["Dec"]))
    try:
        fit_mock(singular)
    except ValueError as error:
        if "Rank-deficient" not in str(error):
            raise
    else:
        raise AssertionError("Rank deficiency was not rejected")
    return {"status": "PASS_FINITE_CONTROLS_ON_DESIGNATED_FIRST_SOURCE_MOCK",
            "atol_mag": ATOL_MAG, "rtol": RTOL,
            "controls": ["zero", "constant_eta_shift", "nx_eta_shift", "independent_full_intercept_svd",
                         "retained_cross_window_covariance", "rank_deficiency_rejection"]}


def artifact_metadata():
    return {"owner": "obsstat", "scope": "SDSS released source-mock estimator diagnostic only",
            "claim_tier": "C0", "artifact_mode": "NON_CLAIM_BEARING_SOURCE_DIAGNOSTIC",
            "allowed_use": "describe the frozen 64-box Y0 source sample and declared working estimator",
            "transfer_source": "none", "null_status": "SDSS_SOURCE_ONLY_SEPARATE_BOX_INDEPENDENCE_NOT_CERTIFIED",
            "covariance_status": "DIAGONAL_WORKING_PLUS_FINITE_SOURCE_EMPIRICAL",
            "sky_support_status": "SOURCE_ANGULAR_MASK_ALL_GALAXY_TYPES",
            "forbidden_uses": ["physical or H02 calibrated coverage", "CF4 TF+6dF joint-law replacement",
                               "native Bianchi or family identification", "42-task completion"],
            "caveats": ["Released equatorial epoch UNKNOWN", "source-fitted mask/selection/FP-error process retained",
                        "shared windows are correlated", "no bias centering, error inflation or window retuning",
                        "undefined empirical correlations at zero scatter are JSON null"],
            "scientific_admission": "HOLD", "requested_model": "gpt-6.1-sol",
            "requested_effort": "high", "observed_model": "UNKNOWN"}


def science_worker(args):
    """Called only by the budget-owning controller, with no second campaign."""
    if os.environ.get("SDSS_SOURCE_BUDGET_RUN") != args.run_id:
        raise ValueError("Budget-controller launch required")
    import numpy as np
    from sdss_estimator import BASIS, WINDOWS, summarize

    bindings = load_json(args.output / "INPUT_BINDINGS.json")
    extraction = args.root / "analysis_selected" / "EXTRACTION.json"
    bound_files = {"selected_members_sha256": args.selection, "actual_header_sha256": args.header,
                   "approval_sha256": args.approval, "estimator_sha256": HERE / "sdss_estimator.py",
                   "driver_sha256": Path(__file__), "extraction_sha256": extraction,
                   "plot_sha256": HERE / "plot_source_analysis.py",
                   "contract_sha256": HERE / "CONTRACT.md"}
    if any(sha256(path) != bindings[key] for key, path in bound_files.items()):
        raise ValueError("Source/code/approval binding changed before campaign")
    selection, approval, header = (load_json(p) for p in (args.selection, args.approval, args.header))
    paths = load_json(extraction)
    values, covariances, means, intercepts = [], [], [], []
    for index, member in enumerate(selection["members"]):
        source = paths[member["name"]]
        path = Path(source["path"])
        if path.is_symlink() or path.stat().st_size != member["size"] or sha256(path) != source["sha256"]:
            raise ValueError("Extracted immutable source member mismatch")
        if index == 0:
            with path.open(encoding="ascii") as stream:
                first_lines = [stream.readline().rstrip("\r\n") for _ in range(8)]
            if first_lines != header["first_eight_lines"]:
                raise ValueError("Actual source header sample changed")
        rows, total = read_mock(path, approval)
        fit = fit_mock(rows)
        if index == 0:
            write_json(args.output / "CONTROLS.json", first_mock_controls(rows, fit))
        result = {"member": member, "source_sha256": source["sha256"], "rows_in_source": total,
                  "rows_in_frozen_z_selection": len(rows["RA"])}
        for key in ("coefficients_mag", "working_covariance_mag2", "weighted_scalar_mean_errors_mag",
                    "profiled_intercepts_mag", "singular_values"):
            if not np.isfinite(fit[key]).all():
                raise ValueError(f"Invalid computed {key}; no zero fill or null substitution")
            result[key] = fit[key]
        write_json(args.output / f"MOCK_{index:02d}_BOX_{member['box']:03d}_Y0.json", result)
        values.append(fit["coefficients_mag"])
        covariances.append(fit["working_covariance_mag2"])
        means.append(fit["weighted_scalar_mean_errors_mag"])
        intercepts.append(fit["profiled_intercepts_mag"])
        print(f"COMPLETED {index + 1}/64 box={member['box']} rows={len(rows['RA'])}", flush=True)
        del fit, rows, result
    summary = summarize(np.asarray(values), np.asarray(covariances))
    empirical = summary["empirical_covariance_mag2"]
    scatter = summary["coefficient_scatter_mag"]
    denominator = scatter[:, None] * scatter[None, :]
    summary["empirical_correlation"] = np.divide(empirical, denominator,
        out=np.full_like(empirical, np.nan), where=denominator > 0)
    # Only the explicitly undefined zero-scatter correlation cells become null.
    # Infinities or NaNs in any other computed quantity remain hard failures.
    for key in ("empirical_correlation", "empirical_crosswindow_correlation"):
        correlation = summary[key]
        undefined = denominator == 0 if key == "empirical_correlation" else denominator[:8, 8:] == 0
        if not np.isfinite(correlation[~undefined]).all():
            raise ValueError("Invalid defined empirical correlation")
        summary[key] = [[None if undefined[i, j] else float(correlation[i, j])
                         for j in range(correlation.shape[1])] for i in range(correlation.shape[0])]
    summary.update(metadata=artifact_metadata(), basis=BASIS, windows=WINDOWS,
                   coefficients_mag=values, working_covariances_mag2=covariances,
                   weighted_scalar_mean_errors_mag=means, profiled_intercepts_mag=intercepts,
                   K_over_64_descriptive=summary["K_exceeding_descriptive_threshold"] / 64.,
                   source_version="v1.1.0", source_bindings=load_json(args.output / "INPUT_BINDINGS.json"))
    write_json(args.output / "SUMMARY.json", summary)
    with (args.output / "REPORT.md").open("x") as stream:
        stream.write("# SDSS source-only diagnostic\n\n")
        stream.write("Non-claim-bearing obsstat output; scientific admission HOLD.\n\n")
        stream.write(f"Descriptive K/64: {summary['K_exceeding_descriptive_threshold']}/64; "
                     f"fixed threshold: {summary['descriptive_threshold']:.12g}.\n\n")
        stream.write("This is not calibrated physical or H02 coverage. Separate-box independence is "
                     "NOT_CERTIFIED; the source-fitted mask/selection/FP-error process is retained. "
                     "The covariance is DIAGONAL_WORKING with shared-window terms. "
                     "No bias centering, error inflation, window retuning or CF4 joint-law substitution.\n\n")
        stream.write("SUMMARY.json contains all 64 uncentered vectors, 16x16 working covariances, "
                     "means/intercepts, empirical covariance/correlations and variance ratios. "
                     "Individual MOCK files preserve each completed box; CONTROLS.json records "
                     "the designated-first-mock controls.\n")
    from plot_source_analysis import plot_summary
    plot_summary(summary, args.output)


def ledger_state(stream):
    stream.seek(0)
    records = [json.loads(line) for line in stream if line.strip()]
    opened, ended, used = {}, set(), 0.
    for row in records:
        run_id = row["run_id"]
        if row["event"] == "START":
            if run_id in opened:
                raise ValueError("Duplicate budget START identity")
            opened[run_id] = row
        elif row["event"] == "END":
            elapsed = row.get("elapsed_s")
            if (run_id not in opened or run_id in ended or type(elapsed) not in (int, float)
                    or not math.isfinite(elapsed) or elapsed < 0):
                raise ValueError("Invalid shared budget completion")
            ended.add(run_id)
            used += elapsed
        else:
            raise ValueError("Unknown shared budget event")
    if set(opened) != ended:
        raise ValueError("HOLD: reconcile incomplete launched science budget entries")
    return records, used


def append_ledger(stream, row):
    stream.seek(0, os.SEEK_END)
    stream.write(json.dumps(row, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def launch_science(args, ledger=LEDGER):
    with Path(ledger).open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        records, used = ledger_state(stream)
        if used >= CAP:
            raise ValueError("HOLD: cumulative 600-second science cap reached")
        if args.tests:
            phase = TEST_PHASE
            command = [sys.executable, "-m", "unittest", "discover", "-s", str(HERE),
                       "-p", "test_source_analysis.py", "-v"]
            output = HERE / f"SOURCE_DRIVER_TESTS_{time.time_ns()}"
        else:
            phase = PHASE
            if any(row.get("phase") == PHASE for row in records):
                raise ValueError("HOLD: actual-source campaign already launched; no hidden rerun")
            if args.output.exists():
                raise ValueError("HOLD: prior source output retained; explicit recovery required")
            # Approval check occurs before reading outcome rows or extracting.
            selection, header, _, bindings, archive_stat = validate_inputs(
                args.root, args.selection, args.header, args.approval)
            extract_selected(args.root, selection, header, archive_stat)
            output = args.output
            command = [sys.executable, str(Path(__file__).resolve()), "--_worker", "--run-id", "PENDING",
                       "--root", str(args.root), "--selection", str(args.selection), "--header", str(args.header),
                       "--approval", str(args.approval), "--output", str(output)]
        # Exclusive directory creation preserves every prior result/failure.
        output.mkdir()
        run_id = str(time.time_ns())
        if not args.tests:
            command[command.index("PENDING")] = run_id
            bindings.update(approval_sha256=sha256(args.approval), estimator_sha256=sha256(HERE / "sdss_estimator.py"),
                            driver_sha256=sha256(Path(__file__)), generating_command=sys.argv,
                            plot_sha256=sha256(HERE / "plot_source_analysis.py"),
                            extraction_sha256=sha256(args.root / "analysis_selected" / "EXTRACTION.json"),
                            observed_head=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
            write_json(output / "INPUT_BINDINGS.json", bindings)
        remaining = CAP - used
        unit_timeout = min(10., remaining) if args.tests else remaining
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
                   NUMEXPR_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1", SDSS_SOURCE_BUDGET_RUN=run_id)
        append_ledger(stream, {"event": "START", "run_id": run_id, "phase": phase, "command": command,
                              "prior_cumulative_s": used, "remaining_s": remaining,
                              "unit_timeout_s": unit_timeout,
                              "requested_model": "gpt-6.1-sol", "requested_effort": "high", "observed_model": "UNKNOWN"})
        started, exit_code = time.monotonic(), 1
        try:
            with (output / "RAW_STDOUT_STDERR.txt").open("xb") as raw:
                try:
                    result = subprocess.run(command, env=env, stdout=raw, stderr=subprocess.STDOUT, timeout=unit_timeout)
                    exit_code = result.returncode
                except subprocess.TimeoutExpired:
                    raw.write(f"\nTIMEOUT after {unit_timeout:.6f}s; shared budget charged, partials retained, no retry.\n".encode())
                    exit_code = 124
                except BaseException:
                    raw.write(traceback.format_exc().encode())
                    raise
        finally:
            elapsed = time.monotonic() - started
            append_ledger(stream, {"event": "END", "run_id": run_id, "phase": phase, "elapsed_s": elapsed,
                                  "cumulative_s": used + elapsed, "exit_code": exit_code})
            write_json(output / "RETURN.json", {"exit_code": exit_code, "elapsed_s": elapsed,
                       "cumulative_s": used + elapsed, "status": "EXECUTED_AWAITING_INDEPENDENT_REVIEW"
                       if exit_code == 0 else "FIRST_FAILURE_OR_PARTIAL_PRESERVED", "scientific_admission": "HOLD"})
        print(f"exit={exit_code}; cumulative={used + elapsed:.6f}/600s; raw={output / 'RAW_STDOUT_STDERR.txt'}")
        return exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--selection", type=Path, default=HERE / "SELECTED_MEMBERS.json")
    parser.add_argument("--header", type=Path, default=HERE / "ACTUAL_HEADER.json")
    parser.add_argument("--approval", type=Path, default=HERE / "ACTUAL_FIELD_APPROVAL.json")
    parser.add_argument("--output", type=Path, default=HERE / "SOURCE_ANALYSIS")
    parser.add_argument("--tests", action="store_true", help="Run only finite driver fixtures, charging the shared budget")
    parser.add_argument("--_worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--run-id", default="", help=argparse.SUPPRESS)
    args = parser.parse_args()
    expected_python = HERE.parents[5] / ".venv" / "bin" / "python"
    # Compare lexical executable paths: the venv symlink resolves to system Python.
    if Path(sys.executable).absolute() != expected_python:
        raise SystemExit(f"Use canonical interpreter {expected_python}")
    if args._worker:
        science_worker(args)
        return 0
    return launch_science(args)


if __name__ == "__main__":
    raise SystemExit(main())
