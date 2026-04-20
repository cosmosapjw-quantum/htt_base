"""Thermodynamic-integration Bayes-factor helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from bass.inference.drivers.emcee_driver import PosteriorSample


@dataclass(frozen=True)
class BayesFactorResult:
    """Evidence-ratio result and provenance payload."""

    ln_B: float
    ln_B_err: float
    method: str
    provenance: dict[str, Any]


def _posterior_evidence(posterior: PosteriorSample) -> tuple[float, float, str]:
    ti = dict(posterior.config.get("thermodynamic_integration", {}))
    if {"ln_Z", "ln_Z_err"} <= ti.keys():
        return float(ti["ln_Z"]), float(ti["ln_Z_err"]), "thermodynamic"
    if {"ln_Z", "ln_Z_err"} <= posterior.config.keys():
        return (
            float(posterior.config["ln_Z"]),
            float(posterior.config["ln_Z_err"]),
            str(posterior.config.get("evidence_method", "nested")),
        )
    raise ValueError("posterior is missing evidence metadata")


def bayes_factor(
    posterior_A: PosteriorSample,
    posterior_B: PosteriorSample,
) -> BayesFactorResult:
    """Return `ln B = ln Z_A - ln Z_B` using thermodynamic integration."""
    ln_z_a, ln_z_a_err, method_a = _posterior_evidence(posterior_A)
    ln_z_b, ln_z_b_err, method_b = _posterior_evidence(posterior_B)
    method = "thermodynamic" if method_a == method_b == "thermodynamic" else method_a
    return BayesFactorResult(
        ln_B=float(ln_z_a - ln_z_b),
        ln_B_err=float(np.hypot(ln_z_a_err, ln_z_b_err)),
        method=method,
        provenance={
            "model_A_seed": posterior_A.seed,
            "model_B_seed": posterior_B.seed,
            "model_A_sampler": posterior_A.sampler,
            "model_B_sampler": posterior_B.sampler,
            "model_A_method": method_a,
            "model_B_method": method_b,
        },
    )

