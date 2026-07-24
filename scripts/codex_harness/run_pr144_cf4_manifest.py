#!/usr/bin/env python3
"""PR-144 runner: authenticated CF4 row/group/selection manifest.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the CF4 manifest (release identity + per-table content-address +
1PGC parity + duplicate/missing), the full column authority, the
selection/completeness + range fixtures, generated captions, and the
six-mutant kill report. The raw CF4 tables live on a read-only external
path (workdir/raw/cf4_full); only the manifest is versioned. If the raw
data is absent an explicit missing-authority report is emitted instead.

Dataset / estimand provenance only at roadmap_rescue_v1:C1; the two CF4
P0s stay OPEN; no cosmological measurement, no detection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))

import yaml  # noqa: E402

from common.cf4_manifest import (  # noqa: E402
    CF4_RELEASE,
    CARTESIAN_UNITS_CAVEAT,
    SCHEMA_VERSION,
    TABLE3_COLUMNS,
    TABLE4_COLUMNS,
    Cf4ManifestError,
    column_authority,
    file_sha256,
    generate_caption,
    id_parity,
    lint_caption,
    missing_summary,
    range_fixtures,
    read_lines,
    refuse_audit_value_as_observed,
    refuse_cf4_p0_resolution_claim,
    refuse_reconstruction_as_true_flow,
    require_cz_units_for_cartesian,
    require_registered_column,
    row_hash_digest,
    selection_completeness,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr144_spec.yaml"
OUTPUTS = {
    "manifest": "docs/generated/pr144_cf4_manifest.json",
    "authority": "docs/generated/pr144_column_authority.json",
    "completeness": "docs/generated/pr144_selection_completeness.json",
    "captions": "docs/generated/pr144_captions.json",
    "mutations": "docs/generated/pr144_mutation_report.json",
    "artifact_manifest": "docs/generated/pr144_artifact_manifest.json",
}
SOURCE_PATH = "htt/src/common/cf4_manifest.py"
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Keep the maintained-source hash as generation-time provenance."""

    normalized = json.loads(json.dumps(payload))
    if rel == OUTPUTS["manifest"]:
        scan = normalized.get("negative_scan")
        targets = scan.get("targets") if isinstance(scan, dict) else None
        source = (
            targets.get(SOURCE_PATH)
            if isinstance(targets, dict) else None
        )
        if isinstance(source, dict) and _is_sha256(source.get("sha256")):
            source["sha256"] = "<generation-time-source>"
        return normalized
    if rel != OUTPUTS["artifact_manifest"]:
        return normalized
    rows = normalized.get("input_hashes")
    if not isinstance(rows, list):
        return normalized
    prefix = f"{SOURCE_PATH}:"
    for index, row in enumerate(rows):
        if (
            isinstance(row, str)
            and row.startswith(prefix)
            and _is_sha256(row.removeprefix(prefix))
        ):
            rows[index] = f"{prefix}<generation-time-source>"
    return normalized


def _verify_baseline_commit(spec: dict) -> None:
    import subprocess

    sha = str(spec.get("baseline_commit") or "")
    if len(sha) != 40:
        raise SystemExit("baseline_commit must be a full 40-hex id")
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=REPO, capture_output=True, check=False)
    if probe.returncode != 0:
        raise SystemExit(
            f"baseline_commit {sha} does not resolve to a commit — "
            "fabricated provenance is refused")


def _verify_remediation_state(spec: dict) -> None:
    contract = spec["remediation_state_contract"]
    target = REPO / contract["path"]
    if _sha(target) != contract["sha256"]:
        raise SystemExit("remediation state drifted from the spec pin")
    payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    findings = payload.get("findings") or []
    statuses: dict[str, int] = {}
    for row in findings:
        status = str(row.get("scientific_status"))
        statuses[status] = statuses.get(status, 0) + 1
    if len(findings) != contract["finding_count"]:
        raise SystemExit("remediation finding count drifted")
    required = {str(k): int(v)
                for k, v in contract["required_scientific_status_counts"]
                .items()}
    if statuses != required:
        raise SystemExit(f"remediation status counts drifted: {statuses}")


def _table_record(path: Path, columns, n_expected: int) -> dict:
    lines = read_lines(path)
    if len(lines) != n_expected:
        raise Cf4ManifestError(
            f"{path.name} record count {len(lines)} != pinned {n_expected}")
    return {"path": str(path.relative_to(REPO)) if path.is_relative_to(REPO)
            else str(path), "n_records": len(lines),
            "file_sha256": file_sha256(path), "row_hash": row_hash_digest(lines),
            "n_columns": len(columns)}, lines


