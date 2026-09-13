"""R9 fixed feature paths; linear representations, not independent data.

D1/D3 of tensor_joint_r9/revision2/THEORY_EXTENSION.md. The historical
6bafca66 donor is not imported: this module feeds the current R7 law API.
No Gaussian, innovation, calibration, or physical interpretation is inferred.
"""
from dataclasses import dataclass
import numpy as np
from .r7_contracts import finite_array, content_id


@dataclass(frozen=True)
class DepthRepresentation:
    dimensions: tuple[int, ...]
    kernels: tuple[np.ndarray, ...]
    feature_ids: tuple[str, ...]
    procedure_id: str
    transport_policy: str = "FIXED_BEFORE_OBSERVATION"

    def __post_init__(self):
        dims = tuple(self.dimensions)
        ids = tuple(self.feature_ids)
        if not dims or any(type(d) is not int or d <= 0 for d in dims):
            raise ValueError("positive integer feature block dimensions required")
        if len(ids) != sum(dims) or len(set(ids)) != len(ids) or not all(ids):
            raise ValueError("unique ordered feature identities required")
        if len(self.kernels) != len(dims)-1 or not self.procedure_id:
            raise ValueError("one transport per adjacent block and a procedure required")
        if self.transport_policy not in {"FIXED_BEFORE_OBSERVATION", "FITTED_REQUIRES_JOINT_LAW"}:
            raise ValueError("explicit transport policy required")
        kernels = tuple(finite_array(k, shape=(dims[j+1], dims[j]), name="transport")
                        for j, k in enumerate(self.kernels))
        object.__setattr__(self, "dimensions", dims)
        object.__setattr__(self, "feature_ids", ids)
        object.__setattr__(self, "kernels", kernels)

    @property
    def identity(self):
        return content_id(self)

    @property
    def H(self):
        offsets = np.cumsum((0, *self.dimensions))
        h = np.zeros((sum(self.dimensions[1:]), sum(self.dimensions)))
        row = 0
        for j, k in enumerate(self.kernels):
            end = row + self.dimensions[j+1]
            h[row:end, offsets[j]:offsets[j+1]] = -k
            h[row:end, offsets[j+1]:offsets[j+2]] = np.eye(self.dimensions[j+1])
            row = end
        return h

    @property
    def T(self):
        return np.vstack((np.eye(sum(self.dimensions))[:self.dimensions[0]], self.H))

    def restore(self, anchored):
        y = finite_array(anchored, shape=(sum(self.dimensions),)).copy()
        offsets = np.cumsum((0, *self.dimensions))
        for j, k in enumerate(self.kernels):
            y[offsets[j+1]:offsets[j+2]] += k @ y[offsets[j]:offsets[j+1]]
        return y


def full_covariance_blocks(blocks, dimensions):
    """A missing block returns None; known zero cross covariance is explicit.

    All ordered blocks (including transposes) are required so no independence
    assumption is silently inserted. PSD/support validation belongs to the law.
    """
    dims = tuple(dimensions)
    if not dims or any(type(d) is not int or d <= 0 for d in dims):
        raise ValueError("positive block dimensions required")
    if blocks is None:
        return None
    if set(blocks)-{(j, k) for j in range(len(dims)) for k in range(len(dims))}:
        raise ValueError("unexpected covariance block")
    if any(blocks.get((j, k)) is None for j in range(len(dims)) for k in range(len(dims))):
        return None
    return np.block([[finite_array(blocks[j, k], shape=(dj, dk))
                      for k, dk in enumerate(dims)] for j, dj in enumerate(dims)])
