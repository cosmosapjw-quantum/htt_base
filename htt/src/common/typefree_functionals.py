"""Finite paired functional images and premise-relative body calculations.

These operations consume supplied joint states. They do not create an observed
law, calibrate coverage, identify physical components, or replace legacy scalar
definitions. A finite source is never a continuous-set supremum.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Callable

import numpy as np

from .anchor_geometry import (AnchorBodySpec, AnchorVector, AnchorGeometryKind,
                              AnchorAvailability, evaluate_anchor_gauge)
from .joint_feasible_set import exact_support


def _text(value, name):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{name} must be nonempty trimmed text")
    return value


def _array(value, *, shape=None, ndim=None, name="array"):
    raw = np.asarray(value)
    if raw.dtype.kind not in "fiu":
        raise ValueError(f"{name} must contain real numbers")
    out = np.asarray(raw, dtype=float)
    if not np.isfinite(out).all():
        raise ValueError(f"{name} must be finite")
    if shape is not None and out.shape != shape:
        raise ValueError(f"{name} requires shape {shape}")
    if ndim is not None and out.ndim != ndim:
        raise ValueError(f"{name} requires ndim {ndim}")
    # Immutable owned bytes, rather than a caller-owned read-only view.
    return np.frombuffer(out.tobytes(), dtype=float).reshape(out.shape)


@dataclass(frozen=True)
class FunctionalSpec:
    definition_id: str
    coordinate_labels: tuple[str, ...]
    output_shape: tuple[int, ...]
    rank: int
    parity: str
    basis: str
    units: str
    frame: str
    epoch: str
    domain_id: str
    normalization: str
    perturbative_order: str
    branch: str

    def __post_init__(self):
        for key in ("definition_id", "parity", "basis", "units", "frame", "epoch",
                    "domain_id", "normalization", "perturbative_order", "branch"):
            _text(getattr(self, key), key)
        labels = tuple(self.coordinate_labels)
        if not labels or len(set(labels)) != len(labels):
            raise ValueError("unique nonempty coordinate labels required")
        for label in labels:
            _text(label, "coordinate label")
        shape = tuple(self.output_shape)
        if any(type(d) is not int or d <= 0 for d in shape):
            raise ValueError("output shape requires positive integer dimensions")
        if math.prod(shape) != len(labels):
            raise ValueError("output shape and flattened coordinate labels differ")
        if type(self.rank) is not int or self.rank < 0:
            raise ValueError("nonnegative tensor rank required")
        object.__setattr__(self, "coordinate_labels", labels)
        object.__setattr__(self, "output_shape", shape)

    @property
    def channel_key(self):
        return (self.coordinate_labels, self.frame, self.normalization,
                self.perturbative_order, self.branch)


@dataclass(frozen=True)
class RelativeAnchor:
    """An existing body in a declared orthonormal relative-span embedding.

    A zero-column embedding represents {0} and requires body=None. Other
    missing anchors are represented by missing FunctionalRecord.anchor.
    """
    body_id: str
    coordinate_labels: tuple[str, ...]
    frame: str
    normalization: str
    perturbative_order: str
    branch: str
    embedding: np.ndarray
    body: AnchorBodySpec | None = None

    def __post_init__(self):
        for key in ("body_id", "frame", "normalization", "perturbative_order", "branch"):
            _text(getattr(self, key), key)
        labels = tuple(self.coordinate_labels)
        if not labels or len(set(labels)) != len(labels):
            raise ValueError("unique ambient coordinate labels required")
        for label in labels:
            _text(label, "coordinate label")
        s = _array(self.embedding, ndim=2, name="relative embedding")
        if s.shape[0] != len(labels) or s.shape[1] > s.shape[0]:
            raise ValueError("embedding dimension mismatch")
        r = s.shape[1]
        tolerance = 64 * max(s.shape, default=1) * np.finfo(float).eps
        if not np.allclose(s.T @ s, np.eye(r), rtol=0, atol=tolerance):
            raise ValueError("relative embedding columns must be orthonormal")
        if r:
            if not isinstance(self.body, AnchorBodySpec):
                raise TypeError("nonzero relative span requires AnchorBodySpec")
            if len(self.body.coordinate_labels) != r:
                raise ValueError("relative body dimension mismatch")
            if (self.body.frame, self.body.normalization, self.body.perturbative_order,
                self.body.branch) != (self.frame, self.normalization,
                                     self.perturbative_order, self.branch):
                raise ValueError("relative body channel mismatch")
        elif self.body is not None:
            raise ValueError("zero span must not carry a nonzero-dimensional body")
        object.__setattr__(self, "coordinate_labels", labels)
        object.__setattr__(self, "embedding", s)

    @property
    def channel_key(self):
        return (self.coordinate_labels, self.frame, self.normalization,
                self.perturbative_order, self.branch)


@dataclass(frozen=True)
class FunctionalRecord:
    latent_id: str
    spec: FunctionalSpec
    values: np.ndarray | None
    reference: np.ndarray | None
    anchor: AnchorBodySpec | RelativeAnchor | None = None
    status: str = "DEFINED"

    def __post_init__(self):
        _text(self.latent_id, "latent_id")
        _text(self.status, "status")
        if not isinstance(self.spec, FunctionalSpec):
            raise TypeError("FunctionalSpec required")
        if self.status == "DEFINED":
            if self.values is None or self.reference is None:
                raise ValueError("defined records need values and same-state reference")
            object.__setattr__(self, "values", _array(self.values, shape=self.spec.output_shape))
            object.__setattr__(self, "reference", _array(self.reference, shape=self.spec.output_shape))
        elif self.values is not None or self.reference is not None:
            raise ValueError("unavailable records must not carry numeric substitutes")
        if self.anchor is not None and not isinstance(self.anchor, (AnchorBodySpec, RelativeAnchor)):
            raise TypeError("typed anchor required")

    @property
    def difference(self):
        if self.status != "DEFINED":
            return None
        return _array(self.values - self.reference)


@dataclass(frozen=True)
class AnchorEvaluation:
    latent_id: str
    definition_id: str
    status: str
    gauge: float | None = None
    margin: float | None = None
    member: bool | None = None


def _relative_coordinates(anchor, value):
    if not isinstance(anchor, RelativeAnchor):
        return "DEFINED", anchor, value
    s = anchor.embedding
    if s.shape[1] == 0:
        return ("NO_DIRECTIONS" if np.all(value == 0) else "OUTSIDE_RELATIVE_SPAN"), None, None
    coordinates = s.T @ value
    if s.shape[1] < s.shape[0]:
        residual = float(np.linalg.norm(value - s @ coordinates))
        error = 128 * max(s.shape) * np.finfo(float).eps * float(np.linalg.norm(value))
        if residual:
            status = "NUMERICALLY_UNRESOLVED" if residual <= error else "OUTSIDE_RELATIVE_SPAN"
            return status, None, None
    return "DEFINED", anchor.body, coordinates


def evaluate_paired_anchor(record):
    if not isinstance(record, FunctionalRecord):
        raise TypeError("FunctionalRecord required")
    args = (record.latent_id, record.spec.definition_id)
    if record.status != "DEFINED":
        return AnchorEvaluation(*args, record.status)
    if record.anchor is None:
        return AnchorEvaluation(*args, "MISSING_ANCHOR")
    if record.spec.channel_key != record.anchor.channel_key:
        return AnchorEvaluation(*args, "CHANNEL_MISMATCH")
    status, body, y = _relative_coordinates(record.anchor, record.difference.reshape(-1))
    if status == "NO_DIRECTIONS":
        return AnchorEvaluation(*args, status, 0.0, 1.0, True)
    if status != "DEFINED":
        return AnchorEvaluation(*args, status)
    vector = AnchorVector(record.latent_id, body.coordinate_labels, tuple(y),
                          body.frame, body.normalization, body.perturbative_order, body.branch)
    result = evaluate_anchor_gauge(body, vector)
    if result.lower is None:
        return AnchorEvaluation(*args, result.status.value)
    return AnchorEvaluation(*args, "DEFINED", result.lower, 1-result.lower, result.lower <= 1)


def _fraction_rank(rows):
    a = [list(row) for row in rows]
    rank = 0
    for col in range(len(a[0]) if a else 0):
        pivot = next((i for i in range(rank, len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        pivot_value = a[rank][col]
        a[rank] = [x/pivot_value for x in a[rank]]
        for i in range(rank+1, len(a)):
            f = a[i][col]
            a[i] = [x-f*y for x, y in zip(a[i], a[rank])]
        rank += 1
    return rank


def anchor_support(body, direction):
    """Support of the existing supported body classes in their own coordinates.

    Exact polytope arithmetic encloses no preprocessing uncertainty. Its
    boundedness follows only after exact opposite-normal and rank checks.
    """
    if not isinstance(body, AnchorBodySpec):
        raise TypeError("AnchorBodySpec required")
    u = _array(direction, shape=(len(body.coordinate_labels),))
    if body.availability is not AnchorAvailability.AVAILABLE:
        return None
    if body.geometry is AnchorGeometryKind.PRODUCT_BLOCK_BALL:
        if any(b.availability is not AnchorAvailability.AVAILABLE for b in body.blocks):
            return None
        return math.fsum(b.radius * float(np.linalg.norm(u[list(b.coordinate_indices)])) for b in body.blocks)
    if body.geometry is AnchorGeometryKind.ELLIPSOID:
        q = np.asarray(body.quadratic_form)
        value = float(u @ np.linalg.solve(q, u))
        return math.sqrt(max(value, 0.0))
    a = [tuple(Fraction(float(x)) for x in h.normal) for h in body.halfspaces]
    b = [Fraction(float(h.bound)) for h in body.halfspaces]
    rows = set(zip(a, b))
    if any((tuple(-x for x in row), bound) not in rows for row, bound in rows):
        raise ValueError("exact symmetric normals required for rational bounded-support adapter")
    if _fraction_rank(a) != len(u):
        raise ValueError("polytope exact boundedness is unresolved")
    return float(exact_support([Fraction(float(x)) for x in u], a, b)["exact_hi"])


@dataclass(frozen=True)
class SupportUtilization:
    status: str
    numerator: float | None = None
    support: float | None = None
    value: float | None = None


def support_utilization(record, direction):
    evaluation = evaluate_paired_anchor(record)
    u = _array(direction, shape=(len(record.spec.coordinate_labels),))
    if evaluation.status != "DEFINED":
        return SupportUtilization(evaluation.status)
    body = record.anchor
    if isinstance(body, RelativeAnchor):
        u = body.embedding.T @ u
        y = body.embedding.T @ record.difference.reshape(-1)
        body = body.body
    else:
        y = record.difference.reshape(-1)
    denominator = anchor_support(body, u)
    if denominator is None:
        return SupportUtilization("ANCHOR_UNAVAILABLE")
    if not math.isfinite(denominator):
        return SupportUtilization("NONFINITE_SUPPORT")
    if denominator <= 0:
        return SupportUtilization("ZERO_SUPPORT_DIRECTION", float(u @ y), denominator)
    numerator = float(u @ y)
    value = numerator / denominator
    if not math.isfinite(value):
        return SupportUtilization("NONFINITE_UTILIZATION")
    return SupportUtilization("DEFINED", numerator, denominator, value)


@dataclass(frozen=True)
class UndefinedValue:
    status: str
    reason: str = ""

    def __post_init__(self):
        _text(self.status, "undefined status")
        if self.status == "DEFINED":
            raise ValueError("undefined output cannot be marked DEFINED")


@dataclass(frozen=True)
class FiniteJointSource:
    joint_id: str
    records: tuple[FunctionalRecord, ...]
    law_kind: str
    domain_id: str
    weights: tuple[float, ...] | None = None

    def __post_init__(self):
        _text(self.joint_id, "joint_id")
        _text(self.domain_id, "domain_id")
        if self.law_kind not in {"EMPIRICAL", "SAMPLING", "NULL", "POSTERIOR", "FINITE_SET"}:
            raise ValueError("explicit supported finite source kind required")
        records = tuple(self.records)
        if any(not isinstance(r, FunctionalRecord) for r in records):
            raise TypeError("paired functional records required")
        if len({r.latent_id for r in records}) != len(records):
            raise ValueError("duplicate latent IDs in joint source")
        if records and any(r.spec != records[0].spec for r in records[1:]):
            raise ValueError("a functional image requires one common definition/channel")
        if self.law_kind == "FINITE_SET":
            if self.weights is not None:
                raise ValueError("set images do not have probability weights")
        else:
            if not records:
                raise ValueError("an empty source is not a probability law")
            raw = np.ones(len(records)) if self.weights is None else _array(self.weights, shape=(len(records),))
            if np.any(raw < 0):
                raise ValueError("nonnegative source weights required")
            total = math.fsum(float(w) for w in raw)
            if not math.isfinite(total) or total <= 0:
                raise ValueError("finite positive total source weight required")
            object.__setattr__(self, "weights", tuple(float(w)/total for w in raw))
        object.__setattr__(self, "records", records)


@dataclass(frozen=True)
class ImageAtom:
    latent_id: str
    value: np.ndarray | None
    mass: float | None
    status: str

    def __post_init__(self):
        _text(self.latent_id, "latent_id")
        _text(self.status, "atom status")
        if self.mass is not None and (isinstance(self.mass, bool) or
                not math.isfinite(float(self.mass)) or not 0 <= self.mass <= 1):
            raise ValueError("atom mass must be finite and in [0,1]")
        if self.status == "DEFINED":
            object.__setattr__(self, "value", _array(self.value))
        elif self.value is not None:
            raise ValueError("undefined atom must retain no numeric substitute")


@dataclass(frozen=True)
class FiniteFunctionalImage:
    joint_id: str
    law_kind: str
    source_domain_id: str
    target_domain_id: str
    definition_id: str
    atoms: tuple[ImageAtom, ...]
    status: str

    def __post_init__(self):
        for key in ("joint_id", "source_domain_id", "target_domain_id", "definition_id"):
            _text(getattr(self, key), key)
        if self.law_kind not in {"EMPIRICAL", "SAMPLING", "NULL", "POSTERIOR", "FINITE_SET"}:
            raise ValueError("explicit supported finite source kind required")
        atoms = tuple(self.atoms)
        if any(not isinstance(a, ImageAtom) for a in atoms):
            raise TypeError("typed image atoms required")
        if len({a.latent_id for a in atoms}) != len(atoms):
            raise ValueError("duplicate output latent IDs")
        shapes = {a.value.shape for a in atoms if a.status == "DEFINED"}
        if len(shapes) > 1:
            raise ValueError("one image requires one output shape")
        if self.law_kind == "FINITE_SET":
            if any(a.mass is not None for a in atoms):
                raise ValueError("set image atoms must not carry probability mass")
        elif (not atoms or any(a.mass is None for a in atoms) or
              abs(math.fsum(a.mass for a in atoms)-1) > 16*np.finfo(float).eps*len(atoms)):
            raise ValueError("full original probability mass must be retained")
        expected = ("EMPTY_SET" if not atoms else "PARTIALLY_UNDEFINED"
                    if any(a.status != "DEFINED" for a in atoms) else "DEFINED")
        if self.status != expected:
            raise ValueError("image status differs from retained atoms")
        object.__setattr__(self, "atoms", atoms)

    @property
    def undefined_mass(self):
        if self.law_kind == "FINITE_SET":
            return None
        return math.fsum(a.mass for a in self.atoms if a.status != "DEFINED")


def finite_joint_pushforward(source, transform: Callable, *, definition_id, target_domain_id):
    """Map each supplied atom once; undefined atoms retain original mass."""
    if not isinstance(source, FiniteJointSource):
        raise TypeError("FiniteJointSource required")
    _text(definition_id, "definition_id")
    _text(target_domain_id, "target_domain_id")
    atoms = []
    output_shape = None
    for i, record in enumerate(source.records):
        value = transform(record) if record.status == "DEFINED" else UndefinedValue(record.status)
        if isinstance(value, UndefinedValue):
            status, numeric = value.status, None
        else:
            raw = np.asarray(value)
            if raw.dtype.kind not in "fiu":
                raise ValueError("transform must return real values or UndefinedValue")
            if not np.isfinite(raw).all():
                status, numeric = "NONFINITE_TRANSFORM", None
            else:
                numeric = _array(value)
                if output_shape is not None and numeric.shape != output_shape:
                    raise ValueError("one functional image must have a common output shape")
                output_shape = numeric.shape
                status = "DEFINED"
        mass = None if source.weights is None else source.weights[i]
        atoms.append(ImageAtom(record.latent_id, numeric, mass, status))
    status = ("EMPTY_SET" if not atoms else
              "PARTIALLY_UNDEFINED" if any(a.status != "DEFINED" for a in atoms) else "DEFINED")
    return FiniteFunctionalImage(source.joint_id, source.law_kind, source.domain_id,
                                 target_domain_id, definition_id, tuple(atoms), status)


def ratio_value(numerator, denominator, *, positive_denominator=False):
    """Pointwise ratio with explicit undefined branch, no denominator floor."""
    n, d = np.broadcast_arrays(np.asarray(numerator), np.asarray(denominator))
    if n.dtype.kind not in "fiu" or d.dtype.kind not in "fiu":
        raise ValueError("ratio requires real numeric inputs")
    if not np.isfinite(n).all() or not np.isfinite(d).all():
        return UndefinedValue("NONFINITE_RATIO_INPUT")
    invalid_domain = np.any(d <= 0) if positive_denominator else np.any(d == 0)
    if invalid_domain:
        return UndefinedValue("OUTSIDE_POSITIVE_DENOMINATOR_DOMAIN" if positive_denominator else "ZERO_DENOMINATOR")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        result = n / d
    return result if np.isfinite(result).all() else UndefinedValue("NONFINITE_RATIO_OUTPUT")


@dataclass(frozen=True)
class ExceedanceMass:
    threshold: float
    scalarization_id: str
    known_exceedance_mass: float
    undefined_mass: float
    lower: float
    upper: float
    rule: str = "value > threshold"


def strict_exceedance(image, threshold, *, scalarization=None, scalarization_id=None):
    if not isinstance(image, FiniteFunctionalImage) or image.law_kind == "FINITE_SET":
        raise TypeError("a finite probability-law image is required")
    if isinstance(threshold, bool) or not math.isfinite(float(threshold)):
        raise ValueError("finite real threshold required")
    identity = image.definition_id if scalarization is None else _text(scalarization_id, "scalarization_id")
    known, undefined = [], []
    for atom in image.atoms:
        if atom.status != "DEFINED":
            undefined.append(atom.mass)
            continue
        value = atom.value if scalarization is None else scalarization(atom.value)
        if isinstance(value, UndefinedValue):
            undefined.append(atom.mass)
            continue
        raw = np.asarray(value)
        if raw.size != 1 or raw.dtype.kind not in "fiu":
            raise ValueError("explicit real scalarization required for vector/tensor output")
        scalar = float(raw.reshape(-1)[0])
        if not math.isfinite(scalar):
            undefined.append(atom.mass)
        elif scalar > threshold:
            known.append(atom.mass)
    p, q = math.fsum(known), math.fsum(undefined)
    return ExceedanceMass(float(threshold), identity, p, q, p, min(1.0, p+q))


__all__ = ["FunctionalSpec", "FunctionalRecord", "RelativeAnchor", "AnchorEvaluation",
           "evaluate_paired_anchor", "anchor_support", "support_utilization", "SupportUtilization",
           "UndefinedValue", "FiniteJointSource", "FiniteFunctionalImage", "ImageAtom",
           "finite_joint_pushforward", "ratio_value", "strict_exceedance", "ExceedanceMass"]
