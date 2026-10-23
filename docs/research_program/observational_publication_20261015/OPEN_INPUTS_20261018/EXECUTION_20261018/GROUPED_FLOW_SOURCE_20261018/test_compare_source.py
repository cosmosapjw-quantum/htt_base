import copy
import json
import numpy as np
import pytest
from compare_source import (EXTERNAL, EXPECTED_TABLE, RADII, build_result,
                            check_prefix, compare, parse_probe, parse_table,
                            rounding_parity, sealed_inputs)


def test_literal_table_selection_units_and_frame():
    html = (EXTERNAL / "courtois_2211.16390v4.html").read_text()
    table = parse_table(html)
    assert table["vectors"] == EXPECTED_TABLE
    assert table["radii"] == RADII
    assert table["radius_unit"] == "h_100^-1 Mpc"
    assert table["velocity_unit"] == "km/s"
    with pytest.raises(ValueError, match="units"):
        parse_table(html.replace('alttext="{}_{100}^{-1}"', 'alttext="h^{-2}"'))
    with pytest.raises(ValueError, match="CMB"):
        parse_table(html.replace("in the cosmic microwave background rest frame", "FRAME_REMOVED"))


def test_seals_and_exact_author_anchors():
    assert sealed_inputs()["giani_main_first13001bytes.jsonpart"]["bytes"] == 13001
    prefix = (EXTERNAL / "giani_main_first13001bytes.jsonpart").read_text()
    geometry = check_prefix(prefix)
    assert geometry["spacing_hinv_Mpc"] == 15.625
    assert geometry["sample_node_extents_hinv_Mpc"] == [-500, 484.375]
    with pytest.raises(ValueError, match="anchor"):
        check_prefix(prefix.replace("t[:,kk,jj,ii]", "t[:,ii,jj,kk]"))


def test_probe_missing_duplicate_convention_and_rows_rejected():
    text = (EXTERNAL / "SPHERE_PROBE_TRANSCRIPT.txt").read_text()
    rows = [line for line in text.splitlines() if line.startswith("{'box':")]
    assert len(parse_probe(text)) == 4
    for broken in ["\n".join(rows[:-1]), text + "\n" + rows[0]]:
        with pytest.raises(ValueError):
            parse_probe(broken)
    record = parse_probe(text)[0]
    for field in ["counts", "xyz_means"]:
        broken = copy.deepcopy(record)
        broken[field].pop()
        with pytest.raises(ValueError, match="row"):
            parse_probe(repr(broken))
    broken = copy.deepcopy(record)
    broken["counts"][1] = broken["counts"][0]
    with pytest.raises(ValueError, match="duplicate"):
        parse_probe(repr(broken))


@pytest.mark.parametrize("offset, parity", [(0., True), (.5, True), (-.5, True),
                                            (.5000001, False), (-.5000001, False)])
def test_rounding_boundaries_only(offset, parity):
    assert bool(rounding_parity([10 + offset], [10])[0]) is parity


def test_finite_parity_required():
    for values in [[np.nan], [np.inf], [1, 2]]:
        with pytest.raises(ValueError):
            rounding_parity(values, [1])


def test_component_reorder_not_spatial_qualification():
    result = build_result()
    author, alternative = result["scenarios"][:2]
    assert author["raw_component_order"] == [2, 1, 0]
    assert alternative["raw_component_order"] == [0, 1, 2]
    np.testing.assert_array_equal(np.asarray(author["means_kms"])[:, ::-1], alternative["means_kms"])
    assert alternative["means_kms"][0] == [-234.821610924338, 81.31811248364092, -90.61960073920335]
    assert not result["spatial_axis_permutation_qualified"]


def test_invalid_large_spheres_retained_and_no_promotion():
    result = build_result()
    assert len(result["scenarios"]) == 8
    for scenario in result["scenarios"]:
        mask = scenario["sphere_truncated_invalid_mask"]
        assert mask == ([False] * 5 + [True] if scenario["L_hinv_Mpc"] == 500 else [False] * 6)
        assert len(scenario["means_kms"]) == 6
        assert not any(scenario["row_rounding_parity"])
        assert scenario["full_sphere_qualification"] == "NOT_QUALIFIED"
        assert np.isfinite(scenario["means_kms"]).all()
    assert result["status"] == "SOURCE_CONFLICT"
    assert result["fitted_or_selected_convention"] is None
    assert result["downstream_H02_physical_flow_use"] == "HOLD"
    assert not result["grid_reexecuted"]
    # Even fabricated table equality would not qualify a physical source contract.
    records = parse_probe((EXTERNAL / "SPHERE_PROBE_TRANSCRIPT.txt").read_text())
    artificial = {"vectors": records[0]["xyz_means"]}
    assert compare(records, artificial)["status"] == "SOURCE_CONFLICT"
    json.dumps(result, allow_nan=False)
