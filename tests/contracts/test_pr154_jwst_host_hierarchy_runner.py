"""Contract tests for the PR-154 reproducible result runner."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
RUNNER = REPO / "scripts/codex_harness/run_pr154_jwst_host_hierarchy.py"
SPEC = REPO / "docs/research_program/long_horizon_rescue/pr154_spec.yaml"


def _module():
    spec = importlib.util.spec_from_file_location("pr154_runner", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_output_set_is_exactly_the_preregistered_artifact_set() -> None:
    module = _module()
    contract = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert set(module.OUTPUTS.values()) == set(
        contract["artifact_contract"]["outputs"]
    )


def test_source_rows_and_upstream_receipts_are_hash_bound() -> None:
    module = _module()
    contract = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    pairs, authority, crossmatch = module._verify_inputs(contract)
    assert {name: len(rows) for name, rows in pairs.items()} == {
        "cchp_trgb_jagb": 7,
        "shoes_jwst_hst": 13,
    }
    assert authority["source_tables_reproduced"] is True
    assert all(row["identity_confirmed"] is False
               for row in crossmatch["matches"])


def test_metadata_carries_full_claim_and_provenance_contract() -> None:
    module = _module()
    contract = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    metadata = module._metadata(contract)
    assert set(metadata) == module.REQUIRED_METADATA
    assert metadata["claim_level"]["level"] == "C2"
    assert metadata["covariance_status"].endswith("not identified")
    assert metadata["input_hashes"]
    assert all(row["sha256"].startswith("sha256:")
               for row in metadata["input_hashes"])


def test_registered_mutants_are_all_killed() -> None:
    module = _module()
    contract = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    pairs, _, _ = module._verify_inputs(contract)
    analyses = {
        family: module.analyze_family(rows, family, production=False)
        for family, rows in pairs.items()
    }
    result = module._run_mutations(
        pairs, analyses, contract
    )
    assert len(result["mutations"]) == 7
    assert result["surviving_mutation_count"] == 0
    assert all(row["executed"] and row["killed"]
               for row in result["mutations"])


def test_hash_mutation_uses_the_production_hash_guard(
        monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    contract = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    pairs, _, _ = module._verify_inputs(contract)
    analyses = {
        family: module.analyze_family(rows, family, production=False)
        for family, rows in pairs.items()
    }
    monkeypatch.setattr(module, "_verify_hash", lambda *_: None)
    result = module._run_mutations(pairs, analyses, contract)
    assert "accept_unpinned_source_table" in result["survivors"]


def test_common_gate_outputs_have_common_owner_and_htt_scientific_owner() -> None:
    module = _module()
    contract = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    metadata = module._metadata(contract, owner="COMMON")
    assert metadata["owner"] == "COMMON"
    assert metadata["scientific_owner"] == "HTT"
    owner_map = contract["artifact_contract"]["owner_by_output"]
    assert owner_map[module.OUTPUTS["manifest"]] == "COMMON"
    assert owner_map[module.OUTPUTS["mutations"]] == "COMMON"


def test_claim_scanner_rejects_registered_forbidden_language() -> None:
    module = _module()
    contract = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    phrase = contract["forbidden_output_language"][0]
    with pytest.raises(SystemExit, match="forbidden claim language"):
        module._scan_claim_language(contract, {"mutant": {"text": phrase}})


def test_manifest_contract_retains_zero_pr4_work_and_planck_raw() -> None:
    contract = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert contract["data_scope"]["pr4_commands_run_required"] == 0
    assert contract["data_scope"]["planck_pr3_raw_deletion"].startswith("forbidden")
