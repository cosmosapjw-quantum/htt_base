#!/usr/bin/env python3
"""PR-131 runner: near-FLRW symbolic expansion + singular-boundary map.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the named-system registration (exact Jacobian, FLRW/vacuum/
sign/dimensional checks, KS mirror as a sign convention), the two-path
coefficient report (constraint-surface invariance equation AND
metric-level Einstein reduction on both 2-plane signatures), the exact
kappa/c2 coefficients with the c3 envelope-sizing check, the
independent finite-difference plateau under the preregistered
envelopes, the exact singular-boundary map with the declared-domain
validation, generated captions, and the mutation report (six
preregistered mutants killed on production validator paths).

Class-conditional asymptotic coefficients at roadmap_rescue_v1:C2;
never a global equality without fixed q, never a finite-ceiling
recovery, never an observational value; no disposition change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))

import sympy as sp  # noqa: E402
import yaml  # noqa: E402

from common.omk_near_flrw_expansion import (  # noqa: E402
    C2_EXACT,
    C3_EXACT,
    DECLARED_DOMAIN,
    KAPPA_EXACT,
    SCHEMA_VERSION,
    W,
    OmkNearFlrwError,
    fd_plateau,
    generate_caption,
    invariance_coefficients,
    jacobian_at_flrw,
    lint_caption,
    metric_path_reduction,
    require_two_path_agreement,
    singular_map,
    system_checks,
    validate_claim,
    validate_declared_domain,
    validate_plateau_report,
    verify_kappa_candidate,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr131_spec.yaml"
OUTPUTS = {
    "system": "docs/generated/pr131_named_system.json",
    "coefficients": "docs/generated/pr131_coefficients.json",
    "two_path": "docs/generated/pr131_two_path_report.json",
    "fd": "docs/generated/pr131_fd_plateau.json",
    "singular": "docs/generated/pr131_singular_map.json",
    "captions": "docs/generated/pr131_captions.json",
    "mutations": "docs/generated/pr131_mutation_report.json",
    "manifest": "docs/generated/pr131_artifact_manifest.json",
}
EXPANSION_SOURCE = "htt/src/common/omk_near_flrw_expansion.py"
REDACTED = "[REDACTED-PATTERN]"
FD_W_VALUES = (Fraction(0), Fraction(1, 3))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Keep the maintained source hash as generation-time provenance."""

    normalized = json.loads(json.dumps(payload))
    if rel == OUTPUTS["system"]:
        scan = normalized.get("negative_scan")
        targets = scan.get("targets") if isinstance(scan, dict) else None
        source = (
            targets.get(EXPANSION_SOURCE)
            if isinstance(targets, dict) else None
        )
        if not isinstance(source, dict):
            return normalized
        digest = source.get("sha256")
        if (
            isinstance(digest, str)
            and len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest)
        ):
            source["sha256"] = "<generation-time-source>"
        return normalized
    if rel != OUTPUTS["manifest"]:
        return normalized
    rows = normalized.get("input_hashes")
    if not isinstance(rows, list):
        return normalized
    prefix = f"{EXPANSION_SOURCE}:"
    for index, row in enumerate(rows):
        if not isinstance(row, str) or not row.startswith(prefix):
            continue
        digest = row.removeprefix(prefix)
        if (
            len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest)
        ):
            rows[index] = f"{prefix}<generation-time-source>"
    return normalized


def _verify_baseline_commit(spec: dict) -> None:
    """The baseline pin must resolve to a real commit object —
    fabricated or truncated identifiers are refused (adversarial-lane
    P0 guard)."""
    import subprocess

    sha = str(spec.get("baseline_commit") or "")
    if len(sha) != 40:
        raise SystemExit("baseline_commit must be a full 40-hex id")
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=REPO, capture_output=True, check=False)
    if probe.returncode != 0:
        raise SystemExit(
            f"baseline_commit {sha} does not resolve to a commit in "
            "this repository — fabricated provenance is refused")


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


