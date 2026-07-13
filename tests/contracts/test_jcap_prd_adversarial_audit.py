from __future__ import annotations

import hashlib
import importlib.util
import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/audits/jcap_prd_adversarial_audit_20260714"
SCRIPT = ROOT / "scripts/audits/jcap_prd_20260714.py"


def _audit_module():
    spec = importlib.util.spec_from_file_location("jcap_prd_audit_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(name: str):
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _write_test_environment(module, audit: Path) -> None:
    payload = {"fixture": "contract-test"}
    payload["environment_hash"] = module.sha256_json(payload)
    (audit / "environment.json").write_text(json.dumps(payload), encoding="utf-8")


def test_prior_audit_is_imported_without_relabeling_as_new():
    payload = _json("prior_crosswalk.json")
    findings = payload["prior_findings"]
    assert len(findings) == 55
    assert Counter(row["severity"] for row in findings) == {
        "P0": 2,
        "P1": 14,
        "P2": 17,
        "P3": 22,
    }
    assert len(payload["audit_completeness_gaps"]) == 14
    assert all(row["delta_status"] == "KNOWN_OPEN" for row in findings)
    assert all(row["novelty_against_prior_audit"] == "not_new_imported" for row in findings)


def test_web_lock_binds_the_initial_crag_packet():
    lock = _json("WEB_LOCK.json")
    packet = AUDIT / "web_crag_initial.json"
    assert lock["status"] == "LOCKED"
    assert lock["locked_packet_sha256"] == _sha256(packet)
    assert "repository-tracked files and Git history" in lock["allowed_evidence"]
    assert "new web search" in lock["forbidden_until_final_shortlist"]


def test_history_and_legacy_inventory_is_fail_closed():
    payload = _json("history_legacy_ledger.json")
    flags = payload["target_commits"]["32a44e9"]["historical_flag_candidates"]
    assert len(flags) == 31
    assert {row["disposition"] for row in flags} <= {
        "resolved",
        "superseded",
        "still_open",
        "unmappable",
        "historical_only",
    }
    assert all(not row["unsafe_entries"] for row in payload["archives"])
    full_session = [
        row for row in payload["archives"] if row["path"].endswith("full_session_archive.zip")
    ]
    assert full_session
    assert payload["salvage_policy"]["full_session_archive"].startswith("content_not_committed")


def test_audit_only_diagnostics_never_mutate_or_promote_production_results():
    payload = _json("diagnostic_results.json")
    assert payload["production_outputs_modified"] is False
    assert payload["lane_count"] == 7
    assert all(row["production_output_modified"] is False for row in payload["lanes"].values())
    assert all(row["web_used"] is False for row in payload["lanes"].values())
    assert payload["lanes"]["act_low_l_transfer_scope"]["status"].startswith("BLOCKED_")
    assert payload["lanes"]["desi_quadrature_and_alpha_refit"]["configuration"] == {
        "alpha_refit_each_mock": True,
        "lmax": 40,
        "n_mock": 400,
        "nside": 64,
        "nz_production_audit": 200,
    }


def test_execution_receipts_have_replay_and_hash_evidence():
    rows = [
        json.loads(line)
        for line in (AUDIT / "execution_ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows
    required = {
        "command_id",
        "agent",
        "command",
        "cwd",
        "started_at",
        "ended_at",
        "exit_code",
        "seed",
        "environment_hash",
        "input_hashes",
        "stdout",
        "stderr",
        "wall_seconds",
    }
    assert all(required <= row.keys() for row in rows)
    for row in rows:
        for stream in ("stdout", "stderr"):
            path = ROOT / row[stream]["path"]
            assert path.is_file()
            assert row[stream]["sha256"] == _sha256(path)

    by_id = {row["command_id"]: row for row in rows}
    sealed = [
        by_id[f"sealed_v2_{lane}"]
        for lane in ("cf4", "grf", "fsigma", "desi", "act", "k6", "jwst")
    ]
    assert len({row["environment_hash"] for row in sealed}) == 1
    runner_hashes = {
        item["sha256"]
        for row in sealed
        for item in row["input_hashes"]
        if item["path"] == "scripts/audits/jcap_prd_20260714.py"
    }
    assert runner_hashes == {_sha256(SCRIPT)}
    for row in sealed:
        for item in row["input_hashes"]:
            path = Path(item["path"])
            if not path.is_absolute():
                path = ROOT / path
            assert item["status"] == "present"
            assert path.is_file()
            assert item["sha256"] == _sha256(path)
    assert all(row["process_result"] == "PASS" for row in sealed)
    assert by_id["sealed_v2_act"]["result"] == "BLOCKED_SCIENTIFIC"
    assert by_id["sealed_v2_act"]["scientific_status"].startswith("BLOCKED_")
    assert all(
        by_id[f"sealed_v2_{lane}"]["result"] == "PASS_PROCESS_ONLY"
        for lane in ("cf4", "grf", "fsigma", "desi", "k6", "jwst")
    )
    diagnostics = _json("diagnostic_results.json")["lanes"]
    lane_names = {
        "cf4": "cf4_monopole_propagation",
        "grf": "hermitian_grf_reference",
        "fsigma": "fsigma8_depth_and_uncertainty",
        "desi": "desi_quadrature_and_alpha_refit",
        "act": "act_low_l_transfer_scope",
        "k6": "k6_stencil_grid_convergence",
        "jwst": "jwst_14_anchor_rerun",
    }
    for lane, stored_name in lane_names.items():
        stdout = ROOT / by_id[f"sealed_v2_{lane}"]["stdout"]["path"]
        assert json.loads(stdout.read_text(encoding="utf-8")) == diagnostics[stored_name]


def test_record_command_fails_closed_on_missing_input_and_duplicate_id(
    tmp_path, monkeypatch
):
    module = _audit_module()
    audit = tmp_path / "audit"
    audit.mkdir()
    _write_test_environment(module, audit)
    monkeypatch.setattr(module, "AUDIT", audit)
    monkeypatch.setattr(module, "EXECUTION_LEDGER", audit / "execution_ledger.jsonl")
    monkeypatch.setattr(module, "DIAGNOSTICS", audit / "diagnostic_results.json")
    sentinel = tmp_path / "must_not_exist"
    args = SimpleNamespace(
        id="missing_input",
        agent="contract-test",
        seed=20260714,
        input=[str(tmp_path / "absent.dat")],
        exec_command=["--", "/usr/bin/touch", str(sentinel)],
    )
    assert module.record_command(args) == 66
    assert not sentinel.exists()
    receipt = json.loads((audit / "execution_ledger.jsonl").read_text().splitlines()[0])
    assert receipt["process_result"] == "NOT_RUN"
    assert receipt["scientific_status"] == "BLOCKED_MISSING_DECLARED_INPUT"
    assert receipt["result"] == "BLOCKED_MISSING_DECLARED_INPUT"
    with pytest.raises(SystemExit, match="duplicate command id"):
        module.record_command(args)
    unsafe = SimpleNamespace(**{**vars(args), "id": "../unsafe"})
    with pytest.raises(SystemExit, match="unsafe command id"):
        module.record_command(unsafe)


def test_record_command_separates_process_success_from_scientific_block(
    tmp_path, monkeypatch
):
    module = _audit_module()
    audit = tmp_path / "audit"
    audit.mkdir()
    _write_test_environment(module, audit)
    (audit / "diagnostic_results.json").write_text(
        json.dumps(
            {
                "lanes": {
                    "act_low_l_transfer_scope": {
                        "status": "BLOCKED_MISSING_RAW_QE_INPUTS_FOR_SKY_POWER_TRANSFER"
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "AUDIT", audit)
    monkeypatch.setattr(module, "EXECUTION_LEDGER", audit / "execution_ledger.jsonl")
    monkeypatch.setattr(module, "DIAGNOSTICS", audit / "diagnostic_results.json")
    args = SimpleNamespace(
        id="blocked_science",
        agent="contract-test",
        seed=20260714,
        input=[],
        exec_command=["--", "/usr/bin/true", "run-diagnostic", "act"],
    )
    assert module.record_command(args) == 0
    receipt = json.loads((audit / "execution_ledger.jsonl").read_text().splitlines()[0])
    assert receipt["process_result"] == "PASS"
    assert receipt["result"] == "BLOCKED_SCIENTIFIC"
    assert receipt["scientific_status"].startswith("BLOCKED_")


def test_record_command_claims_ids_atomically_across_concurrent_agents(
    tmp_path, monkeypatch
):
    module = _audit_module()
    audit = tmp_path / "audit"
    audit.mkdir()
    _write_test_environment(module, audit)
    monkeypatch.setattr(module, "AUDIT", audit)
    monkeypatch.setattr(module, "EXECUTION_LEDGER", audit / "execution_ledger.jsonl")
    monkeypatch.setattr(module, "DIAGNOSTICS", audit / "diagnostic_results.json")

    def invoke(marker):
        args = SimpleNamespace(
            id="same_id",
            agent=marker,
            seed=20260714,
            input=[],
            exec_command=["--", "/bin/sh", "-c", f"sleep 0.2; printf {marker}"],
        )
        try:
            return ("return", module.record_command(args))
        except SystemExit as exc:
            return ("blocked", str(exc))

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(invoke, ("ONE", "TWO")))
    assert Counter(kind for kind, _ in outcomes) == {"return": 1, "blocked": 1}
    rows = [
        json.loads(line)
        for line in (audit / "execution_ledger.jsonl").read_text().splitlines()
    ]
    assert len(rows) == 1
    stdout = Path(rows[0]["stdout"]["path"])
    assert stdout.read_text() in {"ONE", "TWO"}


def test_semantically_empty_json_is_rejected():
    module = _audit_module()
    errors = []
    assert module._require_object({}, "fixture", ("schema",), errors) is None
    assert errors == ["fixture must be a non-empty JSON object"]


def test_seal_validation_detects_tampered_inputs_environment_and_numeric_output():
    module = _audit_module()
    rows = [
        json.loads(line)
        for line in (AUDIT / "execution_ledger.jsonl").read_text().splitlines()
        if line.strip()
    ]
    row = deepcopy(next(item for item in rows if item["command_id"] == "sealed_v2_cf4"))
    data_input = next(
        item
        for item in row["input_hashes"]
        if item["path"] != "scripts/audits/jcap_prd_20260714.py"
    )
    data_input["sha256"] = "sha256:" + "0" * 64
    errors = []
    module._validate_current_input_hashes(row, "tampered", errors)
    assert any("hash mismatch" in error for error in errors)

    environment = _json("environment.json")
    environment["versions"]["numpy"] = "0.0-TAMPERED"
    errors = []
    module._validate_environment_self_hash(environment, errors)
    assert any("self-hash mismatch" in error for error in errors)

    clean_row = next(item for item in rows if item["command_id"] == "sealed_v2_cf4")
    diagnostic = deepcopy(_json("diagnostic_results.json")["lanes"]["cf4_monopole_propagation"])
    diagnostic["n_groups"] += 1
    errors = []
    module._validate_diagnostic_payload_binding(clean_row, diagnostic, "tampered", errors)
    assert errors == ["tampered diagnostic numeric payload differs from captured stdout"]


def test_atomic_provenance_rejects_unrelated_anchors_and_missing_consumers():
    module = _audit_module()
    atomic = _json("atomic_finding_ledger.json")
    mutated = deepcopy(atomic)
    row = mutated["atomic_findings"][0]
    row["source_paths"] = ["docs/generated/claim_ledger.json#NO_SUCH_ANCHOR"]
    row["execution_evidence"] = [
        "docs/generated/claim_ledger.json#NOT_AN_EXECUTION_RECEIPT"
    ]
    row["downstream_artifacts"] = ["definitely/missing/downstream.file"]
    prior = _json("prior_crosswalk.json")
    prior_ids = {item["prior_id"] for item in prior["prior_findings"]}
    prior_ids.update(item["gap_id"] for item in prior["audit_completeness_gaps"])
    execution_rows = [
        json.loads(line)
        for line in (AUDIT / "execution_ledger.jsonl").read_text().splitlines()
        if line.strip()
    ]
    errors = []
    module._validate_atomic_findings(mutated, prior_ids, execution_rows, errors)
    assert any("untyped or nonexistent anchor" in error for error in errors)
    assert any("unsupported execution-evidence type" in error for error in errors)
    assert any("downstream must exist" in error for error in errors)


def test_root_delta_findings_are_complete_and_separate_from_prior_findings():
    payload = _json("atomic_finding_ledger.json")
    findings = payload["atomic_findings"]
    open_findings = [row for row in findings if row["disposition"] == "NEW_OPEN"]
    assert len(open_findings) == 33
    assert Counter(row["severity"] for row in open_findings) == {"P1": 22, "P2": 11}
    assert Counter(row["disposition"] for row in findings) == {
        "NEW_OPEN": 33,
        "REUSE_PRIOR": 2,
        "REMEDIATED_IN_PR117": 1,
    }
    required = {
        "atomic_id",
        "severity",
        "disposition",
        "source_candidates",
        "source_paths",
        "cluster_id",
        "parent_prior_ids",
        "delta_reason",
        "error_claim",
        "strongest_defense",
        "rebuttal",
        "execution_evidence",
        "downstream_artifacts",
        "decisive_falsifier",
        "maximum_claim_tier",
    }
    assert all(required <= row.keys() for row in findings)
    assert len({row["atomic_id"] for row in findings}) == len(findings)
    candidates = [candidate for row in findings for candidate in row["source_candidates"]]
    assert len(candidates) == len(set(candidates)) == 44
    root = _json("root_adjudications.json")
    assert root["new_open_finding_count"] == 33
    assert len(root["finding_clusters"]) == 14


def test_debate_bundle_binds_complete_offline_responses():
    payload = _json("debate_bundle.json")
    assert payload["complete_response_count"] == payload["agent_artifact_count"]
    assert payload["offline_receipt_failures"] == []
    assert payload["root_adjudications_sha256"] == _sha256(AUDIT / "root_adjudications.json")
    assert payload["agent_artifact_count"] >= 27
    phase_counts = Counter(row["phase"] for row in payload["agent_artifacts"])
    assert phase_counts == {
        "initial_crag": 3,
        "theory_wave": 3,
        "statistics_wave": 3,
        "code_wave": 3,
        "data_wave": 3,
        "cross_debate": 3,
        "blind_referees": 3,
        "pr117_review": 3,
        "pr117_rereview": 3,
    }
    for row in payload["agent_artifacts"]:
        prompt = ROOT / row["prompt_path"]
        response = ROOT / row["response_path"]
        assert prompt.is_file()
        assert response.is_file()
        assert row["prompt_sha256"] == _sha256(prompt)
        assert row["response_sha256"] == _sha256(response)


def test_counterfactual_family_sandbox_cannot_leak_to_public_roots():
    contract = _json("diagnostic_results.json")["counterfactual_contract"]
    assert contract == {
        "allowed_use": "internal_only",
        "artifact_mode": "internal_exploratory",
        "claim_tier": "exploratory",
        "hypothesis_only": True,
        "public_use": False,
    }
    module = _audit_module()

    def contains_marker(value):
        if isinstance(value, dict):
            return (
                value.get("hypothesis_only") is True
                or value.get("public_use") is False
                or any(contains_marker(item) for item in value.values())
            )
        if isinstance(value, list):
            return any(contains_marker(item) for item in value)
        return False

    fixtures = {
        "minified.json": '{"nested":{"hypothesis_only":true}}',
        "candidate.yaml": "public_use: false\n",
        "tagged_true.yaml": 'hypothesis_only: !!bool "true"\n',
        "synonym_true.yaml": "hypothesis_only: on\n",
        "tagged_false.yaml": 'public_use: !!bool "false"\n',
        "candidate.md": "COUNTERFACTUAL_SENTINEL\n",
        "caption.tex": r"\caption{Bianchi family identified}",
        "macro_caption.tex": r"\caption{Bianchi family \emph{identified}}",
        "comment_caption.tex": "\\caption{Bianchi family % split\nidentified}",
    }
    assert all(module._counterfactual_public_text_hits(text) for text in fixtures.values())

    for root in (ROOT / "docs/manuscript", ROOT / "docs/generated", ROOT / "figures"):
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {
                ".json", ".yaml", ".yml", ".md", ".tex", ".txt"
            }:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            assert not module._counterfactual_public_text_hits(text), path
            if path.suffix.lower() == ".json":
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                assert not contains_marker(payload), path


def test_manifest_is_complete_and_self_consistent():
    manifest = _json("MANIFEST.json")
    required = {
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "null_mock_status",
        "caveats",
        "generating_command",
        "git_commit_or_worktree_state",
    }
    assert all(manifest[field] for field in required)
    listed = {row["path"]: row for row in manifest["files"]}
    for path in AUDIT.rglob("*"):
        if not path.is_file() or path.name == "MANIFEST.json":
            continue
        relative = str(path.relative_to(ROOT))
        assert relative in listed
        assert listed[relative]["sha256"] == _sha256(path)
