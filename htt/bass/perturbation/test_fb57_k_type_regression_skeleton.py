from __future__ import annotations

import numpy as np
import pytest

from bass.perturbation.k_type_regression import run_k_type_regression_matrix


_TYPE_LABELS = (
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI_0",
    "VI_h",
    "VII_0",
    "VII_h",
    "VIII",
    "IX",
)
_K_VALUES = (0.0, 1.0e-3, 1.0e-2, 1.0e-1)


@pytest.fixture(scope="module")
def regression_matrix():
    return run_k_type_regression_matrix(
        type_labels=_TYPE_LABELS,
        k_values=_K_VALUES,
        ell_max=10,
    )


def _lookup_case(result: dict[str, object], type_label: str, k_value: float) -> dict[str, object]:
    for case in result["cases"]:
        if case["type_label"] == type_label and case["k_comoving"] == k_value:
            return case
    raise AssertionError(f"Missing case for ({type_label}, {k_value})")


@pytest.mark.parametrize("type_label", _TYPE_LABELS)
@pytest.mark.parametrize("k_value", _K_VALUES)
def test_fb57_runner_emits_complete_case_surface(
    regression_matrix,
    type_label: str,
    k_value: float,
) -> None:
    case = _lookup_case(regression_matrix, type_label, k_value)
    ell = np.asarray(case["ell"])
    model = np.asarray(case["D_TT_model"])
    reference = np.asarray(case["D_TT_reference"])
    seed_observables = case["seed_observables"]

    assert case["within_5pct"] is True
    assert case["mode_family"]
    assert case["spectrum_kind"] in {"continuous", "discrete"}
    assert ell.shape == model.shape == reference.shape
    assert ell[0] == 2
    assert np.all(np.isfinite(model))
    assert np.all(np.isfinite(reference))
    assert np.isfinite(float(case["laplacian_eigenvalue"]))
    assert np.isfinite(float(case["proxy_scale"]))
    assert np.isfinite(float(case["max_abs_rel_err"]))
    assert all(np.isfinite(float(v)) for v in seed_observables.values())
    if type_label == "IX":
        assert case["spectrum_kind"] == "discrete"
        assert case["discrete_ell"] is not None
    else:
        assert case["discrete_ell"] is None


def test_fb57_runner_reports_complete_matrix_and_fixture_path(regression_matrix) -> None:
    assert regression_matrix["type_labels"] == _TYPE_LABELS
    assert regression_matrix["k_values"] == _K_VALUES
    assert regression_matrix["ell_max"] == 10
    assert regression_matrix["all_within_5pct"] is True
    assert len(regression_matrix["cases"]) == len(_TYPE_LABELS) * len(_K_VALUES)
    assert str(regression_matrix["reference_path"]).endswith("data/camb_ref_planck2018.npz")


@pytest.mark.parametrize(
    ("kwargs", "match"),
    (
        ({"type_labels": (), "k_values": _K_VALUES, "ell_max": 10}, "type_labels"),
        ({"type_labels": _TYPE_LABELS, "k_values": (), "ell_max": 10}, "k_values"),
        ({"type_labels": _TYPE_LABELS, "k_values": _K_VALUES, "ell_max": 1}, "ell_max"),
    ),
)
def test_fb57_invalid_runner_inputs_raise(
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        run_k_type_regression_matrix(**kwargs)
