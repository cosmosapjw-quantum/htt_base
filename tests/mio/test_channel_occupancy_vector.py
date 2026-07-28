import pytest

from mio.formalism.channel_occupancy_vector import channel_matched_occupancy


def test_channel_matched_occupancy_rows_are_bounded():
    report = channel_matched_occupancy(
        [
            {"channel": "shear", "numerator": 0.2, "denominator": 1.0},
            {"channel": "tilt", "numerator": 0.3, "denominator": 0.6},
        ],
        generating_command="pytest tests/mio/test_channel_occupancy_vector.py",
        worktree_state="test-worktree",
        input_hashes=["sha256:test"],
    )

    assert report["owner"] == "MIO"
    assert report["claim_tier"] == "diagnostic_only"
    assert report["posterior_compatible"] is False
    assert report["physical_occupancy"] is False
    assert [row["ratio"] for row in report["rows"]] == pytest.approx([0.2, 0.5])
    assert all(0.0 <= row["ratio"] <= 1.0 for row in report["rows"])


def test_channel_occupancy_rejects_cross_channel_denominator():
    with pytest.raises(ValueError, match="cross-channel"):
        channel_matched_occupancy(
            [
                {
                    "channel": "shear",
                    "numerator": 0.2,
                    "denominator": 1.0,
                    "denominator_channel": "tilt",
                }
            ],
            generating_command="pytest",
            worktree_state="test",
            input_hashes=["sha256:test"],
        )


def test_channel_occupancy_rejects_clipping_cases():
    with pytest.raises(ValueError, match="legacy ratio.*within \\[0, 1\\]"):
        channel_matched_occupancy(
            [{"channel": "shear", "numerator": 1.2, "denominator": 1.0}],
            generating_command="pytest",
            worktree_state="test",
            input_hashes=["sha256:test"],
        )


def test_scalar_proxy_rows_cannot_use_occupancy_language():
    from mio.formalism.channel_occupancy_vector import classify_occupancy_language

    result = classify_occupancy_language(
        numerator_channel="tilt",
        denominator_channel="shear",
        requested_phrase="physical occupancy",
    )
    assert result["allowed"] is False
    assert result["status"] == "legacy_ratio_only"
    assert "channel_mismatch" in result["blocked_reasons"]


def test_channel_matched_rows_do_not_promote_ratio_to_occupancy():
    from mio.formalism.channel_occupancy_vector import classify_occupancy_language

    result = classify_occupancy_language(
        numerator_channel="shear",
        denominator_channel="shear",
        requested_phrase="physical occupancy",
    )
    assert result["allowed"] is False
    assert result["status"] == "legacy_ratio_only"
    assert "occupancy_language_retired_for_legacy_ratio" in result["blocked_reasons"]


def test_joint_admissible_ceiling_proof_does_not_create_occupancy():
    from mio.formalism.channel_occupancy_vector import classify_occupancy_language

    result = classify_occupancy_language(
        numerator_channel="tilt",
        denominator_channel="shear",
        requested_phrase="occupancy",
        joint_admissible_ceiling_proof="sha256:" + "a" * 64,
    )
    assert result["allowed"] is False
    assert result["status"] == "legacy_ratio_only"
    assert (
        "joint_ceiling_proof_does_not_convert_ratio_to_occupancy"
        in result["blocked_reasons"]
    )
