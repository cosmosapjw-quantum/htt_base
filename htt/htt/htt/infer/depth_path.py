"""HTT-owned model-conditional likelihood adapter for a typed depth path."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum
import hashlib
import json
import math
from numbers import Real
from typing import Sequence

import numpy as np

from common.depth_path import (
    DEPTH_PATH_CLAIM_CEILING,
    DepthCoherenceReport as _DepthCoherenceReport,
    DepthPath,
    DepthPathError,
    ObservableFeatureStep,
)


class DepthHypothesisClass(str, Enum):
    LOCAL_RESPONSE = "LOCAL_RESPONSE"
    GLOBAL_CANDIDATE = "GLOBAL_CANDIDATE"
    SURVEY_SYSTEMATIC = "SURVEY_SYSTEMATIC"
    STRUCTURED_NULL = "STRUCTURED_NULL"


_PREDICTION_TOKEN = object()
_LIKELIHOOD_TOKEN = object()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DepthPathError(f"{name} must be non-empty trimmed text")
    return value


def _real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise DepthPathError(f"{name} must be real")
    result = float(value)
    if not math.isfinite(result):
        raise DepthPathError(f"{name} must be finite")
    return result


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _assert_sealed(payload: object, seal: str, *, name: str) -> None:
    if _sha256_payload(payload) != seal:
        raise DepthPathError(f"{name} identity drifted after construction")


@dataclass(frozen=True)
class DepthModelPrediction:
    prediction_id: str
    path_content_id: str
    model_id: str
    hypothesis_class: DepthHypothesisClass
    stratum_ids: tuple[str, ...]
    feature_names: tuple[tuple[str, ...], ...]
    feature_unit: str
    means: tuple[tuple[float, ...], ...]
    transfer_source: str
    model_config_id: str
    assumptions: tuple[str, ...]
    claim_ceiling: str = DEPTH_PATH_CLAIM_CEILING
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PREDICTION_TOKEN:
            raise DepthPathError("DepthModelPrediction must be factory-built")
        for name in (
            "prediction_id",
            "path_content_id",
            "model_id",
            "feature_unit",
            "transfer_source",
            "model_config_id",
        ):
            _text(getattr(self, name), name)
        if type(self.hypothesis_class) is not DepthHypothesisClass:
            raise DepthPathError(
                "hypothesis_class must use DepthHypothesisClass"
            )
        strata = tuple(_text(value, "stratum_ids") for value in self.stratum_ids)
        if not strata or len(strata) != len(set(strata)):
            raise DepthPathError("stratum_ids must be non-empty and unique")
        names = tuple(
            tuple(_text(value, "feature_names") for value in row)
            for row in self.feature_names
        )
        means = tuple(
            tuple(_real(value, "means") for value in row)
            for row in self.means
        )
        if (
            len(names) != len(strata)
            or len(means) != len(strata)
            or any(not row for row in names)
            or any(len(row) != len(set(row)) for row in names)
            or any(
                len(name_row) != len(mean_row)
                for name_row, mean_row in zip(names, means, strict=True)
            )
        ):
            raise DepthPathError(
                "prediction feature names and means must align by stratum"
            )
        assumptions = tuple(
            _text(value, "assumptions") for value in self.assumptions
        )
        if not assumptions:
            raise DepthPathError("assumptions must not be empty")
        if self.claim_ceiling != DEPTH_PATH_CLAIM_CEILING:
            raise DepthPathError("claim ceiling drifted")
        object.__setattr__(self, "stratum_ids", strata)
        object.__setattr__(self, "feature_names", names)
        object.__setattr__(self, "means", means)
        object.__setattr__(self, "assumptions", assumptions)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "assumptions": list(self.assumptions),
            "claim_ceiling": self.claim_ceiling,
            "feature_names": [list(row) for row in self.feature_names],
            "feature_unit": self.feature_unit,
            "hypothesis_class": self.hypothesis_class.value,
            "means_hex": [
                [value.hex() for value in row] for row in self.means
            ],
            "model_config_id": self.model_config_id,
            "model_id": self.model_id,
            "path_content_id": self.path_content_id,
            "prediction_id": self.prediction_id,
            "schema": "HTT_DEPTH_MODEL_PREDICTION_V1",
            "stratum_ids": list(self.stratum_ids),
            "transfer_source": self.transfer_source,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="depth model prediction",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_depth_model_prediction(
    *,
    prediction_id: str,
    path: DepthPath,
    model_id: str,
    hypothesis_class: DepthHypothesisClass | str,
    means: Sequence[Sequence[object]],
    transfer_source: str,
    model_config_id: str,
    assumptions: Sequence[str],
) -> DepthModelPrediction:
    if type(path) is not DepthPath:
        raise TypeError("path must be an exact DepthPath")
    path.as_payload()
    if isinstance(hypothesis_class, DepthHypothesisClass):
        resolved_class = hypothesis_class
    else:
        try:
            resolved_class = DepthHypothesisClass(str(hypothesis_class))
        except ValueError as exc:
            raise DepthPathError(
                "hypothesis_class must use the registered vocabulary"
            ) from exc
    resolved_means = tuple(tuple(row) for row in means)
    if len(resolved_means) != len(path.strata):
        raise DepthPathError("one prediction vector is required per stratum")
    return DepthModelPrediction(
        prediction_id=prediction_id,
        path_content_id=path.content_id,
        model_id=model_id,
        hypothesis_class=resolved_class,
        stratum_ids=tuple(value.stratum_id for value in path.strata),
        feature_names=tuple(value.feature_names for value in path.strata),
        feature_unit=path.strata[0].feature_unit,
        means=resolved_means,  # type: ignore[arg-type]
        transfer_source=transfer_source,
        model_config_id=model_config_id,
        assumptions=tuple(assumptions),
        _construction_token=_PREDICTION_TOKEN,
    )


@dataclass(frozen=True)
class DepthLikelihoodResult:
    result_id: str
    path_content_id: str
    prediction_content_id: str
    observation_step_content_ids: tuple[str, ...]
    hypothesis_class: DepthHypothesisClass
    per_step_log_likelihood: tuple[float, ...]
    log_likelihood: float
    owner: str = "HTT"
    claim_ceiling: str = DEPTH_PATH_CLAIM_CEILING
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _LIKELIHOOD_TOKEN:
            raise DepthPathError("DepthLikelihoodResult must be factory-built")
        for name in (
            "result_id",
            "path_content_id",
            "prediction_content_id",
        ):
            _text(getattr(self, name), name)
        observation_ids = tuple(
            _text(value, "observation_step_content_ids")
            for value in self.observation_step_content_ids
        )
        if not observation_ids:
            raise DepthPathError(
                "observation_step_content_ids must not be empty"
            )
        if type(self.hypothesis_class) is not DepthHypothesisClass:
            raise DepthPathError(
                "hypothesis_class must use DepthHypothesisClass"
            )
        per_step = tuple(
            _real(value, "per_step_log_likelihood")
            for value in self.per_step_log_likelihood
        )
        total = _real(self.log_likelihood, "log_likelihood")
        if (
            len(per_step) != len(observation_ids)
            or not math.isclose(
                total,
                sum(per_step),
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        ):
            raise DepthPathError(
                "total likelihood must equal the per-step sum"
            )
        if self.owner != "HTT":
            raise DepthPathError("likelihood owner must remain HTT")
        if self.claim_ceiling != DEPTH_PATH_CLAIM_CEILING:
            raise DepthPathError("claim ceiling drifted")
        object.__setattr__(
            self,
            "observation_step_content_ids",
            observation_ids,
        )
        object.__setattr__(self, "per_step_log_likelihood", per_step)
        object.__setattr__(self, "log_likelihood", total)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "claim_ceiling": self.claim_ceiling,
            "hypothesis_class": self.hypothesis_class.value,
            "log_likelihood_hex": self.log_likelihood.hex(),
            "observation_step_content_ids": list(
                self.observation_step_content_ids
            ),
            "owner": self.owner,
            "path_content_id": self.path_content_id,
            "per_step_log_likelihood_hex": [
                value.hex() for value in self.per_step_log_likelihood
            ],
            "prediction_content_id": self.prediction_content_id,
            "result_id": self.result_id,
            "schema": "HTT_DEPTH_LIKELIHOOD_RESULT_V1",
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="depth likelihood result",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def evaluate_depth_path_likelihood(
    *,
    result_id: str,
    path: DepthPath,
    observations: Sequence[ObservableFeatureStep],
    prediction: DepthModelPrediction | _DepthCoherenceReport,
) -> DepthLikelihoodResult:
    """Evaluate one explicit model prediction; MIO reports are refused."""

    if type(path) is not DepthPath:
        raise TypeError("path must be an exact DepthPath")
    path.as_payload()
    if type(prediction) is _DepthCoherenceReport:
        raise DepthPathError(
            "a MIO coherence report is not an HTT model prediction"
        )
    if type(prediction) is not DepthModelPrediction:
        raise TypeError("prediction must be an exact DepthModelPrediction")
    prediction.as_payload()
    resolved_observations = tuple(observations)
    if (
        len(resolved_observations) != len(path.strata)
        or any(
            type(value) is not ObservableFeatureStep
            for value in resolved_observations
        )
    ):
        raise DepthPathError("one exact observation step is required per stratum")
    if (
        prediction.path_content_id != path.content_id
        or prediction.stratum_ids
        != tuple(value.stratum_id for value in path.strata)
        or prediction.feature_names
        != tuple(value.feature_names for value in path.strata)
        or prediction.feature_unit != path.strata[0].feature_unit
    ):
        raise DepthPathError("prediction is not bound to this exact depth path")
    per_step: list[float] = []
    for stratum, observation, mean in zip(
        path.strata,
        resolved_observations,
        prediction.means,
        strict=True,
    ):
        observation.as_payload()
        if (
            observation.stratum_id != stratum.stratum_id
            or observation.stratum_content_id != stratum.content_id
            or observation.feature_names != stratum.feature_names
            or observation.feature_unit != stratum.feature_unit
        ):
            raise DepthPathError(
                "observation is not bound to its exact path stratum"
            )
        covariance = np.asarray(observation.covariance, dtype=float)
        try:
            cholesky = np.linalg.cholesky(covariance)
        except np.linalg.LinAlgError as exc:
            raise DepthPathError(
                "HTT Gaussian likelihood requires positive-definite covariance"
            ) from exc
        log_determinant = 2.0 * float(
            np.sum(np.log(np.diag(cholesky)))
        )
        residual = (
            np.asarray(observation.values, dtype=float)
            - np.asarray(mean, dtype=float)
        )
        whitened = np.linalg.solve(cholesky, residual)
        quadratic = float(whitened @ whitened)
        dimension = residual.size
        per_step.append(
            -0.5
            * (
                quadratic
                + log_determinant
                + dimension * math.log(2.0 * math.pi)
            )
        )
    return DepthLikelihoodResult(
        result_id=result_id,
        path_content_id=path.content_id,
        prediction_content_id=prediction.content_id,
        observation_step_content_ids=tuple(
            value.content_id for value in resolved_observations
        ),
        hypothesis_class=prediction.hypothesis_class,
        per_step_log_likelihood=tuple(per_step),
        log_likelihood=sum(per_step),
        _construction_token=_LIKELIHOOD_TOKEN,
    )


__all__ = [
    "DepthHypothesisClass",
    "DepthLikelihoodResult",
    "DepthModelPrediction",
    "build_depth_model_prediction",
    "evaluate_depth_path_likelihood",
]
