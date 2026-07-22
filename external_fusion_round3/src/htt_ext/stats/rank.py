from __future__ import annotations

import numpy as np


def finite_rank_p(observed: float, null: np.ndarray, *, upper_tail: bool = True) -> float:
    values = np.asarray(null, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("null must be a non-empty vector")
    if upper_tail:
        b = int(np.sum(values >= observed))
    else:
        b = int(np.sum(values <= observed))
    return float((1 + b) / (values.size + 1))
