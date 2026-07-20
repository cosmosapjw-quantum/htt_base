from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from obsstat.catalogs.cf4_raw import (
    CF4_PR179_DENYLIST,
    CF4_PR179_PRIMARY_COLUMNS,
    Cf4RawInputError,
    load_authenticated_cf4_raw_groups,
    require_pr179_columns,
    require_pr179_value_access,
)
from obsstat.directional_cosmography import (
    DirectionalCosmographyConfig,
    assign_group_folds,
    prepare_directional_catalogue,
)
import obsstat.directional_cosmography as directional_module


REPO = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((REPO / "docs/generated/pr144_cf4_manifest.json").read_text())


def _catalogue():
    return load_authenticated_cf4_raw_groups(
        REPO / MANIFEST["tables"]["table3"]["path"],
        REPO / MANIFEST["tables"]["table4"]["path"],
        expected_table3_sha256=MANIFEST["tables"]["table3"]["file_sha256"],
        expected_table4_sha256=MANIFEST["tables"]["table4"]["file_sha256"],
        expected_rows=38053,
    )


def test_authenticated_raw_group_join_and_domain_are_deterministic() -> None:
    catalog = _catalogue()
    assert catalog.row_count == 38053
    assert len(np.unique(catalog.group_id)) == 38053
    assert np.all(np.diff(catalog.group_id) > 0)
    assert catalog.source_hashes == {
        "table3": "c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d",
        "table4": "b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94",
    }
    prepared = prepare_directional_catalogue(catalog, DirectionalCosmographyConfig(null_draws=3))
    assert prepared.support_report["null_support_certifiable"] is True
    assert prepared.support_report["supported_fraction"] > 0.98
    assert prepared.n == 35549
    assert sum(np.count_nonzero(prepared.fold == fold) for fold in range(5)) == prepared.n
    assert set(prepared.null_method_family) == {"FP", "TF", "OTHER"}
    assert catalog.accessed_columns == {
        "table3": tuple(sorted(CF4_PR179_PRIMARY_COLUMNS["table3"] + (
            "o_DMcal", "o_DMsnIa", "o_DMfp", "o_DMtf", "o_DMsbfo",
            "o_DMsbfi", "DMcal", "DMsnIa", "e_DMsnIa", "DMfp", "e_DMfp",
            "DMtf", "e_DMtf", "DMsbfo", "e_DMsbfo", "DMsbfi", "e_DMsbfi",
            "DMsnII", "e_DMsnII",
        ))),
        "table4": tuple(sorted(CF4_PR179_PRIMARY_COLUMNS["table4"])),
    }
    unsupported = prepared.support_report["unsupported_strata"]
    assert len(unsupported) > 0
    assert all(set(row) == {
        "fold", "nside1_pixel", "broad_method_family", "depth_bin",
        "group_count", "group_id_sha256",
    } for row in unsupported)
    assert prepared.support_report["unsupported_strata_sha256"] == (
        directional_module.canonical_json_sha256(unsupported)
    )


def test_reported_error_nuisance_is_not_total_weight_sigma() -> None:
    prepared = prepare_directional_catalogue(
        _catalogue(), DirectionalCosmographyConfig(null_draws=3)
    )
    all_rows = np.arange(prepared.n)
    train = all_rows[prepared.fold != 0]
    design, names = directional_module._base_design(prepared, train, all_rows)
    column = design[:, names.index("centered_log_e_DMzp")]
    raw_log = np.log(prepared.e_dmzp)
    expected = (raw_log - np.mean(raw_log[train])) / np.std(raw_log[train])
    np.testing.assert_allclose(column, expected, rtol=0.0, atol=1e-14)
    total_log = np.log(prepared.sigma)
    wrong = (total_log - np.mean(total_log[train])) / np.std(total_log[train])
    assert not np.allclose(column, wrong)


@pytest.mark.parametrize("column", CF4_PR179_DENYLIST)
def test_every_forbidden_value_column_is_rejected(column: str) -> None:
    mutated = {key: list(value) for key, value in CF4_PR179_PRIMARY_COLUMNS.items()}
    mutated["table4"].append(column)
    with pytest.raises(Cf4RawInputError, match="forbidden"):
        require_pr179_columns(mutated)


def test_unknown_or_missing_primary_column_fails_closed() -> None:
    unknown = {key: list(value) for key, value in CF4_PR179_PRIMARY_COLUMNS.items()}
    unknown["table3"].append("invented")
    with pytest.raises(Cf4RawInputError, match="allowlist drift"):
        require_pr179_columns(unknown)
    missing = {key: list(value) for key, value in CF4_PR179_PRIMARY_COLUMNS.items()}
    missing["table4"].remove("DMzp")
    with pytest.raises(Cf4RawInputError, match="allowlist drift"):
        require_pr179_columns(missing)


def test_runtime_value_access_capability_rejects_denied_and_unknown_columns() -> None:
    for column in CF4_PR179_DENYLIST:
        with pytest.raises(Cf4RawInputError, match="forbidden PR-179 value access"):
            require_pr179_value_access("table4", column)
    with pytest.raises(Cf4RawInputError, match="unregistered PR-179 value access"):
        require_pr179_value_access("table3", "invented")


def test_fold_assignment_never_splits_cluster_and_is_repeatable() -> None:
    pixel = np.asarray([0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 4])
    method = np.asarray(["FP", "FP", "TF", "TF", "TF", "SN", "SN",
                         "FP", "FP", "SBF", "SBF", "SBF"])
    first = assign_group_folds(pixel, method)
    second = assign_group_folds(pixel, method)
    np.testing.assert_array_equal(first, second)
    for key in set(zip(pixel.tolist(), method.tolist())):
        mask = (pixel == key[0]) & (method == key[1])
        assert len(set(first[mask].tolist())) == 1


def test_h_response_gate_is_separate_from_q_and_deletions_are_exhaustive() -> None:
    config = DirectionalCosmographyConfig(null_draws=3)
    prepared = prepare_directional_catalogue(_catalogue(), config)
    models = directional_module._build_fold_models(prepared)
    response = directional_module._response_identifiability(prepared, models, config)
    assert response["analysis_branch"] == "H_ONLY"
    assert response["h_pass_all_folds"] is True
    assert response["q_pass_all_folds"] is False
    assert all(fold["h_condition_number"] < 2.0 for fold in response["folds"])
    assert all(fold["q_conditional_condition_number"] > 4.0 for fold in response["folds"])
    assert all(
        fold["q_directional_cubic_canonical_correlation"] > 0.95
        for fold in response["folds"]
    )
    _, _, cases, failures, expected, _ = directional_module._deletion_operators(
        prepared, "H_ONLY", config
    )
    assert expected == 20
    assert len(cases) == expected
    assert failures == []


def test_deletion_fit_failure_is_counted_and_cannot_green_stability(monkeypatch) -> None:
    config = DirectionalCosmographyConfig(null_draws=3, null_batch_size=3)
    original = directional_module._deletion_response_receipt
    calls = 0

    def fail_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise directional_module.DirectionalCosmographyError("injected rank failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(directional_module, "_deletion_response_receipt", fail_once)
    analysis = directional_module.analyze_directional_cosmography(_catalogue(), config)
    stability = analysis["matched_null"]["stability"]
    assert stability["expected_cases"] == 20
    assert stability["evaluated_cases"] == 19
    assert stability["failed_cases"] == 1
    assert stability["pass"] is False
    assert analysis["result"]["supporting_h_only_matched_null_disposition"] == (
        "NON_INFORMATIVE_SELECTION_SYSTEMATICS_DOMINATED"
    )
