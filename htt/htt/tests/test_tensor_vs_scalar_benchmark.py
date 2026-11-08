"""Unit tests for Matched Tensor-x vs Scalar-x_C Benchmark (R41-07)."""

import os
import json
from pathlib import Path
import numpy as np
import pytest

from common.stf_metric_bridge import G_STF5
from scripts.r41.run_r41_tensor_vs_scalar_benchmark import (
    build_parameter_gram_matrix,
    param_vector_to_theta17,
    PARAM_NAMES,
    D_PARAMS,
)


ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_JSON_PATH = (
    ROOT / "docs/research_program/observational_publication_20261015/R41_PUBLICATION_GATE_20261107/R41_TENSOR_VS_SCALAR_BENCHMARK.json"
)


def test_parameter_gram_matrix():
    """Verify physical parameter Gram matrix structure and positive definiteness."""
    G = build_parameter_gram_matrix()
    assert G.shape == (11, 11)
    # Check block diagonal structure
    assert np.allclose(G[0:3, 0:3], np.eye(3))
    assert np.allclose(G[3:6, 3:6], np.eye(3))
    assert np.allclose(G[6:11, 6:11], G_STF5)
    
    # Positive definiteness
    evals = np.linalg.eigvalsh(G)
    assert np.all(evals > 0)


def test_param_vector_to_theta17():
    """Verify mapping of 11 kinematic parameters to 17-vector state."""
    p = np.arange(1, 12, dtype=np.float64)
    th17 = param_vector_to_theta17(p)
    assert len(th17) == 17
    # beta_MO at [14:17]
    assert np.allclose(th17[14:17], p[0:3])
    # A at [8:11]
    assert np.allclose(th17[8:11], p[3:6])
    # sigma STF5 at [0:5]
    assert np.allclose(th17[0:5], p[6:11])
    # Unsampled components remain zero
    assert np.allclose(th17[5:8], 0.0)
    assert np.allclose(th17[11:14], 0.0)


def test_benchmark_artifact_and_rank_advantage():
    """Verify benchmark JSON artifact, rank gain, and statistical calibration."""
    assert BENCHMARK_JSON_PATH.exists(), f"Benchmark JSON {BENCHMARK_JSON_PATH} must exist"

    with open(BENCHMARK_JSON_PATH, "r") as f:
        data = json.load(f)

    summary = data["benchmark_summary"]
    assert summary["parameter_dimension"] == 11
    assert summary["identifiability_rank_tensor_x"] == 11
    assert summary["identifiability_rank_scalar_xC"] == 7
    assert summary["rank_gain_tensorization"] == 4
    assert summary["fisher_information_gain_nats"] > 0.0

    sbc = data["sbc_ppc_validation"]
    assert sbc["false_positive_rate"] <= 0.05
    assert sbc["power"] >= 0.95
    assert 0.05 <= sbc["ppc_p_value"] <= 0.95
