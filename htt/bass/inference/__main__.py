"""CLI entry point for the FB-11 inference summary workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from collections.abc import Sequence

import numpy as np
import yaml

from bass.background.bianchi_types import ALL_BIANCHI_TYPES
from bass.inference.bayes import bayes_factor
from bass.inference.drivers.emcee_driver import PosteriorSample, run_posterior
from bass.inference.synthetic import (
    make_problem,
    posterior_mle,
    summary_truth_seed,
)


class SurrogateInferenceDatasetError(RuntimeError):
    """Raised when a surrogate dataset is used without explicit opt-in."""


def build_parser() -> argparse.ArgumentParser:
    """Build the deterministic FB-11 CLI parser."""
    parser = argparse.ArgumentParser(prog="python -m bass.inference")
    parser.add_argument("--config", required=True, help="Path to the YAML config.")
    parser.add_argument("--seed", required=True, type=int, help="Deterministic RNG seed.")
    return parser


def _load_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config root must be a mapping")
    return payload


def _validate_dataset_contract(config: dict[str, Any]) -> dict[str, Any]:
    dataset = dict(config.get("dataset", {}))
    kind = str(dataset.get("kind", "")).strip()
    if not kind:
        raise ValueError("dataset.kind must be set explicitly")
    allow_surrogate = bool(dataset.get("allow_surrogate", False))
    if kind in {"synthetic_planck2018", "synthetic_surrogate"}:
        if not allow_surrogate:
            raise SurrogateInferenceDatasetError(
                "FB-11 CLI is being pointed at a surrogate synthetic "
                "dataset without explicit opt-in. Set "
                "dataset.allow_surrogate: true only for audited "
                "regression work. A deployment-grade run must bind to "
                "an actual observation/likelihood dataset."
            )
        dataset["kind"] = "synthetic_surrogate"
        return dataset
    raise NotImplementedError(
        f"dataset.kind={kind!r} is not wired in this worktree. The "
        "surrogate test harness is available via "
        "dataset.kind='synthetic_surrogate' with "
        "dataset.allow_surrogate=true; production inference requires "
        "a first-principles observation/likelihood binding that is not "
        "yet implemented locally."
    )


def _round_float(value: float) -> float:
    return float(np.round(float(value), 12))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _write_markdown(path: Path, rows: list[dict[str, Any]], *, truth_type: str, seed: int) -> None:
    lines = [
        "# FB-11 summary table",
        "",
        f"- truth model: `{truth_type}`",
        f"- seed: `{seed}`",
        "",
        "| Type | ln B | ln B err | Converged | beta_cosmo | beta_obs | Sigma_mnu |",
        "|---|---:|---:|:---:|---:|---:|---:|",
    ]
    for row in rows:
        mle = dict(row["mle"])
        lines.append(
            "| {type} | {ln_B:.6f} | {ln_B_err:.6f} | {converged} | {beta_cosmo:.6e} | {beta_obs:.6e} | {Sigma_mnu:.6f} |".format(
                type=row["type"],
                ln_B=float(row["ln_B"]),
                ln_B_err=float(row["ln_B_err"]),
                converged="yes" if bool(row["converged"]) else "no",
                beta_cosmo=float(mle["beta_cosmo"]),
                beta_obs=float(mle["beta_obs"]),
                Sigma_mnu=float(mle["Sigma_mnu"]),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _save_posterior_npz(path: Path, posterior: PosteriorSample) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        samples=posterior.samples,
        log_prob=posterior.log_prob,
        diagnostics=np.array([posterior.diagnostics], dtype=object),
        config=np.array([posterior.config], dtype=object),
        sampler=np.array([posterior.sampler], dtype=object),
        seed=np.array([posterior.seed], dtype=int),
    )


def _summary_outputs(config: dict[str, Any]) -> tuple[Path, Path, Path]:
    outputs = dict(config.get("outputs", {}))
    summary_json = Path(outputs.get("summary_json", "figures/paper/fb11_summary_table.json"))
    summary_markdown = Path(outputs.get("summary_markdown", "figures/paper/fb11_summary_table.md"))
    posterior_dir = Path(outputs.get("posterior_dir", "figures/paper/fb11_posteriors"))
    return summary_json, summary_markdown, posterior_dir


def _sampler_schedule(config: dict[str, Any]) -> list[dict[str, Any]]:
    sampler_cfg = dict(config.get("sampler", {}))
    schedule = sampler_cfg.get("schedule")
    if isinstance(schedule, list) and schedule:
        parsed = []
        for item in schedule:
            if not isinstance(item, dict):
                raise ValueError("sampler.schedule entries must be mappings")
            parsed.append(
                {
                    "n_walkers": int(item.get("n_walkers", sampler_cfg.get("n_walkers", 48))),
                    "n_steps": int(item.get("n_steps", sampler_cfg.get("n_steps", 320))),
                    "burnin": int(item.get("burnin", sampler_cfg.get("burnin", 120))),
                    "parallel": bool(item.get("parallel", sampler_cfg.get("parallel", False))),
                }
            )
        return parsed
    return [
        {
            "n_walkers": int(sampler_cfg.get("n_walkers", 48)),
            "n_steps": int(sampler_cfg.get("n_steps", 320)),
            "burnin": int(sampler_cfg.get("burnin", 120)),
            "parallel": bool(sampler_cfg.get("parallel", False)),
        }
    ]


def _mle_beta_triplet(posterior: PosteriorSample) -> dict[str, float]:
    names = tuple(posterior.config.get("parameter_names", ()))
    raw = posterior_mle(posterior.samples, posterior.log_prob, names)
    return {
        "beta_cosmo": float(np.tanh(raw.get("eta_cosmo", 0.0))),
        "beta_obs": float(np.tanh(raw.get("eta_obs", 0.0))),
        "Sigma_mnu": float(raw.get("Sigma_mnu", 0.0)),
        "structure_scale": float(raw.get("structure_scale", 0.0)),
    }


def _run_with_schedule(
    problem: Any,
    *,
    seed: int,
    schedule: list[dict[str, Any]],
) -> PosteriorSample:
    posterior: PosteriorSample | None = None
    for stage_index, stage in enumerate(schedule):
        stage_seed = int(seed) if stage_index < 2 else int(seed) + 20000 * (stage_index - 1)
        posterior = run_posterior(
            problem.log_likelihood,
            problem.priors,
            seed=stage_seed,
            n_walkers=int(stage["n_walkers"]),
            n_steps=int(stage["n_steps"]),
            burnin=int(stage["burnin"]),
            parallel=bool(stage["parallel"]),
        )
        if bool(posterior.diagnostics["converged"]):
            break
    assert posterior is not None
    return posterior


def _run_summary(config: dict[str, Any], *, seed: int) -> tuple[dict[str, Any], int]:
    dataset = _validate_dataset_contract(config)
    schedule = _sampler_schedule(config)
    truth_type = str(dataset.get("truth_type", "IX"))
    observation_seed = summary_truth_seed(config, seed)
    observation_problem = make_problem(
        "FLRW",
        truth_type=truth_type,
        seed=observation_seed,
        noise_scale=float(dataset.get("noise_scale", 1.0)),
    )
    observation = np.asarray(observation_problem.observation, dtype=float)
    baseline_problem = make_problem(
        "FLRW",
        truth_type=truth_type,
        seed=observation_seed,
        truth_params=observation_problem.truth_params,
        observation=observation,
    )
    baseline = _run_with_schedule(
        baseline_problem,
        seed=int(seed),
        schedule=schedule,
    )
    summary_json, summary_markdown, posterior_dir = _summary_outputs(config)
    _save_posterior_npz(posterior_dir / "FLRW.npz", baseline)
    rows: list[dict[str, Any]] = []
    exit_code = 0 if bool(baseline.diagnostics["converged"]) else 1
    for index, label in enumerate(ALL_BIANCHI_TYPES):
        problem = make_problem(
            label,
            truth_type=truth_type,
            seed=observation_seed,
            truth_params=observation_problem.truth_params,
            observation=observation,
        )
        posterior = _run_with_schedule(
            problem,
            seed=int(seed) + index + 1,
            schedule=schedule,
        )
        _save_posterior_npz(posterior_dir / f"{label}.npz", posterior)
        comparison = bayes_factor(posterior, baseline)
        row = {
            "type": label,
            "ln_B": _round_float(comparison.ln_B),
            "ln_B_err": _round_float(comparison.ln_B_err),
            "converged": bool(posterior.diagnostics["converged"]),
            "mle": {
                key: _round_float(value)
                for key, value in _mle_beta_triplet(posterior).items()
            },
            "sampler": posterior.sampler,
        }
        rows.append(row)
        if not row["converged"]:
            exit_code = 1
    payload = {
        "seed": int(seed),
        "dataset": {
            "kind": str(dataset["kind"]),
            "allow_surrogate": bool(dataset.get("allow_surrogate", False)),
            "truth_type": truth_type,
            "observation_seed": int(observation_seed),
            "truth_params": {
                key: _round_float(value)
                for key, value in observation_problem.truth_params.items()
            },
        },
        "rows": rows,
    }
    _write_json(summary_json, payload)
    _write_json(summary_json.with_name("bayes_factor_summary.json"), payload)
    _write_markdown(summary_markdown, rows, truth_type=truth_type, seed=int(seed))
    return payload, exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Run the reproducible FB-11 summary workflow.

    `python -m bass.inference --config configs/fb11_summary.yaml --seed 42`
    writes `figures/paper/fb11_summary_table.json` and
    `figures/paper/fb11_summary_table.md`. Two runs on the same machine
    with `seed=42` are byte-identical.
    """
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    config = _load_config(Path(args.config))
    _, exit_code = _run_summary(config, seed=int(args.seed))
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
