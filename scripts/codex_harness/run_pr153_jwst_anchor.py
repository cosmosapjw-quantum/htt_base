#!/usr/bin/env python3
"""PR-153 runner: published-table JWST results plus anchor linkage.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the row-complete cited-seed anchor manifest, the authoritative-reproduction
decision, the probabilistic CF4 cross-match, the tolerance sensitivity, the
row-replay + leave-one-match + label-substitution negative tests, captions and
the six-mutant kill report.  The cross-match reads the real CF4 group catalogue
(``cf4_groups.npz``, ~5 MB) directly.

Content-verified author-source tables produce paired host-level method
consistency measurements.  The CF4 cross-match remains a separate supporting
linkage product; no H0 fit, CF4-conditioned forecast, detection, or
Bianchi-family claim.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import tarfile
import warnings
from fractions import Fraction
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))
warnings.filterwarnings("ignore")

import yaml  # noqa: E402

from obsstat.jwst_anchor_manifest import (  # noqa: E402
    JWSTAnchorError,
    SCHEMA_VERSION,
    authoritative_reproduction_decision,
    build_row_manifest,
    crossmatch_all,
    crossmatch_tolerance_sensitivity,
    generate_caption,
    label_substitution_negative_test,
    leave_one_match_report,
    lint_caption,
    refuse_authoritative_without_table,
    refuse_bianchi_from_jwst,
    refuse_cf4_forecast_downstream_open,
    refuse_jwst_measurement,
    refuse_radius_only_identity,
    refuse_synthetic_renamed_observed,
    row_replay,
)
from obsstat.jwst_distance_consistency import build_distance_result  # noqa: E402

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr153_spec.yaml"
OUTPUTS = {
    "manifest_rows": "docs/generated/pr153_row_manifest.json",
    "decision": "docs/generated/pr153_authoritative_decision.json",
    "distance_result": "docs/generated/pr153_distance_consistency.json",
    "crossmatch": "docs/generated/pr153_crossmatch.json",
    "sensitivity": "docs/generated/pr153_sensitivity.json",
    "negatives": "docs/generated/pr153_negative_tests.json",
    "captions": "docs/generated/pr153_captions.json",
    "mutations": "docs/generated/pr153_mutation_report.json",
    "manifest": "docs/generated/pr153_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"
REQUIRED_ARTIFACT_METADATA = {
    "owner", "implementation_scope", "claim_tier", "transfer_source",
    "config_hash", "input_hashes", "sky_support_status", "mask_status",
    "covariance_status", "null_mock_status", "caveats",
    "generating_command", "git_commit", "worktree_state",
}
TRANSCRIPTION_FIELDS = {
    "cchp_trgb_jagb": [
        "dataset", "host", "method_a", "mu_a_mag", "sigma_a_mag",
        "method_b", "mu_b_mag", "sigma_b_mag", "source_arxiv",
        "source_table"],
    "shoes_jwst_hst": [
        "dataset", "host", "method_a", "mu_a_mag", "sigma_a_mag",
        "method_b", "mu_b_mag", "sigma_b_mag", "source_arxiv",
        "source_table"],
    "li2024_jwst_trgb_hst_cepheid": [
        "dataset", "source_arxiv", "source_locator",
        "parent_sn_calibrator_count", "parent_count_unit",
        "paired_object_count", "paired_count_unit", "paired_sample_definition",
        "method_a", "method_b", "mean_delta_mag",
        "stat_standard_error_mag", "delta_definition"],
    "li2025_complete_trgb_hst_cepheid": [
        "dataset", "source_arxiv", "source_locator",
        "parent_sn_calibrator_count", "parent_count_unit",
        "paired_object_count", "paired_count_unit", "paired_sample_definition",
        "method_a", "method_b", "mean_delta_mag",
        "stat_standard_error_mag", "delta_definition"],
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_prefixed(path: Path) -> str:
    return "sha256:" + _sha(path)


def _valid_sha256(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)


def _canonical_sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False,
                       sort_keys=True) + "\n").encode()


def validate_artifact_metadata(payload: dict) -> None:
    metadata = payload.get("artifact_metadata")
    if not isinstance(metadata, dict):
        raise ValueError("artifact_metadata missing")
    missing = sorted(REQUIRED_ARTIFACT_METADATA - set(metadata))
    if missing:
        raise ValueError(f"artifact metadata missing fields: {missing}")
    if not _valid_sha256(metadata["config_hash"]):
        raise ValueError("artifact config hash invalid")
    if (not isinstance(metadata["input_hashes"], list)
            or not metadata["input_hashes"]
            or not all(isinstance(row, dict)
                       and _valid_sha256(row.get("sha256"))
                       for row in metadata["input_hashes"])):
        raise ValueError("artifact input hashes invalid")


def _verify_fetch_manifest(spec: dict, fetch_manifest: dict,
                           comparison_rows: list[dict],
                           aggregate_rows: list[dict]) -> None:
    """Bind source archives, members, exact source cells, and CSV bytes."""
    ds = spec["data_scope"]["raw_data_paths"]
    comparison_path = REPO / ds["comparison_csv"]
    aggregate_path = REPO / ds["aggregate_csv"]
    seed_path = REPO / ds["seed_csv"]
    problems = []
    expected_pins = {
        "seed_csv": ds["seed_csv"],
        "seed_sha256": _sha_prefixed(seed_path),
        "source_checked_comparison_csv": ds["comparison_csv"],
        "source_checked_comparison_csv_sha256": _sha_prefixed(comparison_path),
        "source_checked_aggregate_csv": ds["aggregate_csv"],
        "source_checked_aggregate_csv_sha256": _sha_prefixed(aggregate_path),
    }
    for field, expected in expected_pins.items():
        if fetch_manifest.get(field) != expected:
            problems.append(f"fetch manifest pin mismatch: {field}")
    if fetch_manifest.get("status") != "source_tables_and_exact_cells_verified":
        problems.append("fetch manifest status is not exact-cell verified")
    fetched = {str(row.get("label")): row
               for row in fetch_manifest.get("fetched", [])}
    if len(fetched) != len(fetch_manifest.get("fetched", [])):
        problems.append("duplicate fetched source label")
    fetch_dir = (REPO / ds["fetch_manifest"]).parent
    for label, contract in spec["source_table_contract"].items():
        row = fetched.get(label) or {}
        verification = row.get("verification") or {}
        archive = fetch_dir / str(row.get("path", ""))
        if (row.get("arxiv") != contract["arxiv"]
                or verification.get("member") != contract["member"]
                or verification.get("ok") is not True
                or verification.get("cell_markers_verified") is not True
                or verification.get("missing_markers")
                or verification.get("missing_cell_markers")
                or row.get("analysis_table_ingested") is not True
                or row.get("sha256") != (_sha_prefixed(archive)
                                           if archive.is_file() else None)):
            problems.append(f"source archive contract mismatch: {label}")
            continue
        try:
            with tarfile.open(archive, mode="r:gz") as bundle:
                handle = bundle.extractfile(contract["member"])
                if handle is None:
                    raise KeyError(contract["member"])
                text = handle.read().decode("utf-8", errors="replace")
        except (OSError, tarfile.TarError, KeyError):
            problems.append(f"source member unreadable: {label}")
            continue
        if verification.get("member_sha256") != (
                "sha256:" + hashlib.sha256(text.encode()).hexdigest()):
            problems.append(f"source member hash mismatch: {label}")
        cell_markers = verification.get("required_cell_markers")
        if (not isinstance(cell_markers, list)
                or len(cell_markers) != contract["cell_marker_count"]
                or any(marker not in text for marker in cell_markers)
                or verification.get("cell_receipt_sha256")
                != _canonical_sha256(cell_markers)):
            problems.append(f"source exact-cell marker mismatch: {label}")

    table_rows = {
        "cchp_trgb_jagb": comparison_rows,
        "shoes_jwst_hst": comparison_rows,
        "li2024_jwst_trgb_hst_cepheid": aggregate_rows,
        "li2025_complete_trgb_hst_cepheid": aggregate_rows,
    }
    receipts = {str(row.get("dataset")): row
                for row in fetch_manifest.get("transcription_receipts", [])}
    expected_datasets = set(spec["transcription_contract"])
    if set(receipts) != expected_datasets:
        problems.append("transcription receipt dataset set mismatch")
    for dataset, contract in spec["transcription_contract"].items():
        receipt = receipts.get(dataset) or {}
        selected = [row for row in table_rows[dataset]
                    if row.get("dataset") == dataset]
        fields = TRANSCRIPTION_FIELDS[dataset]
        exact_cells = [{field: row.get(field) for field in fields}
                       for row in selected]
        source = fetched.get(contract["source_label"], {})
        verification = source.get("verification") or {}
        expected_csv = (ds["comparison_csv"] if dataset in {
            "cchp_trgb_jagb", "shoes_jwst_hst"} else ds["aggregate_csv"])
        expected_csv_hash = (_sha_prefixed(comparison_path)
                             if expected_csv == ds["comparison_csv"]
                             else _sha_prefixed(aggregate_path))
        if (len(selected) != contract["row_count"]
                or receipt.get("registered_row_count") != contract["row_count"]
                or receipt.get("observed_row_count") != contract["row_count"]
                or receipt.get("source_label") != contract["source_label"]
                or receipt.get("source_archive_sha256") != source.get("sha256")
                or receipt.get("source_member_sha256")
                != verification.get("member_sha256")
                or receipt.get("source_cell_receipt_sha256")
                != verification.get("cell_receipt_sha256")
                or receipt.get("transcription_csv") != expected_csv
                or receipt.get("transcription_csv_sha256") != expected_csv_hash
                or receipt.get("exact_cells") != exact_cells
                or receipt.get("exact_cells_sha256")
                != _canonical_sha256(exact_cells)
                or receipt.get("verified") is not True):
            problems.append(f"exact transcription receipt mismatch: {dataset}")
    if problems:
        raise SystemExit("invalid JWST source provenance: " + "; ".join(problems))


def _verify_baseline_commit(spec: dict) -> None:
    import subprocess
    sha = str(spec.get("baseline_commit") or "")
    if len(sha) != 40:
        raise SystemExit("baseline_commit must be a full 40-hex id")
    probe = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                           cwd=REPO, capture_output=True, check=False)
    if probe.returncode != 0:
        raise SystemExit(f"baseline_commit {sha} does not resolve")


def _verify_remediation_state(spec: dict) -> None:
    contract = spec["remediation_state_contract"]
    target = REPO / contract["path"]
    if _sha(target) != contract["sha256"]:
        raise SystemExit("remediation state drifted from the spec pin")
    payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    findings = payload.get("findings") or []
    statuses: dict[str, int] = {}
    for row in findings:
        statuses[str(row.get("scientific_status"))] = \
            statuses.get(str(row.get("scientific_status")), 0) + 1
    if len(findings) != contract["finding_count"]:
        raise SystemExit("remediation finding count drifted")
    required = {str(k): int(v)
                for k, v in contract["required_scientific_status_counts"].items()}
    if statuses != required:
        raise SystemExit(f"remediation status counts drifted: {statuses}")


def _load_seed(path: Path) -> list:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("name,"):
            continue
        f = line.split(",")
        rows.append({"name": f[0], "ra_deg": float(f[1]), "dec_deg": float(f[2]),
                     "jwst_e_dm_mag": float(f[3]), "method": f[4],
                     "source": f[5]})
    return rows


def _load_comparison_table(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(line for line in handle
                                   if not line.startswith("#")))


def build_reports(spec: dict):
    ds = spec["data_scope"]["raw_data_paths"]
    seed_path = REPO / ds["seed_csv"]
    fetch_path = REPO / ds["fetch_manifest"]
    comparison_path = REPO / ds["comparison_csv"]
    aggregate_path = REPO / ds["aggregate_csv"]
    cf4_path = REPO / ds["cf4_groups"]
    for p in (seed_path, fetch_path, comparison_path, aggregate_path, cf4_path):
        if not p.is_file():
            raise SystemExit(f"required input absent: {p}")
    seed_rows = _load_seed(seed_path)
    fetch_manifest = (json.loads(fetch_path.read_text(encoding="utf-8"))
                      if fetch_path.is_file() else {})
    comparison_rows = _load_comparison_table(comparison_path)
    aggregate_rows = _load_comparison_table(aggregate_path)
    _verify_fetch_manifest(
        spec, fetch_manifest, comparison_rows, aggregate_rows)
    m = spec["model"]["match"]
    sigma = float(Fraction(m["position_sigma_deg"]))
    ambig = float(Fraction(m["ambiguity_ratio_threshold"]))
    tol_grid = [float(Fraction(t)) for t in m["tolerance_grid_deg"]]

    decision = authoritative_reproduction_decision(fetch_manifest)
    if not decision["source_tables_reproduced"]:
        raise SystemExit("registered JWST author-source tables are incomplete")
    distance_result = build_distance_result(comparison_rows, aggregate_rows)
    for row in distance_result["expanded_source_reported_aggregates"]["rows"]:
        for key, value in row.items():
            if ("_p_" in key or key.endswith("_p_for_zero")) and (
                    not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                    or not 0.0 < float(value) <= 1.0):
                raise SystemExit(f"invalid finite aggregate probability: {key}")
        shift_p = row["registered_shift_comparison"][
            "one_sided_p_mean_at_least_comparison"]
        if not math.isfinite(shift_p) or not 0.0 < shift_p <= 1.0:
            raise SystemExit("finite aggregate shift probability was erased")

    # anti-drift guards invoked LIVE with admissible input
    refuse_radius_only_identity("probabilistic_uncertainty_weighted")
    refuse_synthetic_renamed_observed("cited_seed_not_synthetic")
    refuse_authoritative_without_table(
        decision["authoritative_table_reproduced"], "cited_seed")
    refuse_cf4_forecast_downstream_open("catalogue_linkage_only")
    refuse_jwst_measurement("published_table_host_consistency")
    refuse_bianchi_from_jwst("no_geometry_claim")

    manifest_rows = {"schema": "pr153.row_manifest.v1",
                     "module_schema": SCHEMA_VERSION,
                     **build_row_manifest(seed_rows, seed_sha256=_sha(seed_path),
                                          fetch_manifest=fetch_manifest)}
    decision_art = {"schema": "pr153.authoritative_decision.v1", **decision}

    z = np.load(cf4_path)
    cf4_ra = np.asarray(z["RAdeg"], float)
    cf4_dec = np.asarray(z["DEdeg"], float)
    cf4_pgc = np.asarray(z["PGC"], float)
    anchors = manifest_rows["rows"]

    crossmatch = {"schema": "pr153.crossmatch.v1",
                  **crossmatch_all(anchors, cf4_ra, cf4_dec, cf4_pgc,
                                   position_sigma_deg=sigma,
                                   ambiguity_ratio_threshold=ambig)}
    sensitivity = {"schema": "pr153.sensitivity.v1",
                   **crossmatch_tolerance_sensitivity(
                       anchors, cf4_ra, cf4_dec, cf4_pgc,
                       tolerance_grid_deg=tol_grid,
                       ambiguity_ratio_threshold=ambig)}
    replay = row_replay(anchors, build_row_manifest(
        _load_seed(seed_path), seed_sha256=_sha(seed_path),
        fetch_manifest=fetch_manifest)["rows"])
    loo = leave_one_match_report(anchors, cf4_ra, cf4_dec, cf4_pgc,
                                 position_sigma_deg=sigma,
                                 ambiguity_ratio_threshold=ambig)
    negtest = label_substitution_negative_test(
        anchors, cf4_ra, cf4_dec, cf4_pgc, position_sigma_deg=sigma,
        ambiguity_ratio_threshold=ambig, seed=20260727)
    negatives = {"schema": "pr153.negative_tests.v1", "row_replay": replay,
                 "leave_one_match": loo, "label_substitution": negtest,
                 "n_credible_identity_broken_by_substitution":
                     negtest["n_credible_identity_broken_by_substitution"]}
    return (fetch_manifest, manifest_rows, decision_art, distance_result,
            crossmatch, sensitivity, negatives)


def build_captions(manifest_rows, decision, distance_result, crossmatch,
                   negatives) -> dict:
    text = generate_caption(manifest_rows, decision, crossmatch,
                            negatives["label_substitution"], distance_result)
    lint_caption(text)
    return {"schema": "pr153.captions.v1", "captions": {"summary": text}}


def _artifact_metadata(spec: dict, fetch_manifest: dict) -> dict:
    ds = spec["data_scope"]["raw_data_paths"]
    input_hashes = [
        {"path": path, "sha256": _sha_prefixed(REPO / path)}
        for path in (
            ds["seed_csv"], ds["comparison_csv"], ds["aggregate_csv"],
            ds["fetch_manifest"], ds["cf4_groups"],
            "htt/obsstat/jwst_anchor_manifest.py",
            "htt/obsstat/jwst_distance_consistency.py",
            "dl_pipeline/scripts/download_jwst_anchors.py",
            "scripts/codex_harness/run_pr153_jwst_anchor.py",
        )
    ]
    for source in fetch_manifest["fetched"]:
        input_hashes.append({
            "path": f"{Path(ds['fetch_manifest']).parent}/{source['path']}",
            "sha256": source["sha256"],
        })
        input_hashes.append({
            "path": f"archive-member:{source['path']}:{source['verification']['member']}",
            "sha256": source["verification"]["member_sha256"],
        })
    caveats = [
        "Host-level Student-t intervals condition on independent host deltas "
        "and exclude shared-anchor/common-systematic covariance.",
        "Published aggregates are source-reported statistical-SE replays; "
        "overlapping samples are not combined.",
        "The coordinate-seed CF4 linkage remains positional-only and does not "
        "confirm physical identity.",
        "No H0 fit, CF4-conditioned precision forecast, detection, geometry, "
        "or Bianchi-family claim is authorized.",
    ]
    return {
        "owner": spec["owner"],
        "implementation_scope": list(spec["implementation_scope"]),
        "claim_tier": spec["claim_tier"],
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha_prefixed(SPEC_PATH),
        "input_hashes": input_hashes,
        "sky_support_status":
            "published_host_tables_plus_separate_positional_cf4_linkage",
        "mask_status": "not_applicable_non_sky_map_distance_table_result",
        "covariance_status": "shared_anchor_covariance_unavailable",
        "null_mock_status":
            "not_applicable_published_table_and_source_reported_aggregate",
        "caveats": caveats,
        "generating_command":
            "venv/bin/python scripts/codex_harness/run_pr153_jwst_anchor.py --write",
        "git_commit": spec["baseline_commit"],
        "worktree_state": "dirty_amend_in_place_from_baseline",
        "runtime_environment": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
        },
    }


def _attach_metadata(payloads: list[dict], metadata: dict) -> None:
    for payload in payloads:
        payload["artifact_metadata"] = metadata
        validate_artifact_metadata(payload)


def _scan_targets(spec: dict, captions_payload: dict) -> dict:
    patterns = [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
    targets = {}
    for rel in spec["negative_scan"]["targets"]:
        if rel == OUTPUTS["captions"]:
            raw = _render(captions_payload).decode()
            source, digest = "fresh_build", hashlib.sha256(raw.encode()).hexdigest()
        else:
            path = REPO / rel
            raw = path.read_text(encoding="utf-8")
            source, digest = "disk", _sha(path)
        hits = []
        for idx, line in enumerate(raw.splitlines(), start=1):
            low = line.lower()
            for pi, pattern in enumerate(patterns):
                if pattern.lower() in low:
                    hits.append({"line": idx, "pattern_index": pi})
        targets[rel] = {"hits": hits, "source": source, "sha256": digest}
    total = sum(len(t["hits"]) for t in targets.values())
    if total:
        raise SystemExit(f"negative scan found {total} hits: {targets}")
    return targets


def _redact(message: str, patterns: list[str]) -> str:
    for pattern in patterns:
        low = message.lower()
        needle = pattern.lower()
        while needle in low:
            start = low.index(needle)
            message = message[:start] + REDACTED + message[start + len(pattern):]
            low = message.lower()
    return message


def run_mutations(spec: dict) -> dict:
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])
    executions = {
        "identity_from_radius_alone":
            lambda: refuse_radius_only_identity("coordinate_radius_only"),
        "synthetic_renamed_observed":
            lambda: refuse_synthetic_renamed_observed(
                "synthetic_fixture_as_observed"),
        "authoritative_reproduction_without_table":
            lambda: refuse_authoritative_without_table(
                False, "authoritative_reproduced"),
        "cf4_forecast_while_downstream_open":
            lambda: refuse_cf4_forecast_downstream_open(
                "cf4_conditioned_forecast"),
        "jwst_measurement_claim":
            lambda: refuse_jwst_measurement("h0_fit_from_host_offsets"),
        "bianchi_family_from_jwst":
            lambda: refuse_bianchi_from_jwst("bianchi_family"),
    }
    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed, message = False, "MUTANT SURVIVED"
        try:
            fn()
        except JWSTAnchorError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr153.mutation_report.v1", "mutations": rows,
            "surviving_mutation_count":
                len([m for m in rows if not m["killed"]])}


def _emit(rel, payload, write, problems, wrote) -> None:
    target = REPO / rel
    rendered = _render(payload)
    if write:
        if target.is_file() and target.read_bytes() == rendered:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_bytes(rendered)
        tmp.replace(target)
        wrote.append(rel)
        return
    if not target.is_file():
        problems.append(f"missing artifact: {rel}")
    elif target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr153_jwst_anchor.v2":
        raise SystemExit("pr153 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    (fetch_manifest, manifest_rows, decision, distance_result, crossmatch,
     sensitivity, negatives) = build_reports(spec)
    captions = build_captions(manifest_rows, decision, distance_result,
                              crossmatch, negatives)
    metadata = _artifact_metadata(spec, fetch_manifest)
    _attach_metadata(
        [manifest_rows, decision, distance_result, crossmatch, sensitivity,
         negatives, captions], metadata)
    decision["negative_scan"] = {"targets": _scan_targets(spec, captions),
                                 "total_hits": 0}
    mutations = run_mutations(spec)
    _attach_metadata([mutations], metadata)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["manifest_rows"], manifest_rows, write, problems, wrote)
    _emit(OUTPUTS["decision"], decision, write, problems, wrote)
    _emit(OUTPUTS["distance_result"], distance_result, write, problems, wrote)
    _emit(OUTPUTS["crossmatch"], crossmatch, write, problems, wrote)
    _emit(OUTPUTS["sensitivity"], sensitivity, write, problems, wrote)
    _emit(OUTPUTS["negatives"], negatives, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr153.artifact_manifest.v2",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "implementation_scope": list(spec["implementation_scope"]),
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": metadata["config_hash"],
        "raw_data_pins": {
            "seed_csv_sha256": _sha(REPO / spec["data_scope"]["raw_data_paths"]["seed_csv"]),
            "comparison_csv_sha256": _sha(
                REPO / spec["data_scope"]["raw_data_paths"]["comparison_csv"]),
            "aggregate_csv_sha256": _sha(
                REPO / spec["data_scope"]["raw_data_paths"]["aggregate_csv"]),
            "fetch_manifest_sha256": _sha(
                REPO / spec["data_scope"]["raw_data_paths"]["fetch_manifest"]),
            "cf4_groups_sha256": _sha(REPO / spec["data_scope"]["raw_data_paths"]["cf4_groups"])},
        "input_hashes": metadata["input_hashes"],
        "sky_support_status": metadata["sky_support_status"],
        "mask_status": metadata["mask_status"],
        "covariance_status": metadata["covariance_status"],
        "null_mock_status": metadata["null_mock_status"],
        "generating_command": metadata["generating_command"],
        "check_command":
            "venv/bin/python scripts/codex_harness/run_pr153_jwst_anchor.py --check",
        "git_commit": metadata["git_commit"],
        "worktree_state": metadata["worktree_state"],
        "runtime_environment": metadata["runtime_environment"],
        "source_transcription_receipts": fetch_manifest[
            "transcription_receipts"],
        "caveats": [
            "Published-table host-distance consistency result at conditional claim tier.",
            "Author-submitted arXiv LaTeX tables and the source-checked "
            "transcription are content-verified and hashed.",
            "The source tables do not expose the full shared-anchor covariance; "
            "host-level inference is primary and inverse-variance pooling is sensitivity-only.",
            "Two expanded-sample values are source-reported aggregate replays; "
            "their overlapping samples are not pooled.",
            "Identity is probabilistic and uncertainty-weighted, never a "
            "coordinate radius alone; the synthetic fixture is never renamed "
            "observed data.",
            "No CF4-conditioned precision forecast is authorized while "
            "N-DATA-CF4-DOWNSTREAM is OPEN.",
            "No H0 fit, CF4-conditioned precision forecast, detection, or Bianchi-family "
            "claim; the two CF4 P0s are untouched and stay OPEN.",
            "All 102 remediation findings remain OPEN.",
        ],
        "artifacts": {rel: (_sha(REPO / rel) if (REPO / rel).is_file() else None)
                      for key, rel in OUTPUTS.items() if key != "manifest"},
    }
    _emit(OUTPUTS["manifest"], manifest, write, problems, wrote)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}))
        return 2

    for key, rel in OUTPUTS.items():
        payload = json.loads((REPO / rel).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.pop("forbidden_use", None)
        text = json.dumps(payload, ensure_ascii=False).lower()
        for phrase in spec["forbidden_output_language"]:
            if phrase.lower() in text:
                print(json.dumps({"ok": False,
                                  "reason": f"forbidden phrase in {rel}"}))
                return 2
    module_text = (REPO / "htt/obsstat/jwst_anchor_manifest.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "n_anchors": manifest_rows["n_anchors"],
        "jwst_lane_status": decision["jwst_lane_status"],
        "cchp_mean_delta_mag": distance_result[
            "cchp_trgb_minus_jagb_consistency"]["primary_host_level"]["mean_delta_mag"],
        "shoes_mean_delta_mag": distance_result[
            "shoes_jwst_minus_hst_consistency"]["primary_host_level"]["mean_delta_mag"],
        "expanded_aggregate_count": distance_result[
            "expanded_source_reported_aggregates"]["n_registered_aggregates"],
        "n_positionally_credible": crossmatch["n_positionally_credible"],
        "n_ambiguous": crossmatch["n_ambiguous"],
        "credible_identities_broken": negatives["n_credible_identity_broken_by_substitution"],
        "surviving_mutations": 0,
    }, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    sys.exit(build(write=args.write))


if __name__ == "__main__":
    main()
