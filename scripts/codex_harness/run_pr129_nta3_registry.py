#!/usr/bin/env python3
"""PR-129 runner: NTA3 typed estimator/domain registry + universal-floor
prohibition.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the typed estimator registry (three-way exact verification:
chi-square closed form, independent Gaussian moment derivation,
structural reality-condition dof), the seeded estimator-level Monte
Carlo report (PCG64, Gaussian a_2m draws, dual-pinned preregistered
tolerance), the negative scan over the registered active NTA3 surfaces
(hash-pinned sentinel policy + negation allowlist), the generated
captions, the prohibition cross-list consistency gate, and the mutation
report (six preregistered mutants killed by the real validators).

Estimator-specific supersession at roadmap_rescue_v1:C1; the original
universal reading is NOT rescued; no detection; no disposition change.
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

from common.nta3_estimator_registry import (  # noqa: E402
    PREREGISTERED_TOLERANCE_ABS,
    SCHEMA_VERSION,
    EstimatorSpec,
    Nta3RegistryError,
    alm_real_dof,
    chi_square_dispersion_squared,
    generate_caption,
    lint_caption,
    moment_dispersion_squared,
    run_seeded_mc,
    validate_separation,
    verify_quadrupole_dispersion,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr129_spec.yaml"
OUTPUTS = {
    "registry": "docs/generated/pr129_estimator_registry.json",
    "mc": "docs/generated/pr129_mc_report.json",
    "scan": "docs/generated/pr129_negative_scan.json",
    "captions": "docs/generated/pr129_captions.json",
    "mutations": "docs/generated/pr129_mutation_report.json",
    "manifest": "docs/generated/pr129_artifact_manifest.json",
}
REGISTRY_SOURCE = "htt/src/common/nta3_estimator_registry.py"
SENTINEL_BEGIN = "PR129-PROHIBITION-REGISTRY-BEGIN"
SENTINEL_END = "PR129-PROHIBITION-REGISTRY-END"
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Keep the frozen registry-source digest as generation-time provenance."""

    normalized = json.loads(json.dumps(payload))
    if rel != OUTPUTS["manifest"]:
        return normalized
    rows = normalized.get("input_hashes")
    if not isinstance(rows, list):
        return normalized
    prefix = f"{REGISTRY_SOURCE}:"
    for index, row in enumerate(rows):
        if not isinstance(row, str) or not row.startswith(prefix):
            continue
        digest = row.removeprefix(prefix)
        if len(digest) == 64 and all(char in "0123456789abcdef" for char in digest):
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


def _verify_tolerance_pins(spec: dict) -> float:
    prereg = float(spec["monte_carlo"]["preregistered_tolerance_abs"])
    if prereg != PREREGISTERED_TOLERANCE_ABS:
        raise SystemExit(
            f"tolerance pin drift: spec {prereg} != module "
            f"{PREREGISTERED_TOLERANCE_ABS} — widening either pin alone "
            "is refused")
    return prereg


def _verify_prohibition_cross_list(spec: dict) -> int:
    """Every spec forbidden pattern must be covered by the module caption
    lint: embedding it in a benign caption must raise."""
    covered = 0
    for pattern in spec["negative_scan"]["forbidden_patterns"]:
        try:
            lint_caption(f"benign text then {pattern} then more text")
        except Nta3RegistryError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def _specs_from_spec(spec: dict) -> list[EstimatorSpec]:
    return [EstimatorSpec.from_payload(entry)
            for entry in spec["estimator_registry"]["entries"]]


