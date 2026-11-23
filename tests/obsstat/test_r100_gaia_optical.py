"""Tests for R100 Part D (Gaia/Quaia rank-47 positive eigenspace, C_sys separation, joint identifiability)."""
from __future__ import annotations

import json
import numpy as np
import pytest

from scripts.r100 import gaia_optical_joint as r100_gaia


def test_whiten_positive_subspace_rank_preservation_and_scaling():
    """Whitening rank-deficient symmetric PSD covariance preserves rank under rescaling and never inverts nullspace."""
    rng = np.random.default_rng(1007)
    A = rng.normal(size=(15, 64))
    C = A.T @ A
    W1, r1, _ = r100_gaia.whiten_positive_subspace(C)
    W2, r2, _ = r100_gaia.whiten_positive_subspace(1e12 * C)
    assert r1 == 15 and r2 == 15
    assert np.allclose(1e6 * W2, W1, rtol=1e-10, atol=1e-12)
    # Nullspace vector maps to zero identically
    u, _, _ = np.linalg.svd(A.T)
    null_v = u[:, 20]
    assert np.linalg.norm(W1 @ null_v) < 1e-12


def test_r100_gaia_joint_result_contracts():
    """Verify GAIA_OPTICAL_JOINT_RESULTS.json avoids 64D/160D inversion and preserves physical_Pi=None."""
    path = r100_gaia.OUT_DIR / "GAIA_OPTICAL_JOINT_RESULTS.json"
    if not path.exists():
        pytest.skip("GAIA_OPTICAL_JOINT_RESULTS.json not generated yet")
    d = json.loads(path.read_text())
    assert d["physical_Pi"] is None
    assert d["calibrated_p"] is None
    assert d["full_160D_or_64D_inversion_avoided"] is True
    assert d["subspace_diagnostics"]["quaia_4shell_64D_jk"]["rank"] <= 47
    assert d["proper_motion_vs_parallax_covariance_audit"]["parallax_columns_substituted"] is False
    for ang_d in d["subspace_diagnostics"]["shared_C_sys_by_angle_deg_separate_from_jk"].values():
        assert ang_d["double_counting_prevented"] is True
