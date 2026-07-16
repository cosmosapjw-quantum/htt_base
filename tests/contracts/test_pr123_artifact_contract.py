from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "docs/research_program/long_horizon_rescue/pr123_spec.yaml"
SCRIPT = REPO_ROOT / "scripts/codex_harness/run_pr123_oracle_lab.py"
GENERATED = REPO_ROOT / "docs/generated"
OUTPUTS = (
    "pr123_oracle_lineage_manifest.json",
    "pr123_mutation_lab_report.json",
    "pr123_k6_continuum_card.json",
    "pr123_surviving_mutations.json",
    "pr123_attempt_history.json",
    "pr123_artifact_manifest.json",
)
REQUIRED_METADATA = {
    "owner",
    "contributors",
    "implementation_scope",
    "claim_tier",
    "claim_level",
    "artifact_mode",
    "allowed_use",
    "forbidden_use",
    "transfer_source",
    "config_hash",
    "input_hashes",
    "sky_support_status",
    "null_mock_status",
    "caveats",
    "generating_command",
    "git_commit_or_worktree_state",
    "consumer_list",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_checked_in_artifacts_have_complete_downclaimed_metadata() -> None:
    spec_hash = _sha256(SPEC)
    for name in OUTPUTS:
        payload = json.loads((GENERATED / name).read_text(encoding="utf-8"))
        metadata = payload["metadata"]
        assert REQUIRED_METADATA <= set(metadata)
        assert metadata["config_hash"] == spec_hash
        assert metadata["owner"] == "COMMON"
        assert metadata["contributors"] == ["OBSSTAT", "HTT"]
        assert metadata["claim_tier"] == "conditional"
        assert metadata["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
        assert metadata["transfer_source"] == "none_or_synthetic"
        assert any("scientific findings remain OPEN" in caveat for caveat in metadata["caveats"])


def test_artifact_manifest_binds_every_nonself_output_exactly() -> None:
    manifest = json.loads((GENERATED / OUTPUTS[-1]).read_text(encoding="utf-8"))
    rows = {Path(row["path"]).name: row for row in manifest["artifacts"]}
    assert set(rows) == set(OUTPUTS[:-1])
    for name, row in rows.items():
        path = GENERATED / name
        assert row["sha256"] == _sha256(path)
        assert row["size_bytes"] == path.stat().st_size
    assert manifest["aggregate_status"] == "PASS_MECHANICS_C2"
    assert manifest["claim_release_allowed"] is False
    assert manifest["scientific_status"] == "OPEN"
    assert manifest["pr4_scope_receipt"]["declared_in_process_commands_run"] == 0
    assert manifest["pr4_scope_receipt"]["historical_shell_audit_claimed"] is False


def test_source_only_check_is_current_and_read_only() -> None:
    before = {name: ((GENERATED / name).stat().st_mtime_ns, _sha256(GENERATED / name)) for name in OUTPUTS}
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--check", "--tier", "contract"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout)["status"] == "current"
    after = {name: ((GENERATED / name).stat().st_mtime_ns, _sha256(GENERATED / name)) for name in OUTPUTS}
    assert before == after


def test_check_fails_closed_when_outputs_are_missing(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCRIPT),
            "--check",
            "--tier",
            "contract",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "stale"
    assert set(payload["artifacts"]) == set(OUTPUTS)
    assert list(tmp_path.iterdir()) == []


def test_spec_and_receipts_preserve_absolute_pr4_firewall() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert spec["data_scope"]["pr4_download"] == "not_started"
    assert spec["data_scope"]["pr4_data_work"] == "skip_entirely_by_user_scope"
    assert spec["data_scope"]["pr4_commands_run_required"] == 0
    mutation = json.loads((GENERATED / "pr123_mutation_lab_report.json").read_text(encoding="utf-8"))
    survivors = json.loads((GENERATED / "pr123_surviving_mutations.json").read_text(encoding="utf-8"))
    assert mutation["pr4_scope_receipt"]["declared_in_process_commands_run"] == 0
    assert mutation["pr4_scope_receipt"]["inputs"] == []
    assert mutation["pr4_scope_receipt"]["historical_shell_audit_claimed"] is False
    assert survivors["survivor_count"] == 0


def test_every_consumed_random_child_has_root_role_and_spawn_path() -> None:
    report = json.loads(
        (GENERATED / "pr123_mutation_lab_report.json").read_text(encoding="utf-8")
    )
    ledger = report["seed_ledger"]
    assert len(ledger) == 96
    assert {row["role"] for row in ledger} == {
        "paired_clean_and_mutant",
        "clean_coverage",
        "clean_posterior_predictive",
        "mutant_plugin_predictive",
    }
    assert all(row["root_entropy"] == 202607123 for row in ledger)
    assert len({tuple(row["spawn_key"]) for row in ledger}) == len(ledger)
    for row in ledger:
        child = np.random.SeedSequence(
            202607123, spawn_key=tuple(row["spawn_key"])
        )
        assert row["stream_hash"] == hashlib.sha256(
            child.generate_state(4).tobytes()
        ).hexdigest()
        assert row["bit_generator"] == "PCG64DXSM"


def test_call_scan_rejects_mapped_symbol_without_an_import(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("pr123_builder", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "indirect_reference.py"
    source.write_text("def reference(x):\n    return mv_weights(x)\n", encoding="utf-8")
    checks = module._automated_scan_checks(source, {"mv_weights"})
    assert checks["forbidden_import_prefixes_clean"] is True
    assert checks["mapped_production_symbol_calls_clean"] is False

    source.write_text(
        "from htt import obsstat\ndef reference(x):\n    return getattr(obsstat, 'mv_weights')(x)\n",
        encoding="utf-8",
    )
    checks = module._automated_scan_checks(source, {"mv_weights"})
    assert checks["forbidden_import_prefixes_clean"] is False
    assert checks["dynamic_import_and_codegen_clean"] is False


@pytest.mark.parametrize(
    ("source_text", "dynamic_must_fail"),
    (
        ("alias = mv_weights\ndef reference(x):\n    return alias(x)\n", False),
        (
            "aliases = [mv_weights]\ndef reference(x):\n"
            "    return aliases[0](x)\n",
            False,
        ),
        (
            "aliases = {'mapped': mv_weights}\ndef reference(x):\n"
            "    return aliases['mapped'](x)\n",
            False,
        ),
        (
            "from functools import partial\n"
            "def reference(x):\n    return partial(mv_weights)(x)\n",
            False,
        ),
        (
            "def reference(obj, values):\n"
            "    return list(map(obj.mv_weights, values))\n",
            False,
        ),
        (
            "g = getattr\ndef reference(obj, x):\n"
            "    return g(obj, 'mv_weights')(x)\n",
            True,
        ),
        (
            "def reference(obj, x):\n"
            "    return __builtins__['getattr'](obj, 'mv_weights')(x)\n",
            True,
        ),
        (
            "def reference(obj, x):\n"
            "    return obj.__dict__['mv_' + 'weights'](x)\n",
            True,
        ),
        (
            "def reference(obj, x):\n"
            "    return obj.__getattribute__('mv_' + 'weights')(x)\n",
            True,
        ),
    ),
)
def test_call_scan_rejects_alias_and_dynamic_indirection(
    tmp_path: Path,
    source_text: str,
    dynamic_must_fail: bool,
) -> None:
    spec = importlib.util.spec_from_file_location("pr123_builder_aliases", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "aliased_reference.py"
    source.write_text(source_text, encoding="utf-8")
    checks = module._automated_scan_checks(source, {"mv_weights"})
    assert checks["mapped_production_symbol_calls_clean"] is False
    assert checks["dynamic_import_and_codegen_clean"] is (not dynamic_must_fail)


@pytest.mark.parametrize(
    "source_text",
    (
        (
            "def harmless():\n    mv_weights = 0\n    return mv_weights\n"
            "def reference(x):\n    aliases = [mv_weights]\n    return aliases[0](x)\n"
        ),
        (
            "def reference(mv_weights, x):\n"
            "    aliases = [mv_weights]\n    return aliases[0](x)\n"
        ),
    ),
)
def test_call_scan_uses_lexical_not_module_global_shadowing(
    tmp_path: Path,
    source_text: str,
) -> None:
    spec = importlib.util.spec_from_file_location("pr123_builder_scopes", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "scoped_reference.py"
    source.write_text(source_text, encoding="utf-8")
    checks = module._automated_scan_checks(
        source,
        {"mv_weights"},
        allowed_local_shadows=frozenset({"mv_weights"}),
    )
    assert checks["mapped_production_symbol_calls_clean"] is False


def test_five_invalidated_attempts_remain_content_addressed_and_nonconsumable() -> None:
    payload = json.loads(
        (GENERATED / "pr123_attempt_history.json").read_text(encoding="utf-8")
    )
    first, second, third, fourth, fifth, sixth = payload["attempts"]
    assert [
        first["status"], second["status"], third["status"], fourth["status"],
        fifth["status"],
    ] == [
        "INVALIDATED_FALSE_GREEN",
        "INVALIDATED_FALSE_GREEN",
        "INVALIDATED_FALSE_GREEN",
        "INVALIDATED_FALSE_GREEN",
        "INVALIDATED_FALSE_GREEN",
    ]
    assert all(
        attempt["counts_must_not_be_consumed"] is True
        for attempt in (first, second, third, fourth, fifth)
    )
    assert len(first["artifact_hashes"]) == 5
    assert len(second["artifact_hashes"]) == 6
    assert len(third["artifact_hashes"]) == 6
    assert len(fourth["artifact_hashes"]) == 6
    assert len(fifth["artifact_hashes"]) == 6
    assert sixth["attempt_id"] == "PR123-ATTEMPT-6"
    assert sixth["status"] == "PASS_MECHANICS_C2"
    assert sixth["prospective_preregistration_claimed"] is False
    assert sixth["scientific_status"] == "OPEN"


def test_remediation_root_is_bound_with_all_102_findings_open() -> None:
    report = json.loads(
        (GENERATED / "pr123_mutation_lab_report.json").read_text(encoding="utf-8")
    )
    receipt = report["remediation_state_receipt"]
    assert receipt["finding_count"] == 102
    assert receipt["scientific_status_counts"] == {"OPEN": 102}
    assert receipt["rescued_count"] == 0
    assert receipt["disposition_changes"] == []
