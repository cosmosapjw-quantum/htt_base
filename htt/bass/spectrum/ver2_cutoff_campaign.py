"""VER2 cutoff/convergence campaign surfaces for the BASS S3 lane."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np

__all__ = [
    "MultipoleNormSummary",
    "CutoffCampaignSpec",
    "CutoffCampaignStub",
    "CutoffChannelDelta",
    "ExecutedCutoffCampaign",
    "summarize_multipole_norms",
    "build_cutoff_campaign_stub",
    "run_executed_cutoff_campaign",
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


@dataclass(frozen=True)
class CutoffChannelDelta:
    """Per-channel relative delta against the chosen baseline cutoff."""

    channel: str
    baseline_norm: float
    cutoff_norm: float
    relative_delta: float

    def __post_init__(self) -> None:
        if not self.channel:
            raise ValueError("channel must be non-empty")
        for name, value in (
            ("baseline_norm", self.baseline_norm),
            ("cutoff_norm", self.cutoff_norm),
            ("relative_delta", self.relative_delta),
        ):
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True)
class ExecutedCutoffCampaign:
    """Executed cutoff campaign with finite norm deltas and runtime logs."""

    spec: CutoffCampaignSpec
    summaries: tuple[MultipoleNormSummary, ...]
    deltas: Mapping[int, tuple[CutoffChannelDelta, ...]]
    runtime_seconds: Mapping[int, float]
    ready: bool = True
    all_cutoffs_recorded: bool = True
    runtime_logging_required: bool = True

    def __post_init__(self) -> None:
        if not self.ready:
            raise ValueError("executed cutoff campaigns must be marked ready")
        recorded = {summary.cutoff_L for summary in self.summaries}
        missing = set(self.spec.cutoffs) - recorded
        if missing:
            raise ValueError(f"missing cutoff summaries for {sorted(missing)}")
        if set(self.runtime_seconds) != set(self.spec.cutoffs):
            raise ValueError("runtime_seconds must record every configured cutoff")
        for cutoff, runtime_sec in self.runtime_seconds.items():
            if cutoff not in self.spec.cutoffs:
                raise ValueError(f"unexpected cutoff runtime entry {cutoff}")
            if not np.isfinite(runtime_sec) or runtime_sec < 0.0:
                raise ValueError("runtime_seconds entries must be finite and non-negative")
        if set(self.deltas) != set(self.spec.cutoffs):
            raise ValueError("deltas must contain one entry per configured cutoff")


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


def _relative_delta(*, baseline: float, cutoff: float) -> float:
    scale = max(float(baseline), 1.0e-30)
    return abs(float(cutoff) - float(baseline)) / scale


def run_executed_cutoff_campaign(
    spec: CutoffCampaignSpec,
    *,
    runner: Callable[[int], tuple[Mapping[str, np.ndarray], float]],
) -> ExecutedCutoffCampaign:
    """Execute the configured Tier-B cutoff campaign through a caller runner."""

    summaries: list[MultipoleNormSummary] = []
    runtime_seconds: dict[int, float] = {}
    for cutoff in spec.cutoffs:
        channel_arrays, runtime_sec = runner(int(cutoff))
        summaries.append(
            summarize_multipole_norms(
                int(cutoff),
                channel_arrays=channel_arrays,
                closure_name=spec.closure_name,
            )
        )
        runtime_seconds[int(cutoff)] = float(runtime_sec)

    summary_by_cutoff = {summary.cutoff_L: summary for summary in summaries}
    baseline = summary_by_cutoff[spec.baseline_cutoff]
    deltas: dict[int, tuple[CutoffChannelDelta, ...]] = {}
    baseline_channels = tuple(sorted(baseline.channel_norms))
    for cutoff in spec.cutoffs:
        summary = summary_by_cutoff[int(cutoff)]
        if tuple(sorted(summary.channel_norms)) != baseline_channels:
            raise ValueError("all cutoff summaries must expose the same channel set")
        deltas[int(cutoff)] = tuple(
            CutoffChannelDelta(
                channel=channel,
                baseline_norm=float(baseline.channel_norms[channel]),
                cutoff_norm=float(summary.channel_norms[channel]),
                relative_delta=_relative_delta(
                    baseline=float(baseline.channel_norms[channel]),
                    cutoff=float(summary.channel_norms[channel]),
                ),
            )
            for channel in baseline_channels
        )

    return ExecutedCutoffCampaign(
        spec=spec,
        summaries=tuple(summaries),
        deltas=deltas,
        runtime_seconds=runtime_seconds,
    )
