#!/usr/bin/env python3
"""PR-132 runner: interval remainder certification + uncertainty
propagation.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the trapping-region certificate (conclusive exact-Fraction
interval branch-and-bound on all four boundary conditions, both
branches), the compact domain API record (out-of-domain refusal,
expansion refusal, shrink versioning), the component-separated
uncertainty budget with downstream ceiling propagation, the boundary
adversarial states (8 corner states accepted, out-of-trap states
claim-blocked, every PR-131 FD probe verified in-trap), generated
captions, and the mutation report (six preregistered mutants killed on
production validator paths).

Class-conditional asymptotic theorem with explicit remainder at
roadmap_rescue_v1:C2; wide bounds are a success condition; no
disposition change.
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

import yaml  # noqa: E402

from common.omk_remainder_certificate import (  # noqa: E402
    DOMAIN_VERSION,
    K_ABS_MAX,
    M_TRAP,
    REGISTERED_DOMAIN,
    SCHEMA_VERSION,
    W_BOX,
    ClaimBlockError,
    OmkRemainderError,
    build_budget,
    central_prediction,
    check_admissible_state,
    enclosure,
    generate_caption,
    lint_caption,
    propagate_to_ceiling,
    prove_trapping_certificate,
    register_domain,
    validate_budget,
    validate_certificate_method,
    validate_report_central,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr132_spec.yaml"
OUTPUTS = {
    "certificate": "docs/generated/pr132_trapping_certificate.json",
    "domain": "docs/generated/pr132_domain_api.json",
    "budget": "docs/generated/pr132_uncertainty_budget.json",
    "boundary": "docs/generated/pr132_boundary_states.json",
    "captions": "docs/generated/pr132_captions.json",
    "mutations": "docs/generated/pr132_mutation_report.json",
    "manifest": "docs/generated/pr132_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"
REFERENCE_STATES = ((Fraction(0), Fraction(1, 100)),
                    (Fraction(1, 3), Fraction(-1, 100)))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


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
        except OmkRemainderError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def build_certificate(spec: dict) -> dict:
    reg = spec["trapping_certificate"]
    if Fraction(reg["M_exact"]) != M_TRAP:
        raise SystemExit("trap constant pin drift (spec vs module)")
    if [Fraction(v) for v in spec["compact_domain"]["w_box"]] != \
            list(W_BOX) or \
            Fraction(spec["compact_domain"]["k_abs_max"]) != K_ABS_MAX:
        raise SystemExit("compact domain pin drift (spec vs module)")
    cert = prove_trapping_certificate()
    validate_certificate_method(cert)   # positive control
    return {
        "schema": "pr132.trapping_certificate.v1",
        "module_schema": SCHEMA_VERSION,
        "statement": reg["statement"],
        "proof_method": reg["proof_method"],
        "transient_note": reg["transient_note"],
        "numeric_corroboration": reg["numeric_corroboration"],
        "certificate": cert,
    }


def build_domain_api(spec: dict) -> dict:
    exercised = {"out_of_domain_refused": False,
                 "expansion_refused": False,
                 "same_version_shrink_refused": False,
                 "versioned_shrink_accepted": False}
    try:
        enclosure(Fraction(0), Fraction(1, 5))
    except OmkRemainderError:
        exercised["out_of_domain_refused"] = True
    try:
        register_domain("omk_domain_v2", Fraction(0), Fraction(1),
                        K_ABS_MAX)
    except OmkRemainderError:
        exercised["expansion_refused"] = True
    try:
        register_domain(DOMAIN_VERSION, Fraction(0), Fraction(1, 3),
                        K_ABS_MAX)
    except OmkRemainderError:
        exercised["same_version_shrink_refused"] = True
    shrunk = register_domain("omk_domain_v1_shrink_demo", Fraction(0),
                             Fraction(1, 3), Fraction(1, 20))
    exercised["versioned_shrink_accepted"] = \
        shrunk.version == "omk_domain_v1_shrink_demo"
    if not all(exercised.values()):
        raise SystemExit(f"domain API exercises incomplete: {exercised}")
    return {
        "schema": "pr132.domain_api.v1",
        "registered_version": DOMAIN_VERSION,
        "w_box": [str(W_BOX[0]), str(W_BOX[1])],
        "k_abs_max": str(K_ABS_MAX),
        "branches": "both",
        "api_rule": spec["compact_domain"]["api_rule"],
        "exercises": exercised,
    }


def build_budget_report(spec: dict) -> dict:
    rows = []
    for w, k in REFERENCE_STATES:
        budget = build_budget(w, k)
        payload = budget.as_payload()
        validate_budget(payload)
        propagation = propagate_to_ceiling(w, k)
        validate_report_central({
            "w": propagation["w"], "K": propagation["K"],
            "central": propagation["central"]})
        rows.append(propagation)
    return {
        "schema": "pr132.uncertainty_budget.v1",
        "separation_rule": spec["uncertainty_components"][
            "separation_rule"],
        "central_value_rule": spec["uncertainty_components"][
            "central_value_rule"],
        "downstream_rule": spec["uncertainty_components"][
            "downstream_rule"],
        "reference_propagations": rows,
    }


def build_boundary_states() -> dict:
    accepted = []
    for w in (W_BOX[0], W_BOX[1]):
        for k in (K_ABS_MAX, -K_ABS_MAX):
            central = central_prediction(w, k)
            radius = M_TRAP * abs(Fraction(k)) ** 3
            for side, sigma in (("upper", central + radius),
                                ("lower", central - radius)):
                check_admissible_state(w, k, sigma)
                accepted.append({"w": str(w), "K": str(k),
                                 "side": side, "sigma": str(sigma),
                                 "accepted": True})
    blocked = 0
    for w in (W_BOX[0], W_BOX[1]):
        for k in (K_ABS_MAX, -K_ABS_MAX):
            central = central_prediction(w, k)
            escape = central + M_TRAP * abs(Fraction(k)) ** 3 \
                + Fraction(1, 10 ** 9)
            try:
                check_admissible_state(w, k, escape)
            except ClaimBlockError:
                blocked += 1
    if blocked != 4:
        raise SystemExit("out-of-trap boundary states not all blocked")

    fd = json.loads(
        (REPO / "docs/generated/pr131_fd_plateau.json")
        .read_text(encoding="utf-8"))
    probes_checked = 0
    for run in fd["runs"]:
        w = Fraction(run["w"])
        branch = 1 if run["branch"] == "biii_K_positive" else -1
        for probe in run["probes"]:
            k = Fraction(probe["K"]) * branch
            sigma = Fraction(probe["sigma_over_k"]) * k
            check_admissible_state(w, k, sigma)
            probes_checked += 1
    return {
        "schema": "pr132.boundary_states.v1",
        "corner_states_accepted": accepted,
        "out_of_trap_states_blocked": blocked,
        "pr131_fd_probes_in_trap": probes_checked,
        "cross_artifact_source": "docs/generated/pr131_fd_plateau.json",
    }


def build_captions() -> dict:
    captions = {}
    for w, k in REFERENCE_STATES:
        text = generate_caption(w, k)
        lint_caption(text)
        captions[f"w_{w.numerator}_{w.denominator}"
                 f"_K_{k.numerator}_{k.denominator}"] = text
    return {"schema": "pr132.captions.v1", "captions": captions}


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

    def mutant_grid_sampling_as_uniform_proof() -> None:
        validate_certificate_method({
            "method": "finite_grid_evaluation",
            "grid_sampling_used": True})

    def mutant_remainder_absorbed_into_central() -> None:
        validate_report_central({
            "w": "0", "K": "1/100",
            "central": str(central_prediction(Fraction(0),
                                              Fraction(1, 100))
                           + Fraction(1, 10 ** 6))})

    def mutant_posthoc_domain_expansion() -> None:
        try:
            enclosure(Fraction(0), Fraction(1, 5))
        except OmkRemainderError:
            pass
        else:
            raise AssertionError("out-of-domain evaluation survived")
        register_domain("omk_domain_v2_wide", Fraction(0), Fraction(1),
                        K_ABS_MAX)

    def mutant_enclosure_escape_claim_block() -> None:
        check_admissible_state(Fraction(0), Fraction(1, 100),
                               Fraction(1))

    def mutant_component_collapse() -> None:
        payload = build_budget(Fraction(0), Fraction(1, 100)).as_payload()
        payload["collapsed_single_number"] = "0.001"
        validate_budget(payload)

    def mutant_wrong_trap_constant() -> None:
        prove_trapping_certificate(Fraction(1, 100))

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "grid_sampling_as_uniform_proof":
            mutant_grid_sampling_as_uniform_proof,
        "remainder_absorbed_into_central":
            mutant_remainder_absorbed_into_central,
        "posthoc_domain_expansion": mutant_posthoc_domain_expansion,
        "enclosure_escape_claim_block":
            mutant_enclosure_escape_claim_block,
        "component_collapse": mutant_component_collapse,
        "wrong_trap_constant": mutant_wrong_trap_constant,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except OmkRemainderError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr132.mutation_report.v1",
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
    elif target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != \
            "htt.long_horizon.pr132_remainder_certification.v1":
        raise SystemExit("pr132 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    problems: list[str] = []
    wrote: list[str] = []

    certificate = build_certificate(spec)
    certificate["prohibition_cross_list_covered"] = cross_covered
    domain = build_domain_api(spec)
    budget = build_budget_report(spec)
    boundary = build_boundary_states()
    captions = build_captions()
    certificate["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["certificate"], certificate, write, problems, wrote)
    _emit(OUTPUTS["domain"], domain, write, problems, wrote)
    _emit(OUTPUTS["budget"], budget, write, problems, wrote)
    _emit(OUTPUTS["boundary"], boundary, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr132.artifact_manifest.v1",
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
            for rel in ("htt/src/common/omk_remainder_certificate.py",
                        "htt/src/common/omk_near_flrw_expansion.py",
                        "docs/generated/pr131_fd_plateau.json")
        ],
        "caveats": [
            "Class-conditional theorem with explicit remainder at C2 "
            "only.",
            "Wide bounds are a success condition; the domain is never "
            "expanded post-hoc.",
            "Four uncertainty components stay separate; nothing is "
            "promoted to MES or observation.",
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
        "trap_M": str(M_TRAP),
        "boundaries_proved": len(
            certificate["certificate"]["boundaries"]),
        "fd_probes_in_trap": boundary["pr131_fd_probes_in_trap"],
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
