"""VER2 cutoff/convergence campaign skeletons for the BASS S3 lane."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

__all__ = [
    "MultipoleNormSummary",
    "CutoffCampaignSpec",
    "CutoffCampaignStub",
    "summarize_multipole_norms",
    "build_cutoff_campaign_stub",
]


@dataclass(frozen=True)
class MultipoleNormSummary:
    """Numerical summary for one cutoff-L run."""

    cutoff_L: int
    channel_norms: Mapping[str, float]
    closure_name: str

    def __post_init__(self) -> None:
        if self.cutoff_L < 2:
            raise ValueError("cutoff_L must be >= 2")
        if not self.channel_norms:
            raise ValueError("channel_norms must be non-empty")
        for name, value in self.channel_norms.items():
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(
                    f"channel_norms[{name!r}] must be finite and non-negative"
                )
        if not self.closure_name:
            raise ValueError("closure_name must be non-empty")


@dataclass(frozen=True)
class CutoffCampaignSpec:
    """Requested cutoffs and policy for the Tier-B convergence campaign."""

    cutoffs: tuple[int, ...] = (4, 6, 8)
    closure_name: str = "explicit_unset"
    baseline_cutoff: int = 6
    compare_observer_exports: bool = True
    diagnostic_l2_override: bool = False

    def __post_init__(self) -> None:
        if not self.cutoffs:
            raise ValueError("cutoffs must be non-empty")
        if tuple(sorted(self.cutoffs)) != self.cutoffs:
            raise ValueError("cutoffs must be strictly increasing")
        if len(set(self.cutoffs)) != len(self.cutoffs):
            raise ValueError("cutoffs must be unique")
        if 2 in self.cutoffs and not self.diagnostic_l2_override:
            raise ValueError("L=2 requires an explicit diagnostic override")
        if any(L < 2 for L in self.cutoffs):
            raise ValueError("all cutoffs must be >= 2")
        if self.baseline_cutoff not in self.cutoffs:
            raise ValueError("baseline_cutoff must appear in cutoffs")
        if not self.closure_name:
            raise ValueError("closure_name must be non-empty")


@dataclass(frozen=True)
class CutoffCampaignStub:
    """Pending convergence report hook for later executable runs."""

    spec: CutoffCampaignSpec
    summaries: tuple[MultipoleNormSummary, ...]
    ready: bool = False
    all_cutoffs_recorded: bool = True
    runtime_logging_required: bool = True

    def __post_init__(self) -> None:
        if not self.runtime_logging_required:
            raise ValueError("cutoff campaigns must log runtime and memory metadata")


def summarize_multipole_norms(
    cutoff_L: int,
    *,
    channel_arrays: Mapping[str, np.ndarray],
    closure_name: str,
) -> MultipoleNormSummary:
    """Return finite L2 norms for one cutoff-L run."""
    norms: dict[str, float] = {}
    for channel, values in channel_arrays.items():
        arr = np.asarray(values, dtype=float)
        if arr.ndim == 0:
            raise ValueError(f"channel {channel!r} must not be scalar")
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"channel {channel!r} contains non-finite values")
        norms[channel] = float(np.linalg.norm(arr))
    return MultipoleNormSummary(
        cutoff_L=cutoff_L,
        channel_norms=norms,
        closure_name=closure_name,
    )


def build_cutoff_campaign_stub(
    spec: CutoffCampaignSpec,
    summaries: tuple[MultipoleNormSummary, ...],
) -> CutoffCampaignStub:
    """Return the explicit S3 convergence-campaign hook."""
    recorded = {summary.cutoff_L for summary in summaries}
    missing = set(spec.cutoffs) - recorded
    if missing:
        raise ValueError(f"missing cutoff summaries for {sorted(missing)}")
    return CutoffCampaignStub(
        spec=spec,
        summaries=summaries,
        all_cutoffs_recorded=True,
    )
