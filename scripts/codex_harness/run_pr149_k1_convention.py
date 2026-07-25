#!/usr/bin/env python3
"""PR-149 runner: Planck K1 canonical convention, mask, transfer path + the
TT BiPoSH odd-L diagonal structural-zero basis theorem.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the frozen convention contract, the structural-zero theorem (independent
Wigner-3j oracle), the real SMICA/Commander map convention checks (downgrade +
mask applied + reality/round-trip/rotation), the observed/null shared-pipeline
equality, the scan-family ledger, captions, and the six-mutant kill report.

Observable feature-extraction and basis-theorem mechanics at
roadmap_rescue_v1:C1--C2; no K1 detection or Bianchi-family claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))
warnings.filterwarnings("ignore")

import yaml  # noqa: E402

from obsstat.k1_convention_contract import (  # noqa: E402
    K1ConventionError,
    SCHEMA_VERSION,
    alm_convention_checks,
    canonical_convention_contract,
    generate_caption,
    lint_caption,
    load_downgrade_mask_alm,
    observed_null_shared_pipeline,
    refuse_k1_detection,
    refuse_mask_not_applied,
    refuse_odd_L_trials,
    refuse_raw_deletion_before_frozen,
    refuse_shared_null_hiding,
    refuse_stale_axis_discovery,
    scan_family_ledger,
    structural_zero_theorem,
    verify_convention_frozen,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr149_spec.yaml"
OUTPUTS = {
    "contract": "docs/generated/pr149_convention_contract.json",
    "theorem": "docs/generated/pr149_structural_zero_theorem.json",
    "map_checks": "docs/generated/pr149_map_convention_checks.json",
    "path_equality": "docs/generated/pr149_observed_null_path_equality.json",
    "ledger": "docs/generated/pr149_scan_family_ledger.json",
    "captions": "docs/generated/pr149_captions.json",
    "mutations": "docs/generated/pr149_mutation_report.json",
    "manifest": "docs/generated/pr149_artifact_manifest.json",
}
SOURCE_PATH = "htt/obsstat/k1_convention_contract.py"
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _round(obj):
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _round(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v) for v in obj]
    return obj


def _render(payload: dict) -> bytes:
    return (json.dumps(_round(payload), indent=2, ensure_ascii=False,
                       sort_keys=True) + "\n").encode()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Treat the maintained source hash as generation-time provenance."""

    normalized = json.loads(json.dumps(_round(payload)))
    if rel == OUTPUTS["contract"]:
        scan = normalized.get("negative_scan")
        targets = scan.get("targets") if isinstance(scan, dict) else None
        source = targets.get(SOURCE_PATH) if isinstance(targets, dict) else None
        if isinstance(source, dict) and _is_sha256(source.get("sha256")):
            source["sha256"] = "<generation-time-source>"
        return normalized
    if rel != OUTPUTS["manifest"]:
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
            rows[index] = f"{SOURCE_PATH}:<generation-time-source>"
    return normalized


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


def _paths(spec: dict) -> dict:
    d = spec["data_scope"]["raw_data_paths"]
    return {k: REPO / v for k, v in d.items()}


def build_reports(spec: dict):
    m = spec["model"]
    proc_nside = m["proc_nside"]
    lmax = m["lmax"]
    l_values = m["structural_zero_l_values"]
    tol = float(m["structural_zero_tolerance"])
    paths = _paths(spec)
    # anti-drift guards invoked LIVE with admissible input
    refuse_stale_axis_discovery("healpix_discovery_scan")
    refuse_mask_not_applied("mask_applied_on_map")
    refuse_shared_null_hiding("independent_oracle_checks")
    refuse_k1_detection("feature_extraction_only")
    refuse_odd_L_trials("structural_zero_no_trials")
    refuse_raw_deletion_before_frozen("frozen_then_pr150")

    contract = canonical_convention_contract(proc_nside=proc_nside, lmax=lmax)
    verify_convention_frozen(contract, "")
    contract_rec = {"schema": "pr149.convention_contract.v1",
                    "module_schema": SCHEMA_VERSION, **contract}

    theorem = {"schema": "pr149.structural_zero_theorem.v1",
               **structural_zero_theorem(l_values, tol=tol,
                                         seed=int(m["null_seed"]))}

    map_rows = []
    smica_alm = None
    for name in ("smica", "commander"):
        d = load_downgrade_mask_alm(paths[name], paths["mask_int"],
                                    proc_nside=proc_nside, lmax=lmax)
        if d["fsky"] <= 0.0:
            raise SystemExit(f"the {name} mask was not applied (fsky 0)")
        checks = alm_convention_checks(d["masked"], d["alm"],
                                       proc_nside=proc_nside, lmax=lmax)
        if not checks["wrong_phase_mutation_caught"]:
            raise SystemExit(f"the {name} rotation cross-check did not catch "
                             "the wrong-phase convention mutation")
        map_rows.append({"map": name, "fsky": d["fsky"], **checks})
        if name == "smica":
            smica_alm = d["alm"]
    map_checks = {"schema": "pr149.map_convention_checks.v1",
                  "proc_nside": proc_nside, "lmax": lmax, "maps": map_rows,
                  "note": "the real Planck maps are downgraded to the frozen "
                          "proc-nside and the frozen mask is APPLIED; reality "
                          "and round trip are internal self-consistency and the "
                          "map-space vs alm-space rotation cross-check is the "
                          "genuine convention test (a wrong-phase mutation is "
                          "caught)"}

    path_eq = {"schema": "pr149.observed_null_shared_pipeline.v1",
               **observed_null_shared_pipeline(smica_alm, proc_nside=proc_nside,
                                               lmax=lmax, l_values=l_values,
                                               null_seed=int(m["null_seed"]))}
    ledger = {"schema": "pr149.scan_family_ledger.v1",
              **scan_family_ledger(l_values=l_values,
                                   orientation_grid_n=m["orientation_grid_n"])}
    return contract_rec, theorem, map_checks, path_eq, ledger


