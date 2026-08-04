#!/usr/bin/env python3
"""Portable intake, generation, validation, and test runner for PR-279."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PROGRAM_DIR = ROOT / "docs/research_program/post_pr275"
SPEC = PROGRAM_DIR / "pr279_spec.yaml"
SNAPSHOT = PROGRAM_DIR / "pr279_source_snapshot.yaml"
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
OUTPUTS = {
    "ledger": PROGRAM_DIR / "PR_RETRACE_LEDGER.yaml",
    "github": PROGRAM_DIR / "github_publication_review_index.yaml",
    "graph": PROGRAM_DIR / "semantic_invalidation_graph.yaml",
    "supersession": PROGRAM_DIR / "supersession_map.yaml",
    "recompute": PROGRAM_DIR / "recompute_matrix.yaml",
    "failure_debt": PROGRAM_DIR / "failure_debt.yaml",
    "runbooks": PROGRAM_DIR / "data_runbooks.yaml",
    "inventory": PROGRAM_DIR / "data_artifact_disposition.yaml",
}


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    source_paths = [
        str(ROOT / "htt/src"),
        str(ROOT / "htt"),
        str(ROOT / "htt/htt"),
    ]
    existing = environment.get("PYTHONPATH")
    if existing:
        source_paths.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(source_paths)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["MPLBACKEND"] = "Agg"
    return environment


def _module():
    source = str(ROOT / "htt/src")
    if source not in sys.path:
        sys.path.insert(0, source)
    import common.pr_retrace as pr_retrace

    return pr_retrace


def _json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _regular_file(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} is missing, non-regular, or a symlink: {path}")
    return resolved


def _intake(args: argparse.Namespace) -> int:
    module = _module()
    inputs = {
        "internal_csv": _regular_file(Path(args.internal_csv), "internal CSV"),
        "github_csv": _regular_file(Path(args.github_csv), "GitHub CSV"),
        "redo_campaign_yaml": _regular_file(
            Path(args.redo_campaign_yaml), "redo campaign YAML"
        ),
        "proposal": _regular_file(
            Path(args.data_group_proposal), "data-group proposal"
        ),
    }
    proposal = _json_mapping(inputs["proposal"])
    spec = module.load_yaml_mapping(SPEC)
    snapshot = module.build_source_snapshot(
        internal_csv=inputs["internal_csv"],
        github_csv=inputs["github_csv"],
        redo_campaign_yaml=inputs["redo_campaign_yaml"],
        data_group_proposal=proposal,
        data_group_proposal_sha256=module.file_sha256(inputs["proposal"]),
        spec=spec,
    )
    module.validate_source_snapshot(snapshot, spec=spec)
    SNAPSHOT.write_bytes(module.dump_yaml_bytes(snapshot))
    print(
        json.dumps(
            {
                "ok": True,
                "mode": "intake",
                "snapshot": str(SNAPSHOT.relative_to(ROOT)),
                "internal_records": 222,
                "github_records": 366,
                "data_groups": 45,
            },
            sort_keys=True,
        )
    )
    return 0


def _build_documents() -> dict[str, dict[str, object]]:
    module = _module()
    spec = module.load_yaml_mapping(SPEC)
    snapshot = module.load_yaml_mapping(SNAPSHOT)
    backlog = module.load_yaml_mapping(BACKLOG)
    status = module.load_yaml_mapping(STATUS)
    module.validate_source_snapshot(snapshot, spec=spec)
    ledger = module.build_internal_ledger_from_snapshot(
        snapshot=snapshot,
        spec=spec,
        backlog=backlog,
        status=status,
    )
    module.validate_internal_ledger(
        ledger,
        snapshot=snapshot,
        spec=spec,
        backlog=backlog,
        status=status,
    )
    github = module.build_github_index_from_snapshot(snapshot=snapshot, spec=spec)
    module.validate_github_index(github, snapshot=snapshot, spec=spec)
    inventory = module.build_data_artifact_inventory_from_snapshot(
        snapshot, repo_root=ROOT, spec=spec
    )
    module.validate_data_artifact_inventory(
        inventory, repo_root=ROOT, spec=spec, snapshot=snapshot
    )
    graph = module.build_semantic_invalidation_graph(
        repo_root=ROOT, spec=spec, ledger=ledger, inventory=inventory
    )
    module.validate_semantic_invalidation_graph(
        graph,
        repo_root=ROOT,
        spec=spec,
        ledger=ledger,
        inventory=inventory,
    )
    supersession = module.build_supersession_map(repo_root=ROOT)
    module.validate_supersession_map(supersession, repo_root=ROOT)
    recompute = module.build_recompute_matrix(ledger, inventory)
    module.validate_recompute_matrix(
        recompute, ledger=ledger, inventory=inventory
    )
    failure_debt = module.build_failure_debt(
        backlog=backlog, inventory=inventory
    )
    module.validate_failure_debt(
        failure_debt, backlog=backlog, inventory=inventory
    )
    runbooks = module.build_data_runbooks(backlog=backlog)
    module.validate_data_runbooks(runbooks, backlog=backlog)
    return {
        "ledger": ledger,
        "github": github,
        "graph": graph,
        "supersession": supersession,
        "recompute": recompute,
        "failure_debt": failure_debt,
        "runbooks": runbooks,
        "inventory": inventory,
    }


def _write_or_check(*, write: bool) -> int:
    module = _module()
    documents = _build_documents()
    drift: list[str] = []
    for key, path in OUTPUTS.items():
        expected = module.dump_yaml_bytes(documents[key])
        if write:
            path.write_bytes(expected)
        elif path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
            drift.append(str(path.relative_to(ROOT)))
    summary = {
        "ok": not drift,
        "mode": "build" if write else "check",
        "drift": drift,
        "historical_internal": documents["ledger"]["summary"]["historical_count"],
        "prospective_internal": documents["ledger"]["summary"]["prospective_count"],
        "github_records": documents["github"]["summary"]["record_count"],
        "data_artifacts": documents["inventory"]["summary"]["artifact_count"],
        "invalidation_roots": documents["graph"]["summary"][
            "invalidation_root_count"
        ],
        "withheld_supersessions": documents["supersession"]["summary"][
            "withheld_relation_count"
        ],
        "data_lanes": documents["runbooks"]["summary"]["lane_count"],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if not drift else 1


def _run(arguments: list[str]) -> int:
    return subprocess.run(
        arguments, cwd=ROOT, env=_environment(), check=False
    ).returncode


def _probe() -> int:
    return _run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "from pathlib import Path; import common; "
                "from common import pr_retrace; "
                "root=Path.cwd().resolve(); "
                "paths=[Path(common.__file__).resolve(), "
                "Path(pr_retrace.__file__).resolve()]; "
                "assert all(path.is_relative_to(root) for path in paths); "
                "print('source-layout-ok')"
            ),
        ]
    )


def _pytest(mode: str) -> int:
    common = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
    ]
    if mode == "focused":
        return _run(
            common
            + [
                "tests/contracts/test_pr_retrace_ledger.py",
                "tests/contracts/test_evidence_graph.py",
                "tests/contracts/test_claim_capability_engine.py",
                "tests/pr_cards/test_pr_276_post275_reconciliation.py",
            ]
        )
    if mode == "collect":
        return _run(common + ["--collect-only"])
    return _run(common + ["-m", "smoke"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    intake = subparsers.add_parser("intake")
    intake.add_argument("--internal-csv", required=True)
    intake.add_argument("--github-csv", required=True)
    intake.add_argument("--redo-campaign-yaml", required=True)
    intake.add_argument("--data-group-proposal", required=True)
    for mode in ("build", "check", "probe", "focused", "collect", "smoke"):
        subparsers.add_parser(mode)
    args = parser.parse_args(argv)
    try:
        if args.mode == "intake":
            return _intake(args)
        if args.mode == "build":
            return _write_or_check(write=True)
        if args.mode == "check":
            return _write_or_check(write=False)
        if args.mode == "probe":
            return _probe()
        return _pytest(args.mode)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "mode": args.mode, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
