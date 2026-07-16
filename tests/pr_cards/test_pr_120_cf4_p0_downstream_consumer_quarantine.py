"""PR-120 CF4 P0 producer/consumer quarantine contract and mutations."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

from common import cf4_p0_quarantine as quarantine


REPO = Path(__file__).resolve().parents[2]
EXPECTED_FINDINGS = {
    "C1-K5-MV-F1",
    "C3-K5-VCORR-ML-F1",
    "N-DATA-CF4-DOWNSTREAM",
}


def _load_script(relative: str, name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("signature_id", "text"),
    [
        ("cf4_mv_r200_headline", "CF4 MV bulk-flow B200 amplitude 405.22 km/s"),
        (
            "cf4_mv_analytic_tension",
            "CF4 bulk-flow LambdaCDM range 4.44-5.40 sigma",
        ),
        ("cf4_mv_mock_significance", "CF4 bulk-flow mock significance 5.8 sigma"),
        (
            "cf4_ml_shape_factor",
            "CF4 velocity correlation f_sigma8 shape_correction_pk_corr=1.4423",
        ),
        ("cf4_ml_corrected_headline", "CF4 Vpec f_sigma8 = 0.4046"),
        ("cf4_ml_raw_replacement", "CF4 raw EH98 f_sigma8 replacement = 0.486"),
        (
            "cf4_ml_published_offset",
            "CF4 f_sigma8 shape-corrected offset is 4.9 sigma",
        ),
        ("cf4_gls_headline", "CF4 GLS bulk-flow = 341 km/s; Omega_tilt follows"),
        ("cf4_gls_headline", "CF4 GLS bulk-flow = 340.73 km/s"),
        ("cf4_gls_headline", "CF4 GLS bulk-flow = 340.7 km/s"),
        (
            "cf4_reconstruction_spread_measured",
            "CF4 bulk-flow status MEASURED_RECONSTRUCTION_SPREAD",
        ),
        (
            "cf4_forward_mock_coverage_claim",
            "CF4 bulk-flow null_mock_status=forward_mock_coverage_calibrated",
        ),
        (
            "cf4_egs3_k5card_real_data",
            "EGS3-K5card runs a K5/CF4 identified-interval pipeline on real CF4",
        ),
        (
            "cf4_teff_numeric_instantiation",
            "K5/CF4 deterministic Teff fingerprint row from the same CF4 bulk-flow rapidity",
        ),
        (
            "cf4_v6_measured_component",
            "v6 K5 CF4 Omega_tilt source_mode=estimated_conditional_coverage",
        ),
        ("cf4_omega_tilt_pushforward", "CF4 Omega_tilt = 4.073e-7"),
        (
            "cf4_audit_sensitivity_replacement",
            "CF4 monopole corrected replacement bulk flow = 94.155 km/s",
        ),
        (
            "cf4_precision_upgrade_phrase",
            "precision upgrade: the CF4 velocity field is now measured",
        ),
    ],
)
def test_contextual_mutation_corpus_is_rejected(signature_id: str, text: str):
    issues = quarantine.validate_active_text(
        "release/public_result.json", text, repo_root=REPO
    )
    assert signature_id in {issue.signature_id for issue in issues}
    assert set().union(*(issue.finding_ids for issue in issues)) <= EXPECTED_FINDINGS


@pytest.mark.parametrize(
    "text",
    [
        "CatWISE rejects a pure-kinematic dipole at 4.9 sigma.",
        "HTTP status 405 is unrelated to any scientific result.",
        "A symbolic Omega_tilt coordinate is not a CF4 numerical pushforward.",
        "CF4 P0 findings remain OPEN and this blocked source has no replacement value.",
        "A toy array contains 0.4046 but no survey, velocity, or growth context.",
        "A generic numerical fixture contains 340.73 as an unrelated constant.",
        "An image pipeline reports MEASURED_RECONSTRUCTION_SPREAD for a camera benchmark.",
        "null_mock_status=forward_mock_coverage_calibrated for a lensing-only benchmark.",
        "EGS3-K5card is QUARANTINED_OPEN_P0 and carries no real-CF4 result.",
        "The symbolic Teff correspondence has no CF4 numerical instantiation.",
        "estimated_conditional_coverage is an unrelated generic schema example.",
    ],
)
def test_contextual_scan_preserves_false_positive_controls(text: str):
    assert (
        quarantine.validate_active_text(
            "release/unrelated_note.txt", text, repo_root=REPO
        )
        == ()
    )


@pytest.mark.parametrize("padding", [255, 256, 300, 420, 421])
def test_context_window_cannot_be_evaded_at_declared_boundaries(padding: int):
    text = "CF4 bulk-flow amplitude " + ("x" * padding) + "405.22 km/s"
    issues = quarantine.validate_active_text(
        "release/padded_consumer.md", text, repo_root=REPO
    )
    assert {issue.signature_id for issue in issues} == {"cf4_mv_r200_headline"}


def test_historical_prefix_requires_a_real_path_boundary(tmp_path: Path):
    spoof = REPO / "docs/audits_spoof_cf4_p0.md"
    spoof.write_text("CF4 bulk-flow amplitude 405.22 km/s", encoding="utf-8")
    try:
        report = quarantine.validate_repository(REPO)
    finally:
        spoof.unlink()
    assert any(
        issue.path == "docs/audits_spoof_cf4_p0.md"
        and issue.signature_id == "cf4_mv_r200_headline"
        for issue in report.issues
    )


@pytest.mark.parametrize(
    "relative",
    [
        "pr120_root_scan_probe.md",
        "src/pr120_src_scan_probe.py",
        "dl_pipeline/pr120_dl_scan_probe.yaml",
    ],
)
def test_exhaustive_scan_covers_root_src_and_dl_pipeline(relative: str):
    probe = REPO / relative
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text("CF4 MV bulk-flow B200 amplitude 405.22 km/s", encoding="utf-8")
    try:
        report = quarantine.validate_repository(REPO)
    finally:
        probe.unlink()
    assert any(
        issue.path == relative and issue.signature_id == "cf4_mv_r200_headline"
        for issue in report.issues
    )


@pytest.mark.parametrize("symlink_kind", ["final", "parent", "broken"])
def test_repository_scan_rejects_final_parent_and_broken_symlinks(
    tmp_path: Path,
    symlink_kind: str,
):
    link = REPO / f"src/pr120_{symlink_kind}_symlink_probe.py"
    if symlink_kind == "parent":
        target_dir = tmp_path / "target_dir"
        target_dir.mkdir()
        (target_dir / "probe.py").write_text("benign = True\n", encoding="utf-8")
        link = REPO / "src/pr120_parent_symlink_probe"
        link.symlink_to(target_dir, target_is_directory=True)
    elif symlink_kind == "broken":
        link.symlink_to(tmp_path / "missing.py")
    else:
        target = tmp_path / "target.py"
        target.write_text("benign = True\n", encoding="utf-8")
        link.symlink_to(target)
    try:
        report = quarantine.validate_repository(REPO)
    finally:
        link.unlink()
    assert any(
        issue.path == link.relative_to(REPO).as_posix()
        and issue.code == "unsafe_or_unreadable_active_path"
        and "symlink" in issue.detail
        for issue in report.issues
    )


def test_canonical_loader_rejects_symlink_even_when_target_bytes_are_exact():
    relative = Path("docs/generated/pr120_exact_block_symlink.json")
    link = REPO / relative
    link.symlink_to(REPO / quarantine.BLOCK_RELATIVE_PATH)
    try:
        with pytest.raises(quarantine.CF4P0PolicyError, match="symlink"):
            quarantine._load_json_mapping(REPO, link, "symlinked canonical block")
    finally:
        link.unlink()


def test_public_safe_text_io_reads_and_atomically_replaces_regular_files(
    tmp_path: Path,
):
    root = tmp_path / "repo"
    target = root / "generated/result.json"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    quarantine.atomic_write_text(root, "generated/result.json", "after\n")
    assert quarantine.read_regular_text(root, "generated/result.json") == "after\n"
    assert quarantine.read_regular_bytes(root, "generated/result.json") == b"after\n"
    assert not list(target.parent.glob(".result.json.*.tmp"))


@pytest.mark.parametrize("kind", ["final", "parent", "broken"])
def test_public_safe_text_io_rejects_final_parent_and_broken_symlinks(
    tmp_path: Path,
    kind: str,
):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    if kind == "parent":
        linked_parent = root / "linked"
        linked_parent.symlink_to(tmp_path, target_is_directory=True)
        relative = "linked/outside.txt"
    else:
        link = root / "target.txt"
        link.symlink_to(outside if kind == "final" else tmp_path / "missing.txt")
        relative = "target.txt"
    with pytest.raises(quarantine.CF4P0PolicyError, match="symlink"):
        quarantine.read_regular_text(root, relative)
    with pytest.raises(quarantine.CF4P0PolicyError, match="symlink"):
        quarantine.read_regular_bytes(root, relative)
    with pytest.raises(quarantine.CF4P0PolicyError, match="symlink"):
        quarantine.atomic_write_text(root, relative, "mutation\n")
    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_atomic_write_failure_preserves_original_and_cleans_temp(
    tmp_path: Path,
    monkeypatch,
):
    root = tmp_path / "repo"
    target = root / "generated/result.txt"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    def _fail_replace(source, destination):
        raise OSError("injected replace failure")

    monkeypatch.setattr(quarantine.os, "replace", _fail_replace)
    with pytest.raises(quarantine.CF4P0PolicyError, match="atomically"):
        quarantine.atomic_write_text(root, "generated/result.txt", "new\n")
    assert target.read_text(encoding="utf-8") == "original\n"
    assert not list(target.parent.glob(".result.txt.*.tmp"))


def test_policy_binds_exact_open_roots_and_no_science_promotion():
    policy, policy_hash = quarantine.load_policy(REPO)
    assert policy["schema"] == quarantine.POLICY_SCHEMA
    assert len(policy_hash) == 64
    assert policy["implementation_scope"] == "propagation_quarantine_only"
    assert policy["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C1"}
    assert policy["claim_tier"] == "blocked"
    assert policy["scan"]["roots"] == ["."]
    assert policy["scan"]["typed_historical_top_level_roots"] == ["legacy"]
    roots = policy["root_state"]
    assert roots["finding_count"] == 102
    assert roots["rescued_count"] == 0
    assert {
        row["finding_id"] for row in roots["required_open_findings"]
    } == EXPECTED_FINDINGS
    assert policy["package_content_modes"]["governance_control_paths"] == [
        "docs/codex_handoff/pr_backlog.yaml",
        "docs/codex_handoff/pr_status.yaml",
        "docs/codex_handoff/pr_dag_research_program.yaml",
        "docs/codex_handoff/pr_dag_revision.yaml",
    ]


def test_package_governance_allowlist_is_exact_and_live_dags_stay_scanned():
    policy, _ = quarantine.load_policy(REPO)
    governance = policy["package_content_modes"]["governance_control_paths"]
    for relative in governance:
        assert quarantine._is_typed_non_science_source(
            relative, policy, quarantine.ContentMode.GOVERNANCE_CONTROL
        )
    assert not quarantine._is_typed_non_science_source(
        "docs/codex_handoff/pr_status.yaml.spoof",
        policy,
        quarantine.ContentMode.GOVERNANCE_CONTROL,
    )
    for relative in governance[1:]:
        assert not quarantine._is_repository_exception(relative, policy)


def test_manuscript_snapshot_is_typed_historical_but_main_gate_stays_active():
    policy, _ = quarantine.load_policy(REPO)
    historical = {
        "docs/manuscript/appendices.tex",
        "docs/manuscript/ch01_introduction.tex",
        "docs/manuscript/ch02_dipole_anomaly.tex",
        "docs/manuscript/ch03_framework.tex",
        "docs/manuscript/ch04_bianchi_bounds.tex",
        "docs/manuscript/ch05_teff_corrections.tex",
        "docs/manuscript/ch06_pipeline.tex",
        "docs/manuscript/ch07_results.tex",
        "docs/manuscript/ch08_robustness.tex",
        "docs/manuscript/ch09_discussion.tex",
        "docs/manuscript/ch10_future.tex",
        "docs/manuscript/ch11_error_hierarchy.tex",
        "docs/manuscript/references.bib",
    }
    assert historical <= set(policy["scan"]["immutable_historical_paths"])
    assert all(
        quarantine._is_repository_exception(relative, policy) for relative in historical
    )
    assert quarantine._is_repository_exception(
        "docs/manuscript/generated/current_figures_results.tex", policy
    )
    assert not quarantine._is_repository_exception("docs/manuscript/main.tex", policy)


def test_policy_rejects_a_prefix_that_exempts_an_entire_scan_root(tmp_path: Path):
    payload = yaml.safe_load(
        (REPO / quarantine.POLICY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    payload["scan"]["immutable_historical_prefixes"] = ["docs/"]
    mutated = tmp_path / "broad-prefix-policy.yaml"
    mutated.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(quarantine.CF4P0PolicyError, match="broad active"):
        quarantine.load_policy(REPO, policy_path=mutated)


def test_authoritative_remediation_root_stays_exactly_all_open():
    payload = yaml.safe_load(
        (REPO / "docs/codex_handoff/research_remediation_state.yaml").read_text()
    )
    assert payload["census"]["finding_count"] == 102
    assert payload["census"]["rescued_count"] == 0
    assert payload["census"]["scientific_status_counts"] == {"OPEN": 102}
    rows = {row["finding_id"]: row for row in payload["findings"]}
    for finding_id in EXPECTED_FINDINGS:
        assert rows[finding_id]["scientific_status"] == "OPEN"
        assert rows[finding_id]["execution_resolution"] is None
        assert rows[finding_id]["claim_tier_ceiling"] == "blocked"


def test_canonical_block_has_no_replacement_and_preserves_open_findings():
    record = quarantine.load_block_record(REPO)
    payload = record.to_dict()
    assert payload["schema"] == quarantine.BLOCK_SCHEMA
    assert payload["status"] == "QUARANTINED_OPEN_FINDINGS"
    assert payload["replacement_value"] is None
    assert payload["scientific_effect"] == "none"
    assert payload["allowed_use"] == "blocked_source_record_only"
    assert {row["finding_id"] for row in payload["findings"]} == EXPECTED_FINDINGS
    assert {row["scientific_status"] for row in payload["findings"]} == {"OPEN"}
    rendered = json.dumps(payload, sort_keys=True)
    for forbidden_replacement in ("94.155", "94.8", "0.486", "3.110e-8"):
        assert forbidden_replacement not in rendered


def test_canonical_payload_generation_is_byte_deterministic():
    first = quarantine.canonical_artifact_bytes(REPO)
    second = quarantine.canonical_artifact_bytes(REPO)
    assert first == second
    assert set(first) == {
        "docs/generated/cf4_p0_quarantine_inventory.json",
        "docs/generated/cf4_p0_quarantine_inventory.md",
        "docs/generated/cf4_p0_quarantine_block.json",
        "docs/generated/cf4_p0_quarantine_block.md",
    }


def test_inventory_is_sorted_unique_and_hashes_every_legacy_file():
    payload = json.loads(
        (REPO / quarantine.INVENTORY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    paths = [row["path"] for row in payload["entries"]]
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths))
    legacy_files = {
        path.relative_to(REPO).as_posix()
        for path in (REPO / "legacy/cf4_p0").rglob("*")
        if path.is_file()
    }
    legacy_entries = {
        row["path"]
        for row in payload["entries"]
        if row["mode"] == "legacy_reproduction_only"
    }
    assert legacy_entries == legacy_files
    for row in payload["entries"]:
        path = REPO / row["path"]
        if row["mode"] == "active_public_binary":
            assert row["byte_validation"] == "dynamic_fail_closed_no_self_reference"
            assert row["binding_gate"].endswith(":verify_package_binary_binding")
            assert "sha256" not in row
        elif row["mode"] == "deterministic_release_output":
            assert row["byte_validation"] == (
                "mandatory_deterministic_builder_check_at_closeout"
            )
            assert row["digest_exclusion_reason"] == (
                "archive_embeds_canonical_inventory"
            )
            assert "sha256" not in row
        else:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_inventory_pins_active_producers_and_shared_release_gates():
    payload = json.loads(
        (REPO / quarantine.INVENTORY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    modes = {row["path"]: row["mode"] for row in payload["entries"]}
    required = {
        "scripts/cf4_p0_quarantine_producer.py",
        "scripts/cf4_mv_bulkflow.py",
        "scripts/cf4_mock_calibrated_significance.py",
        "scripts/cf4_velocity_correlation_ml.py",
        "scripts/cf4_bulkflow_lcdm_variance.py",
        "scripts/make_obsdata_r195_r198_figures.py",
        "scripts/build_egs_results_table.py",
        "scripts/build_egs_results_table_v8.py",
        "scripts/check_publication_claim_freeze.py",
        "scripts/build_external_audit_package.py",
        "scripts/build_research_only_audit_package.py",
    }
    assert required <= set(modes)
    assert {modes[path] for path in required} == {"active_block_consumer"}


def test_binary_binding_validator_is_hash_pinned_and_in_release_lineage():
    policy, _ = quarantine.load_policy(REPO)
    pinned = {row["path"]: row for row in policy["inventory"]["pinned_paths"]}
    helper = pinned["htt/src/common/package_binary_binding.py"]
    assert helper["mode"] == "validator_support"
    assert helper["role"] == "binary_release_binding_validator"
    assert helper["required_markers"] == ["verify_package_binary_binding"]
    htt_gate = pinned["htt/htt/htt/core/cf4_observational_input.py"]
    assert htt_gate["mode"] == "active_block_consumer"
    assert htt_gate["role"] == "active_htt_cf4_input_gate"
    ledger_path = (
        "docs/research_program/long_horizon_rescue/" "cf4_p0_legacy_package_hashes.json"
    )
    ledger = pinned[ledger_path]
    assert ledger["mode"] == "validator_support"
    assert ledger["role"] == "fixed_pr119_legacy_package_hash_authority"
    edge = next(
        row
        for row in policy["inventory"]["lineage_edges"]
        if row["edge_id"] == "binary_binding_validator_to_release_builders"
    )
    assert edge["from_path"] == "htt/src/common/package_binary_binding.py"
    assert set(edge["to_paths"]) == {
        "scripts/build_external_audit_package.py",
        "scripts/build_research_only_audit_package.py",
        "scripts/build_research_evaluation_package.py",
        "scripts/build_statistical_formalism_audit_package.py",
    }
    inventory = json.loads(
        (REPO / quarantine.INVENTORY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    entry = next(
        row
        for row in inventory["entries"]
        if row["path"] == "htt/src/common/package_binary_binding.py"
    )
    helper_bytes = (REPO / entry["path"]).read_bytes()
    assert entry["sha256"] == hashlib.sha256(helper_bytes).hexdigest()
    ledger_edge = next(
        row
        for row in policy["inventory"]["lineage_edges"]
        if row["edge_id"] == "fixed_legacy_hash_ledger_to_validator_support"
    )
    assert ledger_edge["from_path"] == ledger_path


def test_inventory_carries_explicit_producer_consumer_lineage_graph():
    payload = json.loads(
        (REPO / quarantine.INVENTORY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    edges = {edge["edge_id"]: edge for edge in payload["lineage_edges"]}
    assert payload["lineage_edge_count"] == len(edges) == 8
    assert {
        "canonical_block_to_every_active_consumer",
        "binary_binding_validator_to_release_builders",
        "fixed_legacy_hash_ledger_to_validator_support",
        "mv_p0_producer_to_active_gate",
        "ml_p0_producer_to_active_gate",
        "canonical_block_to_derived_cards",
        "canonical_block_to_figure_and_teff_consumers",
        "canonical_block_to_release_consumers",
    } == set(edges)
    all_findings = {
        finding for edge in edges.values() for finding in edge["finding_ids"]
    }
    assert all_findings == EXPECTED_FINDINGS
    assert all(edge["disposition"] for edge in edges.values())


def test_every_active_block_consumer_is_a_downstream_lineage_endpoint():
    policy, _ = quarantine.load_policy(REPO)
    active = {
        row["path"]
        for row in policy["inventory"]["pinned_paths"]
        if row["mode"] == "active_block_consumer"
    }
    covered = {
        path
        for edge in policy["inventory"]["lineage_edges"]
        for path in edge["to_paths"]
    }
    assert active
    assert active <= covered


def test_policy_rejects_an_active_consumer_removed_from_lineage(tmp_path: Path):
    payload = yaml.safe_load(
        (REPO / quarantine.POLICY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    edge = next(
        row
        for row in payload["inventory"]["lineage_edges"]
        if row["edge_id"] == "canonical_block_to_every_active_consumer"
    )
    edge["to_paths"].remove("docs/generated/egs_results_table_v9.md")
    mutated = tmp_path / "missing-lineage-policy.yaml"
    mutated.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(quarantine.CF4P0PolicyError, match="active_block_consumer"):
        quarantine.load_policy(REPO, policy_path=mutated)


def test_policy_locks_cf4_p0_figure_and_conditioned_paths_absent():
    policy, _ = quarantine.load_policy(REPO)
    paths = policy["inventory"]["required_absent_active_paths"]
    assert tuple(paths) == quarantine._EXPECTED_CF4_P0_ACTIVE_ABSENT_PATHS
    assert all(not (REPO / relative).exists() for relative in paths)

    probe = REPO / paths[0]
    frozen = REPO / "legacy/cf4_p0/figures/parallel_track" / probe.name
    probe.write_bytes(frozen.read_bytes())
    try:
        with pytest.raises(quarantine.CF4P0PolicyError, match="must remain absent"):
            quarantine.load_policy(REPO)
    finally:
        probe.unlink()


def test_inventory_enumerates_every_active_public_binary():
    policy, _ = quarantine.load_policy(REPO)
    payload = json.loads(
        (REPO / quarantine.INVENTORY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    actual = {
        row["path"]
        for row in payload["entries"]
        if row["mode"] in {"active_public_binary", "deterministic_release_output"}
    }
    expected = set(quarantine._active_binary_paths(REPO, policy))
    assert actual == expected
    assert payload["active_public_binary_count"] + payload[
        "deterministic_release_output_count"
    ] == len(expected)


def test_deterministic_release_output_allowlist_is_exact_and_requires_checks():
    policy, _ = quarantine.load_policy(REPO)
    outputs = policy["inventory"]["deterministic_release_outputs"]
    assert outputs == quarantine._EXPECTED_DETERMINISTIC_RELEASE_OUTPUTS
    assert len(outputs) == 4
    for output, contract in outputs.items():
        assert (REPO / output).is_file()
        assert (REPO / contract["builder_path"]).is_file()
        manifest = json.loads((REPO / contract["manifest_path"]).read_text())
        assert manifest["artifact_path"] == output
        assert contract["check_command"].endswith(" --check")


@pytest.mark.parametrize(
    "output_path", sorted(quarantine._EXPECTED_DETERMINISTIC_RELEASE_OUTPUTS)
)
def test_deterministic_release_output_closeout_check_passes(output_path: str):
    command = quarantine._EXPECTED_DETERMINISTIC_RELEASE_OUTPUTS[output_path][
        "check_command"
    ]
    completed = subprocess.run(
        shlex.split(command),
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_arbitrary_fifth_release_zip_cannot_inherit_output_allowlist():
    relative = "0_pr120_fifth_release_output.zip"
    probe = REPO / relative
    probe.write_bytes(b"PK\x03\x04not-a-reviewed-release-output")
    try:
        with pytest.raises(quarantine.CF4P0PolicyError) as exc_info:
            quarantine.build_inventory_payload(REPO)
    finally:
        probe.unlink()
    assert relative in str(exc_info.value)


def test_unbound_binary_outside_package_inputs_invalidates_inventory():
    relative = "0_pr120_unbound_binary_probe.png"
    probe = REPO / relative
    probe.write_bytes(b"\x89PNG\r\n\x1a\nnot-independently-bound")
    try:
        with pytest.raises(quarantine.CF4P0PolicyError) as exc_info:
            quarantine.build_inventory_payload(REPO)
    finally:
        probe.unlink()
    assert relative in str(exc_info.value)


def _policy_with_reviewed_binary_pin(
    tmp_path: Path,
    *,
    binary_path: str,
    sidecar_path: str,
) -> Path:
    payload = yaml.safe_load(
        (REPO / quarantine.POLICY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    payload["inventory"]["reviewed_active_binary_sidecars"] = {
        binary_path: {
            "sidecar_path": sidecar_path,
            "sidecar_sha256": (
                "sha256:"
                + hashlib.sha256((REPO / sidecar_path).read_bytes()).hexdigest()
            ),
            "artifact_sha256": (
                "sha256:"
                + hashlib.sha256((REPO / binary_path).read_bytes()).hexdigest()
            ),
            "review_scope": "PR-120-reviewed-active-binary",
        }
    }
    target = tmp_path / "reviewed-binary-policy.yaml"
    target.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return target


def test_committed_binary_uses_head_authority_after_reviewed_pin_retirement():
    binary = "figures/current/fig_egs3_u1_beta_channel.png"
    policy, _ = quarantine.load_policy(REPO)
    assert binary not in policy["inventory"]["reviewed_active_binary_sidecars"]

    entry = quarantine._binary_inventory_entry(REPO, binary, policy)
    assert entry["binding_method"] == "git_head_exact_bytes"
    assert entry["trusted_source"] == f"git-head:{binary}"
    assert "reviewed_sidecar_path" not in entry
    assert "reviewed_artifact_sha256" not in entry
    assert quarantine.reviewed_active_binary_sidecar_pin(REPO, binary) is None


def test_reviewed_binary_pin_snapshot_is_build_local_and_hash_rechecked():
    snapshot = quarantine.reviewed_active_binary_sidecar_pin_snapshot(REPO)
    assert snapshot.pins["codex_shared_context_harness_v1.zip"] == (
        "codex_shared_context_harness_v1.zip.manifest.json",
        "sha256:7671e787f23ba9018859133c0f41488ffd89456f0a5696fff705f810eb24e54b",
    )
    with pytest.raises(TypeError):
        snapshot.pins["unexpected.zip"] = ("unexpected.json", "sha256:" + "0" * 64)
    quarantine.assert_reviewed_active_binary_pin_snapshot_current(REPO, snapshot)

    stale = quarantine.ReviewedActiveBinaryPinSnapshot(
        policy_sha256="0" * 64,
        pins=snapshot.pins,
    )
    with pytest.raises(
        quarantine.CF4P0PolicyError,
        match="policy changed during package construction",
    ):
        quarantine.assert_reviewed_active_binary_pin_snapshot_current(REPO, stale)


def test_reviewed_binary_pin_snapshot_rejects_actual_policy_byte_drift(monkeypatch):
    snapshot = quarantine.reviewed_active_binary_sidecar_pin_snapshot(REPO)
    original_reader = quarantine._read_absolute_regular_bytes

    def drifted_reader(path, *, label):
        data = original_reader(path, label=label)
        if Path(path).name == "cf4_p0_quarantine_policy.yaml":
            return data + b"\n# concurrent drift\n"
        return data

    monkeypatch.setattr(
        quarantine,
        "_read_absolute_regular_bytes",
        drifted_reader,
    )
    with pytest.raises(
        quarantine.CF4P0PolicyError,
        match="policy changed during package construction",
    ):
        quarantine.assert_reviewed_active_binary_pin_snapshot_current(REPO, snapshot)


def test_reviewed_binary_policy_rejects_placeholder_or_stale_digest(
    tmp_path: Path,
):
    binary = "figures/current/fig_egs3_u1_beta_channel.png"
    sidecar = "figures/current/fig_egs3_u1_beta_channel.manifest.json"
    policy_path = _policy_with_reviewed_binary_pin(
        tmp_path,
        binary_path=binary,
        sidecar_path=sidecar,
    )
    payload = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    payload["inventory"]["reviewed_active_binary_sidecars"][binary][
        "sidecar_sha256"
    ] = ("sha256:" + "0" * 64)
    policy_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(quarantine.CF4P0PolicyError, match="sidecar pin is stale"):
        quarantine.load_policy(REPO, policy_path=policy_path)


def test_reviewed_binary_pin_cannot_be_unused_for_head_identical_bytes(
    tmp_path: Path,
    monkeypatch,
):
    binary = "figures/current/fig_egs3_u1_beta_channel.png"
    sidecar = "figures/current/fig_egs3_u1_beta_channel.manifest.json"
    policy_path = _policy_with_reviewed_binary_pin(
        tmp_path,
        binary_path=binary,
        sidecar_path=sidecar,
    )
    policy, _ = quarantine.load_policy(REPO, policy_path=policy_path)
    monkeypatch.setattr(
        quarantine,
        "verify_package_binary_binding",
        lambda *args, **kwargs: {
            "method": "git_head_exact_bytes",
            "sha256": policy["inventory"]["reviewed_active_binary_sidecars"][binary][
                "artifact_sha256"
            ],
            "trusted_source": f"git-head:{binary}",
        },
    )
    with pytest.raises(quarantine.CF4P0PolicyError, match="unused"):
        quarantine._binary_inventory_entry(REPO, binary, policy)


@pytest.mark.parametrize(
    ("relative", "module_name", "active_outputs"),
    [
        (
            "scripts/build_egs_results_table.py",
            "pr120_egs_v7_legacy_gateway",
            (
                "docs/generated/egs_results_table.json",
                "docs/generated/egs_results_table.md",
            ),
        ),
        (
            "scripts/build_egs_results_table_v8.py",
            "pr120_egs_v8_legacy_gateway",
            (
                "docs/generated/egs_results_table_v8.json",
                "docs/generated/egs_results_table_v8.md",
            ),
        ),
    ],
)
def test_historical_table_gateways_fail_closed_and_have_no_active_outputs(
    relative: str,
    module_name: str,
    active_outputs: tuple[str, str],
):
    module = _load_script(relative, module_name)
    assert module.main([]) == 2
    assert all(not (REPO / output).exists() for output in active_outputs)


@pytest.mark.parametrize(
    "builder_name",
    [
        "_plot_cf4_forward_coverage_residual",
        "_plot_k5_cf4_vs_affine_consistency",
        "_plot_observed_sector_response_vector",
        "_plot_k1_k5_joint_diagnostic_axes",
        "_plot_k5_cf4_bulk_flow_coverage",
    ],
)
def test_removed_cf4_p0_report_builders_fail_before_reading_old_schemas(
    builder_name: str,
    tmp_path: Path,
):
    module = _load_script(
        "scripts/make_report_data_analysis_figures.py",
        f"pr120_report_builder_guard_{builder_name}",
    )
    with pytest.raises(module.CF4P0FigureQuarantined, match="remain OPEN"):
        getattr(module, builder_name)(tmp_path / "must-not-exist.png")
    assert not (tmp_path / "must-not-exist.png").exists()


def test_repository_and_canonical_artifacts_validate_clean():
    report = quarantine.validate_repository(REPO)
    assert report.ok, report.to_dict()
    assert report.issues == ()
    assert report.inventory_sha256
    assert report.block_sha256


def test_additional_package_content_never_inherits_historical_exception():
    report = quarantine.validate_repository(
        REPO,
        additional_contents={
            "docs/audits/copied_into_public_package.json": (
                "CF4 MV bulk-flow B200 amplitude 405.22 km/s"
            )
        },
    )
    assert not report.ok
    assert any(issue.signature_id == "cf4_mv_r200_headline" for issue in report.issues)


def test_exact_canonical_controls_can_be_relocated_inside_a_package():
    contents = {
        f"package/quarantine/{Path(relative).name}": (REPO / relative).read_bytes()
        for relative in (
            quarantine.INVENTORY_RELATIVE_PATH,
            quarantine.BLOCK_RELATIVE_PATH,
        )
    }
    report = quarantine.validate_repository(REPO, additional_contents=contents)
    assert report.ok, report.to_dict()


def test_mutated_canonical_control_copy_loses_its_package_exception():
    content = (REPO / quarantine.INVENTORY_RELATIVE_PATH).read_bytes()
    content += b'\n{"claim":"CF4 MV bulk-flow amplitude 405.22 km/s"}\n'
    report = quarantine.validate_repository(
        REPO,
        additional_contents={"package/quarantine/mutated_inventory.json": content},
    )
    assert any(issue.signature_id == "cf4_mv_r200_headline" for issue in report.issues)


def test_hash_bound_governance_package_entry_is_typed_and_accepted():
    content = quarantine.repository_content(
        REPO,
        "docs/codex_handoff/pr_backlog.yaml",
        mode=quarantine.ContentMode.GOVERNANCE_CONTROL,
    )
    report = quarantine.validate_repository(
        REPO,
        additional_contents={"status/pr_backlog.yaml": content},
    )
    assert report.ok, report.to_dict()


def test_typed_governance_mode_rejects_mutated_or_unlisted_source():
    content = quarantine.repository_content(
        REPO,
        "docs/codex_handoff/pr_backlog.yaml",
        mode=quarantine.ContentMode.GOVERNANCE_CONTROL,
    )
    mutated = quarantine.QuarantineContent(
        content=content.content + b"\nmutation",
        mode=content.mode,
        source_path=content.source_path,
        source_sha256=content.source_sha256,
    )
    mutated_report = quarantine.validate_repository(
        REPO,
        additional_contents={"status/pr_backlog.yaml": mutated},
    )
    assert any(
        issue.code == "typed_package_source_hash_mismatch"
        for issue in mutated_report.issues
    )

    active_source = quarantine.repository_content(
        REPO,
        "scripts/cf4_p0_quarantine_producer.py",
        mode=quarantine.ContentMode.GOVERNANCE_CONTROL,
    )
    unauthorized = quarantine.validate_repository(
        REPO,
        additional_contents={"status/not_governance.py": active_source},
    )
    assert any(
        issue.code == "unauthorized_non_science_content_mode"
        for issue in unauthorized.issues
    )

    historical_not_governance = quarantine.repository_content(
        REPO,
        "docs/codex_handoff/pr_backlog.json",
        mode=quarantine.ContentMode.GOVERNANCE_CONTROL,
    )
    historical_report = quarantine.validate_repository(
        REPO,
        additional_contents={"status/pr_backlog.json": historical_not_governance},
    )
    assert any(
        issue.code == "unauthorized_non_science_content_mode"
        for issue in historical_report.issues
    )


def test_binary_package_payloads_defer_to_manifest_and_pdf_gates():
    assert (
        quarantine.validate_active_text(
            "figures/public.png", b"\x89PNG\r\n\x1a\n\xff", repo_root=REPO
        )
        == ()
    )


def test_assert_repository_clean_raises_on_public_mutation():
    with pytest.raises(quarantine.CF4P0QuarantineViolation):
        quarantine.assert_repository_clean(
            REPO,
            additional_contents={
                "package/stale.json": "CF4 f_sigma8 shape correction = 1.4423"
            },
        )


def test_stale_embedded_block_copy_is_rejected_without_numeric_signature():
    payload = quarantine.quarantine_block_payload(REPO)
    payload["inventory_sha256"] = "0" * 64
    report = quarantine.validate_repository(
        REPO,
        additional_contents={
            "package/copied_block.json": json.dumps(payload, sort_keys=True)
        },
    )
    assert any(
        issue.code == "stale_embedded_quarantine_block" for issue in report.issues
    )


def _raw_canonical_block() -> dict:
    return json.loads(
        (REPO / quarantine.BLOCK_RELATIVE_PATH).read_text(encoding="utf-8")
    )


def _valid_minimal_artifact() -> dict:
    return {
        "active_path": "docs/generated/pr120_schema_probe.json",
        "artifact_id": "pr120_schema_probe",
        "artifact_kind": "result_card_block_record",
        "legacy_public_use": False,
        "legacy_reproduction_only_path": "legacy/cf4_p0/cards/pr120_schema_probe.json",
        "producer": "scripts/cf4_mv_bulkflow.py",
    }


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value"),
    [
        ("nested_status", {"scientific_status": "RESCUED"}),
        ("replacement", 94.155),
        ("public_use", True),
        ("evidence", {"family_identification": True}),
    ],
)
def test_nested_artifact_cannot_inject_science_or_public_promotion(
    mutation_key: str,
    mutation_value: object,
):
    canonical = _raw_canonical_block()
    payload = json.loads(json.dumps(canonical))
    payload["artifact"] = _valid_minimal_artifact()
    payload["artifact"][mutation_key] = mutation_value
    issues = quarantine._validate_embedded_block_record(
        "package/pr120_schema_probe.json",
        json.dumps(payload),
        canonical,
        require_path_match=False,
    )
    assert any(issue.code == "embedded_quarantine_promotion" for issue in issues), [
        issue.to_dict() for issue in issues
    ]
    assert any(
        issue.code == "invalid_embedded_quarantine_artifact_schema" for issue in issues
    )


def test_existing_embedded_block_artifacts_match_a_finite_strict_schema():
    canonical = _raw_canonical_block()
    checked = 0
    for source in sorted(REPO.glob("docs/generated/*.json")) + sorted(
        REPO.glob("figures/**/*.json")
    ):
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            continue
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != quarantine.BLOCK_SCHEMA
        ):
            continue
        if "artifact" not in payload:
            continue
        issues = quarantine._validate_embedded_block_record(
            source.relative_to(REPO).as_posix(),
            json.dumps(payload),
            canonical,
            require_path_match=True,
        )
        assert not {
            "embedded_quarantine_promotion",
            "invalid_embedded_quarantine_artifact_schema",
            "embedded_quarantine_path_mismatch",
        } & {issue.code for issue in issues}, [issue.to_dict() for issue in issues]
        checked += 1
    assert checked >= 20


def test_inventory_hash_mutation_is_rejected(tmp_path: Path, monkeypatch):
    payload = json.loads(
        (REPO / quarantine.INVENTORY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    payload["entries"][0]["sha256"] = "0" * 64
    mutated = tmp_path / "inventory.json"
    mutated.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    mutated_bytes = mutated.read_bytes()
    original_read = quarantine._read_regular_bytes

    def _read_with_mutated_inventory(root, relative, *, label):
        if relative == quarantine.INVENTORY_RELATIVE_PATH.as_posix():
            return mutated_bytes
        return original_read(root, relative, label=label)

    monkeypatch.setattr(quarantine, "_read_regular_bytes", _read_with_mutated_inventory)
    with pytest.raises(quarantine.CF4P0PolicyError, match="stale|non-canonical"):
        quarantine.load_block_record(REPO)


def test_block_hash_or_payload_mutation_is_rejected(tmp_path: Path, monkeypatch):
    payload = json.loads(
        (REPO / quarantine.BLOCK_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    payload["replacement_value"] = "audit_sensitivity"
    mutated = tmp_path / "block.json"
    mutated.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    mutated_bytes = mutated.read_bytes()
    original_read = quarantine._read_regular_bytes

    def _read_with_mutated_block(root, relative, *, label):
        if relative == quarantine.BLOCK_RELATIVE_PATH.as_posix():
            return mutated_bytes
        return original_read(root, relative, label=label)

    monkeypatch.setattr(quarantine, "_read_regular_bytes", _read_with_mutated_block)
    with pytest.raises(quarantine.CF4P0PolicyError, match="stale|non-canonical"):
        quarantine.load_block_record(REPO)


def test_legacy_mode_is_explicit_scoped_and_hash_bound():
    legacy = REPO / "legacy/cf4_p0/cards/cf4_mv_bulkflow_card.json"
    with pytest.raises(quarantine.LegacyReproductionRequired, match="explicit"):
        quarantine.require_legacy_reproduction(
            enabled=False, artifact_path=legacy, repo_root=REPO
        )
    with pytest.raises(quarantine.LegacyReproductionRequired, match="must stay under"):
        quarantine.require_legacy_reproduction(
            enabled=True,
            artifact_path="docs/generated/cf4_mv_bulkflow_card.json",
            repo_root=REPO,
        )
    quarantine.require_legacy_reproduction(
        enabled=True, artifact_path=legacy, repo_root=REPO
    )


def test_legacy_path_traversal_is_rejected():
    with pytest.raises(quarantine.CF4P0PolicyError, match="escapes"):
        quarantine.require_legacy_reproduction(
            enabled=True,
            artifact_path="legacy/cf4_p0/../../../outside.json",
            repo_root=REPO,
        )


def test_primary_legacy_runner_rechecks_script_and_output_after_execution(monkeypatch):
    module = _load_script(
        "scripts/cf4_p0_quarantine_producer.py", "pr120_shared_primary_wrapper"
    )
    calls: list[str] = []
    monkeypatch.setattr(
        module,
        "require_legacy_reproduction",
        lambda **kwargs: calls.append(str(kwargs["artifact_path"])),
    )
    monkeypatch.setattr(
        module,
        "_load_module",
        lambda *args, **kwargs: SimpleNamespace(main=lambda argv: 0),
    )
    spec = module.PRODUCERS["mv"]
    assert module._run_legacy(spec, spec.legacy_output, check=False) == 0
    assert calls == [
        spec.legacy_script,
        spec.legacy_output,
        spec.legacy_script,
        spec.legacy_output,
    ]


def test_primary_legacy_runner_mutates_only_temp_copy_and_raises(monkeypatch):
    module = _load_script(
        "scripts/cf4_p0_quarantine_producer.py", "pr120_primary_temp_mutation"
    )
    spec = module.PRODUCERS["mv"]
    canonical = REPO / spec.legacy_output
    before = canonical.read_bytes()
    before_hash = hashlib.sha256(before).hexdigest()
    monkeypatch.setattr(module, "require_legacy_reproduction", lambda **kwargs: None)

    frozen = SimpleNamespace()

    def _mutate_temp(argv):
        frozen.OUT.write_bytes(b"mutated disposable output")
        return 0

    frozen.main = _mutate_temp
    monkeypatch.setattr(module, "_load_module", lambda *args, **kwargs: frozen)
    with pytest.raises(quarantine.LegacyReproductionRequired, match="differs"):
        module._run_legacy(spec, spec.legacy_output, check=False)
    after = canonical.read_bytes()
    assert after == before
    assert hashlib.sha256(after).hexdigest() == before_hash


def test_primary_legacy_module_loads_with_outer_htt_owner_namespace():
    module = _load_script(
        "scripts/cf4_p0_quarantine_producer.py", "pr120_primary_import_order"
    )
    spec = module.PRODUCERS["mv"]
    frozen = module._load_module(
        REPO / spec.legacy_script,
        "pr120_loaded_legacy_mv",
        module_file=REPO / spec.active_producer,
    )
    assert callable(frozen.main)
    assert sys.path.index(str(REPO)) < sys.path.index(str(REPO / "htt"))


def test_primary_legacy_runner_rejects_cross_artifact_output(monkeypatch):
    module = _load_script(
        "scripts/cf4_p0_quarantine_producer.py", "pr120_primary_output_boundary"
    )
    spec = module.PRODUCERS["mv"]
    with pytest.raises(quarantine.LegacyReproductionRequired, match="exactly"):
        module._run_legacy(
            spec,
            module.PRODUCERS["ml"].legacy_output,
            check=False,
        )


def test_derived_legacy_card_routes_recheck_hashes_after_execution(monkeypatch):
    module = _load_script(
        "scripts/cf4_p0_quarantine_derived.py", "pr120_shared_derived_wrapper"
    )
    calls: list[str] = []
    monkeypatch.setattr(
        module,
        "require_legacy_reproduction",
        lambda **kwargs: calls.append(str(kwargs["artifact_path"])),
    )
    monkeypatch.setattr(
        module,
        "_load_module",
        lambda *args, **kwargs: SimpleNamespace(main=lambda argv: 0),
    )

    derived = module.IDENTIFIED_INTERVAL_SPECS["v7"]
    assert module._run_legacy(derived, check=False) == 0
    derived_pins = [
        derived.legacy_script,
        derived.legacy_json,
        derived.legacy_markdown,
    ]
    assert calls == derived_pins + derived_pins

    calls.clear()
    single = module.SINGLE_CARD_SPECS["coverage"]
    assert module.single_card_main(single, ["--legacy-reproduction"]) == 0
    single_pins = [single.legacy_script, single.legacy_json]
    assert calls == single_pins + single_pins


def test_derived_legacy_runner_mutates_only_temp_copy_and_raises(monkeypatch):
    module = _load_script(
        "scripts/cf4_p0_quarantine_derived.py", "pr120_derived_temp_mutation"
    )
    spec = module.IDENTIFIED_INTERVAL_SPECS["v7"]
    canonical_paths = [REPO / spec.legacy_json, REPO / spec.legacy_markdown]
    before = {path: path.read_bytes() for path in canonical_paths}
    before_hashes = {
        path: hashlib.sha256(value).hexdigest() for path, value in before.items()
    }
    monkeypatch.setattr(module, "_verify_pinned_legacy", lambda paths: None)
    frozen = SimpleNamespace()

    def _mutate_temp(argv):
        frozen.OUT_JSON.write_bytes(b"mutated disposable JSON")
        return 0

    frozen.main = _mutate_temp
    monkeypatch.setattr(module, "_load_module", lambda *args, **kwargs: frozen)
    with pytest.raises(RuntimeError, match="differs"):
        module._run_legacy(spec, check=False)
    for path in canonical_paths:
        after = path.read_bytes()
        assert after == before[path]
        assert hashlib.sha256(after).hexdigest() == before_hashes[path]


def test_derived_legacy_module_loads_with_outer_htt_owner_namespace():
    module = _load_script(
        "scripts/cf4_p0_quarantine_derived.py", "pr120_derived_import_order"
    )
    spec = module.IDENTIFIED_INTERVAL_SPECS["v7"]
    frozen = module._load_module(
        REPO / spec.legacy_script,
        "pr120_loaded_legacy_v7",
        module_file=REPO / spec.active_script,
    )
    assert callable(frozen.main)
    assert "htt.tsc" in sys.modules


@pytest.mark.parametrize(
    ("version", "legacy_package"),
    [
        ("v6", "external_audit_research_report_20260709_v6_1"),
        ("v7", "external_audit_research_report_20260710_v7"),
    ],
)
def test_historical_external_report_builders_are_fail_closed_gateways(
    version: str,
    legacy_package: str,
):
    module = _load_script(
        f"scripts/build_external_audit_report_{version}.py",
        f"pr120_external_report_{version}_gateway",
    )
    assert module.main(["--check"]) == 2
    assert not (REPO / legacy_package).exists()
    assert (REPO / "legacy/cf4_p0/packages/external_reports" / legacy_package).is_dir()


def test_historical_v7_v8_table_sources_and_outputs_keep_baseline_bytes():
    expected = {
        "legacy/cf4_p0/scripts/build_egs_results_table.py": (
            "d4ae7e850b49b3417e7d8df08bd3468318e7066e6798f31d12d5f451ff7b9582"
        ),
        "legacy/cf4_p0/scripts/build_egs_results_table_v8.py": (
            "770d1dec43604e6ea0487208c52b90b4255f1a92d90bdc8233723f5d340e87a5"
        ),
        "legacy/cf4_p0/tables/egs_results_table.json": (
            "628c0579db0ed5be8852f19996211d7b3c8fc770661003dd14cf4f8b92487e47"
        ),
        "legacy/cf4_p0/tables/egs_results_table.md": (
            "c10cecf14747401be87fd69850f0b1456054844248d266fb2159baf2e0ee24cf"
        ),
        "legacy/cf4_p0/tables/egs_results_table_v8.json": (
            "a50de53b7e314d3cef50e1db68b5d58e7a7d2205fbc83b2e1144361a8d88b5d7"
        ),
        "legacy/cf4_p0/tables/egs_results_table_v8.md": (
            "331041c97e0bf2096e7058fc45fe019e02c19e4f07b6ed78974b98cc0b91697c"
        ),
    }
    assert {
        path: hashlib.sha256((REPO / path).read_bytes()).hexdigest()
        for path in expected
    } == expected


def test_active_v8_payload_reader_consumes_the_hash_bound_frozen_json(monkeypatch):
    module = _load_script(
        "scripts/build_egs_results_table_v8.py", "pr120_v8_frozen_payload_reader"
    )
    monkeypatch.setattr(
        module,
        "_load_legacy_module",
        lambda: pytest.fail("active successor must not execute the legacy builder"),
    )
    expected = json.loads(
        (REPO / "legacy/cf4_p0/tables/egs_results_table_v8.json").read_text(
            encoding="utf-8"
        )
    )
    assert module._payload() == expected


@pytest.mark.parametrize(
    ("relative", "module_name"),
    [
        ("scripts/build_egs_results_table.py", "pr120_v7_import_no_legacy_exec"),
        ("scripts/build_egs_results_table_v8.py", "pr120_v8_import_no_legacy_exec"),
    ],
)
def test_table_gateway_import_never_reads_or_executes_legacy_python(
    relative: str,
    module_name: str,
    monkeypatch,
):
    original = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        try:
            candidate = path.resolve().relative_to(REPO.resolve()).as_posix()
        except ValueError:
            candidate = ""
        if candidate in {
            "legacy/cf4_p0/scripts/build_egs_results_table.py",
            "legacy/cf4_p0/scripts/build_egs_results_table_v8.py",
        }:
            pytest.fail(
                f"legacy Python read before an explicit reproduction gate: {candidate}"
            )
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    module = _load_script(relative, module_name)
    assert not hasattr(module, "_LEGACY")


def test_derived_legacy_figure_route_rechecks_every_triple_and_declares_png_absent(
    monkeypatch,
):
    module = _load_script(
        "scripts/cf4_p0_quarantine_derived.py", "pr120_derived_figure_wrapper"
    )
    calls: list[str] = []
    monkeypatch.setattr(
        module,
        "require_legacy_reproduction",
        lambda **kwargs: calls.append(str(kwargs["artifact_path"])),
    )
    monkeypatch.setattr(
        module,
        "_load_module",
        lambda *args, **kwargs: SimpleNamespace(main=lambda argv: 0),
    )
    monkeypatch.setattr(module, "quarantine_block_payload", lambda repo: {})
    spec = module.DATA_PROXY_SPEC
    assert module.figure_block_main(spec, ["--legacy-reproduction"]) == 0
    triple = [
        f"{spec.legacy_root}/{spec.stem}.png",
        f"{spec.legacy_root}/{spec.stem}.source.json",
        f"{spec.legacy_root}/{spec.stem}.manifest.json",
    ]
    pins = [spec.legacy_script, spec.legacy_input, *triple]
    assert calls == pins + pins
    payload = module._figure_block_payload(spec, kind="figure_manifest_block_record")
    assert payload["artifact"]["active_png_status"] == "ABSENT_BY_QUARANTINE"


def test_figure_legacy_runner_mutates_only_temp_copy_and_raises(monkeypatch):
    module = _load_script(
        "scripts/cf4_p0_quarantine_derived.py", "pr120_figure_temp_mutation"
    )
    spec = module.DATA_PROXY_SPEC
    legacy_root = REPO / spec.legacy_root
    canonical_paths = [
        legacy_root / f"{spec.stem}.png",
        legacy_root / f"{spec.stem}.source.json",
        legacy_root / f"{spec.stem}.manifest.json",
    ]
    before = {path: path.read_bytes() for path in canonical_paths}
    before_hashes = {
        path: hashlib.sha256(value).hexdigest() for path, value in before.items()
    }
    monkeypatch.setattr(module, "_verify_pinned_legacy", lambda paths: None)
    frozen = SimpleNamespace()

    def _mutate_temp(argv):
        (frozen.FIGURE_DIR / f"{spec.stem}.png").write_bytes(b"mutated disposable PNG")
        return 0

    frozen.main = _mutate_temp
    monkeypatch.setattr(module, "_load_module", lambda *args, **kwargs: frozen)
    with pytest.raises(RuntimeError, match="differs"):
        module.figure_block_main(spec, ["--legacy-reproduction"])
    for path in canonical_paths:
        after = path.read_bytes()
        assert after == before[path]
        assert hashlib.sha256(after).hexdigest() == before_hashes[path]