def build_captions(theorem: dict, map_checks: dict, ledger: dict) -> dict:
    checks = map_checks["maps"][0]
    text = generate_caption(theorem, checks, ledger)
    lint_caption(text)
    return {"schema": "pr149.captions.v1", "captions": {"summary": text}}


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
        "stale_axis_discovery": lambda: refuse_stale_axis_discovery("hardcoded_axis"),
        "mask_not_applied": lambda: refuse_mask_not_applied("mask_hash_only"),
        "shared_null_hides_mutation":
            lambda: refuse_shared_null_hiding("shared_null_hides_mutation"),
        "k1_detection_claim": lambda: refuse_k1_detection("k1_detection"),
        "odd_L_diagonal_trials": lambda: refuse_odd_L_trials("odd_L_diagonal_trials"),
        "approve_raw_deletion_unfrozen":
            lambda: refuse_raw_deletion_before_frozen("approve_deletion_unfrozen"),
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
        except K1ConventionError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr149.mutation_report.v1", "mutations": rows,
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
        return
    if rel in {OUTPUTS["contract"], OUTPUTS["manifest"]}:
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
    if spec.get("schema") != "htt.long_horizon.pr149_k1_convention.v1":
        raise SystemExit("pr149 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    paths = _paths(spec)
    for name, p in paths.items():
        if not p.is_file():
            raise SystemExit(f"Planck {name} map absent — requires the read-"
                             "only external Planck PR3 data")
    problems: list[str] = []
    wrote: list[str] = []

    contract, theorem, map_checks, path_eq, ledger = build_reports(spec)
    captions = build_captions(theorem, map_checks, ledger)
    contract["negative_scan"] = {"targets": _scan_targets(spec, captions),
                                 "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["contract"], contract, write, problems, wrote)
    _emit(OUTPUTS["theorem"], theorem, write, problems, wrote)
    _emit(OUTPUTS["map_checks"], map_checks, write, problems, wrote)
    _emit(OUTPUTS["path_equality"], path_eq, write, problems, wrote)
    _emit(OUTPUTS["ledger"], ledger, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr149.artifact_manifest.v1",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {name: _sha(p) for name, p in paths.items()},
        "input_hashes": [f"htt/obsstat/k1_convention_contract.py:"
                         f"{_sha(REPO / 'htt/obsstat/k1_convention_contract.py')}"],
        "caveats": [
            "Observable feature-extraction and basis-theorem mechanics at "
            "C1--C2 only.",
            "The TT BiPoSH odd-L diagonal structural zero is proved by an "
            "independent Wigner-3j oracle; the odd-L diagonal carries no trials.",
            "Freezing the mask/proc-nside/convention pre-conditions the PR-150 "
            "raw-deletion swap; PR-149 makes no detection and no family claim.",
            "The two CF4 P0s are untouched and stay OPEN.",
            "No detection.",
            "All 102 remediation findings remain OPEN.",
        ],
        "artifacts": {rel: (_sha(REPO / rel) if (REPO / rel).is_file()
                            else None)
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
    module_text = (REPO / "htt/obsstat/k1_convention_contract.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "odd_L_all_zero": theorem["odd_L_diagonal_all_zero"],
        "effective_scan_family": ledger["effective_scan_family_size"],
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
