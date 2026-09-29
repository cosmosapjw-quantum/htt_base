from __future__ import annotations

import numpy as np

from htt.obsstat.catalogs.owned_desi_analysis import summarize_desi


def test_primary_weight_is_not_multiplied_by_components() -> None:
    arrays = {"ra": [0., 90., 180.], "dec": [0., 0., 0.], "z": [.1, .2, .3], "weight": [1., 2., 3.],
              "weight_fkp": [10., 10., 10.], "weight_sys": [5., 5., 5.], "targetid": [1, 1, 2]}
    result = summarize_desi(arrays, dataset_id="desi.bgs.ngc", tracer="BGS", cap="NGC", z_edges=[0., .25, .5])
    assert result["redshift_bins"][0]["weight_sum"] == 3.
    assert result["weight_combination"] == "NO_ADDITIONAL_MULTIPLICATION"
    assert result["duplicate_target_rows"] == 1
    assert result["selection_correction"] == "UNAVAILABLE"


def test_chunk_concatenation_matches_in_memory() -> None:
    first = {"ra": np.array([0., 90.]), "dec": np.zeros(2), "z": np.array([.1, .2]), "weight": np.ones(2)}
    second = {"ra": np.array([180.]), "dec": np.zeros(1), "z": np.array([.3]), "weight": np.ones(1)}
    merged = {key: np.concatenate([first[key], second[key]]) for key in first}
    result = summarize_desi(merged, dataset_id="x", tracer="LRG", cap="SGC", z_edges=[0., .5])
    assert result["row_count"] == 3
    assert np.linalg.norm(result["redshift_bins"][0]["weighted_mean_direction"]) <= 1.0 + 1e-12
