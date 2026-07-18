#!/usr/bin/env python3
"""PR-141 runner: contamination-aware mixture with mandatory abstention.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the recovery/confusion/abstention matrix over the four explicit
competitors, the two extra abstention demos (inadequate, prior-sensitive),
the deterministic-vs-covariance branch comparison, generated captions,
and the six-mutant kill report.

Local/global discrimination-candidate mechanics at roadmap_rescue_v1:C3;
a candidate is never a detection, a geometry, or a family.
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

from common.mixture_competition import (  # noqa: E402
    ABSTENTIONS,
    MODELS,
    SCHEMA_VERSION,
    CompetitionError,
    DiscriminationConfig,
    GenerativeBranch,
    Outcome,
    all_evidences,
    build_templates,
    confusion_matrix,
    deterministic_profile_loglik,
    discriminate,
    generate_caption,
    generate_data,
    lint_caption,
    log_evidence,
    model_list_fingerprint,
    refuse_deterministic_as_evidence,
    refuse_mio_as_likelihood,
    refuse_residual_absorption,
    require_not_detection,
    require_registered_model_list,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr141_spec.yaml"
OUTPUTS = {
    "confusion": "docs/generated/pr141_confusion_matrix.json",
    "demos": "docs/generated/pr141_abstention_demos.json",
    "branch": "docs/generated/pr141_branch_comparison.json",
    "captions": "docs/generated/pr141_captions.json",
    "mutations": "docs/generated/pr141_mutation_report.json",
    "manifest": "docs/generated/pr141_artifact_manifest.json",
}
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


def _config(spec: dict, **override) -> DiscriminationConfig:
    d = spec["decision"]
    m = spec["model"]
    base = dict(
        sig2=float(Fraction(m["sig2"])), tau2=float(Fraction(m["tau2"])),
        gain_margin_log_bf=float(Fraction(d["gain_margin_log_bf"])),
        identifiability_gap=float(Fraction(d["identifiability_gap"])),
        collinearity_threshold=float(Fraction(d["collinearity_threshold"])),
        ppc_reject=float(Fraction(d["ppc_reject"])),
        prior_swing_ceiling=float(Fraction(d["prior_swing_ceiling"])),
        tau2_grid=tuple(float(Fraction(t)) for t in d["tau2_grid"]),
        held_out_gain_floor=float(Fraction(d["held_out_gain_floor"])),
        combination_margin=float(Fraction(d["combination_margin"])),
        seed=int(d["seed"]))
    base.update(override)
    return DiscriminationConfig(**base)


def build_confusion(spec: dict):
    m = spec["model"]
    config = _config(spec)
    regimes = {name: {"collinear": bool(p["collinear"]),
                      "amplitude": float(Fraction(p["amplitude"]))}
               for name, p in spec["regimes"].items()
               if name != "expected"}
    cm = confusion_matrix(regimes, config, n=int(m["n_obs"]),
                          template_seed=int(m["template_seed"]),
                          data_seed=int(m["data_seed"]))
    # verify the pre-registered expectations
    by_cell = {(r["regime"], r["true_branch"]): r for r in cm["rows"]}
    for true in ("local", "sys", "global"):
        if by_cell[("clean", true)]["outcome"] != \
                Outcome.DISCRIMINATION_CANDIDATE.value:
            raise SystemExit(f"clean/{true} did not recover a candidate")
    for true in ("local", "sys"):
        if by_cell[("confused", true)]["outcome"] != \
                Outcome.ABSTAIN_NON_IDENTIFIED.value:
            raise SystemExit(f"confused/{true} was not non_identified")
    if by_cell[("confused", "global")]["outcome"] != \
            Outcome.DISCRIMINATION_CANDIDATE.value:
        raise SystemExit("confused/global did not recover global")
    for true in ("iso", "local", "sys", "global"):
        if by_cell[("weak", true)]["outcome"] != \
                Outcome.ABSTAIN_NO_GAIN.value:
            raise SystemExit(f"weak/{true} was not abstain_no_gain")
    abstain_values = {o.value for o in ABSTENTIONS}
    n_recovered = sum(1 for r in cm["rows"] if r["recovered"])
    n_abstained = sum(1 for r in cm["rows"]
                      if r["outcome"] in abstain_values)
    return {"schema": "pr141.confusion_matrix.v1",
            "module_schema": SCHEMA_VERSION,
            "model_list_fingerprint": model_list_fingerprint(),
            "n_cells": len(cm["rows"]), "n_recovered": n_recovered,
            "n_abstained": n_abstained, "rows": cm["rows"]}, \
        n_recovered, n_abstained


def build_demos(spec: dict) -> dict:
    m = spec["model"]
    n = int(m["n_obs"])
    templates = build_templates(n, int(m["template_seed"]), collinear=False)
    # inadequate: global signal + heavy outlier contamination
    a = spec["abstention_demos"]["inadequate"]
    rng = np.random.Generator(np.random.PCG64(int(a["seed"])))
    y_bad = float(Fraction(a["amplitude"])) * templates["quad"] \
        + rng.normal(0.0, float(Fraction(m["sig2"])) ** 0.5, n)
    idx = slice(0, int(a["n_outliers"]))
    y_bad[idx] = y_bad[idx] + float(Fraction(a["outlier_scale"])) \
        * rng.standard_normal(int(a["n_outliers"]))
    dec_inadeq = discriminate(y_bad, templates, _config(spec))
    if dec_inadeq["outcome"] != Outcome.ABSTAIN_INADEQUATE.value:
        raise SystemExit(f"inadequate demo did not abstain_inadequate "
                         f"(got {dec_inadeq['outcome']})")
    inadeq_detection_refused = _detection_refused(dec_inadeq)
    # prior-sensitive: marginal global signal, wide prior grid
    p = spec["abstention_demos"]["prior_sensitive"]
    cfg_ps = _config(
        spec,
        tau2_grid=tuple(float(Fraction(t)) for t in p["tau2_grid"]),
        prior_swing_ceiling=float(Fraction(p["prior_swing_ceiling"])),
        gain_margin_log_bf=float(Fraction(p["gain_margin_log_bf"])),
        ppc_reject=float(Fraction(p["ppc_reject"])),
        held_out_gain_floor=float(Fraction(p["held_out_gain_floor"])))
    rng2 = np.random.Generator(np.random.PCG64(int(p["seed"])))
    y_ps = float(Fraction(p["amplitude"])) * templates["quad"] \
        + rng2.normal(0.0, float(Fraction(m["sig2"])) ** 0.5, n)
    dec_ps = discriminate(y_ps, templates, cfg_ps)
    if dec_ps["outcome"] != Outcome.ABSTAIN_PRIOR_SENSITIVE.value:
        raise SystemExit(f"prior-sensitive demo did not abstain "
                         f"(got {dec_ps['outcome']})")
    ps_detection_refused = _detection_refused(dec_ps)
    # superposed: a genuine two-component (local + global) signal outside the
    # single-component list abstains non_identified via the combined-model gate
    sp = spec["abstention_demos"]["superposed"]
    rng3 = np.random.Generator(np.random.PCG64(int(sp["seed"])))
    y_sp = float(Fraction(sp["dipole_amplitude"])) * templates["dipole"] \
        + float(Fraction(sp["quad_amplitude"])) * templates["quad"] \
        + rng3.normal(0.0, float(Fraction(m["sig2"])) ** 0.5, n)
    dec_sp = discriminate(y_sp, templates, _config(spec))
    if dec_sp["outcome"] != Outcome.ABSTAIN_NON_IDENTIFIED.value:
        raise SystemExit(f"superposed demo did not abstain non_identified "
                         f"(got {dec_sp['outcome']})")
    sp_detection_refused = _detection_refused(dec_sp)
    return {
        "schema": "pr141.abstention_demos.v1",
        "inadequate": {"outcome": dec_inadeq["outcome"],
                       "ppc_pvalue": dec_inadeq["ppc_pvalue"],
                       "log_bf_vs_iso": dec_inadeq["log_bf_vs_iso"],
                       "held_out_gain": dec_inadeq["held_out_gain"],
                       "detection_refused": inadeq_detection_refused},
        "prior_sensitive": {"outcome": dec_ps["outcome"],
                            "prior_swing": dec_ps["prior_swing"],
                            "log_bf_vs_iso": dec_ps["log_bf_vs_iso"],
                            "ppc_pvalue": dec_ps["ppc_pvalue"],
                            "detection_refused": ps_detection_refused},
        "superposed": {"outcome": dec_sp["outcome"],
                       "combination_gain": dec_sp["combination_gain"],
                       "multi_component": dec_sp["multi_component"],
                       "detection_refused": sp_detection_refused},
        "note": "the inadequate, prior-sensitive, and two-component "
                "superposition gates are exercised on the production path; "
                "each yields a mandatory abstention and a refused detection "
                "claim. Identifiability is governed by the evidence gap, not "
                "template collinearity, so an orthogonal-template "
                "local/global near-tie also abstains.",
    }


def _detection_refused(decision: dict) -> bool:
    try:
        require_not_detection(decision)
        return False
    except CompetitionError:
        return True


def build_branch_comparison(spec: dict) -> dict:
    """Deterministic profile vs covariance evidence under a weak signal."""
    m = spec["model"]
    n = int(m["n_obs"])
    sig2 = float(Fraction(m["sig2"]))
    tau2 = float(Fraction(m["tau2"]))
    templates = build_templates(n, int(m["template_seed"]), collinear=False)
    # a weak global signal: the profile always favors the bigger model, the
    # marginal evidence does not
    y = 0.2 * templates["quad"] + np.random.Generator(
        np.random.PCG64(100)).normal(0.0, sig2 ** 0.5, n)
    profile = {mm: deterministic_profile_loglik(y, templates, cols, sig2)
               for mm, cols in MODELS.items()}
    evidence = all_evidences(y, templates, sig2, tau2)
    profile_best = max(profile, key=profile.get)
    evidence_best = max(evidence, key=evidence.get)
    # the deterministic branch is refused for model comparison
    refused = False
    try:
        refuse_deterministic_as_evidence(GenerativeBranch.DETERMINISTIC)
    except CompetitionError:
        refused = True
    return {
        "schema": "pr141.branch_comparison.v1",
        "deterministic_profile_loglik": profile,
        "covariance_log_evidence": evidence,
        "profile_favors": profile_best,
        "evidence_favors": evidence_best,
        "deterministic_branch_refused_for_comparison": refused,
        "note": "the deterministic profile log-likelihood favors the "
                "largest model regardless of signal, whereas the covariance "
                "evidence penalizes the extra parameter under a weak signal; "
                "the branches are separate and the deterministic branch is "
                "never used for model comparison",
    }


def build_captions(confusion: dict) -> dict:
    text = generate_caption(confusion["n_recovered"],
                            confusion["n_abstained"], confusion["n_cells"])
    lint_caption(text)
    return {"schema": "pr141.captions.v1", "captions": {"summary": text}}


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
    abstain = {"outcome": Outcome.ABSTAIN_NON_IDENTIFIED.value}

    def mutant_residual_absorption() -> None:
        refuse_residual_absorption("absorb_into_global")

    def mutant_mio_score_as_likelihood() -> None:
        refuse_mio_as_likelihood("mio_score")

    def mutant_posthoc_model_change() -> None:
        require_registered_model_list(
            tuple(MODELS) + ("extra",), seen_outcome=True,
            supersedes=None, multiplicity=None)

    def mutant_detection_when_abstention_required() -> None:
        require_not_detection(abstain)

    def mutant_deterministic_as_evidence() -> None:
        refuse_deterministic_as_evidence(GenerativeBranch.DETERMINISTIC)

    def mutant_unregistered_model_before_outcome() -> None:
        require_registered_model_list(
            ("iso", "local"), seen_outcome=False,
            supersedes=None, multiplicity=None)

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "residual_absorption": mutant_residual_absorption,
        "mio_score_as_likelihood": mutant_mio_score_as_likelihood,
        "posthoc_model_change": mutant_posthoc_model_change,
        "detection_when_abstention_required":
            mutant_detection_when_abstention_required,
        "deterministic_as_evidence": mutant_deterministic_as_evidence,
        "unregistered_model_before_outcome":
            mutant_unregistered_model_before_outcome,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except CompetitionError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr141.mutation_report.v1", "mutations": rows,
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
    elif target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr141_mixture.v1":
        raise SystemExit("pr141 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    confusion, n_recovered, n_abstained = build_confusion(spec)
    demos = build_demos(spec)
    branch = build_branch_comparison(spec)
    captions = build_captions(confusion)
    confusion["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["confusion"], confusion, write, problems, wrote)
    _emit(OUTPUTS["demos"], demos, write, problems, wrote)
    _emit(OUTPUTS["branch"], branch, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr141.artifact_manifest.v1",
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
            for rel in ("htt/src/common/mixture_competition.py",)
        ],
        "caveats": [
            "Local/global discrimination-candidate mechanics conditional "
            "on the registered model list at C3 only.",
            "The ONLY admissible non-null result is a discrimination "
            "candidate when every gate passes; otherwise the mandatory "
            "result is abstain / non_identified.",
            "A discrimination candidate is NOT a detection, a geometry, or "
            "a Bianchi family.",
            "The deterministic and covariance branches are separate; a MIO "
            "score is never a likelihood.",
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
    module_text = (REPO / "htt/src/common/mixture_competition.py").read_text(
        encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "n_recovered": n_recovered, "n_abstained": n_abstained,
        "n_cells": confusion["n_cells"],
        "inadequate_demo": demos["inadequate"]["outcome"],
        "prior_sensitive_demo": demos["prior_sensitive"]["outcome"],
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
