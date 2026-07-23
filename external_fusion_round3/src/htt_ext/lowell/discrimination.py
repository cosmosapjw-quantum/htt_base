from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .poles import angular_separation_deg, mean_axis
from .shells import ShellPoleSimulation


@dataclass(frozen=True)
class PoleSummary:
    features: tuple[float, ...]
    names: tuple[str, ...]

    def as_dict(self) -> dict[str, float]:
        return dict(zip(self.names, self.features, strict=True))


def summarize_simulation(sim: ShellPoleSimulation) -> PoleSummary:
    feats: list[float] = []
    names: list[str] = []
    axis = np.asarray(sim.injected_axis)
    for ell in sim.ells:
        shell = sim.shell_trajectories[ell].pole_array()
        cum = sim.cumulative_trajectories[ell].pole_array()
        remote_mean = mean_axis(shell[1:] if len(shell) > 1 else shell)
        local = cum[-1]
        coherence = float(np.mean(np.abs(shell @ remote_mean)))
        endpoint_remote_angle = angular_separation_deg(local, remote_mean)
        injected_remote_angle = angular_separation_deg(remote_mean, axis)
        cumulative_drift = float(
            np.mean([angular_separation_deg(cum[i], cum[-1]) for i in range(len(cum) - 1)])
            if len(cum) > 1
            else 0.0
        )
        for suffix, value in (
            ("remote_coherence", coherence),
            ("endpoint_remote_angle_deg", endpoint_remote_angle),
            ("injected_remote_angle_deg", injected_remote_angle),
            ("cumulative_drift_deg", cumulative_drift),
        ):
            names.append(f"ell{ell}_{suffix}")
            feats.append(float(value))
    return PoleSummary(tuple(feats), tuple(names))


def fit_centroid_classifier(
    summaries: dict[str, list[PoleSummary]], ridge: float = 1e-6
) -> dict:
    if not summaries:
        raise ValueError("summaries must be non-empty")
    names = next(iter(summaries.values()))[0].names
    classes = sorted(summaries)
    x_by_class = {
        c: np.asarray([s.features for s in summaries[c]], dtype=float) for c in classes
    }
    pooled = np.concatenate(list(x_by_class.values()), axis=0)
    cov = np.cov(pooled, rowvar=False) + ridge * np.eye(pooled.shape[1])
    precision = np.linalg.inv(cov)
    centroids = {c: x_by_class[c].mean(axis=0) for c in classes}
    return {
        "feature_names": list(names),
        "classes": classes,
        "centroids": {k: v.tolist() for k, v in centroids.items()},
        "precision": precision.tolist(),
    }


def classify(summary: PoleSummary, model: dict) -> tuple[str, dict[str, float]]:
    x = np.asarray(summary.features, dtype=float)
    precision = np.asarray(model["precision"], dtype=float)
    scores: dict[str, float] = {}
    for c in model["classes"]:
        d = x - np.asarray(model["centroids"][c], dtype=float)
        scores[c] = float(d @ precision @ d)
    return min(scores, key=scores.get), scores
