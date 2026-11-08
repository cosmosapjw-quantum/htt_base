"""Test suite for Cobaya JointFiveProbeLikelihood."""

import pytest
import numpy as np
from cobaya.model import get_model


def test_cobaya_joint_five_probe_evaluation():
    """Verify that Cobaya evaluates joint 5-probe log-likelihood."""
    info = {
        "likelihood": {
            "htt.infer.cobaya_joint_five_probe.JointFiveProbeLikelihood": {
                "verify_sha": False
            }
        },
        "params": {
            "H0": 73.4,
            "Omega_m": 0.334,
            "DeltaOmega_k": 0.0,
            "sigma_xx": 0.0,
            "sigma_yy": 0.0,
            "sigma_xy": 0.0,
            "sigma_xz": 0.0,
            "sigma_yz": 0.0,
            "omega_x": 0.0,
            "omega_y": 0.0,
            "omega_z": 0.0,
            "A_x": 0.0,
            "A_y": 0.0,
            "A_z": 0.0,
            "beta_RM_x": 0.0,
            "beta_RM_y": 0.0,
            "beta_RM_z": 0.0,
            "beta_MO_x": 0.0,
            "beta_MO_y": 0.0,
            "beta_MO_z": 0.0,
        },
    }

    model = get_model(info)
    logpost = model.logposterior({})

    assert np.isfinite(logpost.loglike)
    print("Joint Five-Probe log-likelihood:", logpost.loglike)


def test_cobaya_joint_five_probe_anisotropic_evaluation():
    """Verify that Cobaya evaluates joint 5-probe with non-zero tilt and shear parameters."""
    info = {
        "likelihood": {
            "htt.infer.cobaya_joint_five_probe.JointFiveProbeLikelihood": {
                "verify_sha": False
            }
        },
        "params": {
            "H0": 73.4,
            "Omega_m": 0.334,
            "DeltaOmega_k": 0.0,
            "sigma_xx": 1e-4,
            "sigma_yy": -5e-5,
            "sigma_xy": 2e-5,
            "sigma_xz": 3e-5,
            "sigma_yz": -1e-5,
            "omega_x": 0.0,
            "omega_y": 0.0,
            "omega_z": 0.0,
            "A_x": 1e-3,
            "A_y": -5e-4,
            "A_z": 2e-4,
            "beta_RM_x": 5e-4,
            "beta_RM_y": -3e-4,
            "beta_RM_z": 2e-4,
            "beta_MO_x": -1.2e-3,
            "beta_MO_y": 2.5e-4,
            "beta_MO_z": 8.0e-4,
        },
    }

    model = get_model(info)
    logpost = model.logposterior({})

    assert np.isfinite(logpost.loglike)
    print("Anisotropic Five-Probe log-likelihood:", logpost.loglike)
