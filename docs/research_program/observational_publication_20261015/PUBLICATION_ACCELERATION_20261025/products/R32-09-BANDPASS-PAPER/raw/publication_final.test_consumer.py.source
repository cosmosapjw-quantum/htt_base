"""Targeted cached-statistics formatter regressions."""
import copy
import hashlib
import json
import pytest
import consumer


def example():
    metric = {"minimum_budget_ell": 2.0,
              "one_compensator_radius_per_unit_rho": 0.5,
              "pairwise_max_separation_per_unit_rho": 1.0}
    return {
        "task_id": "R32-04-BANDPASS-BOUNDS", "checks_status": "PASS",
        "source_sha256": "b" * 64,
        "frequencies": list(consumer.FREQUENCIES),
        "moment_order": list(consumer.MOMENTS),
        "full24_coordinate_order": list(consumer.COORDINATES),
        "common_reference_column_scales": [1.0] * 9,
        "branches": {name: {"finite_rank_F2": 7, "free_target_quotient_rank": 0,
                            "common_reference": copy.deepcopy(metric),
                            "raw_identity": copy.deepcopy(metric)}
                     for name in consumer.BRANCHES},
    }


def test_exact_selection_hash_and_changed_source(tmp_path):
    raw = json.dumps(example()).encode()
    (tmp_path / "RESULT.json").write_bytes(raw)
    identity = hashlib.sha256(raw).hexdigest()
    assert consumer.read_bound_result(tmp_path, identity)["checks_status"] == "PASS"
    (tmp_path / "RESULT.json").write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="byte identity"):
        consumer.read_bound_result(tmp_path, identity)


def test_full_signed_order_is_not_replaceable_by_unsigned_norms():
    data = example()
    data["full24_coordinate_order"][2] = "E2:abs_m1"
    with pytest.raises(ValueError, match="coordinate order"):
        consumer.validate_selection(data, "b" * 64)


def test_omitted_branch_cannot_make_a_complete_table():
    data = example()
    del data["branches"][consumer.BRANCHES[-1]]
    with pytest.raises(ValueError, match="six retained"):
        consumer.validate_selection(data, "b" * 64)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, 0, True])
def test_nonfinite_or_invalid_stored_budget_is_rejected(value):
    data = example()
    data["branches"][consumer.BRANCHES[0]]["common_reference"]["minimum_budget_ell"] = value
    with pytest.raises(ValueError, match="finite positive"):
        consumer.validate_selection(data, "b" * 64)


def test_unrestricted_target_rank_and_source_binding_are_required():
    data = example()
    with pytest.raises(ValueError, match="source identity"):
        consumer.validate_selection(data, "c" * 64)
    data["branches"][consumer.BRANCHES[0]]["free_target_quotient_rank"] = 24
    with pytest.raises(ValueError, match="rank scope"):
        consumer.validate_selection(data, "b" * 64)


def test_radius_and_pairwise_columns_preserve_distinct_stored_values():
    rows = consumer.validate_selection(example(), "b" * 64)
    text = consumer.render_table(rows)
    assert "2.000000 & 0.500000 & 1.000000 & 2.000000" in text
    assert len(rows) == 6
