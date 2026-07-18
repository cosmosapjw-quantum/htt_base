#!/usr/bin/env python3
"""PR-153 runner: JWST authenticated-row, cross-match and calibration manifest.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the row-complete cited-seed anchor manifest, the authoritative-reproduction
decision, the probabilistic CF4 cross-match, the tolerance sensitivity, the
row-replay + leave-one-match + label-substitution negative tests, captions and
the six-mutant kill report.  The cross-match reads the real CF4 group catalogue
(``cf4_groups.npz``, ~5 MB) directly.

Because the authoritative machine-readable table is not reproducible, the JWST
lane stays a cited-seed catalogue-linkage scenario and no CF4-conditioned
forecast is authorized.  Catalogue-linkage diagnostic at roadmap_rescue_v1:C1;
no measurement, forecast, detection, or Bianchi-family claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
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

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr153_spec.yaml"
OUTPUTS = {
    "manifest_rows": "docs/generated/pr153_row_manifest.json",
    "decision": "docs/generated/pr153_authoritative_decision.json",
    "crossmatch": "docs/generated/pr153_crossmatch.json",
    "sensitivity": "docs/generated/pr153_sensitivity.json",
    "negatives": "docs/generated/pr153_negative_tests.json",
    "captions": "docs/generated/pr153_captions.json",
    "mutations": "docs/generated/pr153_mutation_report.json",
    "manifest": "docs/generated/pr153_artifact_manifest.json",
}
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


def build_reports(spec: dict):
    ds = spec["data_scope"]["raw_data_paths"]
    seed_path = REPO / ds["seed_csv"]
    fetch_path = REPO / ds["fetch_manifest"]
    cf4_path = REPO / ds["cf4_groups"]
    for p in (seed_path, cf4_path):
        if not p.is_file():
            raise SystemExit(f"required input absent: {p}")
    seed_rows = _load_seed(seed_path)
    fetch_manifest = (json.loads(fetch_path.read_text(encoding="utf-8"))
                      if fetch_path.is_file() else {})
    m = spec["model"]["match"]
    sigma = float(Fraction(m["position_sigma_deg"]))
    ambig = float(Fraction(m["ambiguity_ratio_threshold"]))
    tol_grid = [float(Fraction(t)) for t in m["tolerance_grid_deg"]]

    decision = authoritative_reproduction_decision(fetch_manifest)

    # anti-drift guards invoked LIVE with admissible input
    refuse_radius_only_identity("probabilistic_uncertainty_weighted")
    refuse_synthetic_renamed_observed("cited_seed_not_synthetic")
    refuse_authoritative_without_table(
        decision["authoritative_table_reproduced"], "cited_seed")
    refuse_cf4_forecast_downstream_open("catalogue_linkage_only")
    refuse_jwst_measurement("catalogue_linkage_diagnostic")
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
    return manifest_rows, decision_art, crossmatch, sensitivity, negatives


def build_captions(manifest_rows, decision, crossmatch, negatives) -> dict:
    text = generate_caption(manifest_rows, decision, crossmatch,
                            negatives["label_substitution"])
    lint_caption(text)
    return {"schema": "pr153.captions.v1", "captions": {"summary": text}}


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
            lambda: refuse_jwst_measurement("jwst_measurement"),
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
    if spec.get("schema") != "htt.long_horizon.pr153_jwst_anchor.v1":
        raise SystemExit("pr153 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    manifest_rows, decision, crossmatch, sensitivity, negatives = \
        build_reports(spec)
    captions = build_captions(manifest_rows, decision, crossmatch, negatives)
    decision["negative_scan"] = {"targets": _scan_targets(spec, captions),
                                 "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["manifest_rows"], manifest_rows, write, problems, wrote)
    _emit(OUTPUTS["decision"], decision, write, problems, wrote)
    _emit(OUTPUTS["crossmatch"], crossmatch, write, problems, wrote)
    _emit(OUTPUTS["sensitivity"], sensitivity, write, problems, wrote)
    _emit(OUTPUTS["negatives"], negatives, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr153.artifact_manifest.v1",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {
            "seed_csv_sha256": _sha(REPO / spec["data_scope"]["raw_data_paths"]["seed_csv"]),
            "cf4_groups_sha256": _sha(REPO / spec["data_scope"]["raw_data_paths"]["cf4_groups"])},
        "input_hashes": [f"htt/obsstat/jwst_anchor_manifest.py:"
                         f"{_sha(REPO / 'htt/obsstat/jwst_anchor_manifest.py')}"],
        "caveats": [
            "JWST cited-seed catalogue-linkage diagnostic at C1 only.",
            "The authoritative machine-readable table is not reproducible, so "
            "the anchors are cited-seed and the lane stays a cited-seed scenario.",
            "Identity is probabilistic and uncertainty-weighted, never a "
            "coordinate radius alone; the synthetic fixture is never renamed "
            "observed data.",
            "No CF4-conditioned precision forecast is authorized while "
            "N-DATA-CF4-DOWNSTREAM is OPEN.",
            "No JWST-level measurement, forecast, detection, or Bianchi-family "
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
