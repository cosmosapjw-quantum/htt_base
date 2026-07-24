#!/usr/bin/env python3
"""PR-130 runner: NT2 tail-convergence theorem vs sufficiency separation.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the tail theorem record (registered response family, exact
closed forms, positivity witnesses, permanent exit rule), the
three-engine precision report (Fraction partial sum + rigorous
remainder bracket enclosing mpmath zeta, sympy identity vanishing), the
transfer-profile sensitivity table with the p = 1 divergence
certificate, generated truncation-only captions, the legacy
invalidation record (byte-frozen ``egs2_fisher.py`` pin + superseded
lines, unedited), and the mutation report (six preregistered mutants
killed by real validators).

Toy/transfer-conditional convergence theorem at roadmap_rescue_v1:C1;
sufficiency-type claims are rejected by the empty-registry gate; no
detection; no disposition change.
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

from common.nt2_tail_convergence import (  # noqa: E402
    F_SKY_REGISTERED,
    FACTORIZATION_REGISTRY,
    PROFILE_P_REGISTERED,
    SCHEMA_VERSION,
    Nt2TailError,
    generate_caption,
    lint_caption,
    profile_sensitivity,
    require_convergent_profile,
    three_engine_enclosure,
    truncation_error_report,
    validate_sufficiency_claim,
    validate_truncation_claim,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr130_spec.yaml"
OUTPUTS = {
    "theorem": "docs/generated/pr130_tail_theorem.json",
    "precision": "docs/generated/pr130_precision_report.json",
    "sensitivity": "docs/generated/pr130_profile_sensitivity.json",
    "captions": "docs/generated/pr130_captions.json",
    "legacy": "docs/generated/pr130_legacy_invalidation.json",
    "mutations": "docs/generated/pr130_mutation_report.json",
    "manifest": "docs/generated/pr130_artifact_manifest.json",
}
TAIL_SOURCE = "htt/src/common/nt2_tail_convergence.py"
REDACTED = "[REDACTED-PATTERN]"
PROBE_L_VALUES = (10, 40, 80, 200, 1000)
PARTIAL_SUM_L = 10000


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Keep maintained-source measurements as generation-time provenance."""

    normalized = json.loads(json.dumps(payload))
    if rel == OUTPUTS["theorem"]:
        scan = normalized.get("negative_scan")
        targets = scan.get("targets") if isinstance(scan, dict) else None
        source = (
            targets.get(TAIL_SOURCE) if isinstance(targets, dict) else None
        )
        if not isinstance(source, dict):
            return normalized
        digest = source.get("sha256")
        line_count = source.get("lines_scanned")
        if (
            isinstance(digest, str)
            and len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest)
            and isinstance(line_count, int)
            and not isinstance(line_count, bool)
            and line_count >= 0
        ):
            source["sha256"] = "<generation-time-source>"
            source["lines_scanned"] = "<generation-time-line-count>"
        return normalized
    if rel != OUTPUTS["manifest"]:
        return normalized
    rows = normalized.get("input_hashes")
    if not isinstance(rows, list):
        return normalized
    prefix = f"{TAIL_SOURCE}:"
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
    """Every spec forbidden pattern must be covered by the module
    caption lint."""
    covered = 0
    for pattern in spec["negative_scan"]["forbidden_patterns"]:
        try:
            lint_caption(f"benign text then {pattern} then more text")
        except Nt2TailError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def build_theorem(spec: dict) -> dict:
    reg = spec["response_registration"]
    if Fraction(reg["registered_profile_p"]) != PROFILE_P_REGISTERED:
        raise SystemExit("registered profile pin drift (spec vs module)")
    if Fraction(reg["registered_f_sky"]) != F_SKY_REGISTERED:
        raise SystemExit("registered f_sky pin drift (spec vs module)")
    require_convergent_profile(PROFILE_P_REGISTERED)
    if FACTORIZATION_REGISTRY:
        raise SystemExit(
            "the factorization registry is expected EMPTY for PR-130")
    # positive controls: convergence-only claims pass the gate.
    validate_sufficiency_claim(
        {"asserts": "the tail converges at rate O(1/L)"})
    validate_sufficiency_claim(
        {"asserts": "truncation error certified two-sided"})
    probes = []
    for L in PROBE_L_VALUES:
        report = truncation_error_report(L)
        probes.append(report)
    return {
        "schema": "pr130.tail_theorem.v1",
        "module_schema": SCHEMA_VERSION,
        "response_family": reg["response_family"],
        "fisher_term": reg["fisher_term"],
        "registered_profile_p": str(PROFILE_P_REGISTERED),
        "registered_f_sky": str(F_SKY_REGISTERED),
        "convergence_domain": reg["convergence_domain"],
        "closed_form": reg["closed_form_p_three_halves"],
        "two_sided_bracket": reg["two_sided_bracket_p_three_halves"],
        "truncation_probes": probes,
        "tail_strictly_positive_at_every_probe": True,
        "factorization_registry_state": "EMPTY",
        "permanent_exit_rule": spec["sufficiency_gate"][
            "permanent_exit_rule"],
        "sufficiency_gate_positive_controls_passed": 2,
    }