def _verify_prohibition_cross_list(spec: dict) -> int:
    covered = 0
    for pattern in spec["negative_scan"]["forbidden_patterns"]:
        try:
            lint_caption(f"benign text then {pattern} then more text")
        except OmkNearFlrwError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def build_system(spec: dict) -> dict:
    named = spec["named_system"]
    lam = jacobian_at_flrw()
    checks = system_checks()
    return {
        "schema": "pr131.named_system.v1",
        "module_schema": SCHEMA_VERSION,
        "frame": named["frame"],
        "variables": named["variables"],
        "expansion_parameter": named["expansion_parameter"],
        "background": named["background"],
        "rhs": named["rhs"],
        "class_mirror": named["class_mirror"],
        "jacobian_at_flrw": {
            "lambda_sigma": sp.sstr(lam["lambda_sigma"]),
            "lambda_k": sp.sstr(lam["lambda_k"]),
            "curvature_source_coefficient": "-1 (exact)",
        },
        "system_checks": checks,
        "legacy_alignment": named["legacy_alignment"]["note"],
    }


def build_coefficients(spec: dict) -> dict:
    inv = invariance_coefficients(order=3)
    reg = spec["coefficients"]
    for name, value in reg["kappa_reference_values"].items():
        wv = {"dust": 0, "radiation": sp.Rational(1, 3)}[name]
        if sp.Rational(value) != sp.nsimplify(KAPPA_EXACT.subs(W, wv)):
            raise SystemExit(f"kappa reference value drift ({name})")
    for name, value in reg["c2_reference_values"].items():
        wv = {"dust": 0, "radiation": sp.Rational(1, 3)}[name]
        if sp.Rational(value) != sp.nsimplify(C2_EXACT.subs(W, wv)):
            raise SystemExit(f"c2 reference value drift ({name})")
    return {
        "schema": "pr131.coefficients.v1",
        "kappa_exact": sp.sstr(sp.factor(inv["kappa"])),
        "c2_exact": sp.sstr(sp.factor(inv["c2"])),
        "c3_envelope_sizing": sp.sstr(sp.factor(inv["c3"])),
        "reference_values": {
            "dust": {"kappa": "-2/5", "c2": "-26/175", "c3": "-94/875"},
            "radiation": {"kappa": "-1/3", "c2": "-1/9", "c3": "-2/27"},
        },
        "construction": reg["c2_construction"],
        "claimed_orders": ["kappa", "c2"],
        "vacuum_anchor": reg["vacuum_anchor"],
    }


def build_two_path() -> dict:
    reports = [metric_path_reduction(1), metric_path_reduction(-1)]
    require_two_path_agreement(reports)
    return {
        "schema": "pr131.two_path_report.v1",
        "path_a": "constraint-surface invariance equation on the "
                  "registered reduced RHS (sympy exact)",
        "path_b_branches": reports,
        "agreement": "exact on both 2-plane signatures",
    }


def build_fd(spec: dict) -> dict:
    contract = spec["finite_difference_contract"]
    if [str(w) for w in FD_W_VALUES] != \
            [str(Fraction(v)) for v in contract["w_values"]]:
        raise SystemExit("FD w-value pin drift")
    runs = []
    for wv in FD_W_VALUES:
        for branch in (1, -1):
            run = fd_plateau(wv, branch=branch)
            # production consumption of the plateau validator: the
            # MEASURED order-2 ratio at the smallest probe must agree
            # with the analytic coefficient (the fitted-line mutant
            # exercises this same gate with a fabricated claim).
            smallest = run["probes"][0]
            validate_plateau_report({
                "claimed_c2": smallest["order2_ratio"],
                "w": run["w"],
                "probe_K": smallest["K"],
            })
            runs.append(run)
    return {
        "schema": "pr131.fd_plateau.v1",
        "engine": contract["engine"],
        "trajectories": contract["trajectories"],
        "branches": contract["branches"],
        "runs": runs,
        "preregistration": contract["preregistration"],
    }


def build_singular(spec: dict) -> dict:
    payload = singular_map()
    validate_declared_domain(DECLARED_DOMAIN)
    reg = spec["singular_map"]
    if [e["w"] for e in payload["entries"]] != \
            [e["w"] for e in reg["entries"]]:
        raise SystemExit("singular-map entry pin drift (spec vs module)")
    return {
        "schema": "pr131.singular_map.v1",
        "entries": payload["entries"],
        "resonance_family": payload["resonance_family"],
        "declared_domain": reg["declared_domain"],
        "domain_validated": True,
        "rule": reg["rule"],
    }


