"""Contract: the EGS3 PSD-cone revisionary redesign is a representation-only
change, gated by a bit-identical regression on x_C.

The PSD comparator M = diag(g) must reproduce the graded x_C exactly via the
trace functional x_C = tr(C M); it must not change x_C, Q, F, or any downstream
object.  This is the gate the ticket requires before the redesign may ship in
front of (rather than behind) the additive graded upgrade.
"""
from __future__ import annotations

import numpy as np
import pytest

from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix, admissibility
from htt.obsstat.egs3_graded_comparator import graded_comparator


@pytest.mark.parametrize("g", [
    (2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7),
    (5.0e-6, 5.0e-6, 0.0, 0.0),      # Sigma2 == W2 cancellation
    (0.0, 0.0, 0.0, 0.0),            # FLRW vertex
    (9.25e-6, 1.0e-9, 1.0e-9, 1.0e-9),
])
def test_trace_functional_reconstructs_graded_xc_bit_identically(g):
    M = sector_matrix(g)
    gc = graded_comparator(*g)
    assert np.array_equal(xc_from_matrix(M), gc.x_C)   # bit-identical, not close


def test_psd_admissible_for_all_nonnegative_sector_vectors():
    rng = np.random.default_rng(7)
    for _ in range(64):
        g = rng.uniform(0.0, 1e-5, 4)
        assert admissibility(sector_matrix(g)).is_admissible


def test_redesign_does_not_introduce_a_new_scalar():
    # x_C through the matrix equals x_C through the vector for the same input;
    # the redesign adds structure (cone, eigendirections) but no new number.
    g = (2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7)
    assert xc_from_matrix(sector_matrix(g)) == graded_comparator(*g).x_C
