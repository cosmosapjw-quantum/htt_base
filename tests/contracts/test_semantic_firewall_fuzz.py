from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from common.semantic_guards.no_overclaim import scan_text


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_semantic_firewall_fuzzer_blocks_all_hostile_cases() -> None:
    module = _load_script("generate_semantic_firewall_fuzz_report")

    results = module.evaluate_firewall_cases()
    case_ids = {result.case_id for result in results}
    families = {result.attack_family for result in results}

    assert len(results) >= 14
    assert all(result.blocked for result in results)
    assert all(result.blocker for result in results)
    assert {
        "reserved_language",
        "figure_label",
        "q_metadata",
        "f_semantics",
        "pi_semantics",
        "g_f_semantics",
        "mio_htt_leakage",
        "transfer_provenance",
        "rank_null_covariance",
    }.issubset(families)
    assert {
        "reserved_public_claim_prose",
        "figure_label_owner_definition_mismatch",
        "q_family_metadata",
        "f_sign_dirty_sample",
        "f_super_ceiling_no_clipping",
        "f_external_ceiling_not_certified",
        "f_observational_ceiling_not_certified",
        "pi_curve_only_selected_threshold_smuggle",
        "pi_post_hoc_threshold_selection",
        "g_f_reserved_claim_metadata",
        "g_f_missing_covariance_status",
        "htt_likelihood_rejects_mio_payload",
        "htt_pushforward_rejects_mio_payload",
        "response_rank_deficiency_blocks_model_run",
        "atlas_entry_rejects_external_as_native",
    }.issubset(case_ids)


def test_semantic_firewall_report_payload_is_manifested_and_sanitized() -> None:
    module = _load_script("generate_semantic_firewall_fuzz_report")

    payload = module.build_report_payload(
        repo_root=REPO_ROOT,
        json_output=Path("docs/generated/semantic_firewall_fuzz_report.json"),
        md_output=Path("docs/generated/semantic_firewall_fuzz_report.md"),
        generating_command="python scripts/generate_semantic_firewall_fuzz_report.py",
        git_commit_or_worktree_state="test-worktree",
    )
    report = module.render_markdown(payload)
    parsed = json.loads(module.render_json(payload))

    assert payload["owner"] == "COMMON"
    assert payload["implementation_scope"] == "common"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["attack_count"] == len(payload["cases"])
    assert payload["smuggle_count"] == 0
    assert payload["leakage_path_count"] == 0
    assert payload["publication_ready"] is False
    assert parsed["config_hash"].startswith("sha256:")
    assert parsed["input_hashes"]
    assert "diagnostic-only firewall coverage" in report
    assert scan_text(report, path=Path("semantic_firewall_fuzz_report.md")) == ()

    forbidden_fragments = (
        "Bianchi " + "geometry " + "detected",
        "Bianchi " + "family " + "identified",
        "external transfer " + "validated as " + "native",
        "MIO " + "posterior " + "odds",
        "global " + "tilt",
    )
    for forbidden in forbidden_fragments:
        assert forbidden not in report
        assert forbidden not in module.render_json(payload)


def test_checked_in_semantic_firewall_report_is_current() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "generate_semantic_firewall_fuzz_report.py"),
            "--check",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_semantic_firewall_production_sources_are_hashed_and_packaged() -> None:
    report = json.loads(
        (REPO_ROOT / "docs/generated/semantic_firewall_fuzz_report.json").read_text(
            encoding="utf-8"
        )
    )
    package_manifest = json.loads(
        (
            REPO_ROOT
            / "legacy/cf4_p0/packages/statistical_formalism_audit/statistical_formalism_audit_package_manifest.json"
        ).read_text(encoding="utf-8")
    )

    required_sources = {
        "htt/src/common/semantic_guards/no_overclaim.py",
        "htt/src/common/transfer_registry.py",
        "htt/workspace/contracts/htt_posterior.py",
        "htt/htt/htt/departure/posterior_pushforward.py",
        "htt/htt/htt/departure/response_overlap.py",
        "htt/mio/formalism/budget_spec.py",
        "htt/mio/formalism/departure_bundle.py",
        "htt/mio/formalism/exceedance.py",
        "htt/mio/formalism/filling_fraction.py",
        "htt/mio/formalism/isotropy_gap.py",
        "htt/mio/formalism/normalized_score.py",
        "htt/bass/atlas/atlas_entry.py",
        "htt/bass/transfer/registry.py",
        "scripts/verify_formalism_figure_labels.py",
    }
    hashed_sources = {
        str(item).split(":", 1)[0] for item in report["input_hashes"]
    }
    package_sources = {
        row["source_path"]
        for row in package_manifest["archive_entries"]
        if row["group"] == "formalism_code"
    }

    assert required_sources.issubset(hashed_sources)
    assert required_sources.issubset(package_sources)
