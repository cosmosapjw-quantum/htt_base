"""PR-144 contract tests: authenticated CF4 row/group/selection manifest."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from common.cf4_manifest import (
    CF4_RELEASE,
    TABLE3_COLUMNS,
    TABLE4_COLUMNS,
    Cf4ManifestError,
    ColumnType,
    column_authority,
    file_sha256,
    generate_caption,
    id_parity,
    lint_caption,
    range_fixtures,
    read_lines,
    refuse_audit_value_as_observed,
    refuse_reconstruction_as_true_flow,
    require_cz_units_for_cartesian,
    require_registered_column,
    selection_completeness,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
T3 = REPO_ROOT / "workdir/raw/cf4_full/table3.dat"
T4 = REPO_ROOT / "workdir/raw/cf4_full/table4.dat"
_DATA = T3.is_file() and T4.is_file()
needs_data = pytest.mark.skipif(not _DATA, reason="CF4 raw tables absent")


def _load_runner():
    runner_path = REPO_ROOT / "scripts/codex_harness/run_pr144_cf4_manifest.py"
    spec = importlib.util.spec_from_file_location("run_pr144", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_source_hash_is_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH
    manifest_rel = runner.OUTPUTS["manifest"]
    stored = {
        "status": "authenticated",
        "negative_scan": {
            "targets": {source: {"sha256": "1" * 64, "hits": []}},
        },
    }
    current = {
        "status": "authenticated",
        "negative_scan": {
            "targets": {source: {"sha256": "2" * 64, "hits": []}},
        },
    }
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) == runner._semantic_artifact(manifest_rel, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) != runner._semantic_artifact(manifest_rel, current)
    current["negative_scan"]["targets"][source] = {
        "sha256": "not-a-sha",
        "hits": [],
    }
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) != runner._semantic_artifact(manifest_rel, current)

    artifact_rel = runner.OUTPUTS["artifact_manifest"]
    stored = {
        "input_hashes": [f"{source}:{'1' * 64}"],
        "raw_data_pins": {"table3_sha256": "a"},
    }
    current = {
        "input_hashes": [f"{source}:{'2' * 64}"],
        "raw_data_pins": {"table3_sha256": "a"},
    }
    assert runner._semantic_artifact(
        artifact_rel, stored
    ) == runner._semantic_artifact(artifact_rel, current)
    current["raw_data_pins"]["table3_sha256"] = "changed"
    assert runner._semantic_artifact(
        artifact_rel, stored
    ) != runner._semantic_artifact(artifact_rel, current)


def test_column_authority_types_are_complete() -> None:
    auth3 = column_authority(TABLE3_COLUMNS)
    auth4 = column_authority(TABLE4_COLUMNS)
    # the registry is COMPLETE vs the ReadMe enumeration (30 table3, 22 table4)
    assert len(auth3) == 30
    assert len(auth4) == 22
    # every column carries a byte range, units, and a type
    for auth in (auth3, auth4):
        for meta in auth.values():
            assert meta["byte_end"] >= meta["byte_start"]
            assert meta["type"] in {t.value for t in ColumnType}
    # the peculiar-velocity columns are typed as reconstructions
    for col in ("Vpds", "Vpwf", "Vpec"):
        assert auth4[col]["type"] == ColumnType.RECONSTRUCTION.value
    # Vh is an observable; V3k is frame-derived
    assert auth4["Vh"]["type"] == ColumnType.VELOCITY_OBSERVABLE.value
    assert auth4["V3k"]["type"] == ColumnType.FRAME_DERIVED.value
    # uncertainty columns are typed UNCERTAINTY, never DISTANCE_INDICATOR
    assert auth4["e_DMzp"]["type"] == ColumnType.UNCERTAINTY.value
    for col in ("e_DMsnIa", "e_DMfp", "e_DMtf", "e_DMsbfo", "e_DMsbfi",
                "e_DMsnII", "e_DMav"):
        assert auth3[col]["type"] == ColumnType.UNCERTAINTY.value


def test_guards() -> None:
    for col in ("Vpds", "Vpwf", "Vpec"):
        with pytest.raises(Cf4ManifestError, match="RECONSTRUCTION"):
            refuse_reconstruction_as_true_flow(col)
    refuse_reconstruction_as_true_flow("Vh")   # an observable is fine
    with pytest.raises(Cf4ManifestError, match="audit-only"):
        refuse_audit_value_as_observed(94)
    refuse_audit_value_as_observed(405)   # a real value is not the audit value
    with pytest.raises(Cf4ManifestError, match="not in the CF4 authority"):
        require_registered_column("Vflow_true", TABLE4_COLUMNS)
    require_registered_column("Vpec", TABLE4_COLUMNS)   # registered is fine
    with pytest.raises(Cf4ManifestError, match="cz"):
        require_cz_units_for_cartesian("SGX", "mpc_length")
    from common.cf4_manifest import refuse_cf4_p0_resolution_claim
    with pytest.raises(Cf4ManifestError, match="stay OPEN"):
        refuse_cf4_p0_resolution_claim("cf4_p0_resolved")
    refuse_cf4_p0_resolution_claim("data_lineage")   # provenance scope is fine


def test_id_parity_rejects_duplicate_group_ids() -> None:
    duplicated = ["      1", "      1"]
    with pytest.raises(Cf4ManifestError, match="duplicate 1PGC"):
        id_parity(duplicated, duplicated)


@pytest.mark.parametrize("line", ["       ", "      0", "     -1"])
def test_id_parity_rejects_missing_or_nonpositive_group_ids(line: str) -> None:
    with pytest.raises(Cf4ManifestError, match="present positive integers"):
        id_parity([line], [line])


def test_caption_gate() -> None:
    text = generate_caption(38053, 46)
    lint_caption(text)
    for bad in (" vpec is the " + "true flow.",
                " the cf4 p0 " + "resolved.",
                " sgx is a " + "mpc length."):
        with pytest.raises(Cf4ManifestError, match="forbidden"):
            lint_caption(text + bad)


def test_range_fixtures_flag_nonpositive_and_nonfinite_distance() -> None:
    def line_with_distance(raw: str) -> str:
        chars = [" "] * 157
        chars[21:26] = list(f"{raw:>5}")
        return "".join(chars)

    zero = range_fixtures(
        [line_with_distance("0.0")], {"Dist": [0.0, 1000.0]},
    )
    assert zero["Dist"]["n_out_of_range"] == 1
    nonfinite = range_fixtures(
        [line_with_distance("nan")], {"Dist": [0.0, 1000.0]},
    )
    assert nonfinite["Dist"]["n_out_of_range"] == 1
    assert nonfinite["Dist"]["observed_min"] is None
    assert nonfinite["Dist"]["observed_max"] is None


@needs_data
def test_parse_parity_and_completeness() -> None:
    t3, t4 = read_lines(T3), read_lines(T4)
    assert len(t3) == CF4_RELEASE["n_groups"]
    assert len(t4) == CF4_RELEASE["n_groups"]
    parity = id_parity(t3, t4)
    assert parity["parity"] is True
    assert parity["n_unique"] == CF4_RELEASE["n_groups"]
    assert parity["duplicates_table3"] == 0
    # the Fundamental Plane is the dominant methodology (CF4 paper)
    comp = selection_completeness(t3)
    assert comp["o_DMfp"]["n_groups_with_method"] > \
        comp["o_DMtf"]["n_groups_with_method"] > 0


@needs_data
def test_parity_breaks_on_mismatch() -> None:
    t3, t4 = read_lines(T3), read_lines(T4)
    with pytest.raises(Cf4ManifestError, match="do not match"):
        id_parity(t3, t4[:-1])   # drop one group -> parity fails


@needs_data
def test_range_fixtures_within_readme_bounds() -> None:
    t4 = read_lines(T4)
    fx = range_fixtures(t4, {"RAdeg": [0.0, 360.0], "DEdeg": [-90.0, 90.0],
                             "GLAT": [-90.0, 90.0]})
    assert all(v["n_out_of_range"] == 0 for v in fx.values())


@needs_data
def test_file_sha_deterministic() -> None:
    assert file_sha256(T4) == file_sha256(T4)


@needs_data
def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr144_cf4_manifest.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@needs_data
def test_artifacts_and_mutations() -> None:
    man = json.loads((REPO_ROOT / "docs/generated/pr144_cf4_manifest.json")
                     .read_text(encoding="utf-8"))
    assert man["status"] == "authenticated"
    assert man["id_parity"]["n_unique"] == CF4_RELEASE["n_groups"]
    assert man["tables"]["table3"]["file_sha256"]
    auth = json.loads((REPO_ROOT / "docs/generated/pr144_column_authority.json")
                      .read_text(encoding="utf-8"))
    assert auth["table4"]["Vpec"]["type"] == "reconstruction"
    comp = json.loads(
        (REPO_ROOT / "docs/generated/pr144_selection_completeness.json")
        .read_text(encoding="utf-8"))
    assert comp["per_method_group_counts"]["o_DMfp"]["n_groups_with_method"] > 0
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr144_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 7
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr144_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["raw_data_pins"]["table4_sha256"]
