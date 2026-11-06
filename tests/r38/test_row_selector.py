"""Unit tests for exact vector and 2-axis covariance row selection.

Phase C of HTT-R38 Observational Convergence.
Tests row-order alignment, dimension matching, duplicate ID rejection,
and covariance subsetting positive-definiteness.
"""
from __future__ import annotations

import hashlib
import numpy as np
import pytest

from common.row_selector import (
    ExactRowSelector,
    DuplicateSourceIdError,
    SubsettingMismatchError,
    RowSelectionError,
)

def test_row_selector_basic_selection():
    ids = ["src_01", "src_02", "src_03", "src_04", "src_05"]
    y = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    C = np.diag([1.0, 2.0, 3.0, 4.0, 5.0]) + 0.1 * np.ones((5, 5))
    
    selector = ExactRowSelector(ids, y, C, allow_duplicates=False, name="test_sel")
    assert selector.n == 5
    
    # Select by boolean mask
    mask = [True, False, True, False, True]
    res = selector.select_by_mask(mask)
    assert res.selected_count == 3
    assert np.array_equal(res.selected_indices, [0, 2, 4])
    assert np.allclose(res.selected_vector, [10.0, 30.0, 50.0])
    assert res.selected_covariance.shape == (3, 3)
    assert res.covariance_audit.is_positive_definite
    
    # Check reproducible row-key hash
    expected_key = "\n".join(["0|src_01", "1|src_03", "2|src_05"])
    expected_hash = hashlib.sha256(expected_key.encode()).hexdigest()
    assert res.row_key_sha256 == expected_hash


def test_reject_duplicate_source_ids():
    ids = ["src_01", "src_02", "src_01", "src_04"]
    y = np.ones(4)
    C = np.eye(4)
    with pytest.raises(DuplicateSourceIdError, match="found 1 duplicate source IDs"):
        ExactRowSelector(ids, y, C, allow_duplicates=False)

    # Allowed when explicitly specified
    sel = ExactRowSelector(ids, y, C, allow_duplicates=True)
    assert sel.n == 4


def test_reject_dimension_mismatch():
    ids = ["src_01", "src_02", "src_03"]
    y = np.ones(4) # 4 != 3
    C = np.eye(3)
    with pytest.raises(SubsettingMismatchError, match="data_vector length"):
        ExactRowSelector(ids, y, C)

    y_good = np.ones(3)
    C_bad = np.eye(4) # 4x4 != 3x3
    with pytest.raises(SubsettingMismatchError, match="covariance shape"):
        ExactRowSelector(ids, y_good, C_bad)


def test_reproducible_row_key_sensitivity():
    # If order of rows is swapped, row_key_sha256 must change!
    ids = ["src_A", "src_B", "src_C"]
    y = np.array([1.0, 2.0, 3.0])
    C = np.eye(3)
    selector = ExactRowSelector(ids, y, C)
    
    res1 = selector.select_by_indices([0, 1])
    res2 = selector.select_by_indices([1, 0])
    assert res1.row_key_sha256 != res2.row_key_sha256


def test_select_by_id_list():
    ids = ["g1", "g2", "g3", "g4"]
    y = np.array([1.1, 2.2, 3.3, 4.4])
    C = np.eye(4) * 2.0
    selector = ExactRowSelector(ids, y, C)
    
    res = selector.select_by_id_list(["g3", "g1"], preserve_target_order=True)
    assert res.selected_ids == ("g3", "g1")
    assert np.allclose(res.selected_vector, [3.3, 1.1])
    
    # Missing ID should fail closed
    with pytest.raises(KeyError, match="target IDs not found"):
        selector.select_by_id_list(["g3", "nonexistent_id"])

