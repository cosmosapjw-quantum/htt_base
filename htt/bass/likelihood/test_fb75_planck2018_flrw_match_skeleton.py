from __future__ import annotations

from pathlib import Path

import pytest

from bass.likelihood.planck2018_flrw_match import (
    validate_planck2018_flrw_limit_match,
)

FIXTURE_PATH = Path(__file__).resolve().parents[3] / "data" / "camb_ref_planck2018.npz"


@pytest.fixture(scope="module")
def fb75_result() -> dict[str, object]:
    return validate_planck2018_flrw_limit_match(
        camb_fixture_path=FIXTURE_PATH,
        allow_surrogate=True,
    )


def test_fb75_planck2018_flrw_match_contract_is_callable() -> None:
    assert callable(validate_planck2018_flrw_limit_match)


def test_fb75_missing_fixture_raises() -> None:
    with pytest.raises(FileNotFoundError, match="CAMB Planck-2018 fixture"):
        validate_planck2018_flrw_limit_match(
            camb_fixture_path=Path("/does/not/exist/camb_ref_planck2018.npz"),
            allow_surrogate=True,
        )


def test_fb75_returns_rows_for_all_11_bianchi_types(fb75_result: dict[str, object]) -> None:
    rows = fb75_result["rows"]
    assert len(rows) == 11


@pytest.mark.parametrize("type_label", ["I", "V", "VII_0"])
def test_fb75_flrw_limit_ln_b_is_small_for_limit_types(
    fb75_result: dict[str, object], type_label: str
) -> None:
    rows = {row["type_label"]: row for row in fb75_result["rows"]}
    row = rows[type_label]
    assert abs(float(row["ln_B"])) < 0.1 + 1.0e-14
    assert abs(float(row["ln_B"])) <= 2.0 * float(row["mc_error"])


@pytest.mark.parametrize("type_label", ["II", "III", "IV", "VI_0", "VI_h", "VIII"])
def test_fb75_no_flrw_limit_rows_are_explicitly_flagged(
    fb75_result: dict[str, object], type_label: str
) -> None:
    rows = {row["type_label"]: row for row in fb75_result["rows"]}
    assert rows[type_label]["status"] == "NO_FLRW_LIMIT_EXPLICIT"


def test_fb75_fixture_metadata_matches_camb_fixture(fb75_result: dict[str, object]) -> None:
    meta = fb75_result["fixture_metadata"]
    assert meta["camb_version"] == "1.6.6"
    assert meta["lensed"] is False
    assert meta["omk"] == pytest.approx(0.0, abs=0.0)


def test_fb75_arxiv_ids_are_preserved(fb75_result: dict[str, object]) -> None:
    assert fb75_result["planck_likelihood_arxiv"] == "1907.12875"
    assert fb75_result["planck_parameters_arxiv"] == "1807.06209"


def test_fb75_ln_b_by_type_keys_cover_the_rows(fb75_result: dict[str, object]) -> None:
    rows = {row["type_label"] for row in fb75_result["rows"]}
    assert set(fb75_result["ln_B_by_type"]) == rows


@pytest.mark.parametrize("type_label", ["I", "V", "VII_0"])
def test_fb75_limit_rows_are_marked_as_pass(
    fb75_result: dict[str, object], type_label: str
) -> None:
    rows = {row["type_label"]: row for row in fb75_result["rows"]}
    assert rows[type_label]["status"] == "PASS"


def test_fb75_type_iv_is_negative_against_flrw(fb75_result: dict[str, object]) -> None:
    assert fb75_result["ln_B_by_type"]["IV"] < 0.0


def test_fb75_fixture_path_roundtrips(fb75_result: dict[str, object]) -> None:
    assert fb75_result["fixture_path"] == FIXTURE_PATH


@pytest.mark.parametrize("type_label", ["I", "IV", "VII_h", "IX"])
def test_fb75_row_lookup_contains_named_types(
    fb75_result: dict[str, object], type_label: str
) -> None:
    rows = {row["type_label"]: row for row in fb75_result["rows"]}
    assert type_label in rows
