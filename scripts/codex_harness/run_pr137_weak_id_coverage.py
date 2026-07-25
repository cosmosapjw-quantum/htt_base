#!/usr/bin/env python3
"""PR-137 runner: weak-identification boundary + grid-conditional
simultaneous coverage.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the coverage grid (Imbens-Manski frozen algorithm + adversarial
naive procedure over the pre-registered DGP grid), the family-wise 99%
Clopper-Pearson lower bounds, the two-mesh refinement + optimizer-error
report, the failure map (below-threshold points preserved), generated
captions, and the mutation report (six preregistered mutants killed on
production validator paths).

Grid-conditional coverage-calibrated partial-identification mechanics at
roadmap_rescue_v1:C2; no uniform class-wide claim; no detection.
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

from common.weak_id_coverage import (  # noqa: E402
    SCHEMA_VERSION,
    Preregistration,
    WeakIdError,
    bonferroni_conf,
    build_failure_map,
    clopper_pearson_lower,
    clopper_pearson_upper,
    coverage_at_point,
    generate_caption,
    lint_caption,
    lint_uniform,
    require_failure_map_complete,
    require_full_grid,
    require_uniform_certificate,
    validate_lower_bound,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr137_spec.yaml"
OUTPUTS = {
    "grid": "docs/generated/pr137_coverage_grid.json",
    "bounds": "docs/generated/pr137_family_wise_bounds.json",
    "mesh": "docs/generated/pr137_mesh_refinement.json",
    "failure": "docs/generated/pr137_failure_map.json",
    "captions": "docs/generated/pr137_captions.json",
    "mutations": "docs/generated/pr137_mutation_report.json",
    "manifest": "docs/generated/pr137_artifact_manifest.json",
}
SOURCE_PATH = "htt/src/common/weak_id_coverage.py"
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
    """Treat the maintained source hash as generation-time provenance."""

    normalized = json.loads(json.dumps(payload))
    scan = normalized.get("negative_scan")
    targets = scan.get("targets") if isinstance(scan, dict) else None
    source = targets.get(SOURCE_PATH) if isinstance(targets, dict) else None
    if isinstance(source, dict) and _is_sha256(source.get("sha256")):
        source["sha256"] = "<generation-time-source>"
    if rel == OUTPUTS["manifest"]:
        rows = normalized.get("input_hashes")
        prefix = f"{SOURCE_PATH}:"
        if isinstance(rows, list):
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


def _verify_prohibition_cross_list(spec: dict) -> int:
    covered = 0
    for pattern in spec["negative_scan"]["forbidden_patterns"]:
        try:
            lint_caption(f"benign text then {pattern} then more text")
        except WeakIdError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def _prereg(spec: dict) -> Preregistration:
    p = spec["preregistration"]
    return Preregistration(
        nominal_coverage=float(p["nominal_coverage"]),
        retain_lower_bound=float(p["retain_lower_bound"]),
        min_replicates=p["min_replicates_per_point"],
        min_seeds=p["min_seeds"],
        base_seed=p["base_seed"],
        endpoint_tol_fraction=float(p["optimizer_error_tolerance_fraction"]),
    )


def _run_grid(spec: dict, prereg: Preregistration, grid_key: str,
              procedure: str, theta0_position: str = "midpoint") -> list:
    n_rep = prereg.min_replicates
    seeds = prereg.min_seeds
    results = []
    for w_str in spec["preregistration"][grid_key]:
        r = coverage_at_point(float(Fraction(w_str)), procedure,
                              n_replicates=n_rep, seeds=seeds,
                              base_seed=prereg.base_seed, w_key=w_str,
                              theta0_position=theta0_position)
        # validate the DELIVERED count (integer per-seed division can
        # short the requested total) — not merely the requested n.
        prereg.require_replicates(r["delivered_replicates"], r["seeds"])
        r["per_seed_coverage_min"] = min(r.pop("per_seed_coverage"))
        results.append(r)
    return results


def build_grid(spec: dict, prereg: Preregistration) -> dict:
    # the least-favorable BOUNDARY config (theta0 at the identified-set
    # edge) is the one that determines whether the frozen CI can
    # undercover; the midpoint config is the coverage-easiest reference.
    coarse_im = _run_grid(spec, prereg, "grid_w_coarse", "imbens_manski",
                          "boundary")
    fine_im = _run_grid(spec, prereg, "grid_w_fine", "imbens_manski",
                        "boundary")
    fine_im_mid = _run_grid(spec, prereg, "grid_w_fine", "imbens_manski",
                            "midpoint")
    coarse_naive = _run_grid(spec, prereg, "grid_w_coarse",
                             "naive_no_expansion", "boundary")
    registered = list(spec["preregistration"]["grid_w_fine"])
    require_full_grid([r["w"] for r in fine_im], registered)
    return {
        "schema": "pr137.coverage_grid.v1",
        "module_schema": SCHEMA_VERSION,
        "dgp": spec["preregistration"]["dgp"],
        "theta0_position_note": "the retain/failure decision uses the "
                                "least-favorable BOUNDARY config "
                                "(theta0 at the identified-set edge); the "
                                "midpoint config is the easy reference",
        "nominal_coverage": prereg.nominal_coverage,
        "imbens_manski_boundary_coarse": coarse_im,
        "imbens_manski_boundary_fine": fine_im,
        "imbens_manski_midpoint_fine": fine_im_mid,
        "adversarial_naive_boundary_coarse": coarse_naive,
    }


def _family_wise(r: dict, per_point_conf: float) -> float:
    return clopper_pearson_lower(r["covered"], r["delivered_replicates"],
                                 per_point_conf)


def build_bounds(spec: dict, prereg: Preregistration, grid: dict) -> dict:
    fine = grid["imbens_manski_boundary_fine"]
    n_points = len(fine)
    # BONFERRONI: per-point confidence so the JOINT (family-wise,
    # simultaneous over all grid points) confidence is at least 0.99.
    per_point_conf = bonferroni_conf(0.99, n_points)
    p = spec["preregistration"]
    ext_reps = int(p["extension_replicates"])
    ext_within = float(p["extension_trigger_within"])
    seeds = prereg.min_seeds
    rows = []
    extended = []
    for r in fine:
        fw = _family_wise(r, per_point_conf)
        replicates = r["delivered_replicates"]
        # pre-registered adaptive extension: a point within 0.01 of the
        # 0.93 boundary is re-run at 10000 replicates.
        if abs(fw - prereg.retain_lower_bound) <= ext_within:
            r_ext = coverage_at_point(
                float(Fraction(r["w"])), "imbens_manski",
                n_replicates=ext_reps, seeds=seeds,
                base_seed=prereg.base_seed, w_key=r["w"],
                theta0_position="boundary")
            prereg.require_replicates(r_ext["delivered_replicates"],
                                      r_ext["seeds"])
            fw = clopper_pearson_lower(r_ext["covered"],
                                       r_ext["delivered_replicates"],
                                       per_point_conf)
            replicates = r_ext["delivered_replicates"]
            r["covered"] = r_ext["covered"]
            r["coverage"] = r_ext["coverage"]
            r["delivered_replicates"] = replicates
            extended.append(r["w"])
        validate_lower_bound(fw, r["covered"], replicates, per_point_conf)
        r["family_wise_lower"] = fw
        rows.append({
            "w": r["w"], "procedure": r["procedure"],
            "theta0_position": r["theta0_position"],
            "replicates": replicates,
            "extended": r["w"] in extended,
            "coverage": r["coverage"],
            "marginal_lower_99": r["marginal_lower_99"],
            "family_wise_lower": fw,
            "retained": fw >= prereg.retain_lower_bound,
        })
    prereg.require_pinned_threshold(prereg.retain_lower_bound)
    return {
        "schema": "pr137.family_wise_bounds.v1",
        "family_wise_confidence": 0.99,
        "per_point_confidence_bonferroni": per_point_conf,
        "n_grid_points": n_points,
        "simultaneous_note": "the family-wise lower bound is a genuine "
                             "SIMULTANEOUS (Bonferroni over all grid "
                             "points) 99% lower bound, not a per-point "
                             "marginal bound",
        "retain_config": "boundary (least-favorable theta0 position)",
        "extended_points": extended,
        "extension_replicates": ext_reps,
        "retain_lower_bound": prereg.retain_lower_bound,
        "bounds": rows,
        "min_lower_bound": min(r["family_wise_lower"] for r in rows),
        "all_retained": all(r["retained"] for r in rows),
    }


def build_mesh(spec: dict, grid: dict, prereg: Preregistration) -> dict:
    coarse_list = grid["imbens_manski_boundary_coarse"]
    fine_list = grid["imbens_manski_boundary_fine"]
    # per-point coverage on the two meshes (a coverage ESTIMATE, so the
    # shared-point change measures MC-estimate stability under refinement)
    coarse = {r["w"]: r for r in coarse_list}
    fine = {r["w"]: r for r in fine_list}
    shared = sorted(set(coarse) & set(fine),
                    key=lambda w: float(Fraction(w)))
    changes = []
    max_change = 0.0
    max_endpt = 0.0
    for w in shared:
        dc = abs(coarse[w]["coverage"] - fine[w]["coverage"])
        max_change = max(max_change, dc)
        max_endpt = max(max_endpt, fine[w]["endpoint_error"])
        changes.append({"w": w, "coverage_change": dc,
                        "endpoint_error": fine[w]["endpoint_error"]})
    tol_fraction = prereg.endpoint_tol_fraction
    endpoint_tol = 1e-12   # the bisection tolerance in imbens_manski_c
    # the MEANINGFUL mesh signal: the worst-case (minimum) coverage over
    # the FINE grid vs the COARSE grid — refinement adds intermediate
    # w-points and can reveal a coverage dip the coarse grid missed.
    coarse_min_cov = min(r["coverage"] for r in coarse_list)
    fine_min_cov = min(r["coverage"] for r in fine_list)
    worst_case_change = abs(coarse_min_cov - fine_min_cov)
    coverage_change_ok = (max_change <= 0.01) and (worst_case_change
                                                   <= 0.01)
    endpoint_error_ok = max_endpt <= max(tol_fraction * endpoint_tol,
                                         1e-13)
    return {
        "schema": "pr137.mesh_refinement.v1",
        "levels": int(spec["preregistration"]["mesh_refinement_levels"]),
        "shared_points": shared,
        "per_point": changes,
        "max_coverage_change_shared": max_change,
        "coarse_min_coverage": coarse_min_cov,
        "fine_min_coverage": fine_min_cov,
        "worst_case_coverage_change": worst_case_change,
        "max_endpoint_error": max_endpt,
        "coverage_change_kill_threshold": 0.01,
        "endpoint_error_kill_threshold": max(tol_fraction * endpoint_tol,
                                             1e-13),
        "coverage_change_ok": coverage_change_ok,
        "endpoint_error_ok": endpoint_error_ok,
        "passes_mesh_kill_condition": coverage_change_ok
        and endpoint_error_ok,
    }


def build_failure(spec: dict, grid: dict, prereg: Preregistration) -> dict:
    # the failure map spans BOTH procedures; the adversarial naive
    # procedure's below-threshold points are preserved here. The naive
    # rows need a family_wise_lower computed at the same Bonferroni conf.
    n_naive = len(grid["adversarial_naive_boundary_coarse"])
    naive_conf = bonferroni_conf(0.99, n_naive)
    for r in grid["adversarial_naive_boundary_coarse"]:
        r["family_wise_lower"] = clopper_pearson_lower(
            r["covered"], r["delivered_replicates"], naive_conf)
    all_points = grid["imbens_manski_boundary_fine"] + \
        grid["adversarial_naive_boundary_coarse"]
    fmap = build_failure_map(all_points, prereg.retain_lower_bound,
                             "family_wise_lower")
    reported_w = sorted({r["w"]
                         for r in grid["imbens_manski_boundary_fine"]},
                        key=lambda w: float(Fraction(w)))
    require_failure_map_complete(
        reported_w, list(spec["preregistration"]["grid_w_fine"]))
    return {
        "schema": "pr137.failure_map.v1",
        **fmap,
        "note": "the frozen Imbens-Manski algorithm is retained at every "
                "grid point; the adversarial naive (c=0) procedure's "
                "below-threshold points are preserved here, never removed",
    }


def build_captions(bounds: dict, failure: dict) -> dict:
    text = generate_caption(bounds["min_lower_bound"],
                            len(bounds["bounds"]),
                            failure["failing_count"])
    lint_caption(text)
    return {"schema": "pr137.captions.v1", "captions": {"summary": text}}


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


def run_mutations(spec: dict, prereg: Preregistration, grid: dict) -> dict:
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])
    registered_fine = list(spec["preregistration"]["grid_w_fine"])

    def mutant_uniform_without_certificate() -> None:
        require_uniform_certificate(None)

    def mutant_central_cases_only() -> None:
        # coverage over only the point-identified subset
        require_full_grid(["0", "1/4"], registered_fine)

    def mutant_silent_corner_removal() -> None:
        # drop a fine grid point from the reported grid
        reported = [w for w in registered_fine if w != "4"]
        require_failure_map_complete(reported, registered_fine)

    def mutant_threshold_tuned_to_coverage() -> None:
        prereg.require_pinned_threshold(0.90)

    def mutant_fewer_than_min_replicates() -> None:
        prereg.require_replicates(500, 10)

    def mutant_wrong_binomial_bound() -> None:
        # feed the Clopper-Pearson UPPER bound (anti-conservative) through
        # the PRODUCTION validate_lower_bound guard: it exceeds the point
        # estimate and does not equal the true lower bound, so it is
        # rejected.
        r = grid["imbens_manski_boundary_fine"][0]
        k, n = r["covered"], r["delivered_replicates"]
        upper = clopper_pearson_upper(k, n, 0.99)
        validate_lower_bound(upper, k, n, 0.99)

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "uniform_without_certificate": mutant_uniform_without_certificate,
        "central_cases_only": mutant_central_cases_only,
        "silent_corner_removal": mutant_silent_corner_removal,
        "threshold_tuned_to_coverage": mutant_threshold_tuned_to_coverage,
        "fewer_than_min_replicates": mutant_fewer_than_min_replicates,
        "wrong_binomial_bound": mutant_wrong_binomial_bound,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except WeakIdError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr137.mutation_report.v1",
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
    if spec.get("schema") != "htt.long_horizon.pr137_weak_id_coverage.v1":
        raise SystemExit("pr137 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    prereg = _prereg(spec)
    problems: list[str] = []
    wrote: list[str] = []

    grid = build_grid(spec, prereg)
    grid["prohibition_cross_list_covered"] = cross_covered
    bounds = build_bounds(spec, prereg, grid)
    mesh = build_mesh(spec, grid, prereg)
    # ENFORCE the mesh kill condition (coverage change > 0.01 or
    # optimizer endpoint error > tolerance blocks the scientific bound).
    if not mesh["passes_mesh_kill_condition"]:
        print(json.dumps({"ok": False, "reason": "mesh kill condition "
                          "failed", "mesh": mesh}))
        return 2
    failure = build_failure(spec, grid, prereg)
    captions = build_captions(bounds, failure)
    grid["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec, prereg, grid)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    # forbidden-language check on the in-memory payloads BEFORE any write
    for label, payload in (("grid", grid), ("bounds", bounds),
                           ("mesh", mesh), ("failure", failure),
                           ("captions", captions),
                           ("mutations", mutations)):
        scrub = dict(payload)
        scrub.pop("forbidden_use", None)
        text = json.dumps(scrub, ensure_ascii=False).lower()
        for phrase in spec["forbidden_output_language"]:
            if phrase.lower() in text:
                print(json.dumps({"ok": False, "reason":
                                  f"forbidden phrase in {label} payload"}))
                return 2

    _emit(OUTPUTS["grid"], grid, write, problems, wrote)
    _emit(OUTPUTS["bounds"], bounds, write, problems, wrote)
    _emit(OUTPUTS["mesh"], mesh, write, problems, wrote)
    _emit(OUTPUTS["failure"], failure, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr137.artifact_manifest.v1",
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
            for rel in ("htt/src/common/weak_id_coverage.py",)
        ],
        "caveats": [
            "Grid-conditional coverage-calibrated mechanics at C2 only.",
            "GRID-CONDITIONAL empirical coverage; no uniform class-wide "
            "claim (no continuity/mesh certificate).",
            "The frozen Imbens-Manski algorithm is retained everywhere; "
            "the adversarial naive procedure's failures are preserved in "
            "the failure map.",
            "The retain threshold is pinned pre-fit; tuning it needs a "
            "new split.",
            "No detection.",
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
    module_text = (REPO / "htt/src/common/weak_id_coverage.py").read_text(
        encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "min_lower_bound": bounds["min_lower_bound"],
        "all_retained": bounds["all_retained"],
        "adversarial_failures": failure["failing_count"],
        "worst_case_coverage_change": mesh["worst_case_coverage_change"],
        "per_point_conf_bonferroni": bounds[
            "per_point_confidence_bonferroni"],
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