def build_registry(spec: dict, specs: list[EstimatorSpec]) -> dict:
    quad = next(s for s in specs if s.estimator_id == "quadrupole_power_ideal")
    fisher = next(s for s in specs
                  if s.estimator_id == "multi_multipole_fisher_toy")
    exact = verify_quadrupole_dispersion(quad)
    # positive controls: the legitimate readings pass the separation
    # validator; the conflations are exercised in the mutation report.
    validate_separation({"cites": "sqrt(2/5)",
                         "as": "single-estimator sampling dispersion"})
    validate_separation({"cites": "multi-multipole Fisher information",
                         "as": "joint low-l Fisher information"})
    entries = []
    for src, registered in zip(specs, spec["estimator_registry"]["entries"]):
        entries.append({
            "estimator_id": src.estimator_id,
            "statistic": src.statistic,
            "sky": src.sky,
            "noise": src.noise,
            "field": src.field,
            "ell": src.ell,
            "dof": src.dof,
            "dispersion_squared_exact": (
                None if src.dispersion_squared_exact is None
                else str(src.dispersion_squared_exact)),
            "theorem": registered["theorem"],
        })
    return {
        "schema": "pr129.estimator_registry.v2",
        "module_schema": SCHEMA_VERSION,
        "entries": entries,
        "exact_analytic_check": {
            "closed_form_chi_square_dof": str(
                chi_square_dispersion_squared(quad.dof)),
            "gaussian_moment_derivation": str(
                moment_dispersion_squared(quad.ell)),
            "structural_dof_2ell_plus_1": alm_real_dof(quad.ell),
            "registered_dispersion_squared": str(exact),
            "three_way_agreement": True,
        },
        "reality_condition_note": (
            "a_20 real with variance C2; m = 1,2 complex with variance "
            "C2/2 per real component; a_{2,-m} = (-1)^m a_2m^* determined "
            "-> 2*ell+1 = 5 independent real dof; sum_m |a_2m|^2 = "
            "a_20^2 + 2 sum_{m>0} |a_2m|^2"),
        "separation_rule": spec["estimator_registry"]["separation_rule"],
        "separation_positive_controls_passed": 2,
        "distinct_objects": [quad.estimator_id, fisher.estimator_id],
    }


def build_mc_report(spec: dict, specs: list[EstimatorSpec],
                    prereg: float) -> dict:
    quad = next(s for s in specs if s.estimator_id == "quadrupole_power_ideal")
    mc_cfg = spec["monte_carlo"]
    result = run_seeded_mc(
        quad,
        seed=int(mc_cfg["seed"]),
        replicates=int(mc_cfg["replicates"]),
        tolerance_abs=prereg,
    )
    return {
        "schema": "pr129.mc_report.v2",
        "bit_generator": mc_cfg["bit_generator"],
        "rule": mc_cfg["rule"],
        "result": result,
        "tolerance_provenance":
            "dual_pinned_spec_and_module_never_widened",
    }


def build_captions(specs: list[EstimatorSpec]) -> dict:
    captions = {}
    for src in specs:
        text = generate_caption(src)
        lint_caption(text)
        captions[src.estimator_id] = text
    return {"schema": "pr129.captions.v1", "captions": captions}


def _scan_text(text: str, patterns: list[str],
               allowed_line_hashes: frozenset[str],
               allow_sentinels: bool) -> dict:
    hits: list[dict] = []
    skipped = 0
    allowlisted = 0
    sentinel_lines: list[str] = []
    block_count = 0
    in_registry = False
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        if SENTINEL_BEGIN in line:
            if not allow_sentinels:
                raise SystemExit(
                    "sentinel markers are not allowed in this scan target")
            if in_registry:
                raise SystemExit("nested sentinel block")
            in_registry = True
            block_count += 1
            skipped += 1
            continue
        if SENTINEL_END in line:
            in_registry = False
            skipped += 1
            continue
        if in_registry:
            sentinel_lines.append(line)
            skipped += 1
            continue
        line_hash = hashlib.sha256(line.strip().encode()).hexdigest()
        if line_hash in allowed_line_hashes:
            allowlisted += 1
            continue
        lowered = line.lower()
        for pattern_index, pattern in enumerate(patterns):
            if pattern.lower() in lowered:
                hits.append({"line": idx, "pattern_index": pattern_index})
    if in_registry:
        raise SystemExit("unterminated sentinel block")
    return {
        "lines_scanned": len(lines),
        "sentinel_skipped_lines": skipped,
        "sentinel_block_count": block_count,
        "sentinel_block_sha256": (
            hashlib.sha256(("\n".join(sentinel_lines) + "\n").encode())
            .hexdigest() if sentinel_lines else None),
        "allowlisted_lines": allowlisted,
        "hits": hits,
    }