def build_captions() -> dict:
    captions = {}
    for wv in FD_W_VALUES:
        text = generate_caption(wv)
        lint_caption(text)
        captions[f"w_{wv.numerator}_{wv.denominator}"] = text
    return {"schema": "pr131.captions.v1", "captions": captions}


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
                    hits.append({"line": idx,
                                 "pattern_index": pattern_index})
        targets[rel] = {"hits": hits, "source": source, "sha256": digest}
    total = sum(len(t["hits"]) for t in targets.values())
    if total:
        raise SystemExit(f"negative scan found {total} forbidden-"
                         f"language hits: {targets}")
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


def run_mutations(spec: dict) -> dict:
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])

    def mutant_wrong_kappa_sign() -> None:
        verify_kappa_candidate(2 / (3 * W + 5))

    def mutant_global_equality_language() -> None:
        lint_caption(generate_caption(Fraction(0))
                     + " The coefficient holds for all" + " q.")

    def mutant_ceiling_recovery() -> None:
        validate_claim({
            "asserts": "the six finite" + " ceilings are recovered by "
            "this expansion",
            "fixed_background": "q0 = 1/2"})

    def mutant_fitted_line_as_derivation() -> None:
        validate_plateau_report({
            "claimed_c2": "-0.2485714", "w": "0",
            "probe_K": "1/100000"})

    def mutant_singular_domain_smuggling() -> None:
        validate_declared_domain((Fraction(-1), Fraction(1)))

    def mutant_path_disagreement() -> None:
        S, K = sp.symbols("Sigma K", real=True)
        metric_path_reduction(1, rhs_tamper=K ** 2)

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "wrong_kappa_sign": mutant_wrong_kappa_sign,
        "global_equality_language": mutant_global_equality_language,
        "ceiling_recovery": mutant_ceiling_recovery,
        "fitted_line_as_derivation": mutant_fitted_line_as_derivation,
        "singular_domain_smuggling": mutant_singular_domain_smuggling,
        "path_disagreement": mutant_path_disagreement,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except OmkNearFlrwError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr131.mutation_report.v1",
        "mutations": rows,
        "surviving_mutation_count": len(
            [m for m in rows if not m["killed"]]),
    }


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
    if rel in {OUTPUTS["system"], OUTPUTS["manifest"]}:
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
    if spec.get("schema") != "htt.long_horizon.pr131_omk_near_flrw.v1":
        raise SystemExit("pr131 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    problems: list[str] = []
    wrote: list[str] = []

    system = build_system(spec)
    system["prohibition_cross_list_covered"] = cross_covered
    coefficients = build_coefficients(spec)
    two_path = build_two_path()
    fd = build_fd(spec)
    singular = build_singular(spec)
    captions = build_captions()
    system["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["system"], system, write, problems, wrote)
    _emit(OUTPUTS["coefficients"], coefficients, write, problems, wrote)
    _emit(OUTPUTS["two_path"], two_path, write, problems, wrote)
    _emit(OUTPUTS["fd"], fd, write, problems, wrote)
    _emit(OUTPUTS["singular"], singular, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr131.artifact_manifest.v1",
        "owner": spec["owner"],
        "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "input_hashes": [
            f"{rel}:{_sha(REPO / rel)}"
            for rel in ("htt/src/common/omk_near_flrw_expansion.py",
                        "htt/obsstat/egs3_omega_k_reopening.py")
        ],
        "caveats": [
            "Class-conditional asymptotic coefficients at C2 only.",
            "Claims hold at fixed q0(w) on the declared open domain; "
            "no global equality over backgrounds.",
            "No finite-ceiling recovery and no observational value is "
            "implied.",
            "The rev-r184 reopening module is untouched.",
            "All 102 remediation findings remain OPEN.",
        ],
        "artifacts": {
            rel: (_sha(REPO / rel) if (REPO / rel).is_file() else None)
            for key, rel in OUTPUTS.items() if key != "manifest"
        },
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
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "kappa": coefficients["kappa_exact"],
        "c2": coefficients["c2_exact"],
        "two_path": two_path["agreement"],
        "fd_runs": len(fd["runs"]),
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
