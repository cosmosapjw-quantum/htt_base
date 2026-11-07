"""Test suite for Cobaya QuaiaDipoleLikelihood."""

import pytest
import numpy as np
from cobaya.model import get_model


def test_cobaya_quaia_likelihood_evaluation():
    """Verify that Cobaya can instantiate and evaluate QuaiaDipoleLikelihood."""
    info = {
        "likelihood": {
            "htt.infer.cobaya_quaia_dipole.QuaiaDipoleLikelihood": {
                "verify_sha": False
            }
        },
        "params": {
            "beta_MO_x": 0.0,
            "beta_MO_y": 0.0,
            "beta_MO_z": 0.0,
        },
    }

    model = get_model(info)
    logpost = model.logposterior({})
    
    assert np.isfinite(logpost.loglike)
    print("Cobaya Quaia log-likelihood evaluated successfully:", logpost.loglike)

