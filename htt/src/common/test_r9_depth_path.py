import numpy as np
import pytest
from common.depth_path import DepthRepresentation, full_covariance_blocks


def test_rectangular_path_restores_initial_values_and_full_cross_covariance():
    p = DepthRepresentation((2, 1, 2), (np.array([[2., -1.]]), np.array([[1.], [0.]])),
                            ('a', 'b', 'c', 'd', 'e'), 'fixed')
    y = np.arange(1., 6.)
    np.testing.assert_array_equal(p.restore(p.T @ y), y)
    assert np.linalg.det(p.T) == 1
    p = DepthRepresentation((1, 1, 1), (np.ones((1, 1)),)*2, ('a', 'b', 'c'), 'fixed')
    np.testing.assert_array_equal(p.H @ p.H.T, [[2, -1], [-1, 2]])
    np.testing.assert_array_equal(p.T @ p.T.T, [[1, -1, 0], [-1, 2, -1], [0, -1, 2]])


def test_absent_cross_block_is_not_independence():
    blocks = {(0, 0): [[1]], (1, 1): [[1]]}
    assert full_covariance_blocks(blocks, (1, 1)) is None
    blocks.update({(0, 1): [[.8]], (1, 0): [[.8]]})
    np.testing.assert_array_equal(full_covariance_blocks(blocks, (1, 1)), [[1, .8], [.8, 1]])
    with pytest.raises(ValueError):
        DepthRepresentation((1, 1), (np.eye(2),), ('a', 'b'), 'wrong')
