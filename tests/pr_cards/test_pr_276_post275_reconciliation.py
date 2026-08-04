from __future__ import annotations

import json
import hashlib
import re
import subprocess
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
SPEC = ROOT / "docs/research_program/post_pr275/pr276_spec.yaml"
PUBLICATION_POLICY = (
    ROOT / "docs/research_program/post_pr275/pr276_publication_policy.json"
)
RUNNER = ROOT / "scripts/codex_harness/run_pr276_reconciliation.py"
POST275_IDS = [f"PR-{number:03d}" for number in range(276, 295)]
PR280_ROOT_CAUSE_IDS = ["PR-295", "PR-296", "PR-297"]
COMMON_CARD_FIELDS = {
    "owner",
    "depends",
    "dependency_contracts",
    "capability",
    "inputs",
    "outputs",
    "contributors",
    "adjudicator_role",
    "implementation_scopes",
    "targets",
    "files",
    "tests",
    "dod",
    "kill",
    "claim_tier_ceiling",
    "claim_level",
    "claim_impact",
    "forbidden",
    "anti_drift",
    "roadmap_anchor",
    "activation_state",
    "execution_lane",
    "scientific_artifact_mode",
    "execution_authorization",
    "public_use",
    "spec_first_required",
    "scientific_status_on_intake",
    "track",
    "solver_gate_required",
    "change_set_id",
    "publication_group_id",
}


def _yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _cards() -> dict[str, dict[str, object]]:
    return {card["id"]: card for card in _yaml(BACKLOG)["prs"]}


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=ROOT, text=True, capture_output=True, check=False
    )


def test_verified_pr190_merge_and_terminal_entry_contract_are_frozen() -> None:
    spec = _yaml(SPEC)
    baseline = spec["baseline"]
    assert baseline == {
        "target_branch": "research/pr04-multicomponent",
        "verified_merge_head": "1f11d0df0f55b80439585cf56afef55e9d38599a",
        "merge_subject": "Merge pull request #368 from cosmosapjw-quantum/changeset/pr190-typed-comparator-attainability",
        "first_parent": "7214ef7e91763ed807e0e350e1cfeffb82cec0f5",
        "pr190_candidate": "bae6ac2df15c95ee1e71a3e49b859c0added192d",
        "merge_tree": "32b8a7f464f13fad35e25645aafbac5704fd887b",
        "candidate_tree": "32b8a7f464f13fad35e25645aafbac5704fd887b",
        "ancestry_verified": True,
        "tree_identity_verified": True,
        "pr190_terminal_resolution": "COMPLETED_FAILED_WITH_RECEIPT",
        "pr190_success_dependency_satisfied": False,
        "pr190_receipt": "docs/PR_DELTAS/pr-190.md",
    }
    merge = baseline["verified_merge_head"]
    assert _run("git", "show", "-s", "--format=%P", merge).stdout.strip().split() == [
        baseline["first_parent"],
        baseline["pr190_candidate"],
    ]
    assert _run("git", "show", "-s", "--format=%T", merge).stdout.strip() == baseline[
        "merge_tree"
    ]
    assert _run("git", "show", "-s", "--format=%s", merge).stdout.strip() == baseline[
        "merge_subject"
    ]
    assert _run(
        "git", "show", "-s", "--format=%T", baseline["pr190_candidate"]
    ).stdout.strip() == baseline["candidate_tree"]
    cards = _cards()
    assert cards["PR-276"]["dependency_contracts"] == [
        {"upstream_id": "PR-190", "mode": "requires_terminal_receipt"}
    ]
    for downstream in ("PR-191", "PR-205"):
        assert {"upstream_id": "PR-190", "mode": "requires_success"} in cards[
            downstream
        ]["dependency_contracts"]


