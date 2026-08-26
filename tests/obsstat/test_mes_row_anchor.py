"""PR-325 rowwise active geodesic MES-anchor tests."""
from __future__ import annotations

import importlib
import json
from dataclasses import replace
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import pytest

from common.statistical_foundations import (
    ScalarRange,
    StressStatus,
    evaluate_sector_stress,
)


REPO = Path(__file__).resolve().parents[2]


def _sut():
    try:
        return importlib.import_module("htt.obsstat.mes_row_anchor")
    except ModuleNotFoundError:
        pytest.fail("PR-325 rowwise MES-anchor operator is not implemented")


def _build(module, values=(100.0, 225.0), **overrides):
    arguments = {
        "row_id": "fixture-row",
        "feature_values": values,
        "feature_ids": ("cl_l2", "cl_l3"),
        "feature_units": ("microK_CMB^2", "microK_CMB^2"),
        "residual_dipole_attribution": (
            module.ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO
        ),
        "source_identity": "sha256:" + "1" * 64,
        "covariance_identity": "sha256:" + "2" * 64,
        "operator_identity": "sha256:" + "3" * 64,
    }
    arguments.update(overrides)
    return module.build_mes_row_anchor_state(**arguments)


def test_cl_row_uses_registered_units_and_active_geodesic_formula() -> None:
    """Catch treating C_l as D_l or using a legacy/non-geodesic triple."""

    module = _sut()
    state = module.build_mes_row_anchor_state(
        row_id="fixture-row",
        feature_values=(100.0, 225.0),
        feature_ids=("cl_l2", "cl_l3"),
        feature_units=("microK_CMB^2", "microK_CMB^2"),
        residual_dipole_attribution=(
            module.ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO
        ),
        source_identity="sha256:" + "1" * 64,
        covariance_identity="sha256:" + "2" * 64,
        operator_identity="sha256:" + "3" * 64,
    )

    # Hand-derived from eps_l=sqrt((2l+1) C_l/(4 pi))/T0, T0=2.72548e6 uK,
    # followed by the registered geodesic sigma/omega branches at eps1=0.
    assert dict(state.epsilon_l) == pytest.approx(
        {2: 2.314392806056328e-6, 3: 4.107639747018309e-6},
        rel=0.0,
        abs=1e-20,
    )
    assert state.anchor("sigma").value == pytest.approx(
        1.1362886070392013e-10, rel=0.0, abs=1e-24
    )
    assert state.anchor("omega").value == pytest.approx(
        1.4283770828600755e-13, rel=0.0, abs=1e-27
    )
    assert state.anchor("sigma").branch == "MES_G_SIGMA"
    assert state.anchor("omega").branch == "MES_G_OMEGA"


def test_row_state_is_content_bound_and_shared_identities_fail_closed() -> None:
    """Catch unbound rows or caller labels masquerading as content identity."""

    module = _sut()
    first = _build(module)
    changed = _build(module, values=(101.0, 225.0))

    assert re.fullmatch(r"sha256:[0-9a-f]{64}", first.row_content_identity)
    assert first.row_content_identity != changed.row_content_identity
    assert first.identity_role == "REPRODUCIBILITY_IDENTITY_NOT_AUTHORITY"
    assert first.source_identity == "sha256:" + "1" * 64
    assert first.covariance_identity == "sha256:" + "2" * 64

    with pytest.raises(module.MesRowAnchorError, match="source_identity"):
        _build(module, source_identity="caller-label-only")


def test_attribution_is_explicit_and_self_anchor_semantics_are_typed() -> None:
    """Catch a guessed dipole default or same-row transform sold as new data."""

    module = _sut()
    state = _build(module)

    assert state.methodology_role == "ROWWISE_SELF_ANCHOR_NONLINEAR_STATISTIC"
    assert state.shared_data_dependence is True
    assert state.independent_information_gain is False
    for name in ("sigma", "omega"):
        anchor = state.anchor(name)
        assert str(anchor.conditioning) == "REALIZATION_CONDITIONAL"
        assert dict(anchor.calibration_values)["eps1"] == 0.0
        assert "observer peculiar motion" in anchor.attribution

    with pytest.raises(module.MesRowAnchorError, match="BLOCKED_MES_ATTRIBUTION"):
        _build(module, residual_dipole_attribution=None)
    with pytest.raises(module.MesRowAnchorError, match="C_l units"):
        _build(module, feature_units=("dimensionless", "microK_CMB^2"))
    with pytest.raises(module.MesRowAnchorError, match="finite non-negative"):
        _build(module, values=(float("nan"), 225.0))


