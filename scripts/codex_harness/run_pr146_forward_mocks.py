#!/usr/bin/env python3
"""PR-146 runner: CF4 catalogue forward-mock simulator coverage mechanics.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the primary Cholesky generator verification (per-galaxy dispersion +
analytic bulk-flow cosmic-variance covariance), the independent box-GRF
diagonal-variance reference, the per-variant realism coverage (re-fitting the
PR-145 estimator on every mock), the per-depth simultaneous coverage, the
effective-N and covariance-uncertainty audits, the two CF4 P0 remediation-
CANDIDATE receipts (both stay OPEN, closure needs PR-157), the simulator card,
generated captions, and the six-mutant kill report.

Forward-simulator coverage mechanics at roadmap_rescue_v1:C2; the two CF4 P0s
stay OPEN; no detection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))

warnings.filterwarnings("ignore")

import yaml  # noqa: E402

from obsstat.cf4_forward_simulator import (  # noqa: E402
    BoxGrfConfig,
    ForwardSimulatorError,
    RealismConfig,
    SCHEMA_VERSION,
    build_cholesky_generator,
    coverage_in_band,
    covariance_uncertainty,
    effective_n_modes,
    forward_mock_coverage,
    generate_caption,
    lint_caption,
    load_sample_and_meta,
    per_depth_coverage,
    realism_from_variant,
    refuse_box_grf_for_covariance,
    refuse_cf4_p0_closure,
    refuse_k6_rebind,
    refuse_rare_tail_without_coverage,
    refuse_same_box_octant_independence,
    refuse_wf_mean_as_ensemble,
    require_idealised_covers,
    subsample_with_meta,
    verify_cholesky_generator,
    verify_independent_reference,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr146_spec.yaml"
OUTPUTS = {
    "generator": "docs/generated/pr146_generator_verification.json",
    "reference": "docs/generated/pr146_independent_reference.json",
    "coverage": "docs/generated/pr146_coverage_report.json",
    "depth": "docs/generated/pr146_depth_coverage.json",
    "effective_n": "docs/generated/pr146_effective_n.json",
    "p0": "docs/generated/pr146_p0_remediation_candidates.json",
    "captions": "docs/generated/pr146_captions.json",
    "mutations": "docs/generated/pr146_mutation_report.json",
    "card": "docs/generated/pr146_simulator_card.json",
    "manifest": "docs/generated/pr146_artifact_manifest.json",
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
        raise SystemExit(f"baseline_commit {sha} does not resolve — "
                         "fabricated provenance refused")


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
                for k, v in contract["required_scientific_status_counts"]
                .items()}
    if statuses != required:
        raise SystemExit(f"remediation status counts drifted: {statuses}")


def _groups_path(spec: dict) -> Path:
    return REPO / spec["data_scope"]["raw_data_paths"]["groups"]


def build_reports(spec: dict):
    m = spec["model"]
    h0 = float(Fraction(m["H0_kms_mpc"]))
    full, meta = load_sample_and_meta(_groups_path(spec), h0=h0,
                                      sigma_nl=float(m["sigma_nl_kms"]))
    # anti-drift guards invoked LIVE on the production path with admissible input
    refuse_same_box_octant_independence("independent_realisations")
    refuse_wf_mean_as_ensemble("cholesky_ensemble")
    refuse_k6_rebind("pr123_independent_branch")
    refuse_rare_tail_without_coverage(True, "forward_simulator_mechanics")
    refuse_cf4_p0_closure("remediation_candidate")
    refuse_box_grf_for_covariance("diagonal_variance_reference")

    # 1. primary Cholesky generator
    sub, sub_meta = subsample_with_meta(full, meta, int(m["cholesky_subsample"]),
                                        int(m["cholesky_seed"]))
    gen = build_cholesky_generator(sub)
    generator = {"schema": "pr146.generator_verification.v1",
                 "module_schema": SCHEMA_VERSION,
                 **verify_cholesky_generator(
                     gen, n_real=int(m["cholesky_realizations"]),
                     seed=int(m["cholesky_seed"]))}

    # 2. independent box GRF reference (diagonal variance only)
    subb, _ = subsample_with_meta(full, meta, int(m["box_subsample"]),
                                  int(m["box_seed"]))
    reference = {"schema": "pr146.independent_reference.v1",
                 **verify_independent_reference(
                     subb, BoxGrfConfig(int(m["box_ngrid"]),
                                        float(m["box_size_hmpc"])),
                     n_fields=int(m["box_fields"]), seed=int(m["box_seed"]))}

    # 3-4. realism-variant coverage (re-fit the estimator on every mock)
    cov_spec = spec["coverage"]
    subc, subc_meta = subsample_with_meta(full, meta, int(cov_spec["subsample"]),
                                          int(cov_spec["seed"]))
    flow = [float(x) for x in cov_spec["inject"]["flow_kms"]]
    mono = float(cov_spec["inject"]["monopole_kms"])
    variants = []
    for variant in cov_spec["realism_variants"]:
        cov = forward_mock_coverage(subc, subc_meta, flow, mono,
                                    realism_from_variant(variant),
                                    n_mock=int(cov_spec["n_mock"]),
                                    seed=int(cov_spec["seed"]))
        flags68 = coverage_in_band(cov, 0.68, float(cov_spec["idealised_band_68"]))
        cov["in_band_68"] = flags68
        cov["all_in_band_68"] = all(flags68.values())
        variants.append(cov)
    idealised = next(c for c in variants if c["variant"] == "idealised")
    require_idealised_covers(idealised, float(cov_spec["idealised_band_68"]),
                             float(cov_spec["idealised_band_95"]))
    coverage_report = {"schema": "pr146.coverage_report.v1",
                       "inject": {"flow_kms": flow, "monopole_kms": mono},
                       "variants": variants,
                       "note": "the idealised variant covers by construction "
                               "(propagation self-consistency) and the noise-"
                               "only covariance under-covers; a realism variant "
                               "degradation is REPORTED not hidden (the "
                               "lognormal distance error biases the radial "
                               "monopole)"}

    # 5. per-depth simultaneous coverage
    dspec = spec["depth_coverage"]
    depth = {"schema": "pr146.depth_coverage.v1",
             **per_depth_coverage(subc, subc_meta, flow, mono,
                                  n_shells=int(dspec["n_shells"]),
                                  n_mock=int(dspec["n_mock"]),
                                  seed=int(dspec["seed"]))}

    # 6-7. effective-N + covariance uncertainty
    effective = {"schema": "pr146.effective_n.v1",
                 **effective_n_modes(subc),
                 "covariance_uncertainty":
                     covariance_uncertainty(int(cov_spec["n_mock"]))}
    return generator, reference, coverage_report, depth, effective


def build_p0_candidates(generator: dict, reference: dict,
                        coverage_report: dict) -> dict:
    ideal = next(c for c in coverage_report["variants"]
                 if c["variant"] == "idealised")
    return {
        "schema": "pr146.p0_remediation_candidates.v1",
        "candidates": [
            {"finding_id": "C1-K5-MV-F1", "status": "OPEN",
             "disposition": "remediation_candidate",
             "mechanics": "a CF4 forward simulator now draws correlated mocks "
                          "whose covariance is the fiducial Gorski velocity "
                          "correlation; the primary Cholesky generator "
                          "reproduces the analytic bulk-flow cosmic-variance "
                          f"covariance (diag ratios "
                          f"{[round(r, 2) for r in generator['bulk_flow_cov_diag_ratio']]}) "
                          "as a propagation self-consistency check (same "
                          "Gorski C_ab in and out, not an independent "
                          "covariance validation), and an independent FFT box "
                          "independently confirms only the per-galaxy variance "
                          "NORMALISATION (ratio "
                          f"{round(reference['normalisation_ratio_box_over_band'], 2)}, "
                          "ruling out a shared code bug in the variance scale); "
                          "the off-diagonal covariance structure is the "
                          "fiducial Gorski model, not independently validated; "
                          "the idealised coverage holds (min 68 percent "
                          f"{round(min(ideal['coverage_68']), 2)})",
             "closure": "impossible before the PR-157 adjudication"},
            {"finding_id": "C3-K5-VCORR-ML-F1", "status": "OPEN",
             "disposition": "remediation_candidate",
             "scope_note": "PR-146 does NOT implement the velocity-correlation "
                           "ML estimator; it supplies the shared forward-mock "
                           "simulator (correlated generator + independent "
                           "reference + realism layers) that the ML branch "
                           "will use for its coverage",
             "mechanics": "the forward-mock coverage machinery, the "
                          "independent variance reference, the effective-N "
                          "audit and the covariance uncertainty are available "
                          "for the ML branch; the ML f sigma_8 remediation "
                          "itself is a scoped follow-up",
             "closure": "impossible before the PR-157 adjudication"},
        ],
        "note": "both CF4 P0s stay OPEN; PR-146 supplies forward-simulator "
                "coverage mechanics, not closure",
    }


def build_card(generator, reference, coverage_report, depth, effective) -> dict:
    ideal = next(c for c in coverage_report["variants"]
                 if c["variant"] == "idealised")
    degraded = [{"variant": c["variant"], "component": lab,
                 "coverage_68": round(cov, 3)}
                for c in coverage_report["variants"]
                for lab, cov, ok in zip(c["labels"], c["coverage_68"],
                                        [c["in_band_68"][k]
                                         for k in c["labels"]])
                if not ok]
    return {
        "schema": "pr146.simulator_card.v1",
        "module_schema": SCHEMA_VERSION,
        "artifact_mode": "forward_simulator_coverage_mechanics",
        "claim_level": "roadmap_rescue_v1:C2",
        "primary_generator": {
            "kind": "cholesky_from_gorski_correlation",
            "per_galaxy_std_kms": generator["per_galaxy_std_kms"],
            "sigma_v_1d_kms": generator["sigma_v_1d_kms"],
            "bulk_flow_cov_diag_ratio": generator["bulk_flow_cov_diag_ratio"]},
        "independent_reference": {
            "kind": "box_grf_fft_diagonal_variance_only",
            "normalisation_ratio_box_over_band":
                reference["normalisation_ratio_box_over_band"],
            "band_captured_fraction_sigma":
                reference["band_captured_fraction_sigma"],
            "variance_deficit_super_sample_below_kfund":
                reference["variance_deficit_super_sample_below_kfund"],
            "variance_deficit_sub_grid_above_knyquist":
                reference["variance_deficit_sub_grid_above_knyquist"],
            "off_diagonal_ratio_box_over_analytic_approx":
                reference["off_diagonal_ratio_box_over_analytic_approx"],
            "validates_diagonal_normalisation_only": True,
            "used_for_covariance": False},
        "coverage_summary": {
            "variant_kinds": {
                "idealised": "propagation self-consistency (DGP == assessed)",
                "nongaussian_distance_error": "genuine stressor (asymmetric "
                    "error biases the monopole; unmodeled)",
                "nonlinear_scatter": "genuine stressor (extra variance not in "
                    "the model)",
                "selection_malmquist": "genuine stressor (mag-limited "
                    "subsample + unmodeled distance-correlated Malmquist bias)",
                "grouping": "genuine stressor (grouped subsample + unmodeled "
                    "intra-group dispersion)"},
            "idealised_min_coverage_68": round(min(ideal["coverage_68"]), 3),
            "idealised_covers": ideal["all_in_band_68"],
            "noise_only_under_covers":
                max(ideal["coverage_68_noise_only"]) < 0.60,
            "reported_degradations": degraded},
        "depth_coverage": {
            "n_shells": depth["n_shells"],
            "least_favourable_shell": depth["least_favourable_shell"],
            "least_favourable_min_coverage_68":
                depth["least_favourable_min_coverage_68"]},
        "effective_n": {
            "field_participation_ratio": effective["field_participation_ratio"],
            "bulk_flow_participation_ratio":
                effective["bulk_flow_participation_ratio"],
            "covariance_fractional_uncertainty":
                effective["covariance_uncertainty"][
                    "monte_carlo_fractional_uncertainty_per_variance_element"]},
        "cf4_p0_status": "both OPEN, remediation candidates, closure needs "
                         "PR-157",
        "caveats": [
            "Forward-simulator coverage mechanics at C2 only.",
            "The box GRF is a diagonal-variance reference only, never used for "
            "the covariance or coverage.",
            "Same-box regions are never counted as independent samples; the "
            "field has few independent large-scale modes.",
            "A realism-variant coverage degradation (the lognormal distance "
            "error biases the radial monopole) is reported, not hidden.",
            "No rare-tail or significance claim is produced; no detection.",
            "All 102 remediation findings remain OPEN.",
        ],
    }


def build_captions(reference: dict, coverage_report: dict,
                   effective: dict) -> dict:
    ideal = next(c for c in coverage_report["variants"]
                 if c["variant"] == "idealised")
    text = generate_caption(reference["normalisation_ratio_box_over_band"],
                            effective["field_participation_ratio"],
                            min(ideal["coverage_68"]))
    lint_caption(text)
    return {"schema": "pr146.captions.v1", "captions": {"summary": text}}


def _scan_targets(spec: dict, captions_payload: dict) -> dict:
    patterns = [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
    targets = {}
    for rel in spec["negative_scan"]["targets"]:
        if rel == OUTPUTS["captions"]:
            raw = _render(captions_payload).decode()
            source, digest = "fresh_build", hashlib.sha256(
                raw.encode()).hexdigest()
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

    def mutant_same_box_octant_independence() -> None:
        refuse_same_box_octant_independence("same_box_octants")

    def mutant_wf_mean_as_ensemble() -> None:
        refuse_wf_mean_as_ensemble("wf_mean")

    def mutant_k6_rebind() -> None:
        refuse_k6_rebind("k6_rebind")

    def mutant_rare_tail_without_coverage() -> None:
        refuse_rare_tail_without_coverage(False, "rare_tail")

    def mutant_cf4_p0_closure() -> None:
        refuse_cf4_p0_closure("cf4_p0_closed")

    def mutant_box_grf_for_covariance() -> None:
        refuse_box_grf_for_covariance("covariance")

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "same_box_octant_independence": mutant_same_box_octant_independence,
        "wf_mean_as_ensemble": mutant_wf_mean_as_ensemble,
        "k6_rebind": mutant_k6_rebind,
        "rare_tail_without_coverage": mutant_rare_tail_without_coverage,
        "cf4_p0_closure": mutant_cf4_p0_closure,
        "box_grf_for_covariance": mutant_box_grf_for_covariance,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed, message = False, "MUTANT SURVIVED"
        try:
            fn()
        except ForwardSimulatorError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr146.mutation_report.v1", "mutations": rows,
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
    if spec.get("schema") != "htt.long_horizon.pr146_forward_simulator.v1":
        raise SystemExit("pr146 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    if not _groups_path(spec).is_file():
        raise SystemExit("CF4 groups npz absent — requires the read-only "
                         "external CF4 catalogue")
    problems: list[str] = []
    wrote: list[str] = []

    generator, reference, coverage_report, depth, effective = build_reports(spec)
    p0 = build_p0_candidates(generator, reference, coverage_report)
    card = build_card(generator, reference, coverage_report, depth, effective)
    captions = build_captions(reference, coverage_report, effective)
    card["negative_scan"] = {"targets": _scan_targets(spec, captions),
                             "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["generator"], generator, write, problems, wrote)
    _emit(OUTPUTS["reference"], reference, write, problems, wrote)
    _emit(OUTPUTS["coverage"], coverage_report, write, problems, wrote)
    _emit(OUTPUTS["depth"], depth, write, problems, wrote)
    _emit(OUTPUTS["effective_n"], effective, write, problems, wrote)
    _emit(OUTPUTS["p0"], p0, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)
    _emit(OUTPUTS["card"], card, write, problems, wrote)

    manifest = {
        "schema": "pr146.artifact_manifest.v1",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {"groups_sha256": _sha(_groups_path(spec))},
        "input_hashes": [f"{rel}:{_sha(REPO / rel)}" for rel in
                         ("htt/obsstat/cf4_forward_simulator.py",
                          "htt/obsstat/cf4_velocity_estimators.py")],
        "caveats": [
            "Forward-simulator coverage mechanics at C2 only.",
            "The primary Cholesky generator is validated against the analytic "
            "cosmic-variance covariance; an independent FFT box confirms the "
            "variance normalisation.",
            "The box GRF is a diagonal-variance reference only.",
            "Same-box regions are never counted as independent.",
            "The two CF4 P0s stay OPEN with remediation CANDIDATES; closure "
            "is impossible before the PR-157 adjudication.",
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
    module_text = (REPO / "htt/obsstat/cf4_forward_simulator.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "box_norm_ratio": round(
            reference["normalisation_ratio_box_over_band"], 3),
        "field_modes": round(effective["field_participation_ratio"], 1),
        "idealised_min_68": round(min(next(
            c for c in coverage_report["variants"]
            if c["variant"] == "idealised")["coverage_68"]), 3),
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
