"""Prior/error sensitivity gate for evidence-style labels.

REV-R096 replaces proxy prior-support surfaces with an explicit prior/error
sensitivity gate. A single Jeffreys evidence label (e.g. "decisive") is only
admissible when the marginal-likelihood rows are actual evidence runs and the
sign of ln B is robust across the prior-floor/ceiling and sigma_beta grid. A
sign flip across the grid blocks any single evidence label.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

__all__ = [
    "PriorErrorSensitivityReport",
    "summarize_prior_error_grid",
    "render_markdown",
]


def _finite(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


@dataclass(frozen=True)
class PriorErrorSensitivityReport:
    rows: tuple[dict[str, float], ...]
    config_hash: str
    input_hashes: tuple[str, ...]
    generating_command: str
    worktree_state: str
    rows_are_marginal_likelihoods: bool
    sign_tol: float

    @property
    def lnb_values(self) -> tuple[float, ...]:
        return tuple(row["lnB"] for row in self.rows)

    @property
    def sign_flip_detected(self) -> bool:
        values = self.lnb_values
        has_positive = any(value > self.sign_tol for value in values)
        has_negative = any(value < -self.sign_tol for value in values)
        return has_positive and has_negative

    @property
    def single_jeffreys_label_allowed(self) -> bool:
        return (not self.sign_flip_detected) and self.rows_are_marginal_likelihoods

    @property
    def claim_tier(self) -> str:
        if self.sign_flip_detected or not self.rows_are_marginal_likelihoods:
            return "blocked"
        return "conditional"

    def as_payload(self) -> dict[str, Any]:
        values = self.lnb_values
        return {
            "owner": "HTT",
            "implementation_scope": "htt",
            "schema_version": "htt.prior_error_sensitivity.v1",
            "claim_tier": self.claim_tier,
            "n_rows": len(self.rows),
            "lnB_robust_range": {
                "min": min(values),
                "max": max(values),
                "spread": max(values) - min(values),
            },
            "sign_flip_detected": self.sign_flip_detected,
            "single_jeffreys_label_allowed": self.single_jeffreys_label_allowed,
            "rows_are_marginal_likelihoods": self.rows_are_marginal_likelihoods,
            "boundary_mass_status": "not_computed_placeholder",
            "kl_divergence_status": "not_computed_placeholder",
            "rows": [dict(row) for row in self.rows],
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "worktree_state": self.worktree_state,
            "caveats": [
                "prior/error sensitivity gate, not an evidence run",
                "a sign flip across the grid blocks any single Jeffreys label",
                "boundary-mass and KL diagnostics are placeholders, not computed",
                "no native low-ell solver output is introduced",
            ],
        }


def summarize_prior_error_grid(
    *,
    rows: Sequence[Mapping[str, object]],
    config_hash: str,
    input_hashes: Sequence[str],
    generating_command: str,
    worktree_state: str,
    rows_are_marginal_likelihoods: bool = False,
    sign_tol: float = 0.0,
) -> PriorErrorSensitivityReport:
    if isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("rows must be a non-empty sequence")
    parsed: list[dict[str, float]] = []
    for index, row in enumerate(rows):
        parsed.append(
            {
                "prior_floor": _finite(row.get("prior_floor"), f"rows[{index}].prior_floor"),
                "ceiling": _finite(row.get("ceiling"), f"rows[{index}].ceiling"),
                "sigma_beta": _finite(row.get("sigma_beta"), f"rows[{index}].sigma_beta"),
                "lnB": _finite(row.get("lnB"), f"rows[{index}].lnB"),
            }
        )
    return PriorErrorSensitivityReport(
        rows=tuple(parsed),
        config_hash=str(config_hash),
        input_hashes=tuple(str(item) for item in input_hashes),
        generating_command=str(generating_command),
        worktree_state=str(worktree_state),
        rows_are_marginal_likelihoods=bool(rows_are_marginal_likelihoods),
        sign_tol=float(sign_tol),
    )


def render_markdown(payload: dict[str, Any]) -> str:
    rng = payload["lnB_robust_range"]
    lines = [
        "# Prior/Error Sensitivity Report (REV-R096)",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        f"config_hash: `{payload['config_hash']}`",
        "input_hashes:",
        *[f"- {item}" for item in payload["input_hashes"]],
        f"generating_command: `{payload['generating_command']}`",
        f"git_commit_or_worktree_state: `{payload['worktree_state']}`",
        "",
        "## Robustness",
        "",
        f"- ln B robust range: [{rng['min']}, {rng['max']}] (spread {rng['spread']})",
        f"- Sign flip detected: {str(payload['sign_flip_detected']).lower()}",
        (
            "- Single Jeffreys label allowed: "
            f"{str(payload['single_jeffreys_label_allowed']).lower()}"
        ),
        (
            "- Rows are marginal likelihoods: "
            f"{str(payload['rows_are_marginal_likelihoods']).lower()}"
        ),
        f"- Boundary-mass status: {payload['boundary_mass_status']}",
        f"- KL divergence status: {payload['kl_divergence_status']}",
        "",
        "## Grid",
        "",
        "| prior_floor | ceiling | sigma_beta | lnB |",
        "| --- | --- | --- | --- |",
        *[
            f"| {row['prior_floor']} | {row['ceiling']} | {row['sigma_beta']} | {row['lnB']} |"
            for row in payload["rows"]
        ],
        "",
        "## Caveats",
        "",
        *[f"- {item}" for item in payload["caveats"]],
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    """Write the audited prior/error sensitivity report (sign flip -> blocked)."""
    import hashlib
    import json
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[4]
    rows = [
        {"prior_floor": 1e-12, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": 26.40},
        {"prior_floor": 1e-6, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": -39.1},
        {"prior_floor": 1e-9, "ceiling": 1.0, "sigma_beta": 5.4e-4, "lnB": 3.2},
    ]
    config_hash = "sha256:" + hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    report = summarize_prior_error_grid(
        rows=rows,
        config_hash=config_hash,
        input_hashes=(
            "docs/generated/current_science_plot_payload.json:prior_support_proxy",
        ),
        generating_command="venv/bin/python -m htt.infer.prior_error_sensitivity",
        worktree_state="prior_error_sensitivity_fixture",
        rows_are_marginal_likelihoods=False,
    )
    payload = report.as_payload()
    out_json = repo_root / "docs" / "generated" / "prior_error_sensitivity_report.json"
    out_md = repo_root / "docs" / "generated" / "prior_error_sensitivity_report.md"
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