def test_post275_cards_are_atomic_complete_and_claim_limited() -> None:
    backlog = _yaml(BACKLOG)
    cards = {card["id"]: card for card in backlog["prs"]}
    assert len(cards) == 244
    assert list(cards)[-22:-3] == POST275_IDS
    assert list(cards)[-3:] == PR280_ROOT_CAUSE_IDS
    assert set(POST275_IDS) <= set(backlog["policy"]["topological_order"])
    assert set(PR280_ROOT_CAUSE_IDS) <= set(
        backlog["policy"]["topological_order"]
    )
    for pr_id in (*POST275_IDS, *PR280_ROOT_CAUSE_IDS):
        card = cards[pr_id]
        assert not (COMMON_CARD_FIELDS - set(card)), pr_id
        assert card["claim_tier_ceiling"] == "diagnostic_only"
        assert card["public_use"] is False
        assert card["spec_first_required"] is True
        assert card["solver_gate_required"] is False
        assert card["scientific_status_on_intake"] == "OPEN"
        forbidden = " ".join(card["forbidden"]).lower()
        assert "native" in forbidden
        assert "family-identification" in forbidden

    policy = json.loads(PUBLICATION_POLICY.read_text(encoding="utf-8"))
    assert policy["change_set_id"] == cards["PR-276"]["change_set_id"]
    assert policy["publication_group_id"] == cards["PR-276"][
        "publication_group_id"
    ]
    assert policy["target_sha"] == _yaml(SPEC)["baseline"]["verified_merge_head"]
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert policy["attended_publication"]["authorization_mode"] == (
        "attended_explicit_user"
    )
    assert policy["attended_publication"]["max_transactions"] == 1
    assert policy["attended_publication"][
        "direct_mutation_commands_forbidden"
    ] is True
    assert policy["claim_ceiling"] == "diagnostic_only"


