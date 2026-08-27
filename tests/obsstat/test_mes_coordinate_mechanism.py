import numpy as np
import pytest

from obsstat.mes_coordinate_mechanism import (
    FACTORIAL_CELL_IDS,
    epsilon1_grid,
    factorial_coordinate_cells,
    mes_coordinate_forward,
    mes_coordinate_inverse,
)
from obsstat.finite_null_reducers import legacy_absolute_median_scan


def _rows() -> np.ndarray:
    rows = np.zeros((5, 12), dtype=float)
    rows[:, 0] = [100.0, 200.0, 300.0, 500.0, 800.0]
    rows[:, 1] = [120.0, 180.0, 360.0, 420.0, 900.0]
    rows[:, 4:] = np.arange(40.0).reshape(5, 8) / 40.0
    return rows


def test_exact_mes_identity_inverse_and_w_rank() -> None:
    eps2 = np.array([1e-6, 2e-6, 5e-6])
    eps3 = np.array([2e-6, 1e-6, 7e-6])
    sigma2, w2 = mes_coordinate_forward(eps2, eps3, epsilon1=0.0)
    recovered2, recovered3 = mes_coordinate_inverse(sigma2, w2)
    assert np.allclose(recovered2, eps2, rtol=2e-15, atol=0.0)
    assert np.allclose(recovered3, eps3, rtol=2e-15, atol=0.0)
    assert np.allclose(w2, 1.5 * ((2.0 / 15.0) * eps2) ** 2)
    assert np.allclose(sigma2, (27.0 / 98.0) * (7.0 * eps2 + eps3) ** 2)

    source = _rows()
    mes_rows = factorial_coordinate_cells(source)["MES_SQUARED"]
    c2_scan = legacy_absolute_median_scan(source[:, [0]], ("two-sided",))
    w2_scan = legacy_absolute_median_scan(mes_rows[:, [1]], ("two-sided",))
    assert w2_scan.local_p_all_rows == c2_scan.local_p_all_rows


def test_factorial_cells_have_exact_registered_coordinates() -> None:
    cells = factorial_coordinate_cells(_rows())
    assert tuple(cells) == FACTORIAL_CELL_IDS
    assert all(value.shape == (5, 10) for value in cells.values())
    assert np.allclose(cells["SQUARE_ONLY"][:, :2], cells["EPS_LINEAR"][:, :2] ** 2)
    assert np.allclose(cells["MES_SQUARED"][:, :2], 1.5 * cells["CARRIER_ONLY"][:, :2] ** 2)


def test_epsilon1_grid_is_predeclared_and_negative_refused() -> None:
    grid = epsilon1_grid()
    assert grid.shape == (101,)
    assert grid[0] == 0.0 and grid[-1] == 1.0e-5
    assert np.allclose(np.diff(grid), 1.0e-7)
    with pytest.raises(ValueError, match="epsilon1"):
        mes_coordinate_forward(np.array([1e-6]), np.array([2e-6]), epsilon1=-1.0)
