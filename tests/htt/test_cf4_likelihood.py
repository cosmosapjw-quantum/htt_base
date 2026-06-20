from __future__ import annotations

import json

import numpy as np
import pytest


_COMMAND = "python -m pytest tests/htt/test_cf4_likelihood.py -q"
_WORKTREE = "test-worktree"


def _sha(char: str = "a") -> str:
    return "sha256:" + char * 64


def _velocity_manifest(tmp_path) -> str:
    manifest_path = tmp_path / "cf4_velocity_noise_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "variable_definition": "toy peculiar velocity fixture for schema tests",
                "redshift_frame": "CMB",
                "noise_model": "gaussian_exact",
                "covariance_status": "toy_diagonal_manifest",
                "calibration_status": "toy_fixture_calibration",
                "config_hash": _sha("1"),
                "input_hashes": [_sha("2")],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return str(manifest_path)


def _catalog(*, distance_variable_kind: str = "logdistance", gaussian_ref: str = ""):
    from obsstat.catalogs.cf4 import (
        Cf4CatalogMetadata,
        build_cf4_catalog_from_mapping,
    )

    payload = {
        "object_id": np.asarray(["cf4-1", "cf4-2", "cf4-3"]),
        "ra_deg": np.asarray([0.0, 90.0, 180.0]),
        "dec_deg": np.asarray([0.0, 0.0, 30.0]),
        "redshift": np.asarray([0.012, 0.021, 0.034]),
        "distance_variable": np.asarray([0.10, -0.04, 0.06]),
        "distance_uncertainty": np.asarray([0.05, 0.06, 0.07]),
        "group_id": np.asarray(["g1", "g2", "g3"]),
        "is_grouped": np.asarray([False, False, True]),
        "method_flag": np.asarray(["TF", "SNIa", "TF"]),
        "calibration_flag": np.asarray(["cal-a", "cal-b", "cal-a"]),
    }
    metadata = Cf4CatalogMetadata(
        release="toy_cf4_fixture",
        source_path="memory://toy-cf4.npz",
        checksum=_sha("b"),
        redshift_frame="CMB",
        distance_variable_kind=distance_variable_kind,
        calibration_status="toy_fixture_calibration",
        velocity_distribution_status=(
            "gaussian_exact" if gaussian_ref else "not_assumed_gaussian"
        ),
        gaussian_velocity_manifest_ref=gaussian_ref,
    )
    return build_cf4_catalog_from_mapping(payload, metadata=metadata)