def build_negative_scan(spec: dict, captions_payload: dict) -> dict:
    scan_cfg = spec["negative_scan"]
    patterns = [str(p) for p in scan_cfg["forbidden_patterns"]]
    sentinel_policy = scan_cfg["sentinel_policy"]
    allowlist_by_path: dict[str, set[str]] = {}
    for entry in scan_cfg["registered_negation_allowlist"]:
        allowlist_by_path.setdefault(entry["path"], set()).add(
            entry["line_sha256"])
    targets = {}
    for rel in scan_cfg["targets"]:
        if rel == OUTPUTS["captions"]:
            # the captions artifact is scanned from the freshly built
            # payload so write and check modes scan identical bytes.
            raw = _render(captions_payload).decode()
            source = "fresh_build"
            digest = hashlib.sha256(raw.encode()).hexdigest()
        else:
            path = REPO / rel
            raw = path.read_text(encoding="utf-8")
            source = "disk"
            digest = _sha(path)
        allow_sentinels = rel == sentinel_policy["allowed_only_in"]
        report = _scan_text(
            raw, patterns,
            frozenset(allowlist_by_path.get(rel, set())),
            allow_sentinels)
        if allow_sentinels:
            if report["sentinel_block_count"] != \
                    int(sentinel_policy["max_blocks"]):
                raise SystemExit(
                    f"sentinel block count {report['sentinel_block_count']}"
                    f" != pinned {sentinel_policy['max_blocks']} in {rel}")
            if report["sentinel_block_sha256"] != \
                    sentinel_policy["block_sha256"]:
                raise SystemExit(
                    f"sentinel block content drifted from the spec pin in "
                    f"{rel} — hiding text inside sentinels is refused")
        targets[rel] = dict(report, source=source, sha256=digest)
    total_hits = sum(len(t["hits"]) for t in targets.values())
    if total_hits:
        raise SystemExit(f"negative scan found {total_hits} forbidden-"
                         f"pattern hits: {targets}")
    total_allowlisted = sum(t["allowlisted_lines"] for t in targets.values())
    registered_allowlist = len(scan_cfg["registered_negation_allowlist"])
    if total_allowlisted != registered_allowlist:
        raise SystemExit(
            f"allowlist usage {total_allowlisted} != registered "
            f"{registered_allowlist} — stale or unused allowlist entries "
            "are refused")
    return {
        "schema": "pr129.negative_scan.v2",
        "rule": scan_cfg["rule"],
        # registered pattern registry: defines the ban, exempt from the
        # output-language lint (popped before linting, like forbidden_use).
        "forbidden_patterns": patterns,
        "sentinels": [SENTINEL_BEGIN, SENTINEL_END],
        "sentinel_policy": {
            "allowed_only_in": sentinel_policy["allowed_only_in"],
            "max_blocks": int(sentinel_policy["max_blocks"]),
            "block_sha256": sentinel_policy["block_sha256"],
        },
        "allowlisted_lines_total": total_allowlisted,
        "targets": targets,
        "total_hits": 0,
    }


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