def test_portable_runner_resolves_current_source_layout(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "probe"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "source-layout-ok" in result.stdout


def test_post275_dependency_dag_and_pending_amendments_match_spec() -> None:
    spec = _yaml(SPEC)
    backlog = _yaml(BACKLOG)
    cards = {card["id"]: card for card in backlog["prs"]}
    for pr_id, contracts in spec["post275_dependency_contracts"].items():
        assert cards[pr_id]["dependency_contracts"] == contracts
        assert cards[pr_id]["depends"] == [
            contract["upstream_id"] for contract in contracts
        ]
    additions = backlog["policy"]["dependency_overlays"]["additions"]
    for pr_id, dependencies in spec["pending_card_dependency_amendments"].items():
        assert set(dependencies) <= set(additions[pr_id])
    assert backlog["policy"]["dependency_overlays"]["authority"] == "PR-276"
    root_amendment = spec["pr280_root_cause_amendment"]
    for pr_id in PR280_ROOT_CAUSE_IDS:
        assert cards[pr_id]["dependency_contracts"] == root_amendment[
            "successor_dependencies"
        ][pr_id]
    for pr_id in root_amendment["direct_consumers"]:
        assert cards[pr_id]["dependency_contracts"] == [
            {"upstream_id": "PR-280", "mode": "requires_terminal_receipt"}
        ]
        assert set(root_amendment["required_successors_for_each_direct_consumer"]) <= set(
            additions[pr_id]
        )

    result = _run(
        sys.executable,
        "scripts/codex_harness/validate_pr_dag.py",
        "docs/codex_handoff/pr_backlog.yaml",
        "--status",
        "docs/codex_handoff/pr_status.yaml",
        "--strict-rescue-slice",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK: 244 PRs, DAG valid" in result.stdout


def test_status_is_total_and_preserves_negative_chronology() -> None:
    status = _yaml(STATUS)
    states: dict[str, str] = {}
    for field in (
        "completed",
        "blocked",
        "pending",
        "dormant_external",
        "background_in_progress",
    ):
        for pr_id in status.get(field, []) or []:
            assert pr_id not in states
            states[pr_id] = field
    if status.get("in_progress") is not None:
        assert status["in_progress"] not in states
        states[status["in_progress"]] = "in_progress"
    assert len(states) == 244
    assert states["PR-190"] == "blocked"
    assert states["PR-172"] == "blocked"
    assert states["PR-184"] == "completed"
    assert status["execution_resolutions"]["PR-190"][
        "resolution"
    ] == "COMPLETED_FAILED_WITH_RECEIPT"
    assert status["execution_resolutions"]["PR-190"][
        "success_dependency_satisfied"
    ] is False
    assert states["PR-277"] == "completed"
    assert status["execution_resolutions"]["PR-277"][
        "resolution"
    ] == "COMPLETED_SUCCESS"
    assert status["execution_resolutions"]["PR-277"][
        "success_dependency_satisfied"
    ] is True
    resolutions = status["execution_resolutions"]
    for pr_id in POST275_IDS:
        state = states[pr_id]
        resolution = resolutions.get(pr_id)
        if state == "completed":
            assert isinstance(resolution, dict), pr_id
            assert resolution["resolution"] == "COMPLETED_SUCCESS", pr_id
            assert resolution["success_dependency_satisfied"] is True, pr_id
        elif state == "blocked":
            assert isinstance(resolution, dict), pr_id
            assert resolution["resolution"] in {
                "COMPLETED_FAILED_WITH_RECEIPT",
                "BLOCKED_WITH_RECEIPT",
                "ABANDONED_WITH_RECEIPT",
            }, pr_id
            assert resolution["success_dependency_satisfied"] is False, pr_id
        else:
            assert state in {
                "pending",
                "in_progress",
                "background_in_progress",
                "dormant_external",
            }, pr_id
            assert resolution is None, pr_id
    if states["PR-276"] == "in_progress":
        assert "PR-276" not in status["execution_resolutions"]
    else:
        assert states["PR-276"] == "completed"
        assert status["execution_resolutions"]["PR-276"][
            "resolution"
        ] == "COMPLETED_SUCCESS"
    for pr_id in PR280_ROOT_CAUSE_IDS:
        assert states[pr_id] == "pending"
        assert pr_id not in resolutions


def test_only_defined_g1_through_g8_are_registered() -> None:
    spec = _yaml(SPEC)
    assert [row["gate_id"] for row in spec["defined_scientific_gates"]] == [
        f"G{index}" for index in range(1, 9)
    ]
    assert spec["undefined_gate_ids_forbidden"] == ["G9", "G10", "G11", "G12"]
    assert all(row["statement"] for row in spec["defined_scientific_gates"])


def test_human_gates_are_metadata_and_none_is_authorized() -> None:
    status = _yaml(STATUS)
    events = status["external_events"]
    assert set(events) == {
        "G-CI-H",
        "H-PLANCK",
        "H-CF4",
        "H-HSC-KiDS",
        "H-ACT",
        "H-DESI",
        "H-JWST",
    }
    assert all(event["status"] == "NOT_AUTHORIZED" for event in events.values())
    cards = _cards()
    assert cards["PR-201"]["external_execution_gates"][0]["gate_id"] == "H-CF4"
    assert cards["PR-203"]["external_execution_gates"][0]["gate_id"] == "H-DESI"
    assert cards["PR-204"]["external_execution_gates"][0]["gate_id"] == "H-ACT"
    for pr_id, gate_id in {
        "PR-290": "H-PLANCK",
        "PR-291": "H-CF4",
        "PR-292": "H-HSC-KiDS",
        "PR-293": "H-JWST",
    }.items():
        assert cards[pr_id]["external_execution_gates"][0]["gate_id"] == gate_id
    backlog_ids = set(cards)
    assert not (set(events) & backlog_ids)


def test_typed_state_ssot_symbols_and_frozen_decisions_are_current() -> None:
    symbols = (ROOT / ".agent-harness/context/SYMBOLS.md").read_text(
        encoding="utf-8"
    )
    for symbol in _yaml(SPEC)["typed_foundation_symbols"]:
        assert f"`{symbol}`" in symbols
    decisions = (ROOT / ".agent-harness/context/FROZEN_DECISIONS.md").read_text(
        encoding="utf-8"
    )
    assert "D-TYPED-FOUNDATION" in decisions
    assert "D-GOVERNANCE-BRAKE-2026-08" in decisions

    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "`JointAnisotropyState`" in claude
    assert "`LegacyProjectionReport`" in claude
    assert "BC1/BC2" in claude
    assert "not the current state authority" in " ".join(claude.split())
    for path in (
        ROOT / "docs/02_long_range_PR_backlog.md",
        ROOT / "docs/codex_handoff/02_long_range_PR_backlog.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "Typed-state MIO" in text
        assert "LegacyProjectionReport" in text
        assert "auto-promoted" in text


def test_current_handoff_has_no_false_pr258_pending_chronology() -> None:
    forbidden = (
        "PR-258 remains pending",
        "local, unmerged candidate",
        "Active DAG before PR-258 merge",
        "if PR-258 has not been human-reviewed",
    )
    for name in (
        "PROJECT_STATE.md",
        "BLOCKERS.md",
        "NEXT_SESSION_PROMPT.md",
        "DECISION_LOG.md",
        "PR_PROGRESS.md",
        "VALIDATION_LEDGER.md",
    ):
        text = (ROOT / "docs/harness" / name).read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, (name, phrase)
    assert "PR-276" in (ROOT / "docs/harness/PROJECT_STATE.md").read_text(
        encoding="utf-8"
    )


def test_pr270_completed_header_and_frozen_path_are_consistent() -> None:
    delta = (ROOT / "docs/PR_DELTAS/pr-270.md").read_text(encoding="utf-8")
    assert delta.splitlines()[2] == "Status: `COMPLETED_SUCCESS`"
    assert "docs/research_program/vector_tensor/cas/CAS_ADJUDICATION.json" in delta
    assert "does not\nmove, duplicate, or reseal" in delta


def test_generated_status_surfaces_cover_current_dag_and_worktree() -> None:
    snapshot = json.loads(
        (ROOT / "docs/generated/status_snapshot.json").read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (ROOT / "docs/generated/claim_ledger.json").read_text(encoding="utf-8")
    )
    assert snapshot["metadata"]["total_prs"] == 244
    assert len(snapshot["rows"]) == 244
    assert len(ledger["rows"]) == 244
    short_head = _run("git", "rev-parse", "--short=8", "HEAD").stdout.strip()
    short_parent = _run("git", "rev-parse", "--short=8", "HEAD^").stdout.strip()
    allowed_sources = {f"{short_head}+dirty", f"{short_parent}+dirty"}
    status = _yaml(STATUS)
    closeout_specs = {
        "PR-276": (
            "PR-276: Reconcile post-275 execution authority",
            _yaml(SPEC)["baseline"]["verified_merge_head"],
        ),
        "PR-277": (
            "PR-277: Add evidence-conditioned capability engine",
            "a6d3bd8b24e15727fbb6011c515d66d49cd4ba92",
        ),
    }
    for pr_id, (subject, parent_sha) in closeout_specs.items():
        closeout = status.get("execution_resolutions", {}).get(pr_id)
        assert isinstance(closeout, dict)
        content_sha = closeout.get("candidate_sha")
        assert isinstance(content_sha, str) and len(content_sha) == 40
        resolved = _run("git", "rev-parse", f"{content_sha}^{{commit}}")
        assert resolved.returncode == 0, resolved.stderr
        assert resolved.stdout.strip() == content_sha
        assert _run("git", "rev-parse", f"{content_sha}^").stdout.strip() == parent_sha
        assert (
            _run("git", "show", "-s", "--format=%s", content_sha).stdout.strip()
            == subject
        )
        allowed_sources.add(f"{content_sha[:8]}+dirty")
    # A tracked generated file cannot contain the SHA of the commit that
    # contains it without a Git-hash self-reference.  The generator therefore
    # records the dirty source state immediately before the containing commit;
    # during an amend/closeout transition that is HEAD, its first parent, or
    # the Git-verified content candidate named by the terminal receipt.  The
    # last form is required in a detached latest-target integration worktree,
    # whose HEAD intentionally stays on the target while candidate bytes are
    # applied to the index.  The immutable candidate seal binds the exact tree.
    snapshot_metadata = snapshot["metadata"]
    ledger_metadata = ledger["metadata"]
    assert snapshot_metadata["source_commit"] == ledger_metadata["source_commit"]
    assert snapshot_metadata["input_hashes"] == ledger_metadata["input_hashes"]
    source_commit = snapshot_metadata["source_commit"]
    if source_commit not in allowed_sources:
        match = re.fullmatch(r"([0-9a-f]{8})\+dirty", source_commit)
        assert match is not None
        prefix = match.group(1)
        candidates = {
            receipt["candidate_sha"]
            for receipt in status.get("execution_resolutions", {}).values()
            if isinstance(receipt, dict)
            and isinstance(receipt.get("candidate_sha"), str)
            and receipt["candidate_sha"].startswith(prefix)
        }
        assert len(candidates) == 1
        candidate_sha = candidates.pop()
        resolved = _run("git", "rev-parse", f"{candidate_sha}^{{commit}}")
        assert resolved.returncode == 0, resolved.stderr
        assert resolved.stdout.strip() == candidate_sha
    for row in snapshot_metadata["input_hashes"]:
        relative, expected = row.rsplit(":", 1)
        path = ROOT / relative
        assert path.is_file() and not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    assert snapshot["metadata"]["worktree_state"] == "dirty"
    matrix = (ROOT / "docs/generated/status_matrix.md").read_text(encoding="utf-8")
    assert "| Total PRs | 244 |" in matrix
    assert "| In progress | 1 |" in matrix or "| In progress | 0 |" in matrix


def test_canonical_and_compatibility_mirrors_are_equivalent() -> None:
    result = _run(
        sys.executable,
        "scripts/codex_harness/sync_pr_dag_mirrors.py",
        "--check",
    )
    assert result.returncode == 0, result.stdout + result.stderr