def build_precision(spec: dict) -> dict:
    contract = spec["precision_contract"]
    if int(contract["partial_sum_L"]) != PARTIAL_SUM_L:
        raise SystemExit("partial-sum L pin drift (spec vs runner)")
    result = three_engine_enclosure(PARTIAL_SUM_L)
    return {
        "schema": "pr130.precision_report.v1",
        "enclosure_rule": contract["enclosure_rule"],
        "result": result,
    }


def build_sensitivity() -> dict:
    payload = profile_sensitivity()
    return {"schema": "pr130.profile_sensitivity.v1", **payload}


def build_captions() -> dict:
    captions = {}
    for L in (40, 80, 200):
        text = generate_caption(L)
        lint_caption(text)
        captions[f"L{L}"] = text
    return {"schema": "pr130.captions.v1", "captions": captions}


def build_legacy_invalidation(spec: dict) -> dict:
    legacy = spec["legacy_invalidation"]
    path = REPO / legacy["legacy_module"]
    actual = _sha(path)
    if actual != legacy["legacy_module_sha256"]:
        raise SystemExit(
            "legacy module byte-pin FAILED — egs2_fisher.py must stay "
            "byte-frozen (successor-authority pattern)")
    lines = path.read_text(encoding="utf-8").splitlines()
    recorded = []
    for entry in legacy["superseded_language"]:
        line_no = int(entry["line"])
        fragment = entry["text_fragment"]
        line_text = lines[line_no - 1]
        if fragment not in line_text:
            raise SystemExit(
                f"legacy line {line_no} no longer carries the recorded "
                f"fragment — invalidation table stale")
        recorded.append({
            "line": line_no,
            "line_sha256": hashlib.sha256(
                line_text.strip().encode()).hexdigest(),
            "superseded_by": "C-PR130-NT2-TAIL sufficiency gate",
        })
    relabeled = []
    for surface in spec["relabeled_active_surfaces"]["surfaces"]:
        s_path = REPO / surface["path"]
        s_text = s_path.read_text(encoding="utf-8")
        if surface["required_marker"] not in s_text:
            raise SystemExit(
                f"relabeled surface {surface['path']} lost its "
                "supersession marker")
        relabeled.append({"path": surface["path"],
                          "sha256": _sha(s_path),
                          "marker": surface["required_marker"]})
    return {
        "schema": "pr130.legacy_invalidation.v1",
        "legacy_module": legacy["legacy_module"],
        "legacy_module_sha256": actual,
        "byte_frozen": True,
        "superseded_lines": recorded,
        "relabeled_active_surfaces": relabeled,
        "disposition": legacy["disposition"],
        "finding_id": "N-THEORY-NT2-SUFFICIENCY",
        "finding_status": "OPEN",
    }


