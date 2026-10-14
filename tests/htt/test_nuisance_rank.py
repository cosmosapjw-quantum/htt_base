import numpy as np
import pytest

from htt.infer.nuisance_rank import nuisance_projected_rank


def test_proportional_target_and_nuisance_is_rank_deficient():
    audit = nuisance_projected_rank(
        target_response=[1.0, 0.0],
        nuisance_response=[1.0, 0.0],
        covariance=np.eye(2),
    )

    assert audit.owner == "HTT"
    assert audit.claim_tier == "diagnostic_only"
    assert audit.projected_rank == 0
    assert audit.target_dimension == 1
    assert audit.full_rank is False
    assert "rank_deficient_after_nuisance_projection" in audit.no_claim_reasons


def test_independent_target_survives_nuisance_projection():
    audit = nuisance_projected_rank(
        target_response=[[0.0, 1.0], [1.0, 0.0], [0.0, 1.0]],
        nuisance_response=[1.0, 0.0, 0.0],
        covariance=np.eye(3),
    )

    assert audit.projected_rank == 2
    assert audit.full_rank is True
    assert audit.no_claim_reasons == ()
    payload = audit.as_payload()
    assert payload["full_rank"] is True
    assert payload["singular_values"][0] >= payload["singular_values"][1] > 0


def test_nuisance_rank_requires_positive_definite_covariance():
    with pytest.raises(ValueError, match="positive definite"):
        nuisance_projected_rank(
            target_response=[1.0, 0.0],
            nuisance_response=None,
            covariance=[[1.0, 0.0], [0.0, 0.0]],
        )


def test_small_physical_covariance_and_rectangular_nullspace():
    target=np.column_stack((np.eye(3),np.eye(3)))
    a=nuisance_projected_rank(target,None,1e-13*np.eye(3))
    assert a.projected_rank==3 and not a.full_rank and np.isinf(a.condition_number)
    b=nuisance_projected_rank(target,np.eye(3),1e-13*np.eye(3))
    assert b.projected_rank==0
    scaled=nuisance_projected_rank(target*1e-9,None,1e-31*np.eye(3))
    assert scaled.projected_rank==a.projected_rank
