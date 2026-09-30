"""Signed paired feature transport on the existing R9 depth representation.

This is a linear transformation of one joint input, not independent data or a
time-evolution law. HTT's existing depth_law owns likelihood transformation.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from .depth_path import DepthRepresentation, full_covariance_blocks
from .r7_contracts import NumericalUnresolved
from .typefree_functionals import FunctionalRecord, _array, _text


@dataclass(frozen=True)
class SignedDepthResult:
    status: str
    latent_id: str
    definition_id: str
    transport_definition_id: str
    contrasts: np.ndarray | None = None
    initial_and_contrasts: np.ndarray | None = None
    contrast_covariance: np.ndarray | None = None
    initial_and_contrasts_covariance: np.ndarray | None = None
    signed_coherence: tuple[float | None, ...] = ()
    coherence_statuses: tuple[str, ...] = ()
    covariance_status: str = "COVARIANCE_UNAVAILABLE"
    independent_likelihood: bool = False

    def __post_init__(self):
        for name in ("contrasts", "initial_and_contrasts", "contrast_covariance",
                     "initial_and_contrasts_covariance"):
            if getattr(self, name) is not None:
                object.__setattr__(self, name, _array(getattr(self, name)))


def signed_depth_transport(records, representation, *, transport_definition_id,
                           covariance=None, covariance_blocks=None, frame_transports=None):
    """Transport one same-latent path; retain signs and every cross block.

    The optional covariance is the original full ordered joint covariance.
    Missing covariance affects uncertainty availability, not observed contrasts.
    Nonlinear coherence uncertainty is not inferred from covariance alone.
    """
    rows = tuple(records)
    if not isinstance(representation, DepthRepresentation):
        raise TypeError("DepthRepresentation required")
    if not rows or any(not isinstance(r, FunctionalRecord) for r in rows):
        raise TypeError("nonempty paired FunctionalRecord path required")
    _text(transport_definition_id, "transport_definition_id")
    if len(rows) != len(representation.dimensions):
        raise ValueError("depth block count mismatch")
    if len({r.latent_id for r in rows}) != 1:
        raise ValueError("depth path must retain one shared latent realization")
    definition = rows[0].spec.definition_id
    if any(r.spec.definition_id != definition for r in rows):
        raise ValueError("explicit functional conversion required before transport")
    semantics = lambda r: (r.spec.units, r.spec.basis, r.spec.parity, r.spec.rank,
                            r.spec.normalization, r.spec.perturbative_order, r.spec.branch)
    if any(semantics(r) != semantics(rows[0]) for r in rows[1:]):
        raise ValueError("functional units/basis/parity/channel mismatch")
    labels = tuple(label for r in rows for label in r.spec.coordinate_labels)
    if labels != representation.feature_ids:
        raise ValueError("ordered depth feature identities differ")
    if any(len(r.spec.coordinate_labels) != d for r, d in zip(rows, representation.dimensions)):
        raise ValueError("functional/depth dimensions differ")
    edges = tuple((a.spec.frame, b.spec.frame) for a, b in zip(rows, rows[1:]))
    if frame_transports is not None and tuple(tuple(e) for e in frame_transports) != edges:
        raise ValueError("declared frame transport endpoints differ")
    if any(a != b for a, b in edges) and frame_transports is None:
        raise ValueError("cross-frame transport must explicitly bind its endpoints")
    if covariance is not None and covariance_blocks is not None:
        raise ValueError("supply one original covariance representation")
    if any(r.status != "DEFINED" for r in rows):
        return SignedDepthResult("FUNCTIONAL_INPUT_UNAVAILABLE", rows[0].latent_id,
                                 definition, transport_definition_id)
    vector = np.concatenate([r.difference.reshape(-1) for r in rows])
    h, t = representation.H, representation.T
    c = covariance if covariance is not None else full_covariance_blocks(covariance_blocks, representation.dimensions)
    cstatus = "COVARIANCE_UNAVAILABLE"
    contrast_covariance = anchored_covariance = None
    if c is not None:
        c = _array(c, shape=(len(vector), len(vector)), name="full joint covariance")
        error = 64*len(c)*np.finfo(float).eps*float(np.linalg.norm(c, 2))
        if np.max(np.abs(c-c.T)) > error:
            raise ValueError("joint covariance must be symmetric")
        c = (c+c.T)/2
        eigenvalues = np.linalg.eigvalsh(c)
        if np.min(eigenvalues) < -error:
            raise ValueError("joint covariance must be positive semidefinite")
        if np.any((eigenvalues != 0) & (np.abs(eigenvalues) <= error)):
            raise NumericalUnresolved("joint covariance support is numerically unresolved")
        contrast_covariance, anchored_covariance = h@c@h.T, t@c@t.T
        cstatus = "SUPPLIED_JOINT_COVARIANCE"
    offsets = np.cumsum((0, *representation.dimensions))
    coherence, coherence_status = [], []
    for j, kernel in enumerate(representation.kernels):
        previous = kernel@vector[offsets[j]:offsets[j+1]]
        current = vector[offsets[j+1]:offsets[j+2]]
        left = float(np.max(np.abs(previous), initial=0))
        right = float(np.max(np.abs(current), initial=0))
        if left == 0 or right == 0:
            coherence.append(None)
            coherence_status.append("ZERO_NORM_UNDEFINED")
        elif not math.isfinite(left) or not math.isfinite(right):
            coherence.append(None)
            coherence_status.append("NONFINITE_COHERENCE")
        else:
            # Scale before the norm to avoid overflow for large finite vectors.
            a, b = previous/left, current/right
            value = float((a/np.linalg.norm(a))@(b/np.linalg.norm(b)))
            if not math.isfinite(value):
                coherence.append(None)
                coherence_status.append("NONFINITE_COHERENCE")
            else:
                coherence.append(min(1., max(-1., value)))
                coherence_status.append("DEFINED")
    status = ("SCENARIO_ONLY" if representation.transport_policy != "FIXED_BEFORE_OBSERVATION"
              else "NO_DEPTH_CONTRASTS" if not len(h) else "DEFINED")
    return SignedDepthResult(status, rows[0].latent_id, definition, transport_definition_id,
                             h@vector, t@vector, contrast_covariance, anchored_covariance,
                             tuple(coherence), tuple(coherence_status), cstatus)


__all__ = ["SignedDepthResult", "signed_depth_transport"]