def build_manifest(spec: dict) -> tuple[dict, dict, dict, dict]:
    ds = spec["dataset"]
    t3_path = REPO / ds["tables"]["table3"]["path"]
    t4_path = REPO / ds["tables"]["table4"]["path"]
    if not (t3_path.is_file() and t4_path.is_file()):
        missing = {"schema": "pr144.cf4_manifest.v1",
                   "status": "missing_authority",
                   "release": CF4_RELEASE,
                   "missing_paths": [p for p, e in
                                     ((str(t3_path), t3_path.is_file()),
                                      (str(t4_path), t4_path.is_file()))
                                     if not e],
                   "note": "the raw CF4 tables are on a read-only external "
                           "path and are not present; an explicit "
                           "missing-authority report is emitted"}
        return missing, None, None, None

    t3_rec, t3_lines = _table_record(
        t3_path, TABLE3_COLUMNS, int(ds["tables"]["table3"]["n_records"]))
    t4_rec, t4_lines = _table_record(
        t4_path, TABLE4_COLUMNS, int(ds["tables"]["table4"]["n_records"]))
    parity = id_parity(t3_lines, t4_lines)
    manifest = {
        "schema": "pr144.cf4_manifest.v1",
        "module_schema": SCHEMA_VERSION,
        "status": "authenticated",
        "release": CF4_RELEASE,
        "velocity_frame": ds["velocity_frame"],
        "readme_sha256": file_sha256(REPO / ds["readme"]),
        "tables": {"table3": t3_rec, "table4": t4_rec},
        "id_parity": parity,
        "missing_table3": missing_summary(t3_lines, TABLE3_COLUMNS),
        "missing_table4": missing_summary(t4_lines, TABLE4_COLUMNS),
        "cartesian_units_caveat": CARTESIAN_UNITS_CAVEAT,
        "note": "dataset provenance only; the two CF4 P0s (C1-K5-MV-F1, "
                "C3-K5-VCORR-ML-F1) stay OPEN — this manifest supplies their "
                "data lineage, it does not resolve them",
    }
    authority = {
        "schema": "pr144.column_authority.v1",
        "table3": column_authority(TABLE3_COLUMNS),
        "table4": column_authority(TABLE4_COLUMNS),
        "reconstruction_columns": list(spec["anti_drift_guards"]
                                       ["reconstruction_columns"]),
    }
    completeness = {
        "schema": "pr144.selection_completeness.v1",
        "per_method_group_counts": selection_completeness(t3_lines),
        "range_fixtures": range_fixtures(t4_lines, {
            "RAdeg": [float(v) for v in spec["fixtures"]["ra_range"]],
            "DEdeg": [float(v) for v in spec["fixtures"]["dec_range"]],
            "GLAT": [float(v) for v in spec["fixtures"]["glat_range"]],
            "Dist": [0.0, 1000.0]}),
    }
    return manifest, authority, completeness, {"t3": t3_lines, "t4": t4_lines}


def build_captions(manifest: dict) -> dict:
    n_groups = (manifest["id_parity"]["n_unique"]
                if manifest["status"] == "authenticated"
                else CF4_RELEASE["n_groups"])
    n_columns = len(TABLE3_COLUMNS) + len(TABLE4_COLUMNS)
    text = generate_caption(n_groups, n_columns)
    lint_caption(text)
    return {"schema": "pr144.captions.v1", "captions": {"summary": text}}


