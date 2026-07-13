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
import yaml


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


def test_pr_backlog_yaml_json_and_root_mirrors_are_semantically_identical():
    payloads = {}
    for root in ("docs/codex_handoff", "machine_readable"):
        yaml_path = ROOT / root / "pr_backlog.yaml"
        json_path = ROOT / root / "pr_backlog.json"
        payloads[(root, "yaml")] = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        payloads[(root, "json")] = json.loads(json_path.read_text(encoding="utf-8"))
        assert payloads[(root, "yaml")] == payloads[(root, "json")]
    assert payloads[("docs/codex_handoff", "yaml")] == payloads[("machine_readable", "yaml")]
    pr118 = next(
        row
        for row in payloads[("docs/codex_handoff", "yaml")]["prs"]
        if row["id"] == "PR-118"
    )
    assert pr118["tests"][-1].endswith("validate --final")


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
    module = _audit_module()
    assert runner_hashes == {module.PR117_SEALED_RUNNER_SHA256}
    for row in sealed:
        for item in row["input_hashes"]:
            path = Path(item["path"])
            if not path.is_absolute():
                path = ROOT / path
            assert item["status"] == "present"
            assert path.is_file()
            if item["path"] == "scripts/audits/jcap_prd_20260714.py":
                assert item["sha256"] == module.PR117_SEALED_RUNNER_SHA256
            else:
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
    required_phase_counts = {
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
    for phase, count in required_phase_counts.items():
        assert phase_counts[phase] == count
    for row in payload["agent_artifacts"]:
        prompt = ROOT / row["prompt_path"]
        response = ROOT / row["response_path"]
        assert prompt.is_file()
        assert response.is_file()
        assert row["prompt_sha256"] == _sha256(prompt)
        assert row["response_sha256"] == _sha256(response)


def test_advocate_divergence_is_balanced_offline_and_author_nonpromoting():
    module = _audit_module()
    errors = []
    candidates, author_by_candidate = module._load_advocate_responses(errors)
    assert errors == []
    assert len(candidates) == len(author_by_candidate) == 32
    assert Counter(row["axis"] for row in candidates) == {
        "theory": 8,
        "statistics": 8,
        "code": 8,
        "data_analysis": 8,
    }
    assert len(set(author_by_candidate.values())) == 4
    assert all(row["hypothesis_only"] is True for row in candidates)
    assert all(row["public_use"] is False for row in candidates)
    assert all(row["author_cannot_promote"] is True for row in candidates)
    assert all(row["web_used"] is False for row in candidates)
    assert all(row["decisive_falsifier"] for row in candidates)


def test_advocate_loader_rejects_whitespace_and_string_boolean_mutations(
    tmp_path, monkeypatch
):
    module = _audit_module()
    payload = json.loads(
        module.ADVOCATE_RESPONSE_PATHS["theory"].read_text(encoding="utf-8")
    )
    payload["candidates"][0]["title"] = "   "
    payload["candidates"][0]["native_atlas_required"] = "false"
    mutated = tmp_path / "theory_response.json"
    mutated.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setitem(module.ADVOCATE_RESPONSE_PATHS, "theory", mutated)
    errors = []
    module._load_advocate_responses(errors)
    assert any("TH-01 has empty/non-text title" in error for error in errors)
    assert any("TH-01 native_atlas_required must be a strict boolean" in error for error in errors)


def test_advocate_and_judge_packets_reject_unknown_fields_and_type_confusion(
    tmp_path, monkeypatch
):
    module = _audit_module()
    advocate = json.loads(
        module.ADVOCATE_RESPONSE_PATHS["theory"].read_text(encoding="utf-8")
    )
    advocate["undeclared_authority"] = "promote"
    advocate_path = tmp_path / "theory_unknown_field.json"
    advocate_path.write_text(json.dumps(advocate), encoding="utf-8")
    monkeypatch.setitem(module.ADVOCATE_RESPONSE_PATHS, "theory", advocate_path)
    advocate_errors = []
    module._load_advocate_responses(advocate_errors)
    assert any(
        "unknown=['undeclared_authority']" in error for error in advocate_errors
    )

    judge = json.loads(
        (
            AUDIT
            / "agents/advocate_judging/pre_solver_judge_response.json"
        ).read_text(encoding="utf-8")
    )
    judge["judge_id"] = 7
    judge["candidate_scores"][0]["rationale"] = True
    judge["candidate_scores"][0]["undeclared_score_authority"] = "yes"
    judge_path = tmp_path / "judge_type_confusion.json"
    judge_path.write_text(json.dumps(judge), encoding="utf-8")
    candidate_ids = {
        row["candidate_id"]
        for row in _json("advocate_candidate_ledger.json")["candidates"]
    }
    judge_errors = []
    module._load_judge_rows(
        judge_path,
        "pre_solver",
        candidate_ids,
        set(),
        judge_errors,
    )
    assert any("judge_id must be non-whitespace text" in error for error in judge_errors)
    assert any("rationale must be non-whitespace text" in error for error in judge_errors)
    assert any(
        "unknown=['undeclared_score_authority']" in error for error in judge_errors
    )


def test_independent_judges_and_deterministic_shortlist_exclude_candidate_authors():
    module = _audit_module()
    ledger = _json("advocate_candidate_ledger.json")
    assert sum(ledger["weights"]["pre_solver"].values()) == 100
    assert sum(ledger["weights"]["post_native_solver"].values()) == 100
    authorities = ledger["ranking_authority"]
    assert authorities["candidate_authors_excluded"] is True
    judges = {
        authorities["pre_solver_judge"],
        authorities["post_native_solver_judge"],
        authorities["integrity_veto_judge"],
    }
    assert len(judges) == 3
    assert judges.isdisjoint(ledger["author_ids"])
    assert ledger["candidate_count"] == 32
    assert ledger["axis_counts"] == {
        "theory": 8,
        "statistics": 8,
        "code": 8,
        "data_analysis": 8,
    }
    assert 8 <= ledger["shortlist_count"] <= 12
    assert ledger["shortlist_hash"] == module.sha256_json(
        sorted(ledger["shortlist_candidate_ids"])
    )
    assert ledger["shortlist_basis"] == (
        "pre_crag_selection_score_frozen_before_final_crag"
    )
    shortlisted = set(ledger["shortlist_candidate_ids"])
    freeze = _json("shortlist_freeze.json")
    assert freeze["shortlist_candidate_ids"] == ledger["shortlist_candidate_ids"]
    assert freeze["shortlist_hash"] == ledger["shortlist_hash"]
    assert ledger["shortlist_freeze_sha256"] == _sha256(AUDIT / "shortlist_freeze.json")
    for axis in ledger["axis_counts"]:
        top_two = {
            row["candidate_id"]
            for row in ledger["candidates"]
            if row["axis"] == axis and row["axis_rank"] <= 2
        }
        assert top_two <= shortlisted
    for row in ledger["candidates"]:
        integrity = row["integrity_veto_review"]
        expected = not any(
            integrity[name]
            for name in ("unresolved_p0", "missing_falsifier", "provenance_unsecured")
        )
        assert integrity["eligible_for_retain"] is expected
        if not expected:
            assert row["final_disposition"] != "rescued"
        for review_key, weights in (
            ("pre_solver_review", ledger["weights"]["pre_solver"]),
            ("post_native_solver_review", ledger["weights"]["post_native_solver"]),
        ):
            review = row[review_key]
            assert review["pre_crag_total"] == review["total"]
            if row["shortlisted_for_final_crag"]:
                expected_scores = dict(review["scores"])
                expected_scores["novelty"] = row["final_crag_update"]["novelty_after"]
                expected_total = round(
                    sum(
                        float(expected_scores[key]) * weight / 10.0
                        for key, weight in weights.items()
                    ),
                    3,
                )
                assert review["post_crag_scores"] == expected_scores
                assert review["post_crag_total"] == expected_total
            else:
                assert review["post_crag_scores"] is None
                assert review["post_crag_total"] is None


def test_final_crag_is_short_primary_only_and_exactly_shortlist_bounded():
    ledger = _json("advocate_candidate_ledger.json")
    crag = _json("web_crag_final.json")
    assert crag["reopened_after_shortlist"] is True
    assert crag["closed_after_completion"] is True
    assert crag["shortlist_hash"] == ledger["shortlist_hash"]
    assert set(crag["candidate_ids"]) == set(ledger["shortlist_candidate_ids"])
    assert len(crag["candidate_ids"]) == 12
    assert len(crag["queries"]) <= 12
    assert len(crag["sources"]) <= 24
    assert crag["raw_query_count"] >= len(crag["queries"])
    assert crag["raw_source_count"] >= len(crag["sources"])
    assert all(row["primary_or_official"] is True for row in crag["sources"])
    assert {
        row["candidate_id"] for row in crag["candidate_updates"]
    } == set(crag["candidate_ids"])
    allowed = {
        "rescued",
        "downclaimed",
        "rebuild_required",
        "native_solver_dependent",
        "falsified",
        "abandoned",
    }
    assert all(
        row["recommended_disposition"] in allowed
        for row in crag["candidate_updates"]
    )
    source_by_id = {row["source_id"]: row for row in crag["sources"]}
    for update in crag["candidate_updates"]:
        candidate_id = update["candidate_id"]
        assert len(update["source_ids"]) <= 2
        assert any(
            candidate_id in query["candidate_ids"] for query in crag["queries"]
        )
        assert any(
            source_id in source_by_id
            and candidate_id in source_by_id[source_id]["candidate_ids"]
            for source_id in update["source_ids"]
        )


def test_criticism_matrix_covers_every_prior_gap_and_new_delta_once():
    prior = _json("prior_crosswalk.json")
    atomic = _json("atomic_finding_ledger.json")
    matrix = _json("criticism_response_matrix.json")
    expected = {row["prior_id"] for row in prior["prior_findings"]}
    expected |= {row["gap_id"] for row in prior["audit_completeness_gaps"]}
    expected |= {
        row["atomic_id"]
        for row in atomic["atomic_findings"]
        if row["disposition"] == "NEW_OPEN"
    }
    rows = matrix["rows"]
    assert len(rows) == matrix["row_count"] == 102
    assert {row["criticism_id"] for row in rows} == expected
    assert Counter(row["origin"] for row in rows) == {
        "prior": 55,
        "audit_gap": 14,
        "delta_new": 33,
    }
    assert all(row["strongest_advocate_response"] for row in rows)
    assert all(row["response_to_rebuttal"] for row in rows)
    assert all(row["residual_risk"] for row in rows)
    assert all(row["decisive_closeout_evidence"] for row in rows)
    assert all(row["source_hash"].startswith("sha256:") for row in rows)
    assert all(row["authoritative_state"] in {"KNOWN_OPEN", "NEW_OPEN"} for row in rows)
    assert matrix["disposition_counts"] == {
        "abandoned": 3,
        "downclaimed": 43,
        "rebuild_required": 56,
    }
    assert not any(row["disposition"] == "rescued" for row in rows)
    p0 = next(row for row in rows if row["criticism_id"] == "C1-K5-MV-F1")
    prior_p0 = next(
        row for row in prior["prior_findings"] if row["prior_id"] == "C1-K5-MV-F1"
    )
    assert p0["severity"] == prior_p0["severity"] == "P0"
    assert p0["criticism"] == prior_p0["title"]
    assert p0["authoritative_state"] == "KNOWN_OPEN"


def test_final_metadata_validator_rejects_stale_and_missing_inputs():
    module = _audit_module()
    ledger = deepcopy(_json("advocate_candidate_ledger.json"))
    ledger["config_hash"] = "sha256:" + "0" * 64
    ledger["input_hashes"] = ["definitely/missing.json:sha256:" + "f" * 64]
    errors = []
    module._validate_artifact_metadata(ledger, "mutated ledger", errors)
    assert any("input is missing" in error for error in errors)
    assert any("config_hash is stale" in error for error in errors)


def test_final_closeout_rejects_p0_rewrite_even_with_unchanged_id_census(monkeypatch):
    module = _audit_module()
    matrix = deepcopy(_json("criticism_response_matrix.json"))
    p0 = next(row for row in matrix["rows"] if row["criticism_id"] == "C1-K5-MV-F1")
    p0.update(
        {
            "severity": "P3",
            "criticism": "harmless wording issue",
            "disposition": "rescued",
            "maximum_claim_tier": "validated science",
        }
    )
    matrix["disposition_counts"] = dict(
        Counter(row["disposition"] for row in matrix["rows"])
    )
    original_validate_json = module._validate_json

    def mutated_loader(path, collected_errors):
        if Path(path).name == "criticism_response_matrix.json":
            return deepcopy(matrix)
        return original_validate_json(path, collected_errors)

    monkeypatch.setattr(module, "_validate_json", mutated_loader)
    execution_rows = [
        json.loads(line)
        for line in (AUDIT / "execution_ledger.jsonl").read_text().splitlines()
        if line.strip()
    ]
    errors = []
    module._validate_final_closeout(
        _json("prior_crosswalk.json"),
        _json("atomic_finding_ledger.json"),
        execution_rows,
        errors,
    )
    assert any("C1-K5-MV-F1 rewrites authoritative severity" in error for error in errors)
    assert any("C1-K5-MV-F1 rewrites authoritative criticism" in error for error in errors)
    assert any("C1-K5-MV-F1 rewrites authoritative maximum_claim_tier" in error for error in errors)


def test_canonical_replay_rejects_veto_erasure_and_shortlist_substitution(monkeypatch):
    module = _audit_module()
    errors = []
    canonical = module._canonical_advocate_ranking(errors)
    assert errors == []
    crag = _json("web_crag_final.json")
    expected = module._finalize_advocate_ranking(canonical, crag, errors)
    assert errors == []
    mutated = deepcopy(expected)
    da01 = next(row for row in mutated if row["candidate_id"] == "DA-01")
    da01["integrity_veto_review"]["provenance_unsecured"] = False
    da01["integrity_veto_review"]["eligible_for_retain"] = True
    da01["final_disposition"] = "rescued"
    assert mutated != expected

    ledger = deepcopy(_json("advocate_candidate_ledger.json"))
    ledger["candidates"] = mutated
    original_validate_json = module._validate_json

    def mutated_loader(path, collected_errors):
        if Path(path).name == "advocate_candidate_ledger.json":
            return deepcopy(ledger)
        return original_validate_json(path, collected_errors)

    monkeypatch.setattr(module, "_validate_json", mutated_loader)
    execution_rows = [
        json.loads(line)
        for line in (AUDIT / "execution_ledger.jsonl").read_text().splitlines()
        if line.strip()
    ]
    closeout_errors = []
    module._validate_final_closeout(
        _json("prior_crosswalk.json"),
        _json("atomic_finding_ledger.json"),
        execution_rows,
        closeout_errors,
    )
    assert any("canonical author/judge/CRAG replay" in error for error in closeout_errors)

    freeze = deepcopy(_json("shortlist_freeze.json"))
    freeze["shortlist_candidate_ids"].remove("TH-02")
    freeze["shortlist_candidate_ids"].append("TH-08")
    assert freeze["shortlist_candidate_ids"] != module._shortlist_freeze_projection(
        module._canonical_advocate_ranking([])
    )["shortlist_candidate_ids"]


def test_canonical_replay_rejects_derived_final_crag_and_ledger_collusion(monkeypatch):
    module = _audit_module()
    crag = deepcopy(_json("web_crag_final.json"))
    update = next(
        row for row in crag["candidate_updates"] if row["candidate_id"] == "TH-02"
    )
    update["nearest_prior_art"] = "invented derived-only novelty claim"
    ledger = deepcopy(_json("advocate_candidate_ledger.json"))
    candidate = next(
        row for row in ledger["candidates"] if row["candidate_id"] == "TH-02"
    )
    candidate["final_crag_update"]["nearest_prior_art"] = update[
        "nearest_prior_art"
    ]
    original_validate_json = module._validate_json

    def colluding_loader(path, collected_errors):
        if Path(path).name == "web_crag_final.json":
            return deepcopy(crag)
        if Path(path).name == "advocate_candidate_ledger.json":
            return deepcopy(ledger)
        return original_validate_json(path, collected_errors)

    monkeypatch.setattr(module, "_validate_json", colluding_loader)
    execution_rows = [
        json.loads(line)
        for line in (AUDIT / "execution_ledger.jsonl").read_text().splitlines()
        if line.strip()
    ]
    errors = []
    module._validate_final_closeout(
        _json("prior_crosswalk.json"),
        _json("atomic_finding_ledger.json"),
        execution_rows,
        errors,
    )
    assert any(
        "final CRAG differs from canonical raw-response replay at candidate_updates"
        in error
        for error in errors
    )


def test_canonical_replay_rejects_derived_new_open_rescue(monkeypatch):
    module = _audit_module()
    matrix = deepcopy(_json("criticism_response_matrix.json"))
    finding = next(
        row for row in matrix["rows"] if row["authoritative_state"] == "NEW_OPEN"
    )
    finding["disposition"] = "rescued"
    matrix["disposition_counts"] = dict(
        Counter(row["disposition"] for row in matrix["rows"])
    )
    original_validate_json = module._validate_json

    def mutated_loader(path, collected_errors):
        if Path(path).name == "criticism_response_matrix.json":
            return deepcopy(matrix)
        return original_validate_json(path, collected_errors)

    monkeypatch.setattr(module, "_validate_json", mutated_loader)
    execution_rows = [
        json.loads(line)
        for line in (AUDIT / "execution_ledger.jsonl").read_text().splitlines()
        if line.strip()
    ]
    errors = []
    module._validate_final_closeout(
        _json("prior_crosswalk.json"),
        _json("atomic_finding_ledger.json"),
        execution_rows,
        errors,
    )
    assert any(
        "canonical raw-mapper/root replay at disposition_counts" in error
        or "cannot rescue an open finding" in error
        for error in errors
    )


def test_pr118_result_artifacts_carry_complete_audit_metadata():
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
    for name in (
        "advocate_candidate_ledger.json",
        "web_crag_final.json",
        "criticism_response_matrix.json",
        "final_referee_decisions.json",
        "next_dag_candidates.json",
        "latex_pdf_validation.json",
    ):
        payload = _json(name)
        assert required <= payload.keys(), name
        assert all(payload[field] for field in required), name
        assert payload["claim_tier"] == "diagnostic_only", name

    latex = _json("latex_pdf_validation.json")
    assert latex["pdf"]["pdfinfo_status"] == "PASS"
    assert latex["log"]["undefined_reference_warnings"] == 0
    assert latex["log"]["undefined_citation_warnings"] == 0
    assert latex["scientific_readiness"] is False
    assert latex["publication_readiness"] is False


def test_final_reports_preserve_separate_editorial_objects_and_blockers():
    report = (AUDIT / "final_referee_report.md").read_text(encoding="utf-8")
    summary = (AUDIT / "executive_summary_ko.md").read_text(encoding="utf-8")
    for term in (
        "JCAP referee decision",
        "PRD referee decision",
        "Independent skeptical referee decision",
        "As-shipped",
        "Post-surgery",
        "Strongest defensible thesis",
        "Dissent",
        "Unexecuted blockers",
    ):
        assert term in report
    for term in ("현재 상태", "최소 수정", "pre-solver", "native solver", "가장 강한 방어 가능 명제"):
        assert term in summary
    assert "hypothesis_only=true" in report
    assert "public_use=false" in report
    assert "44 / 78" in report and "`not_examined`" in report
    assert "not proof of exact isotropy" in report
    assert "44/78" in summary and "`not_examined`" in summary
    assert "exact isotropy의 증명도" in summary


def test_proposed_followup_cards_preserve_owner_staging_and_target_semantics():
    payload = _json("next_dag_candidates.json")
    assert payload["status"] == "proposed_only_not_inserted_into_active_backlog"
    assert payload["closure_contract"]
    assert {row["id"]: row["owner"] for row in payload["cards"]} == {
        "AUD-R01A": "OBSSTAT",
        "AUD-R01B": "HTT",
        "AUD-R02A": "OBSSTAT",
        "AUD-R02B": "COMMON",
        "AUD-R03": "COMMON",
        "AUD-R04": "OBSSTAT",
        "AUD-R05A": "BASS_PY",
        "AUD-R05B": "OBSSTAT",
        "AUD-R05C": "HTT",
    }
    assert all("targets" in row and "closes" not in row for row in payload["cards"])
    assert all(row["targets"] for row in payload["cards"])


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
        "passive_caption.tex": r"\caption{Bianchi family is identified}",
        "active_caption.tex": r"\caption{We identify a Bianchi family}",
        "perfect_caption.tex": r"\caption{Bianchi geometry has been detected}",
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


def test_final_audit_package_validator_accepts_the_sealed_closeout():
    module = _audit_module()
    assert module.validate(final=True) == []
