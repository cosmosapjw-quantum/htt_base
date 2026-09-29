from __future__ import annotations

import numpy as np
import pytest

from htt.obsstat.owned_cf4_query_analysis import summarize_cf4_queries


def test_duplicate_cells_do_not_become_independent_samples() -> None:
    arrays = {"sgx": [1., 1., 5.], "sgy": [0., 0., 0.], "sgz": [0., 0., 0.],
              "grid_index": [[1, 2, 3], [1, 2, 3], [2, 2, 3]], "vxyz_mean": [[1., 0., 0.], [3., 0., 0.], [0., 2., 0.]],
              "vxyz_std": np.ones((3, 3))}
    result = summarize_cf4_queries(arrays, dataset_id="cf4.query", depth_edges_mpc_h=[0., 10., 30.])
    assert result["query_rows"] == 3
    assert result["unique_grid_cells"] == 2
    assert result["duplicate_query_rows"] == 1
    assert result["independent_sample_count"] is None
    assert result["depth_summaries"][0]["mean_reconstructed_velocity"] == [1.0, 1.0, 0.0]


def test_out_of_grid_coordinates_are_refused_not_clipped() -> None:
    arrays = {"sgx": [501.], "sgy": [0.], "sgz": [0.], "grid_index": [[127, 1, 1]],
              "vxyz_mean": [[0., 0., 0.]], "vxyz_std": [[1., 1., 1.]]}
    with pytest.raises(ValueError, match="clipping refused"):
        summarize_cf4_queries(arrays, dataset_id="cf4.query", depth_edges_mpc_h=[0., 600.])
