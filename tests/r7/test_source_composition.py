"""Integration oracles against the real common-package consumer import."""
from copy import deepcopy
from itertools import permutations
from pathlib import Path

import numpy as np
import pytest
from common import mes_krylov_completion as decoder


def witness():
    q = np.diag([1., 2., -3.])
    o = np.empty((3, 3, 3))
    values = {(0,0,0):1., (0,0,1):2., (0,0,2):3., (0,1,1):4.,
              (0,1,2):5., (1,1,1):6., (1,1,2):7., (0,2,2):-5.,
              (1,2,2):-8., (2,2,2):-10.}
    for indices, value in values.items():
        for p in set(permutations(indices)):
            o[p] = value
    return q, o


def test_target_import_and_out_of_image_sign_flip():
    root = Path(__file__).resolve().parents[2]
    assert Path(decoder.__file__).resolve() == root / "htt/src/common/mes_krylov_completion.py"
    packet = deepcopy(decoder.krylov16(*witness()))
    packet["values"][6:] = [-v for v in packet["values"][6:]]
    with pytest.raises(decoder.OrbitInputError):
        decoder.reconstruct_krylov16(packet)


def test_roundtrip_on_consumer_import():
    packet = decoder.krylov16(*witness())
    q, o = decoder.reconstruct_krylov16(packet)
    np.testing.assert_allclose(decoder.krylov16(q, o)["values"], packet["values"],
                               rtol=1e-7, atol=1e-10)
