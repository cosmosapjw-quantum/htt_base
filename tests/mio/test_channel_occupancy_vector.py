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
    assert [row["occupancy"] for row in report["rows"]] == pytest.approx([0.2, 0.5])
    assert all(0.0 <= row["occupancy"] <= 1.0 for row in report["rows"])


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
    with pytest.raises(ValueError, match="within \\[0, 1\\]"):
        channel_matched_occupancy(
            [{"channel": "shear", "numerator": 1.2, "denominator": 1.0}],
            generating_command="pytest",
            worktree_state="test",
            input_hashes=["sha256:test"],
        )
