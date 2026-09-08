"""R7 serializable observation, method-scope and physical-state contracts.

Likelihood callables and confidence calculations belong to htt.infer.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import json
import math
from typing import Any

import numpy as np


CONVENTIONS = "R7_K_ORTHONORMAL_REAL_OUTWARD_THETA3H_V1"
VERSION = "r7.1"


class NumericalUnresolved(ValueError):
    """A declared numerical error budget cannot resolve this calculation."""


class UnsupportedObservable(NotImplementedError):
    """The named provider does not supply this observable or domain."""


def finite_array(value, *, ndim=None, shape=None, name="array"):
    raw = np.asarray(value)
    if raw.dtype.kind not in "fiu":
        raise ValueError(f"{name} requires real numeric values")
    a = np.array(raw, dtype=float, copy=True)
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{name} must be finite")
    if ndim is not None and a.ndim != ndim:
        raise ValueError(f"{name} requires ndim={ndim}")
    if shape is not None and a.shape != shape:
        raise ValueError(f"{name} requires shape={shape}, got {a.shape}")
    a.setflags(write=False)
    return a


def json_value(value):
    if isinstance(value, np.ndarray): return json_value(value.tolist())
    if isinstance(value, np.generic): return json_value(value.item())
    if isinstance(value,float) and not math.isfinite(value):
        if math.isnan(value): raise ValueError("NaN cannot be a scientific result")
        return {"extended_real":"positive_infinity" if value>0 else "negative_infinity"}
    if isinstance(value, Enum): return value.value
    if hasattr(value, "__dataclass_fields__"): return json_value(asdict(value))
    if isinstance(value, dict): return {str(k): json_value(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [json_value(v) for v in value]
    return value


def content_id(value):
    data = json.dumps(json_value(value), sort_keys=True, separators=(",",":"),
                      allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class ScopeKey:
    experiment_id: str
    law_id: str
    model_id: str
    dataset_ids: tuple[str, ...]
    conventions: str = CONVENTIONS
    version: str = VERSION
    method_id: str = "gaussian_acceptance"
    method_config_id: str = ""

    def __post_init__(self):
        if any(not isinstance(s,str) or not s for s in (
            self.experiment_id,self.law_id,self.model_id,self.conventions,
            self.version,self.method_id,self.method_config_id)):
            raise ValueError("all scope identity fields must be nonempty")
        if not self.dataset_ids or len(set(self.dataset_ids)) != len(self.dataset_ids):
            raise ValueError("dataset identities must be nonempty and unique")
        object.__setattr__(self,"dataset_ids",tuple(self.dataset_ids))

    @property
    def identity(self): return content_id(self)


@dataclass(frozen=True)
class AcceptanceResult:
    inside_support: bool
    quadratic: float | None
    rank: int | None
    threshold: float | None
    accepted: bool
    numeric_status: str


@dataclass(frozen=True)
class ConditionalGaussian:
    mean: np.ndarray
    covariance: np.ndarray
    gain: np.ndarray
    conditioning_rank: int
    numeric_status: str = "RESOLVED"


@dataclass(frozen=True)
class InformationResult:
    old_information: np.ndarray
    new_information: np.ndarray
    gain: np.ndarray
    old_null_directions: np.ndarray
    new_null_directions: np.ndarray
    gain_null_directions: np.ndarray
    numeric_status: str = "RESOLVED"


@dataclass(frozen=True)
class TensorRecord:
    sample_id: str
    retained: np.ndarray
    Q: np.ndarray
    O: np.ndarray
    frame: str
    product_id: str
    release: str
    processing_id: str
    covariance: np.ndarray | None = None
    source_realization_id: str | None = None
    noise_realization_id: str | None = None
    units: str = "K"
    harmonic_layout: str = "ORTHONORMAL_REAL_M0_COS_SIN"
    mask_id: str = "FULL_SKY"
    chart_status: str = "NOT_EVALUATED"
    covariance_id: str | None = None
    covariance_role: str = "MEASUREMENT_COVARIANCE"

    def __post_init__(self):
        for key in ("sample_id","frame","product_id","release","processing_id","mask_id"):
            if not getattr(self,key): raise ValueError(f"TensorRecord needs {key}")
        if self.units != "K" or self.harmonic_layout != "ORTHONORMAL_REAL_M0_COS_SIN":
            raise ValueError("TensorRecord requires K and orthonormal real layout")
        for key,shape in (("retained",(32,)),("Q",(3,3)),("O",(3,3,3))):
            object.__setattr__(self,key,finite_array(getattr(self,key),shape=shape,name=key))
        if self.covariance is not None:
            c = finite_array(self.covariance,ndim=2,name="measurement covariance")
            if c.shape not in {(12,12),(32,32)}: raise ValueError("ordered 12 or 32 covariance required")
            if not self.covariance_id: raise ValueError("measurement covariance needs identity")
            object.__setattr__(self,"covariance",c)


@dataclass(frozen=True)
class RadiationJet:
    theta: float
    tbar: float
    convention: str
    frame: str
    domain_id: str
    q: np.ndarray | None = None
    q_dot: np.ndarray | None = None
    tbar_dot: float | None = None
    grad_d: np.ndarray | None = None
    div_o: np.ndarray | None = None
    curl_d: np.ndarray | None = None
    curl_d_dot: np.ndarray | None = None
    curl_div_q: np.ndarray | None = None
    geodesic: bool = True
    collisionless: bool = True
    approximation: str = "FIRST_ORDER"
    remainder_bound: tuple[float,float] | None = None
    covariance_id: str | None = None


@dataclass(frozen=True)
class PhysicalState:
    shear: np.ndarray | None
    vorticity: np.ndarray | None
    theta: float
    frame: str
    jet_domain: str
    status: str
    assumptions: tuple[str, ...]
    missing: tuple[str, ...] = ()
    acceleration: np.ndarray | None = None
    tilts: dict[str, Any] = field(default_factory=dict)
    curvature: float | None = None


TERMINAL = frozenset({"COMPLETED_SUCCESS","COMPLETED_FAILED_WITH_RECEIPT",
                     "BLOCKED_WITH_RECEIPT","ABANDONED_WITH_RECEIPT"})
OUTCOMES = frozenset({"NOT_EVALUATED","COMPATIBLE","REJECTED_CONJUNCTION",
    "PARTIALLY_IDENTIFIED","NONIDENTIFIED","CONDITIONAL_BOUND","SCENARIO_ONLY",
    "NUMERICALLY_UNRESOLVED","INPUT_UNAVAILABLE","VALIDATION_FAILED"})


@dataclass(frozen=True)
class BranchResult:
    node_id: str
    process_status: str
    scientific_outcome: str
    capabilities: tuple[str, ...] = ()
    scope: dict = field(default_factory=dict)
    evidence: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    valid_estimands: tuple[str, ...] = ()
    uncertainty_type: str = "NONE"
    next_discriminator: str | None = None
    product_results: dict = field(default_factory=dict)
    attempt: int = 1

    def __post_init__(self):
        if self.process_status not in TERMINAL | {"PENDING","RUNNING"}:
            raise ValueError("unknown process status")
        if self.scientific_outcome not in OUTCOMES: raise ValueError("unknown scientific outcome")
        if self.scientific_outcome == "REJECTED_CONJUNCTION" and self.process_status != "COMPLETED_SUCCESS":
            raise ValueError("a computation failure cannot reject a physical model")
        if self.capabilities and not self.evidence:
            raise ValueError("capability outputs require actual validation evidence")


@dataclass(frozen=True)
class UnavailableLaw:
    product_id: str
    outcome: str
    reasons: tuple[str,...]
    controls: dict | None = None
