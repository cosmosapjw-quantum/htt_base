"""Shared state incidence and exact product-processing identities for R9."""
from dataclasses import dataclass
import numpy as np
from .r7_contracts import finite_array, content_id


@dataclass(frozen=True)
class ProductIntake:
    product_id: str
    release: str
    source_ids: tuple[str, ...]
    row_ids: tuple[str, ...]
    feature_units: tuple[str, ...]
    frame: str
    epoch: str
    extraction: str
    selection: str
    group: str
    calibration: str
    mask: str
    covariance_source: str | None
    covariance_row_ids: tuple[str, ...] | None
    law_kind: str

    def __post_init__(self):
        for name in ("product_id", "release", "frame", "epoch", "extraction", "selection",
                     "group", "calibration", "mask"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"explicit {name} required (use declared NOT_APPLICABLE where appropriate)")
        for name in ("source_ids", "row_ids", "feature_units"):
            values = tuple(getattr(self, name))
            if not values or not all(isinstance(v, str) and v for v in values):
                raise ValueError(f"nonempty {name} required")
            object.__setattr__(self, name, values)
        if len(set(self.row_ids)) != len(self.row_ids) or len(self.feature_units) != len(self.row_ids):
            raise ValueError("unique rows and their ordered units required")
        if self.covariance_row_ids is not None:
            object.__setattr__(self, "covariance_row_ids", tuple(self.covariance_row_ids))
            if self.covariance_row_ids != self.row_ids:
                raise ValueError("covariance rows must match exact feature order")
        if self.law_kind not in {"KNOWN_GAUSSIAN", "RELEASE_CONDITIONAL_GAUSSIAN",
                                 "ESTIMATED_REQUIRES_CALIBRATION", "SCENARIO_ONLY", "UNAVAILABLE"}:
            raise ValueError("explicit sampling-law kind required")

    @property
    def identity(self):
        return content_id(self)


@dataclass(frozen=True)
class SharedStateEmbedding:
    state_id: str
    state_names: tuple[str, ...]
    state_units: tuple[str, ...]
    state_roles: tuple[str, ...]
    frame: str
    epoch: str
    local_parameter_names: tuple[str, ...]
    local_parameter_units: tuple[str, ...]
    nuisance_names: tuple[str, ...]
    nuisance_units: tuple[str, ...]
    theta_map: np.ndarray
    eta_map: np.ndarray

    def __post_init__(self):
        for name in ("state_names", "state_units", "state_roles", "local_parameter_names",
                     "local_parameter_units", "nuisance_names", "nuisance_units"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        n = len(self.state_names)
        if not self.state_id or not self.frame or not self.epoch or not n:
            raise ValueError("named state/frame/epoch required")
        if len(set(self.state_names)) != n or len(self.state_units) != n or len(self.state_roles) != n:
            raise ValueError("ordered unique state names, units and roles required")
        if set(self.state_roles)-{"OBSERVABLE", "PHYSICAL", "SHARED_NUISANCE", "PRODUCT_NUISANCE", "ANCHOR", "JET"}:
            raise ValueError("state role must distinguish physical, observation and nuisance variables")
        for prefix, map_name in (("local_parameter", "theta_map"), ("nuisance", "eta_map")):
            names = getattr(self, prefix+"_names"); units = getattr(self, prefix+"_units")
            if len(names) != len(units) or len(set(names)) != len(names):
                raise ValueError("unique local variables and their units required")
            a = finite_array(getattr(self, map_name), shape=(len(names), n), name=map_name)
            # This is an incidence adapter, not an implicit unit/frame converter.
            if np.any((a != 0) & (a != 1)) or np.any(a.sum(axis=1) != 1):
                raise ValueError("each local variable maps to exactly one common-state coordinate")
            for i, unit in enumerate(units):
                if unit != self.state_units[int(np.argmax(a[i]))]:
                    raise ValueError("unit conversion must occur explicitly before embedding")
            object.__setattr__(self, map_name, a)

    def split(self, state):
        x = finite_array(state, shape=(len(self.state_names),), name="common state")
        return self.theta_map @ x, self.eta_map @ x

    @property
    def identity(self):
        return content_id(self)