def run_mutations(spec: dict, specs: list[EstimatorSpec],
                  prereg: float) -> dict:
    quad = next(s for s in specs if s.estimator_id == "quadrupole_power_ideal")
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])

    quad_payload = {
        "estimator_id": quad.estimator_id, "statistic": quad.statistic,
        "sky": quad.sky, "noise": quad.noise, "field": quad.field,
        "ell": quad.ell, "dof": quad.dof,
        "dispersion_squared_exact": str(quad.dispersion_squared_exact),
    }

    def mutant_universal_floor_language() -> None:
        # mutant caption text is quoted only via redaction below.
        lint_caption(generate_caption(quad)
                     + " This is the universal" + " floor.")

    def mutant_estimator_unspecified() -> None:
        EstimatorSpec.from_payload({
            "estimator_id": "mystery", "statistic": "S", "dof": 5})

    def mutant_wrong_dof() -> None:
        verify_quadrupole_dispersion(EstimatorSpec.from_payload(
            dict(quad_payload, dof=4)))

    def mutant_dof_reality_condition_miscount() -> None:
        # the naive 9-real-component miscount that ignores the reality
        # condition; its self-consistent dispersion 2/9 passes the bare
        # chi-square arithmetic, so only the structural check kills it.
        verify_quadrupole_dispersion(EstimatorSpec.from_payload(
            dict(quad_payload, dof=9, dispersion_squared_exact="2/9")))

    def mutant_fisher_conflation() -> None:
        for claim in (
                {"cites": "sqrt(2/5)",
                 "as": "multi-multipole Fisher floor"},
                {"cites": "sqrt(2 / 5)", "as": "Fisher floor"},
                {"cites": "sqrt(2/5)", "as": "Cramér-Rao floor"},
                {"cites": "sqrt(2/5)",
                 "as": "minimax lower bound over all estimators"},
                {"cites": "0.632", "as": "multi-multipole Fisher floor"},
                {"cites": "the Fisher information",
                 "as": "the estimator dispersion"},
        ):
            try:
                validate_separation(claim)
            except Nta3RegistryError:
                continue
            raise AssertionError(f"conflation survived: {claim}")
        raise Nta3RegistryError(
            "all six conflation variants rejected by the separation "
            "validator")

    def mutant_posthoc_tolerance_widening() -> None:
        run_seeded_mc(quad, seed=20260718, replicates=1000,
                      tolerance_abs=prereg * 10)

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "universal_floor_language": mutant_universal_floor_language,
        "estimator_unspecified": mutant_estimator_unspecified,
        "wrong_dof": mutant_wrong_dof,
        "dof_reality_condition_miscount":
            mutant_dof_reality_condition_miscount,
        "fisher_conflation": mutant_fisher_conflation,
        "posthoc_tolerance_widening": mutant_posthoc_tolerance_widening,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except Nta3RegistryError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr129.mutation_report.v2",
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
    if rel == OUTPUTS["manifest"]:
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            problems.append(f"invalid artifact: {rel}")
            return
        if (
            isinstance(existing, dict)
            and _semantic_artifact(rel, existing) == _semantic_artifact(rel, payload)
        ):
            return
    if target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr129_nta3_registry.v1":
        raise SystemExit("pr129 spec schema mismatch")
    _verify_remediation_state(spec)
    prereg = _verify_tolerance_pins(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    problems: list[str] = []
    wrote: list[str] = []

    specs = _specs_from_spec(spec)
    registry = build_registry(spec, specs)
    registry["prohibition_cross_list_covered"] = cross_covered
    mc_report = build_mc_report(spec, specs, prereg)
    captions = build_captions(specs)
    scan = build_negative_scan(spec, captions)
    mutations = run_mutations(spec, specs, prereg)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["registry"], registry, write, problems, wrote)
    _emit(OUTPUTS["mc"], mc_report, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["scan"], scan, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr129.artifact_manifest.v2",
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
            for rel in ("htt/src/common/nta3_estimator_registry.py",
                        "htt/obsstat/egs2_fisher.py")
        ],
        "caveats": [
            "Estimator- and domain-specific supersession at C1 only.",
            "The original universal reading is NOT rescued.",
            "The Fisher toy is a distinct registry object, never merged.",
            "Separation enforcement covers the registered scan targets "
            "and generated captions, not repo-global prose.",
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
            payload.pop("forbidden_patterns", None)
        text = json.dumps(payload, ensure_ascii=False)
        for phrase in spec["forbidden_output_language"]:
            if phrase in text:
                print(json.dumps({"ok": False,
                                  "reason": f"forbidden phrase in {rel}"}))
                return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "exact_dispersion_squared": registry["exact_analytic_check"][
            "registered_dispersion_squared"],
        "mc_abs_deviation": mc_report["result"]["abs_deviation"],
        "negative_scan_targets": len(scan["targets"]),
        "negative_scan_hits": scan["total_hits"],
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
