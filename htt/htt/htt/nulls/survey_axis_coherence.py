"""Survey-axis coherent PR-062 null generator."""
from __future__ import annotations

import math

import numpy as np

from htt.nulls.local_boost_depth_null import (
    _angle_deg,
    DepthNullSample,
    LocalBoostNullConfig,
)
from htt.nulls.selection_response_depth import (
    SelectionResponseDepthNull,
    SelectionResponseMetadata,
    SurveyAxisMetadata,
    SurveySystematicNullMockBank,
)


def _axis_tangent_basis(axis: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    reference = np.asarray((0.0, 0.0, 1.0), dtype=float)
    if abs(float(axis @ reference)) > 0.9:
        reference = np.asarray((0.0, 1.0, 0.0), dtype=float)
    first = np.cross(axis, reference)
    first = first / float(np.linalg.norm(first))
    second = np.cross(axis, first)
    second = second / float(np.linalg.norm(second))
    return first, second


class SurveyAxisCoherenceNull(SelectionResponseDepthNull):
    """Generate survey-axis coherent direction/depth systematic mocks."""

    null_model_id = "survey_axis_coherence"
    physical_scope = "observer_side_survey_axis"
    null_model_scope = "survey_axis_coherence_null"
    amplitude_multiplier = 1.15
    jitter_multiplier = 0.55

    def __init__(
        self,
        config: LocalBoostNullConfig,
        *,
        selection_metadata: SelectionResponseMetadata,
        survey_axis_metadata: SurveyAxisMetadata,
    ) -> None:
        super().__init__(config, selection_metadata=selection_metadata)
        if not isinstance(survey_axis_metadata, SurveyAxisMetadata):
            raise TypeError("survey_axis_metadata must be a SurveyAxisMetadata")
        self.survey_axis_metadata = survey_axis_metadata

    def _base_axis(self) -> np.ndarray:
        return np.asarray(self.survey_axis_metadata.survey_axis, dtype=float)

    def _sample_direction(
        self,
        rng: np.random.Generator,
        base_axis: np.ndarray,
        depth_index: int,
    ) -> np.ndarray:
        first, second = _axis_tangent_basis(base_axis)
        phase = float(rng.vonmises(0.0, 16.0))
        radius = abs(
            rng.normal(
                0.0,
                self.config.direction_jitter_sigma
                * self.jitter_multiplier
                * (1.0 + 0.12 * depth_index),
            )
        )
        vector = base_axis + radius * (math.cos(phase) * first + math.sin(phase) * second)
        norm = float(np.linalg.norm(vector))
        if norm <= 0.0:
            return base_axis
        return vector / norm

    def _beta_for_depth(
        self,
        rng: np.random.Generator,
        amplitude: float,
        response_weight: float,
        depth_index: int,
    ) -> float:
        coherence_boost = 1.0 + 0.08 * depth_index
        beta_center = amplitude * response_weight * coherence_boost
        beta_noise = rng.normal(0.0, self.config.amplitude_beta_sigma * 0.05)
        return max(beta_center + beta_noise, 0.0)

    def generate(self) -> SurveySystematicNullMockBank:
        samples: list[DepthNullSample] = []
        target = np.asarray(self.config.target_direction, dtype=float)
        base_axis = self._base_axis()
        for mock_index in range(self.config.n_mocks):
            mock_seed = int(self.config.seed + mock_index)
            rng = np.random.default_rng(mock_seed)
            amplitude = max(
                rng.normal(
                    self.config.amplitude_beta_mean * self.amplitude_multiplier,
                    self.config.amplitude_beta_sigma * self.amplitude_multiplier,
                ),
                0.0,
            )
            for depth_index, bin_spec in enumerate(self.config.depth_bins):
                direction = self._sample_direction(rng, base_axis, depth_index)
                beta = self._beta_for_depth(
                    rng,
                    amplitude,
                    bin_spec.response_weight,
                    depth_index,
                )
                log_g_f = float((beta / self.config.gf_beta_scale) ** 2)
                g_f = float(math.exp(min(log_g_f, 60.0)))
                angle = _angle_deg(direction, target)
                triggered = (
                    g_f >= self.config.gf_threshold
                    and angle <= self.config.direction_threshold_deg
                )
                samples.append(
                    DepthNullSample(
                        mock_index=mock_index,
                        seed=mock_seed,
                        depth_label=bin_spec.label,
                        z_mid=bin_spec.z_mid,
                        distance_mpc_mid=bin_spec.distance_mpc_mid,
                        beta=beta,
                        log_g_f=log_g_f,
                        g_f=g_f,
                        direction_unit_vector=tuple(float(item) for item in direction),
                        angular_separation_deg=angle,
                        triggered=triggered,
                    )
                )
        return SurveySystematicNullMockBank(
            null_model_id=self.null_model_id,
            config=self.config,
            selection_metadata=self.selection_metadata,
            survey_axis_metadata=self.survey_axis_metadata,
            samples=tuple(samples),
            physical_scope=self.physical_scope,
            null_model_scope=self.null_model_scope,
        )


__all__ = ["SurveyAxisCoherenceNull"]
