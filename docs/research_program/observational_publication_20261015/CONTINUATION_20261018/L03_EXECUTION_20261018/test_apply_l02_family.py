import numpy as np
import pytest
from apply_l02_family import explicit_field_indices, variants, apply, differences, VARIANTS


def chart():
    return [{"ell": ell, "m": m, "phase": phase, "E_or_B": field}
            for ell in range(2, 6) for field in ("E", "B") for m in range(ell+1)
            for phase in (("m0",) if m == 0 else ("cos", "sin"))]


def test_explicit_interleaved_chart_retrieves_every_field_column():
    indices = explicit_field_indices(chart())
    assert len(indices["T"]) == len(indices["E"]) == len(indices["B"]) == 32
    assert indices["E"][:12].tolist() == list(range(32, 37))+list(range(42, 49))
    assert indices["B"][:12].tolist() == list(range(37, 42))+list(range(49, 56))
    assert set(np.concatenate(list(indices.values()))) == set(range(96))


def test_wrong_column_chart_fails_instead_of_silently_reslicing():
    layout = chart()
    layout[0], layout[1] = layout[1], layout[0]
    with pytest.raises(ValueError, match="EXPLICIT_SPIN_CHART"):
        explicit_field_indices(layout)


def test_variants_use_same_signal_and_noise_rows_without_crossing():
    coeff = np.arange(8*2*96).reshape(8, 2, 96).astype(float)
    v = variants(coeff)
    assert tuple(v) == VARIANTS
    np.testing.assert_array_equal(v["sum_noise_1.00"], coeff[:, 0]+coeff[:, 1])
    np.testing.assert_allclose(v["sum_noise_1.05"], coeff[:, 0]+1.05*coeff[:, 1])


def test_fixed_family_preserves_eight_ids_and_unknown_components():
    coeff = np.zeros((8, 2, 96))
    rows, baseline = apply(coeff, explicit_field_indices(chart()))
    assert len(rows) == 40 and len(baseline) == 24
    assert set(r["simulation_id"] for r in rows) == set(range(8))
    assert all(r["signal_id"] == r["noise_id"] == r["simulation_id"] for r in rows)
    for row in rows:
        assert set(row["fields"]) == {"T", "E", "B"}
        assert set(row["same_row_cross_fields"]) == {"TE", "TB", "EB"}
        for field in row["fields"].values():
            assert all(v is None for v in field["SO3_signed"].values())
            assert field["orientation"]["joint_axis_overlap_squared"] is None
    shifted = differences(rows)
    assert shifted["B"]["1.05"]["chirality"]["maximum_absolute_shift"] is None
    assert shifted["B"]["1.05"]["chirality"]["undefined_pair_count"] == 8


def test_signal_only_descriptor_sensitivity_is_zero():
    coeff = np.zeros((8, 2, 96))
    coeff[:, 0] = np.random.default_rng(91).normal(size=(8, 96))*1e-6
    rows, _ = apply(coeff, explicit_field_indices(chart()))
    shifted = differences(rows)
    for field in shifted.values():
        for factor in field.values():
            assert all(v["maximum_absolute_shift"] == 0 for v in factor.values())
