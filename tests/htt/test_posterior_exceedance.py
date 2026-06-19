import pytest

from htt.infer.posterior_exceedance import posterior_exceedance_summary


def test_htt_posterior_exceedance_is_model_conditional_not_mio_pi():
    summary = posterior_exceedance_summary(
        samples=[0.01, 0.05, 0.20, 0.30],
        threshold=0.10,
        model_label="legacy_transfer_conditioned_tilt",
        source_quantity="Q_HTT",
        input_hashes=["sha256:samples"],
        generating_command="pytest tests/htt/test_posterior_exceedance.py",
        worktree_state="test-worktree",
    )

    assert summary["owner"] == "HTT"
    assert summary["implementation_scope"] == "htt"
    assert summary["claim_tier"] == "transfer_conditional"
    assert summary["quantity_name"] == "P_post"
    assert summary["threshold"] == 0.10
    assert summary["samples_count"] == 4
    assert summary["exceedance_count"] == 2
    assert summary["exceedance_probability"] == 0.5
    assert summary["mio_pi_compatible"] is False
    assert "model-conditional posterior exceedance" in summary["definition"]
    assert "not a MIO diagnostic Pi" in summary["caveats"]
    assert "not a truth probability" in summary["caveats"]
    assert "not family or geometry evidence" in summary["caveats"]


def test_htt_posterior_exceedance_requires_provenance_and_nonempty_samples():
    with pytest.raises(ValueError, match="samples"):
        posterior_exceedance_summary(
            samples=[],
            threshold=0.10,
            model_label="legacy_transfer_conditioned_tilt",
            source_quantity="Q_HTT",
            input_hashes=["sha256:samples"],
            generating_command="pytest tests/htt/test_posterior_exceedance.py",
            worktree_state="test-worktree",
        )

    with pytest.raises(ValueError, match="input_hashes"):
        posterior_exceedance_summary(
            samples=[0.2],
            threshold=0.10,
            model_label="legacy_transfer_conditioned_tilt",
            source_quantity="Q_HTT",
            input_hashes=[],
            generating_command="pytest tests/htt/test_posterior_exceedance.py",
            worktree_state="test-worktree",
        )


def test_htt_posterior_exceedance_rejects_mio_source_quantity():
    with pytest.raises(ValueError, match="MIO diagnostic"):
        posterior_exceedance_summary(
            samples=[0.2],
            threshold=0.10,
            model_label="legacy_transfer_conditioned_tilt",
            source_quantity="MIO_Pi",
            input_hashes=["sha256:samples"],
            generating_command="pytest tests/htt/test_posterior_exceedance.py",
            worktree_state="test-worktree",
        )


def test_htt_posterior_exceedance_rejects_unsafe_claim_tier():
    with pytest.raises(ValueError, match="claim_tier"):
        posterior_exceedance_summary(
            samples=[0.2],
            threshold=0.10,
            model_label="legacy_transfer_conditioned_tilt",
            source_quantity="Q_HTT",
            input_hashes=["sha256:samples"],
            generating_command="pytest tests/htt/test_posterior_exceedance.py",
            worktree_state="test-worktree",
            claim_tier="native_solver_result",
        )


def test_htt_posterior_exceedance_rejects_unsafe_transfer_source():
    unsafe_transfer = "".join(
        [
            "external",
            " transfer",
            " validated",
            " as",
            " native",
        ]
    )
    with pytest.raises(ValueError, match="transfer_source"):
        posterior_exceedance_summary(
            samples=[0.2],
            threshold=0.10,
            model_label="legacy_transfer_conditioned_tilt",
            source_quantity="Q_HTT",
            input_hashes=["sha256:samples"],
            generating_command="pytest tests/htt/test_posterior_exceedance.py",
            worktree_state="test-worktree",
            transfer_source=unsafe_transfer,
        )


def test_htt_posterior_exceedance_rejects_reserved_metadata_language():
    with pytest.raises(ValueError, match="metadata"):
        posterior_exceedance_summary(
            samples=[0.2],
            threshold=0.10,
            model_label="legacy_transfer_conditioned_tilt",
            source_quantity="Q_HTT",
            input_hashes=["sha256:samples"],
            generating_command="pytest tests/htt/test_posterior_exceedance.py",
            worktree_state="test-worktree",
            metadata={"note": {"unsafe": "Bianchi " + "geometry detected"}},
        )