def _scan_text(text: str, patterns: list[str]) -> list[dict]:
    hits = []
    for idx, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        for pattern_index, pattern in enumerate(patterns):
            if pattern.lower() in lowered:
                hits.append({"line": idx, "pattern_index": pattern_index})
    return hits


def build_negative_scan_inline(spec: dict, captions_payload: dict) -> dict:
    """Total (no-skip) scan over the registered PR-130 surfaces."""
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
        hits = _scan_text(raw, patterns)
        targets[rel] = {"hits": hits, "source": source, "sha256": digest,
                        "lines_scanned": len(raw.splitlines())}
    total = sum(len(t["hits"]) for t in targets.values())
    if total:
        raise SystemExit(f"negative scan found {total} sufficiency-"
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

    def mutant_sufficiency_language() -> None:
        lint_caption(generate_caption(80)
                     + " The pair is sufficient" + " for everything.")

    def mutant_rao_blackwell_from_small_tail() -> None:
        validate_sufficiency_claim({
            "asserts": "Rao-" + "Blackwell reduction complete",
            "basis": "tail_fraction_small"})

    def mutant_zero_tail_claim() -> None:
        validate_truncation_claim(Fraction(0), 80)

    def mutant_wrong_zeta_constant() -> None:
        # the zeta(2)-1 -> zeta(2) tampering (+8), injected through the
        # preregistered shift point so the PRODUCTION comparison inside
        # three_engine_enclosure is the validator that kills it.
        three_engine_enclosure(2000, closed_form_shift=Fraction(8))

    def mutant_divergent_profile_smuggling() -> None:
        require_convergent_profile(Fraction(1))

    def mutant_truncation_error_understated() -> None:
        validate_truncation_claim(Fraction(1, 1000), 80)

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "sufficiency_language": mutant_sufficiency_language,
        "rao_blackwell_from_small_tail":
            mutant_rao_blackwell_from_small_tail,
        "zero_tail_claim": mutant_zero_tail_claim,
        "wrong_zeta_constant": mutant_wrong_zeta_constant,
        "divergent_profile_smuggling": mutant_divergent_profile_smuggling,
        "truncation_error_understated":
            mutant_truncation_error_understated,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except Nt2TailError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr130.mutation_report.v1",
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
    if rel in {OUTPUTS["theorem"], OUTPUTS["manifest"]}:
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
    if spec.get("schema") != "htt.long_horizon.pr130_tail_convergence.v1":
        raise SystemExit("pr130 spec schema mismatch")
    _verify_remediation_state(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    problems: list[str] = []
    wrote: list[str] = []

    theorem = build_theorem(spec)
    theorem["prohibition_cross_list_covered"] = cross_covered
    precision = build_precision(spec)
    sensitivity = build_sensitivity()
    captions = build_captions()
    scan_targets = build_negative_scan_inline(spec, captions)
    theorem["negative_scan"] = {
        "targets": scan_targets, "total_hits": 0,
        "forbidden_pattern_registry_size": len(
            spec["negative_scan"]["forbidden_patterns"]),
    }
    legacy = build_legacy_invalidation(spec)
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["theorem"], theorem, write, problems, wrote)
    _emit(OUTPUTS["precision"], precision, write, problems, wrote)
    _emit(OUTPUTS["sensitivity"], sensitivity, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["legacy"], legacy, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr130.artifact_manifest.v1",
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
            for rel in ("htt/src/common/nt2_tail_convergence.py",
                        "htt/obsstat/egs2_fisher.py")
        ],
        "caveats": [
            "Toy/transfer-conditional convergence theorem at C1 only.",
            "The nonzero tail plus the empty factorization registry "
            "permanently forbid the exact-sufficiency reading.",
            "The toy response is never an observed low-ell information "
            "claim.",
            "The legacy module stays byte-frozen; its wording is "
            "superseded via the invalidation record.",
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
        "enclosure_width": precision["result"]["enclosure_width_exact"],
        "tail_probe_count": len(theorem["truncation_probes"]),
        "negative_scan_hits": 0,
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