def test_cf4_forward_likelihood_is_diagnostic_only() -> None:
    from htt.rest_frame.cf4_likelihood import evaluate_cf4_forward_likelihood

    catalog = _catalog()
    result = evaluate_cf4_forward_likelihood(
        catalog,
        baseline_distance_variable=np.asarray([0.08, -0.02, 0.04]),
        local_flow_basis=np.eye(3, 2),
        local_flow_coefficients=np.asarray([0.01, -0.02]),
        global_vector=np.asarray([0.01, 0.0, 0.0]),
        calibration_offset=0.0,
        config_hash=_sha("c"),
        input_hashes=(_sha("d"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = result.as_payload()

    assert payload["owner"] == "HTT"
    assert payload["implementation_scope"] == "htt"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["publication_ready"] is False
    assert payload["native_solver_result"] is False
    assert payload["log_likelihood"] == pytest.approx(result.log_likelihood)
    assert payload["ndof"] == 3
    assert "matched_nulls_not_bound" in payload["blocked_reasons"]
    assert "cf4_forward_catalog_not_production_bound" in payload["blocked_reasons"]
    assert "response_rank_not_full" in payload["blocked_reasons"]
    assert "local_global_overlap_not_externally_audited" in payload["blocked_reasons"]
    assert payload["score_semantics"] == "diagonal_diagnostic_gaussian_score"
    assert payload["noise_model"]["covariance_status"] == "diagonal_only_no_group_method_covariance"
    assert payload["response_rank_audit"]["rank_status"] == "rank_deficient"
    assert "diagnostic_toy_or_schema_only" in payload["status"]
    text = json.dumps(payload, sort_keys=True).lower()
    assert "mio certificate" not in text
    assert ("family " + "identified") not in text
    assert ("geometry " + "detected") not in text


def test_cf4_forward_likelihood_rejects_shape_mismatches() -> None:
    from htt.rest_frame.cf4_likelihood import evaluate_cf4_forward_likelihood

    with pytest.raises(ValueError, match="baseline_distance_variable"):
        evaluate_cf4_forward_likelihood(
            _catalog(),
            baseline_distance_variable=np.asarray([0.0, 0.0]),
            local_flow_basis=np.eye(3, 1),
            local_flow_coefficients=np.asarray([0.0]),
            global_vector=np.asarray([0.0, 0.0, 0.0]),
            calibration_offset=0.0,
            config_hash=_sha("c"),
            input_hashes=(_sha("d"),),
            generating_command=_COMMAND,
            worktree_state=_WORKTREE,
        )


def test_cf4_forward_likelihood_blocks_peculiar_velocity_gaussian_without_manifest() -> None:
    from htt.rest_frame.cf4_likelihood import evaluate_cf4_forward_likelihood

    with pytest.raises(ValueError, match="Gaussian velocity manifest"):
        evaluate_cf4_forward_likelihood(
            _catalog(distance_variable_kind="peculiar_velocity"),
            baseline_distance_variable=np.zeros(3),
            local_flow_basis=np.eye(3, 1),
            local_flow_coefficients=np.asarray([0.0]),
            global_vector=np.asarray([0.0, 0.0, 0.0]),
            calibration_offset=0.0,
            config_hash=_sha("c"),
            input_hashes=(_sha("d"),),
            generating_command=_COMMAND,
            worktree_state=_WORKTREE,
        )


def test_cf4_forward_likelihood_rejects_malformed_provenance_hashes() -> None:
    from htt.rest_frame.cf4_likelihood import evaluate_cf4_forward_likelihood

    with pytest.raises(ValueError, match="config_hash"):
        evaluate_cf4_forward_likelihood(
            _catalog(),
            baseline_distance_variable=np.zeros(3),
            local_flow_basis=np.eye(3, 1),
            local_flow_coefficients=np.asarray([0.0]),
            global_vector=np.asarray([0.0, 0.0, 0.0]),
            calibration_offset=0.0,
            config_hash="sha256:not-a-real-hash",
            input_hashes=(_sha("d"),),
            generating_command=_COMMAND,
            worktree_state=_WORKTREE,
        )

    with pytest.raises(ValueError, match="input_hashes"):
        evaluate_cf4_forward_likelihood(
            _catalog(),
            baseline_distance_variable=np.zeros(3),
            local_flow_basis=np.eye(3, 1),
            local_flow_coefficients=np.asarray([0.0]),
            global_vector=np.asarray([0.0, 0.0, 0.0]),
            calibration_offset=0.0,
            config_hash=_sha("c"),
            input_hashes=("",),
            generating_command=_COMMAND,
            worktree_state=_WORKTREE,
        )


def test_cf4_forward_likelihood_allows_manifested_velocity_gaussian_but_stays_blocked(tmp_path) -> None:
    from htt.rest_frame.cf4_likelihood import evaluate_cf4_forward_likelihood

    manifest_ref = _velocity_manifest(tmp_path)
    result = evaluate_cf4_forward_likelihood(
        _catalog(
            distance_variable_kind="peculiar_velocity",
            gaussian_ref=manifest_ref,
        ),
        baseline_distance_variable=np.zeros(3),
        local_flow_basis=np.eye(3, 1),
        local_flow_coefficients=np.asarray([0.0]),
        global_vector=np.asarray([0.0, 0.0, 0.0]),
        calibration_offset=0.0,
        config_hash=_sha("c"),
        input_hashes=(_sha("d"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )

    payload = result.as_payload()
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["publication_ready"] is False
    assert payload["velocity_gaussian_manifest_ref"] == manifest_ref
    assert payload["velocity_gaussian_manifest_hash"].startswith("sha256:")
