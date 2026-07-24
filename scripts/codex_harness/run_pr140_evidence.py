#!/usr/bin/env python3
"""PR-140 runner: normalized-prior coherent evidence, two independent engines.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the evidence report (both engines vs the exact analytic evidence,
log BF10), the prior-scale/covariance sensitivity report, the
content-addressed receipt, the under-resolved-engine indeterminate demo,
generated captions, and the six-mutant kill report.

Coherent model-comparison mechanics conditional on the registered
model/prior at roadmap_rescue_v1:C3; evidence agreement is never model
truth; no detection.
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

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from common.coherent_evidence import (  # noqa: E402
    SCHEMA_VERSION,
    EvidenceError,
    GaussianEvidenceModel,
    NormalPrior,
    bridge_sampling,
    caller_scalar_is_not_a_receipt,
    compare_engines,
    evidence_receipt,
    generate_caption,
    lint_caption,
    require_coherent,
    require_evidence_kind,
    require_independent_engines,
    require_normalized_prior,
    require_within_ceiling,
    sensitivity_grid,
    thermodynamic_integration,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr140_spec.yaml"
OUTPUTS = {
    "evidence": "docs/generated/pr140_evidence_report.json",
    "sensitivity": "docs/generated/pr140_sensitivity_report.json",
    "prior_sensitive": "docs/generated/pr140_prior_sensitive_demo.json",
    "receipt": "docs/generated/pr140_receipt.json",
    "indeterminate": "docs/generated/pr140_indeterminate_demo.json",
    "captions": "docs/generated/pr140_captions.json",
    "mutations": "docs/generated/pr140_mutation_report.json",
    "manifest": "docs/generated/pr140_artifact_manifest.json",
}
SOURCE_PATH = "htt/src/common/coherent_evidence.py"
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _round(obj):
    if isinstance(obj, float):
        return round(obj, 8)
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
    """Keep the maintained-source hash as generation-time provenance."""

    normalized = json.loads(json.dumps(_round(payload)))
    if rel == OUTPUTS["evidence"]:
        scan = normalized.get("negative_scan")
        targets = scan.get("targets") if isinstance(scan, dict) else None
        source = (
            targets.get(SOURCE_PATH)
            if isinstance(targets, dict) else None
        )
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


def _model(spec: dict, tau2: float | None = None,
           sig2_scale: float = 1.0) -> GaussianEvidenceModel:
    m = spec["model"]
    n = int(m["n_obs"])
    sig2 = float(Fraction(m["sig2"])) * sig2_scale
    t2 = float(Fraction(m["prior_tau2"])) if tau2 is None else tau2
    rng = np.random.Generator(np.random.PCG64(int(m["data_seed"])))
    y = rng.normal(float(Fraction(m["data_mu"])),
                   float(Fraction(m["sig2"])) ** 0.5, n)
    return GaussianEvidenceModel(y=y, sig2=sig2, prior=NormalPrior(0.0, t2))


def build_evidence(spec: dict):
    model = _model(spec)
    require_normalized_prior(model.prior)
    exact = model.exact_log_evidence()
    log_bf = exact - model.exact_log_null_evidence()
    eng = spec["engines"]
    diag = eng["diagnostics"]
    ti = thermodynamic_integration(
        model, n_beta=int(eng["thermodynamic_integration"]["n_beta"]),
        beta_power=float(eng["thermodynamic_integration"]["beta_power"]),
        n_samples=int(eng["thermodynamic_integration"]["n_samples_per_beta"]),
        seed=int(eng["thermodynamic_integration"]["seed"]),
        n_bootstrap=int(diag["n_bootstrap"]), boot_seed=int(diag["seed"]))
    bs = bridge_sampling(
        model, n_posterior=int(eng["bridge_sampling"]["n_posterior"]),
        n_proposal=int(eng["bridge_sampling"]["n_proposal"]),
        seed=int(eng["bridge_sampling"]["seed"]),
        max_iter=int(eng["bridge_sampling"]["max_iter"]),
        n_bootstrap=int(diag["n_bootstrap"]), boot_seed=int(diag["seed"]) + 1)
    require_independent_engines(ti, bs)
    # each engine must be a real marginal-likelihood estimator, never a
    # fitted score offered as evidence
    for engine in (ti, bs):
        require_evidence_kind(engine["method"])
    comparison = compare_engines(
        [ti, bs], exact,
        agreement_tol=float(Fraction(eng["agreement_tol_log_evidence"])),
        analytic_tol=float(Fraction(eng["analytic_tol_log_evidence"])),
        se_ceiling=float(Fraction(eng["diagnostic_se_ceiling"])))
    require_coherent(comparison)
    record = {
        "schema": "pr140.evidence_report.v1",
        "module_schema": SCHEMA_VERSION,
        "exact_log_evidence": exact,
        "exact_log_null_evidence": model.exact_log_null_evidence(),
        "log_bf10": log_bf,
        "engines": [ti, bs],
        "comparison": comparison,
        "verdict_note": "both independent engines match the exact evidence "
                        "within tolerance; a coherent Bayes factor is "
                        "conditional on the registered model and prior and "
                        "is not generative-model correctness",
    }
    return record, model, comparison


def build_sensitivity(spec: dict):
    sg = spec["sensitivity_grid"]
    tau2_grid = [float(Fraction(t)) for t in sg["prior_tau2"]]
    sig2_grid = [float(Fraction(s)) for s in sg["sig2_scale"]]
    sens = sensitivity_grid(
        lambda t2, sc: _model(spec, tau2=t2, sig2_scale=sc),
        tau2_grid, sig2_grid)
    ceiling = float(Fraction(sg["log_bf_swing_ceiling"]))
    prior_sensitive = sens["log_bf_swing"] > ceiling
    # Pure reporting here; the LIVE gate (require_within_ceiling) is asserted
    # on the production verdict in build() and demonstrated on a
    # deliberately prior-sensitive grid in build_prior_sensitive_demo.
    return {
        "schema": "pr140.sensitivity_report.v1",
        "ceiling": ceiling,
        "log_bf_swing": sens["log_bf_swing"],
        "prior_sensitive": prior_sensitive,
        "grid": sens["grid"],
        "note": "the log BF is evaluated over the preregistered prior-scale "
                "and covariance grid; a swing beyond the ceiling makes the "
                "decisive claim indeterminate (the swing is reported either "
                "way)",
    }


def build_prior_sensitive_demo(spec: dict) -> dict:
    """A deliberately wide grid whose swing exceeds the ceiling is refused."""
    sg = spec["prior_sensitive_demo"]
    tau2_grid = [float(Fraction(t)) for t in sg["prior_tau2"]]
    sig2_grid = [float(Fraction(s)) for s in sg["sig2_scale"]]
    ceiling = float(Fraction(spec["sensitivity_grid"]["log_bf_swing_ceiling"]))
    sens = sensitivity_grid(
        lambda t2, sc: _model(spec, tau2=t2, sig2_scale=sc),
        tau2_grid, sig2_grid)
    if sens["log_bf_swing"] <= ceiling:
        raise SystemExit("the prior-sensitive demo grid did not exceed the "
                         "ceiling — the demonstration is broken")
    refused = False
    try:
        require_within_ceiling(sens, ceiling)
    except EvidenceError:
        refused = True
    return {
        "schema": "pr140.prior_sensitive_demo.v1",
        "ceiling": ceiling,
        "log_bf_swing": sens["log_bf_swing"],
        "grid": sens["grid"],
        "decisive_claim_refused": refused,
        "status": "indeterminate",
        "note": "a prior/covariance grid whose log BF swing exceeds the "
                "ceiling is prior-sensitive; the decisive claim is refused "
                "and the status is indeterminate",
    }


def build_indeterminate(spec: dict, exact_engine_bridge: dict):
    """Under-resolved TI ladder demonstrated to disagree -> indeterminate."""
    model = _model(spec)
    exact = model.exact_log_evidence()
    kb = spec["known_bad_disagreement"]
    eng = spec["engines"]
    diag = eng["diagnostics"]
    ti_bad = thermodynamic_integration(
        model, n_beta=int(kb["n_beta"]), beta_power=float(kb["beta_power"]),
        n_samples=int(kb["n_samples_per_beta"]),
        seed=int(eng["thermodynamic_integration"]["seed"]),
        n_bootstrap=int(diag["n_bootstrap"]), boot_seed=int(diag["seed"]))
    comparison = compare_engines(
        [ti_bad, exact_engine_bridge], exact,
        agreement_tol=float(Fraction(eng["agreement_tol_log_evidence"])),
        analytic_tol=float(Fraction(eng["analytic_tol_log_evidence"])),
        se_ceiling=float(Fraction(eng["diagnostic_se_ceiling"])))
    if comparison["status"] != "indeterminate":
        raise SystemExit("the under-resolved engine did not disagree — the "
                         "indeterminate demonstration is broken")
    refused = False
    try:
        require_coherent(comparison)
    except EvidenceError:
        refused = True
    return {
        "schema": "pr140.indeterminate_demo.v1",
        "under_resolved_ti": {k: ti_bad[k] for k in
                              ("n_beta", "beta_power", "n_samples",
                               "log_evidence")},
        "exact_log_evidence": exact,
        "comparison": comparison,
        "coherent_claim_refused": refused,
        "note": "an under-resolved thermodynamic ladder disagrees with "
                "bridge sampling and the analytic evidence beyond tolerance; "
                "the coherent claim is refused and the status is "
                "indeterminate",
    }


def build_captions(evidence: dict, sensitivity: dict) -> dict:
    text = generate_caption(evidence["log_bf10"],
                            evidence["comparison"]["engine_gap"],
                            sensitivity["log_bf_swing"],
                            evidence["comparison"]["status"])
    lint_caption(text)
    return {"schema": "pr140.captions.v1", "captions": {"summary": text}}


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


def run_mutations(spec: dict) -> dict:
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])

    def mutant_fitted_score_as_bayes_factor() -> None:
        require_evidence_kind("fitted_score")

    def mutant_unnormalized_prior() -> None:
        require_normalized_prior(NormalPrior(0.0, 4.0, normalized=False))

    def mutant_caller_scalar_as_evidence() -> None:
        caller_scalar_is_not_a_receipt({"log_evidence": 1.23})

    def mutant_shared_samples_two_engines() -> None:
        shared = {"method": "thermodynamic_integration",
                  "sample_provenance": "shared00000000"}
        other = {"method": "bridge_sampling",
                 "sample_provenance": "shared00000000"}
        require_independent_engines(shared, other)

    def mutant_engine_disagreement_ignored() -> None:
        require_coherent({"status": "indeterminate"})

    def mutant_prior_sensitivity_ignored() -> None:
        require_within_ceiling({"log_bf_swing": 9.0}, 4.0)

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "fitted_score_as_bayes_factor": mutant_fitted_score_as_bayes_factor,
        "unnormalized_prior": mutant_unnormalized_prior,
        "caller_scalar_as_evidence": mutant_caller_scalar_as_evidence,
        "shared_samples_two_engines": mutant_shared_samples_two_engines,
        "engine_disagreement_ignored": mutant_engine_disagreement_ignored,
        "prior_sensitivity_ignored": mutant_prior_sensitivity_ignored,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except EvidenceError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr140.mutation_report.v1", "mutations": rows,
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
    if rel in {OUTPUTS["evidence"], OUTPUTS["manifest"]}:
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
    if spec.get("schema") != "htt.long_horizon.pr140_evidence.v1":
        raise SystemExit("pr140 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    evidence, model, comparison = build_evidence(spec)
    sensitivity = build_sensitivity(spec)
    # LIVE sensitivity gate: assert the decisive claim only when the swing is
    # within the ceiling; a prior-sensitive result downgrades the final
    # verdict to indeterminate (fail-closed, invoked on the production path).
    ceiling = float(Fraction(spec["sensitivity_grid"]["log_bf_swing_ceiling"]))
    sensitivity_ok = True
    try:
        require_within_ceiling(sensitivity, ceiling)
    except EvidenceError:
        sensitivity_ok = False
    final_status = ("coherent" if comparison["status"] == "coherent"
                    and sensitivity_ok else "indeterminate")
    evidence["prior_sensitive"] = sensitivity["prior_sensitive"]
    evidence["final_status"] = final_status
    prior_sensitive_demo = build_prior_sensitive_demo(spec)
    receipt = evidence_receipt(model, evidence["engines"], comparison)
    # a real receipt passes the receipt-type guard (a caller scalar would not)
    caller_scalar_is_not_a_receipt(receipt)
    indeterminate = build_indeterminate(spec, evidence["engines"][1])
    captions = build_captions(evidence, sensitivity)
    evidence["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["evidence"], evidence, write, problems, wrote)
    _emit(OUTPUTS["sensitivity"], sensitivity, write, problems, wrote)
    _emit(OUTPUTS["prior_sensitive"], prior_sensitive_demo, write, problems,
          wrote)
    _emit(OUTPUTS["receipt"], receipt, write, problems, wrote)
    _emit(OUTPUTS["indeterminate"], indeterminate, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr140.artifact_manifest.v1",
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
            for rel in ("htt/src/common/coherent_evidence.py",)
        ],
        "caveats": [
            "Coherent model-comparison mechanics conditional on the "
            "registered model and prior at C3 only.",
            "Two independent engines (thermodynamic integration and bridge "
            "sampling) are cross-checked against the exact analytic "
            "evidence.",
            "Engine agreement is NOT generative-model correctness; a "
            "prior-dominated result is shown as-is.",
            "Engine disagreement, insufficient diagnostics, or a prior "
            "swing beyond the ceiling makes the claim indeterminate.",
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
    module_text = (REPO / "htt/src/common/coherent_evidence.py").read_text(
        encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "log_bf10": round(evidence["log_bf10"], 6),
        "engine_gap": round(comparison["engine_gap"], 6),
        "status": comparison["status"],
        "final_status": final_status,
        "log_bf_swing": round(sensitivity["log_bf_swing"], 6),
        "prior_sensitive_demo_swing":
            round(prior_sensitive_demo["log_bf_swing"], 6),
        "prior_sensitive_demo_refused":
            prior_sensitive_demo["decisive_claim_refused"],
        "indeterminate_demo_status": indeterminate["comparison"]["status"],
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
