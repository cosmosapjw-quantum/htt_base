"""PA-6 runtime constraint-residual reporter.

The audit (R17-P3) found that constraint residuals (Gauss, Codazzi,
Jacobi, twice-contracted Bianchi) are computed during background
integration and bundled into :class:`BackgroundResidualSummary` —
**but** the summary is produced only at end-of-run and never emits
per-η-checkpoint records, so a constraint that grows mid-trajectory
without violating the end-of-run threshold goes silently unreported.

This module exposes:

- :class:`ConstraintCheckpointRecord` — per-η residual snapshot.
- :class:`ConstraintResidualReport` — full report with thresholded
  flags and the worst-η index for each constraint family.
- :func:`build_constraint_residual_report` — non-destructive analyzer
  that takes a finished :class:`BackgroundEvolutionResult` and emits
  the report.
- :func:`write_constraint_residual_report` — sidecar JSON writer for
  the ver3 archive.

The reporter is **non-destructive**: it neither modifies integrator
state nor changes the integration tolerance. It's purely an
observer pattern over the residual history. CI can grep the JSON
output for ``threshold_breaches`` to fail builds on regression.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np

from bass.background.evolution import (
    BackgroundEvolutionResult,
    BackgroundResidualSummary,
    summarize_background_residuals,
)

__all__ = [
    "ConstraintCheckpointRecord",
    "ConstraintResidualReport",
    "DEFAULT_CONSTRAINT_THRESHOLDS",
    "build_constraint_residual_report",
    "write_constraint_residual_report",
]


#: Default per-constraint normalised thresholds.
#:
#: Values are conservative: at the BASS Round-15 P0 baseline the
#: Bianchi-I orthogonal trajectory holds Gauss/Codazzi/Bianchi residuals
#: below 1e-9 in dimensionless H² units. We set the gate at 1e-6 so
#: numerical noise (LSODA step adaptation) does not trigger false
#: positives but a *real* algebraic regression (sign flip, missing term)
#: triggers reliably.
DEFAULT_CONSTRAINT_THRESHOLDS: Mapping[str, float] = {
    "gauss_over_H2_ref": 1.0e-6,
    "codazzi_over_H2_ref": 1.0e-6,
    "jacobi_over_structure_ref": 1.0e-6,
    "bianchi_over_H2_ref": 1.0e-6,
}


@dataclass(frozen=True)
class ConstraintCheckpointRecord:
    """One η-grid sample of normalised constraint residuals."""

    eta_index: int
    eta: float
    H: float
    gauss_over_H2_ref: float
    codazzi_over_H2_ref: float
    jacobi_over_structure_ref: float
    bianchi_over_H2_ref: float

    def as_payload(self) -> dict[str, float | int]:
        return {
            "eta_index": int(self.eta_index),
            "eta": float(self.eta),
            "H": float(self.H),
            "gauss_over_H2_ref": float(self.gauss_over_H2_ref),
            "codazzi_over_H2_ref": float(self.codazzi_over_H2_ref),
            "jacobi_over_structure_ref": float(self.jacobi_over_structure_ref),
            "bianchi_over_H2_ref": float(self.bianchi_over_H2_ref),
        }


@dataclass(frozen=True)
class ConstraintResidualReport:
    """Per-η-checkpoint constraint report with threshold flags."""

    family: str
    branch: str
    H_reference: float
    structure_reference: float
    samples: int
    thresholds: Mapping[str, float]
    summary: BackgroundResidualSummary
    checkpoints: tuple[ConstraintCheckpointRecord, ...]
    worst_eta_index: Mapping[str, int]
    threshold_breaches: Mapping[str, int]
    passed: bool
    metadata: Mapping[str, object] = field(default_factory=dict)

    def as_payload(self) -> dict[str, object]:
        return {
            "family": str(self.family),
            "branch": str(self.branch),
            "H_reference": float(self.H_reference),
            "structure_reference": float(self.structure_reference),
            "samples": int(self.samples),
            "thresholds": {k: float(v) for k, v in self.thresholds.items()},
            "summary": {
                "samples": int(self.summary.samples),
                "gauss_max_over_H2_ref": float(self.summary.gauss_max_over_H2_ref),
                "codazzi_max_over_H2_ref": float(
                    self.summary.codazzi_max_over_H2_ref
                ),
                "jacobi_max_over_structure_ref": float(
                    self.summary.jacobi_max_over_structure_ref
                ),
                "bianchi_max_over_H2_ref": float(
                    self.summary.bianchi_max_over_H2_ref
                ),
            },
            "checkpoints": [cp.as_payload() for cp in self.checkpoints],
            "worst_eta_index": {k: int(v) for k, v in self.worst_eta_index.items()},
            "threshold_breaches": {
                k: int(v) for k, v in self.threshold_breaches.items()
            },
            "passed": bool(self.passed),
            "metadata": dict(self.metadata),
        }


def _select_checkpoint_indices(n: int, max_records: int) -> Iterable[int]:
    if n <= 0:
        return ()
    if n <= max_records:
        return tuple(range(n))
    return tuple(int(i) for i in np.linspace(0, n - 1, max_records, dtype=int))


def build_constraint_residual_report(
    result: BackgroundEvolutionResult,
    *,
    family: str = "I",
    branch: str | None = None,
    thresholds: Mapping[str, float] | None = None,
    max_records: int = 64,
    metadata: Mapping[str, object] | None = None,
) -> ConstraintResidualReport:
    """Analyse a background trajectory and return a per-η residual report.

    Parameters
    ----------
    result
        Finished :class:`BackgroundEvolutionResult` from
        :func:`solve_background_evolution`.
    family
        Bianchi family label for metadata (default ``"I"``).
    branch
        Orthogonal vs tilted (defaults to
        ``result.initial_conditions.metadata.branch`` when available).
    thresholds
        Per-constraint normalised thresholds; falls back to
        :data:`DEFAULT_CONSTRAINT_THRESHOLDS`.
    max_records
        Maximum number of checkpoint records to emit (sub-sampled
        uniformly when the trajectory has more samples). 0 disables
        checkpoints.
    metadata
        Additional fields to attach to the report's metadata dict.

    Returns
    -------
    ConstraintResidualReport
        Threshold-flagged report ready for sidecar emission.
    """
    summary = summarize_background_residuals(result)
    H_ref = max(float(np.max(np.abs(result.H))), 1.0e-30)
    H2_ref = H_ref * H_ref
    structure_ref = max(
        float(np.linalg.norm(result.initial_conditions.algebra.C)),
        1.0e-30,
    )
    n = len(result.residuals)
    indices = tuple(_select_checkpoint_indices(n, max_records))
    eta = np.asarray(result.eta, dtype=np.float64) if hasattr(result, "eta") else np.arange(n, dtype=np.float64)
    if eta.size != n:
        # Fall back to integer index as η when the result does not expose
        # a real-eta array.
        eta = np.arange(n, dtype=np.float64)

    checkpoints: list[ConstraintCheckpointRecord] = []
    gauss_arr = np.asarray(
        [abs(res.gauss) for res in result.residuals], dtype=np.float64
    )
    codazzi_arr = np.asarray(
        [float(np.linalg.norm(res.codazzi)) for res in result.residuals],
        dtype=np.float64,
    )
    jacobi_arr = np.asarray(
        [float(np.linalg.norm(res.jacobi)) for res in result.residuals],
        dtype=np.float64,
    )
    bianchi_arr = np.asarray(
        [
            float(np.linalg.norm(res.twice_contracted_bianchi))
            for res in result.residuals
        ],
        dtype=np.float64,
    )

    H_arr = np.asarray(result.H, dtype=np.float64)
    H_arr = H_arr if H_arr.size == n else np.full(n, H_ref, dtype=np.float64)

    for idx in indices:
        i = int(idx)
        checkpoints.append(
            ConstraintCheckpointRecord(
                eta_index=i,
                eta=float(eta[i]),
                H=float(H_arr[i]),
                gauss_over_H2_ref=float(gauss_arr[i] / H2_ref),
                codazzi_over_H2_ref=float(codazzi_arr[i] / H2_ref),
                jacobi_over_structure_ref=float(jacobi_arr[i] / structure_ref),
                bianchi_over_H2_ref=float(bianchi_arr[i] / H2_ref),
            )
        )

    worst: dict[str, int] = {
        "gauss_over_H2_ref": int(np.argmax(gauss_arr)) if n else 0,
        "codazzi_over_H2_ref": int(np.argmax(codazzi_arr)) if n else 0,
        "jacobi_over_structure_ref": int(np.argmax(jacobi_arr)) if n else 0,
        "bianchi_over_H2_ref": int(np.argmax(bianchi_arr)) if n else 0,
    }

    th = dict(DEFAULT_CONSTRAINT_THRESHOLDS) if thresholds is None else dict(thresholds)
    breaches: dict[str, int] = {}
    breaches["gauss_over_H2_ref"] = int(
        np.sum((gauss_arr / H2_ref) > th["gauss_over_H2_ref"])
    )
    breaches["codazzi_over_H2_ref"] = int(
        np.sum((codazzi_arr / H2_ref) > th["codazzi_over_H2_ref"])
    )
    breaches["jacobi_over_structure_ref"] = int(
        np.sum((jacobi_arr / structure_ref) > th["jacobi_over_structure_ref"])
    )
    breaches["bianchi_over_H2_ref"] = int(
        np.sum((bianchi_arr / H2_ref) > th["bianchi_over_H2_ref"])
    )
    passed = all(v == 0 for v in breaches.values())

    detected_branch = branch
    if detected_branch is None:
        detected_branch = str(getattr(result, "branch", "orthogonal"))

    return ConstraintResidualReport(
        family=str(family),
        branch=str(detected_branch),
        H_reference=H_ref,
        structure_reference=structure_ref,
        samples=n,
        thresholds=th,
        summary=summary,
        checkpoints=tuple(checkpoints),
        worst_eta_index=worst,
        threshold_breaches=breaches,
        passed=passed,
        metadata=dict(metadata or {}),
    )


def write_constraint_residual_report(
    report: ConstraintResidualReport,
    outdir: str | Path,
    *,
    filename: str = "constraint_residual_report.json",
) -> str:
    """Write the report as a sidecar JSON file next to the archive."""
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / filename
    path.write_text(
        json.dumps(report.as_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return str(path)
