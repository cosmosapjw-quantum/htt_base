import numpy as np
import pytest

from scripts.r105.common_time_moments import nested_samples


def test_nested_indices_preserve_vector_sign_and_reference_scale():
    common = np.array([-0.5, 0.0])
    for stride in (1, 2, 4):
        edges = np.linspace(-1, 0, 2 * stride + 1)[1:]
        fluid = np.tile([3., 4., 0.], (len(edges), 1))
        diff = np.column_stack([edges, -2 * edges, edges - 1])
        samples = nested_samples(common, edges, fluid + diff, fluid)
        assert [v["cell_index"] for v in samples] == [stride - 1, 2 * stride - 1]
        for v in samples:
            np.testing.assert_array_equal(v["sky_minus_fluid"], diff[v["cell_index"]])
            assert v["relative_norm"] == np.linalg.norm(diff[v["cell_index"]]) / 5


def test_even_one_ulp_offset_or_zero_reference():
    edges = np.array([-0.5, 0.0])
    zeros = np.zeros((2, 3))
    assert nested_samples(edges, edges, zeros + 1, zeros)[0]["relative_norm"] is None
    shifted = np.nextafter(edges, 1.)
    with pytest.raises(ValueError, match="do not match exactly"):
        nested_samples(edges, shifted, zeros, zeros)