def test_pool_is_row_permutation_and_observation_swap_equivariant() -> None:
    """Catch observation-only branches, row-order state, or pooled leakage."""

    module = _sut()
    common = {
        "feature_ids": ("cl_l2", "cl_l3"),
        "feature_units": ("microK_CMB^2", "microK_CMB^2"),
        "residual_dipole_attribution": (
            module.ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO
        ),
        "source_identity": "sha256:" + "1" * 64,
        "covariance_identity": "sha256:" + "2" * 64,
        "operator_identity": "sha256:" + "3" * 64,
    }
    row_by_id = {
        "observation": (100.0, 225.0),
        "null-1": (400.0, 900.0),
        "null-2": (64.0, 144.0),
    }

    def run(order, rows=row_by_id):
        return module.build_mes_row_anchor_pool(
            row_ids=order,
            feature_matrix=tuple(rows[row_id] for row_id in order),
            **common,
        )

    baseline = {state.row_id: state for state in run(tuple(row_by_id))}
    permuted = {
        state.row_id: state
        for state in run(("null-2", "observation", "null-1"))
    }
    observation_swapped = {
        state.row_id: state
        for state in run(("null-1", "observation", "null-2"))
    }
    assert permuted == baseline
    assert observation_swapped == baseline

    changed_other = dict(row_by_id)
    changed_other["null-2"] = (81.0, 169.0)
    changed_pool = {
        state.row_id: state
        for state in run(tuple(row_by_id), rows=changed_other)
    }
    assert changed_pool["observation"] == baseline["observation"]
    assert changed_pool["null-2"] != baseline["null-2"]


def test_exact_pr324_pool_yields_301_serializable_typed_states() -> None:
    """Catch partial-row execution, shared-identity drift, or an untyped export."""

    module = _sut()
    package = REPO / "docs/generated/pr315_planck_smica_feature_replay.npz"
    metadata = json.loads(
        (REPO / "docs/generated/pr315_planck_smica_feature_replay.json").read_text(
            encoding="utf-8"
        )
    )
    with np.load(package, allow_pickle=False) as bundle:
        observed = np.asarray(bundle["observed_features"], dtype=float)
        nulls = np.asarray(bundle["null_features"], dtype=float)
        row_ids = tuple(str(value) for value in bundle["row_ids"].tolist())
        feature_ids = tuple(str(value) for value in bundle["feature_ids"].tolist())
        feature_units = tuple(
            str(value) for value in bundle["feature_units"].tolist()
        )
        covariance = np.asarray(bundle["covariance"], dtype=float)

    states = module.build_mes_row_anchor_pool(
        row_ids=("PLANCK-PR3-SMICA-OBSERVED", *row_ids),
        feature_matrix=np.vstack((observed, nulls)),
        feature_ids=feature_ids,
        feature_units=feature_units,
        residual_dipole_attribution=(
            module.ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO
        ),
        source_identity=metadata["package_sha256"],
        covariance_identity=module.numeric_array_content_identity(
            covariance, role="PR315_EXACT_300_NULL_COVARIANCE"
        ),
        operator_identity=metadata["operator_identity_sha256"],
    )
    payload = module.mes_row_anchor_pool_payload(states)

    assert len(states) == 301
    assert payload["row_count"] == 301
    assert len(payload["row_anchor_states"]) == 301
    assert payload["shared_source_identity"] == metadata["package_sha256"]
    assert payload["row_operator_scope"] == "ONE_PURE_OPERATOR_ALL_301_ROWS"
    assert payload["independent_information_gain"] is False
    assert states[0].anchor("sigma").value == pytest.approx(
        2.400087022175844e-10, rel=0.0, abs=1e-24
    )
    assert states[0].anchor("omega").value == pytest.approx(
        3.0061887930898035e-13, rel=0.0, abs=1e-27
    )

    # A same-row denominator remains ratio-unidentified even against a
    # channel-matched hypothetical numerator; it is never a defined stress.
    sigma = states[0].anchor("sigma")
    stress = evaluate_sector_stress(
        sector="Sigma2",
        numerator=ScalarRange(0.0, sigma.value),
        numerator_channel_key=sigma.channel_key,
        anchor=sigma,
    )
    assert stress.status is StressStatus.RATIO_UNIDENTIFIED


