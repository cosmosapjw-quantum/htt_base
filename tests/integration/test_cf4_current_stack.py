"""PR-307 end-to-end observation-free CF4 profile contract."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "scripts/observed_runs/run_cf4_current_stack.py"


def _load_worker():
    spec = importlib.util.spec_from_file_location("pr307_cf4_worker", WORKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _independent_affine_case(*, no_flow: bool):
    worker = _load_worker()
    rng = np.random.default_rng(312)
    rows = 96
    directions = rng.normal(size=(rows, 3))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    distance = np.linspace(24.0, 180.0, rows)
    h0 = 70.0
    if no_flow:
        trace_over_three = 0.35
        bulk = np.zeros(3)
        shear = np.zeros((3, 3))
    else:
        trace_over_three = 0.35
        bulk = np.asarray((24.0, -13.0, 7.0))
        shear = np.asarray(
            (
                (0.08, 0.03, -0.02),
                (0.03, -0.05, 0.01),
                (-0.02, 0.01, -0.03),
            )
        )
    gradient = trace_over_three * np.eye(3) + shear
    peculiar = directions @ bulk + distance * np.einsum(
        "ni,ij,nj->n", directions, gradient, directions
    )
    sigma = np.linspace(85.0, 125.0, rows)
    covariance = 0.025 * np.outer(sigma, sigma)
    covariance.flat[:: rows + 1] = np.square(sigma)
    ids = np.arange(312000, 312000 + rows, dtype=np.int64)
    inputs = worker.Cf4OperatorInputs(
        group_ids=ids,
        galactic_longitude_deg=(
            np.degrees(np.arctan2(directions[:, 1], directions[:, 0])) % 360.0
        ),
        galactic_latitude_deg=np.degrees(np.arcsin(directions[:, 2])),
        distance_mpc=distance,
        cmb_velocity_km_s=h0 * distance + peculiar,
        covariance_km2_s2=covariance,
        covariance_group_ids=ids.copy(),
        selected_group_ids=ids.copy(),
    )
    config = worker.Cf4OperatorConfig(
        depth_thresholds_mpc=(180.0,),
        zoa_half_widths_deg=(0.0,),
        nuisance_profiles=(
            worker.Cf4NuisanceProfile("independent", h0, 1.0, 1.0),
        ),
    )
    truth = np.asarray(
        (
            trace_over_three,
            *bulk,
            shear[0, 0],
            shear[1, 1],
            shear[0, 1],
            shear[0, 2],
            shear[1, 2],
        )
    )
    return worker, inputs, config, truth


def test_pr312_recovers_independent_affine_trace_without_flow_leakage() -> None:
    worker, inputs, config, truth = _independent_affine_case(no_flow=False)

    result = worker.analyze_cf4_current_stack(inputs, config)
    profile = result["cells"][0]["profiles"][0]

    assert np.allclose(profile["coefficients"], truth, atol=1.0e-10)
    assert (
        result["operator_contract"]["coefficient_names"][0]
        == "isotropic_trace_over_3_km_s_mpc"
    )
    assert result["operator_contract"]["coefficient_units"][0] == "km s-1 Mpc-1"
    assert (
        result["terminal_disposition"]
        == "NO_FLOW_CALIBRATION_UNAVAILABLE_ABSTAIN"
    )


def test_pr312_exact_no_flow_member_forces_typed_abstention() -> None:
    worker, inputs, config, _ = _independent_affine_case(no_flow=True)

    result = worker.analyze_cf4_current_stack(inputs, config)
    identified_set = result["cells"][0]["identified_set"]

    assert np.max(np.abs(identified_set["joint_flow_members"])) < 1.0e-10
    assert result["cells"][0]["profiles"][0]["no_flow_member"] is True
    assert (
        identified_set["no_flow_calibration_status"]
        == "EXACT_NO_FLOW_MEMBER_ABSTAIN"
    )
    assert result["terminal_disposition"] == "EXACT_NO_FLOW_MEMBER_ABSTAIN"


@pytest.mark.parametrize("rows", ("1", "8", "32", "128", "full"))
def test_pr307_synthetic_profile_is_observation_free(
    tmp_path: Path, rows: str
) -> None:
    output = tmp_path / f"profile-{rows}.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(WORKER),
            "--synthetic-profile",
            "--rows",
            rows,
            "--mode",
            "serial",
            "--workers",
            "1",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
        env={
            "HOME": "/nonexistent",
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": ":".join(
                (
                    str(ROOT / "htt/src"),
                    str(ROOT / "htt"),
                    str(Path(np.__file__).resolve().parent.parent),
                )
            ),
        },
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="ascii"))
    assert payload["row_label"] == rows
    assert payload["observed_statistic_seen"] is False
    assert payload["observed_science_executed"] is False
    assert payload["terminal_dispositions"] == [
        "NO_FLOW_CALIBRATION_UNAVAILABLE_ABSTAIN"
    ]


def test_pr307_synthetic_profile_rejects_admission_and_data_root(
    tmp_path: Path,
) -> None:
    worker = _load_worker()
    output = tmp_path / "forbidden.json"
    assert (
        worker.main(
            [
                "--synthetic-profile",
                "--rows",
                "1",
                "--admission",
                str(tmp_path / "admission.json"),
                "--data-root",
                str(tmp_path),
                "--output",
                str(output),
            ]
        )
        == 2
    )
    assert not output.exists()


def test_pr307_covariance_abstention_preserves_diagnostic_shape() -> None:
    worker = _load_worker()
    inputs, baseline = worker._synthetic_inputs(307999)
    profile = worker.Cf4NuisanceProfile("underflow", 75.0, 1.0, 1.0e-300)
    config = worker.Cf4OperatorConfig(
        depth_thresholds_mpc=baseline.depth_thresholds_mpc,
        zoa_half_widths_deg=baseline.zoa_half_widths_deg,
        nuisance_profiles=(profile,),
    )

    result = worker.analyze_cf4_current_stack(inputs, config)
    record = result["cells"][0]["profiles"][0]

    assert record["disposition"] == "COVARIANCE_INVALID_ABSTAIN"
    assert record["diagnostics"] == {
        "affine_rank": 0,
        "affine_columns": 9,
        "projected_flow_rank": 0,
        "projected_flow_columns": 8,
    }


def test_pr307_rank_abstention_is_strict_json_serializable(tmp_path: Path) -> None:
    worker = _load_worker()
    inputs, config = worker._synthetic_inputs(307998)
    collinear = worker.Cf4OperatorInputs(
        **{
            **inputs.__dict__,
            "galactic_longitude_deg": np.zeros(len(inputs.group_ids)),
            "galactic_latitude_deg": np.zeros(len(inputs.group_ids)),
        }
    )
    result = worker.analyze_cf4_current_stack(collinear, config)
    output = tmp_path / "rank-abstention.json"

    worker._write_json(output, result)

    restored = json.loads(output.read_text(encoding="ascii"))
    assert restored["terminal_disposition"] == "RANK_DEFICIENT_ABSTAIN"
    for cell in restored["cells"]:
        for profile in cell["profiles"]:
            assert profile["coefficients"] is None
            assert profile["diagnostics"][
                "affine_standardized_condition_number"
            ] is None


@pytest.mark.parametrize(
    ("platform", "expected"),
    (("linux", 126_976), ("darwin", 124)),
)
def test_pr307_max_rss_normalizes_platform_units(
    monkeypatch: pytest.MonkeyPatch, platform: str, expected: int
) -> None:
    worker = _load_worker()
    monkeypatch.setattr(worker.sys, "platform", platform)
    monkeypatch.setattr(
        worker.resource,
        "getrusage",
        lambda _kind: SimpleNamespace(ru_maxrss=124),
    )

    assert worker._max_rss_bytes() == expected
