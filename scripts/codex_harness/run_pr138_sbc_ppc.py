#!/usr/bin/env python3
"""PR-138 runner: lineage-bound posterior draws, SBC, replicated-data
PPC.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the SBC report (known-good passes rank-uniformity, both known-bad
fail), the PPC report (Bayesian p-values over the frozen discrepancies),
the lineage record, the separate residual_check, generated captions, and
the mutation report (six preregistered mutants killed on production
validator paths).

Model/transfer-conditional predictive-adequacy mechanics at
roadmap_rescue_v1:C2; a PPC pass is never model truth; no detection.
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

from common.sbc_ppc import (  # noqa: E402
    SCHEMA_VERSION,
    GaussianModel,
    InadequateModelError,
    SbcPpcError,
    freeze_discrepancies,
    generate_caption,
    lineage_hash,
    lint_caption,
    ppc_verdict,
    require_frozen_discrepancies,
    require_not_ppc,
    require_ppc_receipt,
    require_sbc_calibrated,
    require_valid_posterior,
    run_ppc,
    run_sbc,
    sbc_lineage_hash,
    sbc_verdict,
    standardized_residual_check,
    verify_lineage,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr138_spec.yaml"
OUTPUTS = {
    "sbc": "docs/generated/pr138_sbc_report.json",
    "ppc": "docs/generated/pr138_ppc_report.json",
    "lineage": "docs/generated/pr138_lineage.json",
    "residual": "docs/generated/pr138_residual_check.json",
    "captions": "docs/generated/pr138_captions.json",
    "mutations": "docs/generated/pr138_mutation_report.json",
    "manifest": "docs/generated/pr138_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"


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
        except SbcPpcError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def _model(spec: dict, var_scale: Fraction) -> GaussianModel:
    m = spec["model"]
    return GaussianModel(Fraction(m["prior_tau2"]),
                         Fraction(m["likelihood_sig2"]),
                         int(m["n_obs"]), var_scale)


def _sbc_config(sc: dict) -> dict:
    return {"n_simulations": str(sc["n_simulations"]),
            "n_draws": str(sc["n_posterior_draws"]),
            "n_bins": str(sc["n_bins"]), "seed": str(sc["seed"])}


def build_sbc(spec: dict) -> dict:
    sc = spec["sbc"]
    floor = float(sc["pass_pvalue_floor"])
    config = _sbc_config(sc)
    good = _model(spec, Fraction(1))
    good_lh = sbc_lineage_hash(good, config)
    good_sbc = run_sbc(good, n_simulations=int(sc["n_simulations"]),
                       n_draws=int(sc["n_posterior_draws"]),
                       seed=int(sc["seed"]), n_bins=int(sc["n_bins"]),
                       lineage_hash=good_lh, config=config)
    if sbc_verdict(good_sbc, floor) != "calibrated":
        raise SystemExit("the known-good model failed SBC — model/toy "
                         "is mis-set")
    bad_reports = {}
    for vs in (Fraction(1, 2), Fraction(2)):
        bad = _model(spec, vs)
        bad_lh = sbc_lineage_hash(bad, config)
        bs = run_sbc(bad, n_simulations=int(sc["n_simulations"]),
                     n_draws=int(sc["n_posterior_draws"]),
                     seed=int(sc["seed"]), n_bins=int(sc["n_bins"]),
                     lineage_hash=bad_lh, config=config)
        if sbc_verdict(bs, floor) != "inadequate_sbc_failed":
            raise SystemExit(f"known-bad var_scale={vs} did not fail SBC")
        # confirm the SBC-pass claim is refuted for the known-bad model
        try:
            require_sbc_calibrated(bs, floor, "sbc_pass")
            raise SystemExit("known-bad SBC-pass claim was not refuted")
        except InadequateModelError:
            pass
        bad_reports[str(vs)] = {
            "uniformity_pvalue": bs["uniformity_pvalue"],
            "chi_square": bs["chi_square"],
            "verdict": sbc_verdict(bs, floor),
        }
    return {
        "schema": "pr138.sbc_report.v1",
        "module_schema": SCHEMA_VERSION,
        "reference": sc["reference"],
        "pass_pvalue_floor": floor,
        "n_bins": good_sbc["n_bins"],
        "dof": good_sbc["dof"],
        "known_good": {
            "uniformity_pvalue": good_sbc["uniformity_pvalue"],
            "chi_square": good_sbc["chi_square"],
            "rank_histogram_binned": good_sbc["rank_histogram_binned"],
            "lineage_verified": good_sbc["lineage_verified"],
            "verdict": sbc_verdict(good_sbc, floor),
        },
        "known_bad": bad_reports,
    }


def build_ppc(spec: dict) -> tuple[dict, dict]:
    import numpy as np

    pc = spec["ppc"]
    reject = float(pc["bayesian_p_two_sided_reject"])
    good = _model(spec, Fraction(1))
    frozen = freeze_discrepancies(pc["frozen_discrepancies"])
    # a fixed, seeded observed data set from the known-good model
    rng = np.random.Generator(np.random.PCG64(int(pc["seed"]) - 1))
    y_obs = rng.normal(0.5, float(good.sig2) ** 0.5, good.n_obs)
    dh = hashlib.sha256(np.asarray(y_obs).tobytes()).hexdigest()[:16]
    config = {"n_predictive": str(pc["n_posterior_predictive"])}
    diagnostics = {"sampler": "exact_conjugate", "rhat": "1.0"}
    lh = lineage_hash(good, dh, config, diagnostics)
    lineage = {"claimed_hash": lh, "data_hash": dh, "config": config,
               "diagnostics": diagnostics}
    ppc = run_ppc(good, y_obs, frozen,
                  n_predictive=int(pc["n_posterior_predictive"]),
                  seed=int(pc["seed"]), lineage=lineage)
    require_ppc_receipt(ppc)
    verdict = ppc_verdict(ppc, reject)
    # KNOWN-BAD PPC demonstration: a mis-specified under-dispersed fit
    # (fit_sig2 = 1/9) is DEMONSTRATED to produce extreme p-values and
    # the inadequate verdict. Its lineage binds the mis-specified fit.
    fit_sig2 = float(Fraction(pc["known_bad_fit_sig2"]))
    bad_fit = GaussianModel(good.tau2,
                            Fraction(fit_sig2).limit_denominator(10 ** 9),
                            good.n_obs, good.var_scale)
    bad_lh = lineage_hash(bad_fit, dh, config, diagnostics)
    bad_lineage = {"claimed_hash": bad_lh, "data_hash": dh,
                   "config": config, "diagnostics": diagnostics}
    bad_ppc = run_ppc(good, y_obs, frozen,
                      n_predictive=int(pc["n_posterior_predictive"]),
                      seed=int(pc["seed"]), fit_sig2=fit_sig2,
                      lineage=bad_lineage)
    bad_verdict = ppc_verdict(bad_ppc, reject)
    if bad_verdict != "inadequate_ppc_extreme":
        raise SystemExit(
            f"the known-bad PPC (fit_sig2={fit_sig2}) did not fail "
            f"(verdict {bad_verdict}) — the demonstration is broken")
    lineage_record = {
        "schema": "pr138.lineage.v1",
        "lineage_hash": lh,
        "inputs": good.lineage_inputs(),
        "data_hash": dh,
        "config": config,
        "diagnostics": diagnostics,
        "note": "the posterior draws are content-addressed to these "
                "inputs; a PPC on a mismatched lineage is refused",
    }
    ppc_record = {
        "schema": "pr138.ppc_report.v1",
        "frozen_hash": frozen["frozen_hash"],
        "frozen_discrepancies": frozen["discrepancies"],
        "two_sided_reject": reject,
        "n_predictive": ppc["n_predictive"],
        "known_good": {
            "fit_sig2": ppc["fit_sig2"],
            "lineage_verified": ppc["lineage_verified"],
            "discrepancy_results": ppc["discrepancy_results"],
            "verdict": verdict,
        },
        "known_bad_misspecified": {
            "fit_sig2": bad_ppc["fit_sig2"],
            "lineage_verified": bad_ppc["lineage_verified"],
            "discrepancy_results": bad_ppc["discrepancy_results"],
            "verdict": bad_verdict,
        },
        "verdict": verdict,
        "verdict_note": "a PPC pass is model/transfer-conditional "
                        "predictive adequacy, NOT model truth; the "
                        "known-bad mis-specified fit is demonstrated to "
                        "fail",
    }
    return ppc_record, lineage_record


def build_residual(spec: dict) -> dict:
    import numpy as np

    good = _model(spec, Fraction(1))
    rng = np.random.Generator(np.random.PCG64(777))
    y_obs = rng.normal(0.5, float(good.sig2) ** 0.5, good.n_obs)
    rc = standardized_residual_check(good, y_obs, 0.5)
    require_not_ppc(rc)
    return {"schema": "pr138.residual_check.v1", **rc}


def build_captions(sbc: dict, ppc: dict) -> dict:
    bad_verdicts = [v["verdict"] for v in sbc["known_bad"].values()]
    text = generate_caption(sbc["known_good"]["uniformity_pvalue"],
                            bad_verdicts, ppc["verdict"])
    lint_caption(text)
    return {"schema": "pr138.captions.v1", "captions": {"summary": text}}


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
    import numpy as np

    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])
    good = _model(spec, Fraction(1))
    frozen = freeze_discrepancies(spec["ppc"]["frozen_discrepancies"])

    def mutant_caller_prediction_as_ppc() -> None:
        require_ppc_receipt({"kind": "caller_prediction",
                            "point_prediction": 0.5, "bayesian_p": 0.5})

    def mutant_discrepancy_swap_after_failure() -> None:
        require_frozen_discrepancies(
            frozen, ["sample_variance", "sample_mean"])

    def mutant_ppc_on_invalid_posterior() -> None:
        require_valid_posterior(float("nan"))

    def mutant_known_bad_sbc_passes() -> None:
        bad = _model(spec, Fraction(1, 2))
        cfg = _sbc_config(spec["sbc"])
        bs = run_sbc(bad, n_simulations=1000, n_draws=20,
                     seed=int(spec["sbc"]["seed"]),
                     n_bins=int(spec["sbc"]["n_bins"]),
                     lineage_hash=sbc_lineage_hash(bad, cfg), config=cfg)
        require_sbc_calibrated(bs, float(spec["sbc"]["pass_pvalue_floor"]),
                               "sbc_pass")

    def mutant_lineage_mismatch() -> None:
        y = np.array([0.1, 0.2, 0.3])
        dh = hashlib.sha256(y.tobytes()).hexdigest()[:16]
        lh = lineage_hash(good, dh, {"n": "8"}, {"rhat": "1.0"})
        verify_lineage(lh, good, dh, {"n": "9"}, {"rhat": "1.0"})

    def mutant_residual_as_ppc() -> None:
        require_not_ppc({"type": "residual_check", "is_ppc": True})

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "caller_prediction_as_ppc": mutant_caller_prediction_as_ppc,
        "discrepancy_swap_after_failure":
            mutant_discrepancy_swap_after_failure,
        "ppc_on_invalid_posterior": mutant_ppc_on_invalid_posterior,
        "known_bad_sbc_passes": mutant_known_bad_sbc_passes,
        "lineage_mismatch": mutant_lineage_mismatch,
        "residual_as_ppc": mutant_residual_as_ppc,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except SbcPpcError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr138.mutation_report.v1",
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
    if spec.get("schema") != "htt.long_horizon.pr138_sbc_ppc.v1":
        raise SystemExit("pr138 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    problems: list[str] = []
    wrote: list[str] = []

    sbc = build_sbc(spec)
    sbc["prohibition_cross_list_covered"] = cross_covered
    ppc, lineage = build_ppc(spec)
    residual = build_residual(spec)
    captions = build_captions(sbc, ppc)
    sbc["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["sbc"], sbc, write, problems, wrote)
    _emit(OUTPUTS["ppc"], ppc, write, problems, wrote)
    _emit(OUTPUTS["lineage"], lineage, write, problems, wrote)
    _emit(OUTPUTS["residual"], residual, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr138.artifact_manifest.v1",
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
            for rel in ("htt/src/common/sbc_ppc.py",)
        ],
        "caveats": [
            "Model/transfer-conditional predictive-adequacy mechanics "
            "at C2 only.",
            "A PPC pass is conditional adequacy, NEVER model truth; a "
            "failure is inadequacy, not a threshold-tuning opportunity.",
            "SBC is computation calibration, not observed-fit "
            "validation.",
            "The residual_check is a separate plug-in type, never a PPC.",
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
    module_text = (REPO / "htt/src/common/sbc_ppc.py").read_text(
        encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "good_sbc_p": sbc["known_good"]["uniformity_pvalue"],
        "known_bad_all_inadequate": all(
            v["verdict"] == "inadequate_sbc_failed"
            for v in sbc["known_bad"].values()),
        "ppc_verdict": ppc["verdict"],
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