def test_duplicate_channels_and_forged_claim_semantics_are_refused() -> None:
    """Catch ambiguous C_l selection and caller-forged authority metadata."""

    module = _sut()
    with pytest.raises(module.MesRowAnchorError, match="duplicate feature_ids"):
        _build(
            module,
            feature_values=(100.0, 101.0, 225.0),
            feature_ids=("cl_l2", "cl_l2", "cl_l3"),
            feature_units=(
                "microK_CMB^2",
                "microK_CMB^2",
                "microK_CMB^2",
            ),
        )

    state = _build(module)
    with pytest.raises(module.MesRowAnchorError, match="factory"):
        replace(
            state,
            methodology_role="POSTERIOR_EVIDENCE",
            shared_data_dependence=False,
            independent_information_gain=True,
        )


def test_portable_runner_requires_attribution_and_emits_equivariance_receipt(
    tmp_path: Path,
) -> None:
    """Catch silent attribution defaults or a partial/asymmetric pool export."""

    runner = importlib.import_module(
        "scripts.observed_runs.run_planck_mes_morphology"
    )
    package = REPO / "docs/generated/pr315_planck_smica_feature_replay.npz"
    metadata = REPO / "docs/generated/pr315_planck_smica_feature_replay.json"

    with pytest.raises(runner.MesRowAnchorError, match="BLOCKED_MES_ATTRIBUTION"):
        runner.run_planck_mes_row_anchors(
            feature_package_path=package,
            feature_metadata_path=metadata,
            output_path=tmp_path / "must-not-exist.json",
            residual_dipole_attribution=None,
        )
    assert not (tmp_path / "must-not-exist.json").exists()

    output = tmp_path / "pr325-row-anchors.json"
    result = runner.run_planck_mes_row_anchors(
        feature_package_path=package,
        feature_metadata_path=metadata,
        output_path=output,
        residual_dipole_attribution=(
            runner.ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO
        ),
    )
    written = json.loads(output.read_text(encoding="utf-8"))

    assert written == result
    assert written["row_count"] == 301
    assert written["source_feature_package_identity"] == (
        "sha256:b262425eb4f3a879513c02644bcbdd3ab313e487d101f6a29cb85284c30f845b"
    )
    assert written["equivariance_receipt"] == {
        "observation_swap": "PASS",
        "row_permutation": "PASS",
    }
    assert written["generic_control_preserved"] is True
    assert written["MES_anchor_state"] is True
    assert written["MES_observed_result"] is False
    assert written["global_claim_boundary"] == "ABSTAIN_GLOBAL_RESPONSE_UNAVAILABLE"
    source_metadata = json.loads(metadata.read_text(encoding="utf-8"))
    for field_name in (
        "transfer_source",
        "sky_support_status",
        "covariance_status",
        "null_mock_status",
        "caveats",
    ):
        assert written[field_name] == source_metadata[field_name]
    assert "preregistered observational-coordinate construction input" in written[
        "allowed_use"
    ]
    assert "calibrated observational coordinate construction" not in written[
        "allowed_use"
    ]


def test_runner_cli_executes_from_repository_root(tmp_path: Path) -> None:
    """Catch a script-path bootstrap that works only when imported in pytest."""

    output = tmp_path / "cli-row-anchors.json"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        str(REPO / path) for path in ("htt", "htt/src", "htt/htt")
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/observed_runs/run_planck_mes_morphology.py",
            "--feature-package",
            "docs/generated/pr315_planck_smica_feature_replay.npz",
            "--feature-metadata",
            "docs/generated/pr315_planck_smica_feature_replay.json",
            "--output",
            str(output),
            "--residual-dipole-attribution",
            "SAG_OBSERVER_MOTION_EPS1_ZERO",
        ],
        cwd=REPO,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(output.read_text(encoding="utf-8"))["row_count"] == 301
