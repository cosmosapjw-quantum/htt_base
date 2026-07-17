#!/usr/bin/env python3
"""PR-139 runner: dependency-aware holdout and train-only refit.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the exact group-refit ELPD (train-only transforms), the PSIS
report verified against the exact refit, the leakage report (leaky
preprocessing inflates the held-out score), the dependency report
(group-joint vs optimistic row-level holdout, plus LOO_not_identified),
generated captions, and the six-mutant kill report.

Dependency-qualified held-out predictive-score mechanics at
roadmap_rescue_v1:C2; a channel ablation or evidence difference is never
a LOO score; no detection.
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

from common.dependency_holdout import (  # noqa: E402
    SCHEMA_VERSION,
    DependencyGraph,
    GroupModel,
    HoldoutError,
    HoldoutStatus,
    compare_exact_psis,
    dependency_optimism,
    exact_group_elpd,
    generate_caption,
    influential_folds,
    lint_caption,
    psis_group_elpd,
    refuse_as_loo,
    require_exchangeable_unit,
    require_reliable_or_exact,
    require_train_only,
    require_units_respect_dependency,
    select_features,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr139_spec.yaml"
OUTPUTS = {
    "elpd": "docs/generated/pr139_elpd_report.json",
    "psis": "docs/generated/pr139_psis_report.json",
    "leakage": "docs/generated/pr139_leakage_report.json",
    "dependency": "docs/generated/pr139_dependency_report.json",
    "captions": "docs/generated/pr139_captions.json",
    "mutations": "docs/generated/pr139_mutation_report.json",
    "manifest": "docs/generated/pr139_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _round(obj):
    """Round every float to 8 decimals so --check is byte-stable."""
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


def _build_dataset(spec: dict, cfg: dict):
    m = spec["model"]
    intercept = float(Fraction(m["intercept"]))
    sig2 = float(Fraction(m["sig2"]))
    prior_tau2 = float(Fraction(m["prior_tau2"]))
    G = int(cfg["n_groups"])
    ng = int(cfg["rows_per_group"])
    pc = int(cfg["n_candidate_features"])
    pt = int(cfg["n_true_features"])
    tau_b2 = float(Fraction(cfg["tau_b2"]))
    betas = np.array([float(Fraction(b)) for b in cfg["beta_true"]])
    N = G * ng
    groups = tuple(int(i // ng) for i in range(N))
    rng = np.random.Generator(np.random.PCG64(int(cfg["data_seed"])))
    X = rng.standard_normal((N, pc))
    b_g = rng.normal(0.0, tau_b2 ** 0.5, G)
    eps = rng.normal(0.0, sig2 ** 0.5, N)
    signal = X[:, :pt] @ betas if pt > 0 else np.zeros(N)
    y = intercept + signal + np.array([b_g[groups[i]] for i in range(N)]) + eps
    model = GroupModel(X=X, y=y, group=groups, sig2=sig2, tau_b2=tau_b2,
                       prior_tau2=prior_tau2)
    graph = DependencyGraph("group", tuple(groups))
    return model, graph


def build_elpd(spec: dict):
    cfg = spec["model"]["signal_config"]
    model, graph = _build_dataset(spec, cfg)
    pt = int(cfg["n_true_features"])
    exact = exact_group_elpd(model, graph, cols=range(pt))
    scopes = {f["standardize_scope"] for f in exact["folds"]} | \
        {f["selection_scope"] for f in exact["folds"]}
    if scopes != {"train_only"}:
        raise SystemExit(f"exact ELPD used a non-train-only transform: "
                         f"{scopes}")
    # every fold's train-only transform is refused if marked full_data
    for f in exact["folds"]:
        require_train_only({"scope": f["standardize_scope"]})
    return exact, model, graph, pt


def build_psis(spec: dict, model, graph, pt: int, exact: dict):
    pc = spec["psis"]
    psis = psis_group_elpd(model, graph, n_draws=int(pc["n_posterior_draws"]),
                           seed=int(pc["seed"]), cols=range(pt))
    k_thr = float(Fraction(pc["pareto_k_threshold"]))
    tol = float(Fraction(pc["elpd_agreement_tol"]))
    comparison = compare_exact_psis(exact, psis, tol, k_thr)
    if not comparison["psis_reliable"]:
        raise SystemExit(f"PSIS unreliable (max k "
                         f"{comparison['max_pareto_k']}) — the toy must "
                         "yield a well-conditioned PSIS demonstration")
    if not comparison["psis_agrees_with_exact"]:
        raise SystemExit("PSIS and exact refit disagree beyond tolerance")
    # the reliability guard passes for the reliable case
    require_reliable_or_exact(psis, k_thr, used_exact_fallback=False)
    return {
        "schema": "pr139.psis_report.v1",
        "reference": pc["reference"],
        "n_draws": psis["n_draws"],
        "seed": psis["seed"],
        "elpd": psis["elpd"],
        "elpd_per_obs": psis["elpd_per_obs"],
        "max_pareto_k": psis["max_pareto_k"],
        "comparison": comparison,
        "influential_folds": influential_folds(psis, k_thr),
        "per_fold": psis["folds"],
    }, comparison


def build_leakage(spec: dict):
    cfg = spec["model"]["leakage_config"]
    model, graph = _build_dataset(spec, cfg)
    k = int(spec["leakage"]["select_k"])
    train_only = exact_group_elpd(model, graph, select_k=k,
                                  leaky_selection=False)
    leaky_sel = exact_group_elpd(model, graph, select_k=k,
                                 leaky_selection=True)
    leaky_std = exact_group_elpd(model, graph, select_k=k,
                                 leaky_selection=False,
                                 leaky_standardize=True)
    sel_gap = leaky_sel["elpd"] - train_only["elpd"]
    std_gap = leaky_std["elpd"] - train_only["elpd"]
    if sel_gap <= 1.0:
        raise SystemExit(f"selection leakage gap {sel_gap:.3f} is not "
                         "demonstrably optimistic")
    # a full-data selection provenance is refused by the train-only guard
    _, leaky_meta = select_features(model.X, model.y,
                                    list(range(model.X.shape[0])), k,
                                    "full_data")
    leaky_refused = False
    try:
        require_train_only(leaky_meta["provenance"])
    except HoldoutError:
        leaky_refused = True
    if not leaky_refused:
        raise SystemExit("a full-data selection provenance was not refused")
    return {
        "schema": "pr139.leakage_report.v1",
        "select_k": k,
        "train_only_elpd": train_only["elpd"],
        "leaky_selection_elpd": leaky_sel["elpd"],
        "leaky_standardize_elpd": leaky_std["elpd"],
        "selection_leakage_gap": sel_gap,
        "standardize_leakage_gap": std_gap,
        "leaky_selection_chosen_first_fold":
            leaky_sel["folds"][0]["chosen_features"],
        "train_only_chosen_first_fold":
            train_only["folds"][0]["chosen_features"],
        "full_data_provenance_refused": leaky_refused,
        "note": "leaky (full-data) preprocessing inflates the held-out "
                "ELPD; the material effect is feature selection on the "
                "held-out fold; a full-data transform provenance is "
                "refused by the train-only guard",
    }


def build_dependency(spec: dict):
    cfg = spec["model"]["dependency_config"]
    model, graph = _build_dataset(spec, cfg)
    pt = int(cfg["n_true_features"])
    opt = dependency_optimism(model, graph, cols=range(pt))
    if opt["row_optimism"] <= 0.0:
        raise SystemExit("row-level holdout was not shown optimistic")
    if not opt["row_fold_split_refused"]:
        raise SystemExit("a row-level fold-split was not refused")
    # LOO_not_identified: a single cluster over every row has no unit
    single = DependencyGraph("group", tuple(0 for _ in model.group))
    if single.status() is not HoldoutStatus.LOO_NOT_IDENTIFIED:
        raise SystemExit("single-cluster graph was not LOO_not_identified")
    not_identified_refused = False
    try:
        require_exchangeable_unit(single)
    except HoldoutError:
        not_identified_refused = True
    return {
        "schema": "pr139.dependency_report.v1",
        "unit_kind": graph.unit_kind,
        "n_groups": len(graph.folds()),
        "group_loo_per_obs": opt["group_loo_per_obs"],
        "row_loo_per_obs": opt["row_loo_per_obs"],
        "row_optimism": opt["row_optimism"],
        "row_fold_split_refused": opt["row_fold_split_refused"],
        "single_cluster_status": single.status().value,
        "single_cluster_refused": not_identified_refused,
        "note": opt["note"],
    }


def build_captions(exact: dict, comparison: dict, leakage: dict) -> dict:
    text = generate_caption(exact["elpd_per_obs"],
                            comparison["max_pareto_k"],
                            leakage["selection_leakage_gap"],
                            HoldoutStatus.LOO_IDENTIFIED.value)
    lint_caption(text)
    return {"schema": "pr139.captions.v1", "captions": {"summary": text}}


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
    dep_cfg = spec["model"]["dependency_config"]
    model, graph = _build_dataset(spec, dep_cfg)
    group_folds = [list(model.rows_of_group(g)) for g in model.group_ids()]

    def mutant_dependent_rows_as_loo_unit() -> None:
        row_folds = [[i] for i in range(model.X.shape[0])]
        require_units_respect_dependency(row_folds, group_folds)

    def mutant_selection_leakage() -> None:
        require_train_only({"scope": "full_data", "k": 3})

    def mutant_standardize_leakage() -> None:
        require_train_only({"scope": "full_data", "means": [], "stds": []})

    def mutant_psis_used_when_unreliable() -> None:
        require_reliable_or_exact({"max_pareto_k": 1.4}, 0.7,
                                  used_exact_fallback=False)

    def mutant_ablation_labeled_loo() -> None:
        refuse_as_loo("channel_ablation")

    def mutant_loo_on_single_cluster() -> None:
        single = DependencyGraph("group", tuple(0 for _ in model.group))
        require_exchangeable_unit(single)

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "dependent_rows_as_loo_unit": mutant_dependent_rows_as_loo_unit,
        "selection_leakage": mutant_selection_leakage,
        "standardize_leakage": mutant_standardize_leakage,
        "psis_used_when_unreliable": mutant_psis_used_when_unreliable,
        "ablation_labeled_loo": mutant_ablation_labeled_loo,
        "loo_on_single_cluster": mutant_loo_on_single_cluster,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except HoldoutError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr139.mutation_report.v1", "mutations": rows,
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
    if spec.get("schema") != "htt.long_horizon.pr139_holdout.v1":
        raise SystemExit("pr139 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    exact, model, graph, pt = build_elpd(spec)
    exact_record = {"schema": "pr139.elpd_report.v1", **exact}
    psis_record, comparison = build_psis(spec, model, graph, pt, exact)
    leakage = build_leakage(spec)
    dependency = build_dependency(spec)
    captions = build_captions(exact, comparison, leakage)
    exact_record["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["elpd"], exact_record, write, problems, wrote)
    _emit(OUTPUTS["psis"], psis_record, write, problems, wrote)
    _emit(OUTPUTS["leakage"], leakage, write, problems, wrote)
    _emit(OUTPUTS["dependency"], dependency, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr139.artifact_manifest.v1",
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
            for rel in ("htt/src/common/dependency_holdout.py",)
        ],
        "caveats": [
            "Dependency-qualified held-out predictive-score mechanics at "
            "C2 only.",
            "The exchangeable unit is the group; row-level holdout on "
            "correlated rows is optimistic.",
            "PSIS is reported only when reliable (Pareto k <= 0.7) and "
            "verified against the exact refit; otherwise the exact refit "
            "is required.",
            "A channel ablation or full-vs-fold evidence difference is "
            "NEVER a LOO score.",
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
    module_text = (REPO / "htt/src/common/dependency_holdout.py").read_text(
        encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "exact_elpd_per_obs": round(exact["elpd_per_obs"], 6),
        "psis_max_pareto_k": round(psis_record["max_pareto_k"], 6),
        "psis_agrees": comparison["psis_agrees_with_exact"],
        "selection_leakage_gap": round(leakage["selection_leakage_gap"], 6),
        "row_optimism": round(dependency["row_optimism"], 6),
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
