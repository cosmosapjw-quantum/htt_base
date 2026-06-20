"""Amplitude-matched contamination null as a source-identification blocker.

REV-R095 binds the externally audited amplitude-matched contamination result
(triggers firing on contamination-only mocks) as a current negative result. A
high false-positive rate means the trigger does not identify a physical source,
so no positive headline Bayes factor may be drawn.

This module does not run new long mocks; it records the audited
false-positive count with an exact Wilson score interval and classifies the
source-identification status.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Sequence

__all__ = [
    "ContaminationFprReport",
    "contamination_fpr_report",
    "render_markdown",
]

# Standard normal 0.975 quantile for a two-sided 95% interval.
_Z_95 = 1.959963984540054


def _wilson_interval(k: int, n: int, z: float = _Z_95) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("n_trials must be positive")
    if not 0 <= k <= n:
        raise ValueError("n_false_positive must be within [0, n_trials]")
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


@dataclass(frozen=True)
class ContaminationFprReport:
    n_trials: int
    n_false_positive: int
    trigger: str
    config_hash: str
    input_hashes: tuple[str, ...]
    generating_command: str
    worktree_state: str
    fpr_ceiling: float
    raw_fpr: float
    wilson_lo: float
    wilson_hi: float

    @property
    def source_identification_failed(self) -> bool:
        # Source identification fails when even the 95% lower confidence bound on
        # the false-positive rate exceeds the tolerated contamination ceiling.
        return self.wilson_lo > self.fpr_ceiling

    @property
    def claim_tier(self) -> str:
        return "blocked" if self.source_identification_failed else "conditional"

    def as_payload(self) -> dict[str, Any]:
        failed = self.source_identification_failed
        return {
            "owner": "HTT",
            "implementation_scope": "htt",
            "schema_version": "htt.amplitude_matched_contamination.v1",
            "claim_tier": self.claim_tier,
            "trigger": self.trigger,
            "n_trials": self.n_trials,
            "n_false_positive": self.n_false_positive,
            "fpr_ceiling": self.fpr_ceiling,
            "false_positive_rate": {
                "raw": self.raw_fpr,
                "wilson_95": [self.wilson_lo, self.wilson_hi],
                "interval_method": "wilson_score_z_1.96",
            },
            "source_identification_status": (
                "failed" if failed else "not_blocked_by_contamination"
            ),
            "headline_bayes_factor_allowed": not failed,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "worktree_state": self.worktree_state,
            "caveats": [
                "amplitude-matched contamination null is a negative result",
                "a high false-positive rate blocks source identification",
                "no positive Bayes-factor headline may be drawn while blocked",
                "no native low-ell solver output is introduced",
            ],
        }


def contamination_fpr_report(
    *,
    n_trials: int,
    n_false_positive: int,
    trigger: str,
    config_hash: str,
    input_hashes: Sequence[str],
    generating_command: str,
    worktree_state: str,
    fpr_ceiling: float = 0.05,
) -> ContaminationFprReport:
    n = int(n_trials)
    k = int(n_false_positive)
    lo, hi = _wilson_interval(k, n)
    return ContaminationFprReport(
        n_trials=n,
        n_false_positive=k,
        trigger=str(trigger),
        config_hash=str(config_hash),
        input_hashes=tuple(str(item) for item in input_hashes),
        generating_command=str(generating_command),
        worktree_state=str(worktree_state),
        fpr_ceiling=float(fpr_ceiling),
        raw_fpr=k / n,
        wilson_lo=lo,
        wilson_hi=hi,
    )


def render_markdown(payload: dict[str, Any]) -> str:
    fpr = payload["false_positive_rate"]
    lines = [
        "# Amplitude-Matched Contamination Report (REV-R095)",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: externally_audited_amplitude_matched_contamination",
        f"config_hash: `{payload['config_hash']}`",
        "input_hashes:",
        *[f"- {item}" for item in payload["input_hashes"]],
        f"generating_command: `{payload['generating_command']}`",
        f"git_commit_or_worktree_state: `{payload['worktree_state']}`",
        "",
        "## Negative result",
        "",
        (
            f"Trigger `{payload['trigger']}` fired on "
            f"{payload['n_false_positive']} of {payload['n_trials']} "
            "amplitude-matched contamination-only mocks."
        ),
        "",
        f"- Raw false-positive rate: {fpr['raw']}",
        (
            f"- Wilson 95% interval: [{fpr['wilson_95'][0]:.4f}, "
            f"{fpr['wilson_95'][1]:.4f}] ({fpr['interval_method']})"
        ),
        f"- Tolerated contamination ceiling: {payload['fpr_ceiling']}",
        f"- Source identification status: {payload['source_identification_status']}",
        (
            "- Headline Bayes factor allowed: "
            f"{str(payload['headline_bayes_factor_allowed']).lower()}"
        ),
        "",
        "## Caveats",
        "",
        *[f"- {item}" for item in payload["caveats"]],
        "",
    ]
    return "\n".join(lines)


def _stable_config_hash(*, n_trials: int, n_false_positive: int, trigger: str) -> str:
    encoded = json.dumps(
        {
            "schema_version": "htt.amplitude_matched_contamination.v1",
            "n_trials": int(n_trials),
            "n_false_positive": int(n_false_positive),
            "trigger": str(trigger),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def main() -> int:
    """Write the audited 95/100 lnB>5 contamination report artifacts."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[4]
    n_trials, n_false_positive, trigger = 100, 95, "lnB_gt_5"
    report = contamination_fpr_report(
        n_trials=n_trials,
        n_false_positive=n_false_positive,
        trigger=trigger,
        config_hash=_stable_config_hash(
            n_trials=n_trials, n_false_positive=n_false_positive, trigger=trigger
        ),
        input_hashes=("audit_ver2.md:externally_audited_amplitude_matched_contamination",),
        generating_command="venv/bin/python -m htt.infer.amplitude_matched_contamination",
        worktree_state="externally_audited_fixture",
    )
    payload = report.as_payload()
    out_json = repo_root / "docs" / "generated" / "amplitude_matched_contamination_report.json"
    out_md = repo_root / "docs" / "generated" / "amplitude_matched_contamination_report.md"
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
