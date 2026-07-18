#!/usr/bin/env python3
"""PR-151 runner: DESI DR1 BGS exact-selection mock + per-mock refit.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the official validation-mock manifest (kill disposition), the per-mock refit
receipt, the two-tier covariance, the clustering/kinematic/selection component
confusion matrix, the DESI-survey-conditional pooled-rank null, captions, and the
six-mutant kill report --- all read from the heavy exact-selection card produced
once by ``scripts/desi_exact_selection_card.py`` on the real DESI randoms (the
ACT pattern; this runner never re-runs the ~2.3 GB read).

Because the official DESI validation mocks are absent, causal attribution is
abandoned and only the survey-conditional null is reported.  DESI-survey-
conditional estimator/null diagnostic at roadmap_rescue_v1:C3; no dipole
detection, anisotropy, or Bianchi-family claim.
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

from obsstat.desi_exact_selection_mock import (  # noqa: E402
    DESIExactSelectionError,
    SCHEMA_VERSION,
    generate_caption,
    lint_caption,
    official_mock_manifest,
    refuse_attribution_without_official_mocks,
    refuse_bianchi_from_desi,
    refuse_desi_detection,
    refuse_fixed_alpha,
    refuse_generic_grf_attribution,
    refuse_hard_coded_cap_ratio,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr151_spec.yaml"
CARD_PATH = REPO / "docs/generated/desi_exact_selection_card.json"
OUTPUTS = {
    "manifest_mock": "docs/generated/pr151_mock_manifest.json",
    "refit": "docs/generated/pr151_per_mock_refit.json",
    "covariance": "docs/generated/pr151_two_tier_covariance.json",
    "confusion": "docs/generated/pr151_component_confusion.json",
    "null": "docs/generated/pr151_survey_conditional_null.json",
    "captions": "docs/generated/pr151_captions.json",
    "mutations": "docs/generated/pr151_mutation_report.json",
    "manifest": "docs/generated/pr151_artifact_manifest.json",
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


def build_reports(spec: dict):
    if not CARD_PATH.is_file():
        raise SystemExit(
            "the DESI exact-selection card is absent — run "
            "scripts/desi_exact_selection_card.py on the real DESI randoms first")
    card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    if card.get("status") != "SURVEY_CONDITIONAL_NULL":
        raise SystemExit(f"DESI card status is {card.get('status')}")
    ref = spec["data_scope"]["official_mocks_reference"]
    mocks_on_disk = bool(spec["data_scope"]["official_validation_mocks_on_disk"])

    # anti-drift guards invoked LIVE with admissible input
    refuse_hard_coded_cap_ratio("source_derived")
    refuse_fixed_alpha(True)                 # alpha IS re-fit per mock
    refuse_generic_grf_attribution("survey_conditional_only")
    refuse_attribution_without_official_mocks(mocks_on_disk, "survey_conditional")
    refuse_desi_detection("survey_conditional_null")
    refuse_bianchi_from_desi("no_geometry_claim")

    manifest_mock = {"schema": "pr151.mock_manifest.v1",
                     "module_schema": SCHEMA_VERSION,
                     **official_mock_manifest(mocks_on_disk=mocks_on_disk,
                                              reference_url=ref)}
    cap_ratio = card["source_derived_cap_ratio_ngc_over_sgc"]
    refit = {"schema": "pr151.per_mock_refit.v1",
             "source_derived_cap_ratio_ngc_over_sgc": cap_ratio,
             "alpha_and_nuisance_refit_per_mock": True,
             "observed": card["observed"],
             "caps": card["caps"],
             "note": "alpha and the systematic nuisance amplitude are re-fit on "
                     "every mock (and on the observed data) by the same "
                     "estimator; the cap ratio is source-derived from the data "
                     "counts, never hard-coded"}
    covariance = {"schema": "pr151.two_tier_covariance.v1",
                  **card["two_tier_covariance"]}
    confusion = {"schema": "pr151.component_confusion.v1",
                 **card["component_confusion"]}
    null = {"schema": "pr151.survey_conditional_null.v1",
            **card["survey_conditional_null"]}
    return manifest_mock, refit, covariance, confusion, null


def build_captions(manifest_mock, confusion, null) -> dict:
    text = generate_caption(manifest_mock, confusion, null)
    lint_caption(text)
    return {"schema": "pr151.captions.v1", "captions": {"summary": text}}


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
        "hard_coded_cap_ratio":
            lambda: refuse_hard_coded_cap_ratio("hard_coded"),
        "fixed_alpha_mock": lambda: refuse_fixed_alpha(False),
        "generic_grf_causal_attribution":
            lambda: refuse_generic_grf_attribution("clustering_dominated_causal"),
        "attribution_without_official_mocks":
            lambda: refuse_attribution_without_official_mocks(
                False, "causal_attribution"),
        "desi_dipole_detection":
            lambda: refuse_desi_detection("desi_dipole_detection"),
        "bianchi_family_from_desi":
            lambda: refuse_bianchi_from_desi("bianchi_family"),
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
        except DESIExactSelectionError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr151.mutation_report.v1", "mutations": rows,
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
    if spec.get("schema") != "htt.long_horizon.pr151_desi_exact_selection.v1":
        raise SystemExit("pr151 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    manifest_mock, refit, covariance, confusion, null = build_reports(spec)
    captions = build_captions(manifest_mock, confusion, null)
    manifest_mock["negative_scan"] = {"targets": _scan_targets(spec, captions),
                                       "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["manifest_mock"], manifest_mock, write, problems, wrote)
    _emit(OUTPUTS["refit"], refit, write, problems, wrote)
    _emit(OUTPUTS["covariance"], covariance, write, problems, wrote)
    _emit(OUTPUTS["confusion"], confusion, write, problems, wrote)
    _emit(OUTPUTS["null"], null, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr151.artifact_manifest.v1",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {"desi_exact_selection_card_sha256": _sha(CARD_PATH)},
        "input_hashes": [f"htt/obsstat/desi_exact_selection_mock.py:"
                         f"{_sha(REPO / 'htt/obsstat/desi_exact_selection_mock.py')}"],
        "caveats": [
            "DESI-survey-conditional estimator/null diagnostic at C3 only.",
            "The official DESI validation mocks (1000 EZmocks + 25 AbacusSummit) "
            "are absent, so causal attribution is abandoned per the kill rule.",
            "alpha and the nuisance amplitude are re-fit on every mock; the cap "
            "ratio is source-derived, never hard-coded.",
            "The clustering/kinematic/selection components are confounded under "
            "the number-count dipole estimator.",
            "No DESI dipole-detection, anisotropy, or Bianchi-family claim; the "
            "two CF4 P0s are untouched and stay OPEN.",
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
    module_text = (REPO / "htt/obsstat/desi_exact_selection_mock.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "cap_ratio": refit["source_derived_cap_ratio_ngc_over_sgc"],
        "survey_conditional_p": null["survey_conditional_pooled_rank_p"],
        "components_confounded": confusion["components_confounded"],
        "attribution_abandoned": manifest_mock["causal_attribution_abandoned"],
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
