"""Typed vector/tensor/multicomponent state containers.

Every block carries frame, congruence, units, source ownership, parity, epoch,
and basis metadata.  This prevents numerically compatible arrays with
physically incompatible meanings from being silently concatenated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple
import hashlib
import json
import numpy as np

_REP_DIM = {'scalar': 1, 'vector': 3, 'stf2': 5}


@dataclass(frozen=True)
class BlockSpec:
    name: str
    representation: str
    units: str
    frame: str
    congruence: str
    source_owner: str
    epoch: str = 'unspecified'
    parity: str = 'even'
    basis: str = 'canonical'
    dimension: Optional[int] = None

    def resolved_dimension(self) -> int:
        if self.dimension is not None:
            if self.dimension <= 0:
                raise ValueError('dimension must be positive')
            return int(self.dimension)
        if self.representation not in _REP_DIM:
            raise ValueError(f'unknown representation {self.representation!r}; provide dimension')
        return _REP_DIM[self.representation]

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        d['dimension'] = self.resolved_dimension()
        return d


@dataclass
class StateBlock:
    spec: BlockSpec
    value: np.ndarray
    covariance: Optional[np.ndarray] = None

    def __post_init__(self) -> None:
        self.value = np.asarray(self.value, dtype=float).reshape(-1)
        d = self.spec.resolved_dimension()
        if self.value.shape != (d,):
            raise ValueError(f'{self.spec.name}: expected value shape {(d,)}, got {self.value.shape}')
        if not np.all(np.isfinite(self.value)):
            raise ValueError(f'{self.spec.name}: non-finite value')
        if self.covariance is not None:
            self.covariance = np.asarray(self.covariance, dtype=float)
            _validate_covariance(self.covariance, d, self.spec.name)

    def as_dict(self) -> dict:
        return {
            'spec': self.spec.as_dict(),
            'value': self.value.tolist(),
            'covariance': None if self.covariance is None else self.covariance.tolist(),
        }


def _validate_covariance(c: np.ndarray, d: int, owner: str, tol: float = 1e-10) -> None:
    if c.shape != (d, d):
        raise ValueError(f'{owner}: expected covariance {(d,d)}, got {c.shape}')
    if not np.all(np.isfinite(c)) or not np.allclose(c, c.T, atol=tol, rtol=0):
        raise ValueError(f'{owner}: covariance must be finite and symmetric')
    scale = max(1.0, float(np.linalg.norm(c, ord=2)))
    if float(np.min(np.linalg.eigvalsh(c))) < -tol * scale:
        raise ValueError(f'{owner}: covariance is not positive semidefinite')


@dataclass
class MulticomponentState:
    blocks: Sequence[StateBlock]
    joint_covariance: Optional[np.ndarray] = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.blocks = tuple(self.blocks)
        names = [b.spec.name for b in self.blocks]
        if len(names) != len(set(names)):
            raise ValueError('block names must be unique')
        if self.joint_covariance is not None:
            self.joint_covariance = np.asarray(self.joint_covariance, dtype=float)
            _validate_covariance(self.joint_covariance, self.dimension, 'joint')

    @property
    def dimension(self) -> int:
        return sum(b.spec.resolved_dimension() for b in self.blocks)

    @property
    def names(self) -> Tuple[str, ...]:
        return tuple(b.spec.name for b in self.blocks)

    def slices(self) -> Dict[str, slice]:
        out: Dict[str, slice] = {}
        start = 0
        for block in self.blocks:
            stop = start + block.spec.resolved_dimension()
            out[block.spec.name] = slice(start, stop)
            start = stop
        return out

    def flatten(self) -> np.ndarray:
        if not self.blocks:
            return np.empty(0, dtype=float)
        return np.concatenate([b.value for b in self.blocks])

    def covariance(self, require_complete: bool = True) -> np.ndarray:
        if self.joint_covariance is not None:
            return self.joint_covariance.copy()
        if require_complete and any(b.covariance is None for b in self.blocks):
            missing = [b.spec.name for b in self.blocks if b.covariance is None]
            raise ValueError(f'missing block covariance for {missing}')
        c = np.zeros((self.dimension, self.dimension), dtype=float)
        for block, sl in zip(self.blocks, self.slices().values()):
            if block.covariance is not None:
                c[sl, sl] = block.covariance
        return c

    def block(self, name: str) -> StateBlock:
        for block in self.blocks:
            if block.spec.name == name:
                return block
        raise KeyError(name)

    def stable_hash(self) -> str:
        payload = {
            'blocks': [b.as_dict() for b in self.blocks],
            'joint_covariance': None if self.joint_covariance is None else self.joint_covariance.tolist(),
            'metadata': dict(self.metadata),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), default=str).encode()
        return hashlib.sha256(raw).hexdigest()

    def as_dict(self) -> dict:
        return {
            'blocks': [b.as_dict() for b in self.blocks],
            'joint_covariance': None if self.joint_covariance is None else self.joint_covariance.tolist(),
            'metadata': dict(self.metadata),
            'state_hash': self.stable_hash(),
        }