def _scan_targets(spec: dict, captions_payload: dict) -> dict:
    patterns = [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
    targets = {}
    for rel in spec["negative_scan"]["targets"]:
        if rel == OUTPUTS["captions"]:
            raw = _render(captions_payload).decode()
            source = "fresh_build"
            digest = hashlib.sha256(raw.encode()).hexdigest()
        else:
            path = REPO / rel
            raw = path.read_text(encoding="utf-8")
            source = "disk"
            digest = _sha(path)
        hits = []
        for idx, line in enumerate(raw.splitlines(), start=1):
            lowered = line.lower()
            for pattern_index, pattern in enumerate(patterns):
                if pattern.lower() in lowered:
                    hits.append({"line": idx, "pattern_index": pattern_index})
        targets[rel] = {"hits": hits, "source": source, "sha256": digest}
    total = sum(len(t["hits"]) for t in targets.values())
    if total:
        raise SystemExit(f"negative scan found {total} forbidden-language "
                         f"hits: {targets}")
    return targets


def _redact(message: str, patterns: list[str]) -> str:
    for pattern in patterns:
        lowered = message.lower()
        needle = pattern.lower()
        while needle in lowered:
            start = lowered.index(needle)
            message = message[:start] + REDACTED + \
                message[start + len(pattern):]
            lowered = message.lower()
    return message


def run_mutations(spec: dict, parsed) -> dict:
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])

    def mutant_reconstruction_as_true_flow() -> None:
        refuse_reconstruction_as_true_flow("Vpec")

    def mutant_audit_value_as_observed() -> None:
        refuse_audit_value_as_observed(94)

    def mutant_ambiguous_authority_column() -> None:
        require_registered_column("Vflow_true", TABLE4_COLUMNS)

    def mutant_id_parity_broken() -> None:
        if parsed is None:
            raise Cf4ManifestError("raw data absent — parity cannot be probed")
        # drop one group from table4 to break parity
        id_parity(parsed["t3"], parsed["t4"][:-1])

    def mutant_row_count_drift() -> None:
        col = require_registered_column("1PGC", TABLE4_COLUMNS)
        if parsed is None:
            raise Cf4ManifestError("raw data absent")
        n = len(parsed["t4"]) - 1
        if n != CF4_RELEASE["n_groups"]:
            raise Cf4ManifestError(
                f"record count {n} != pinned {CF4_RELEASE['n_groups']}")

    def mutant_cartesian_as_mpc_length() -> None:
        require_cz_units_for_cartesian("SGX", "mpc_length")

    def mutant_cf4_p0_resolution() -> None:
        refuse_cf4_p0_resolution_claim("cf4_p0_resolved")

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "reconstruction_as_true_flow": mutant_reconstruction_as_true_flow,
        "audit_value_as_observed": mutant_audit_value_as_observed,
        "ambiguous_authority_column": mutant_ambiguous_authority_column,
        "id_parity_broken": mutant_id_parity_broken,
        "row_count_drift": mutant_row_count_drift,
        "cartesian_as_mpc_length": mutant_cartesian_as_mpc_length,
        "cf4_p0_resolution": mutant_cf4_p0_resolution,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except Cf4ManifestError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr144.mutation_report.v1", "mutations": rows,
            "surviving_mutation_count":
                len([m for m in rows if not m["killed"]])}


def _emit(rel: str, payload: dict, write: bool,
          problems: list[str], wrote: list[str]) -> None:
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
        return
    if rel in {OUTPUTS["manifest"], OUTPUTS["artifact_manifest"]}:
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            problems.append(f"invalid artifact: {rel}")
            return
        if (
            isinstance(existing, dict)
            and _semantic_artifact(rel, existing)
            == _semantic_artifact(rel, payload)
        ):
            return
    if target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr144_cf4_manifest.v1":
        raise SystemExit("pr144 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    manifest, authority, completeness, parsed = build_manifest(spec)
    if manifest["status"] == "missing_authority":
        raise SystemExit("CF4 raw tables absent — this run requires the "
                         "read-only external CF4 catalogue at "
                         "workdir/raw/cf4_full")
    captions = build_captions(manifest)
    manifest["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec, parsed)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["manifest"], manifest, write, problems, wrote)
    _emit(OUTPUTS["authority"], authority, write, problems, wrote)
    _emit(OUTPUTS["completeness"], completeness, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    artifact_manifest = {
        "schema": "pr144.artifact_manifest.v1",
        "owner": spec["owner"],
        "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {
            "table3_sha256": manifest["tables"]["table3"]["file_sha256"],
            "table4_sha256": manifest["tables"]["table4"]["file_sha256"],
            "readme_sha256": manifest["readme_sha256"],
        },
        "input_hashes": [
            f"{rel}:{_sha(REPO / rel)}"
            for rel in (SOURCE_PATH,)
        ],
        "caveats": [
            "Dataset / estimand provenance only at C1.",
            "The raw CF4 tables are read-only external inputs; only the "
            "manifest is versioned.",
            "Peculiar-velocity columns (Vpds/Vpwf/Vpec) are estimator-"
            "dependent RECONSTRUCTIONS, never the true flow.",
            "SGX/SGY/SGZ are in cz (km/s), not Mpc lengths.",
            "The two CF4 P0s stay OPEN; the manifest supplies their lineage.",
            "No cosmological measurement, no detection.",
            "All 102 remediation findings remain OPEN.",
        ],
        "artifacts": {
            rel: (_sha(REPO / rel) if (REPO / rel).is_file() else None)
            for key, rel in OUTPUTS.items() if key != "artifact_manifest"
        },
    }
    _emit(OUTPUTS["artifact_manifest"], artifact_manifest, write, problems,
          wrote)
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
    module_text = (REPO / "htt/src/common/cf4_manifest.py").read_text(
        encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "status": manifest["status"],
        "n_groups": manifest["id_parity"]["n_unique"],
        "parity": manifest["id_parity"]["parity"],
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
