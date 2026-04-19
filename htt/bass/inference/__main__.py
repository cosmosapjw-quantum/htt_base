"""FB-11 skeleton CLI for the inference driver and summary seam.

The future CLI reads a YAML config plus an explicit seed and dispatches
to `run_posterior` and the FB-11.6 summary workflow. The skeleton plants
that command-line contract only; it does not parse YAML or emit
posterior artifacts yet.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the future FB-11 CLI parser.

    Determinism contract: the future command
    `python -m bass.inference --config configs/fb11_summary.yaml --seed 42`
    must remain the reproducible entry point for both the same-machine
    byte-identical `run_posterior(..., seed=42)` workflow documented in
    FB-11.2 and the FB-11.6 summary run.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §3.3.
    """
    parser = argparse.ArgumentParser(prog="python -m bass.inference")
    parser.add_argument("--config", required=True, help="Path to the YAML config.")
    parser.add_argument("--seed", required=True, type=int, help="Deterministic RNG seed.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Reserve the FB-11 inference CLI entry point.

    Contract only: once implemented,
    `python -m bass.inference --config configs/fb11_summary.yaml --seed 42`
    must be able to emit `figures/paper/fb11_summary_table.json` and
    `figures/paper/fb11_summary_table.md`. Two runs on the same machine
    with `seed=42` must produce byte-identical summary outputs.
    """
    build_parser().parse_args(list(argv) if argv is not None else None)
    raise NotImplementedError(
        "FB-11.2 skeleton only: the inference CLI is reserved for the "
        "future emcee-backed driver implementation."
    )


if __name__ == "__main__":
    raise SystemExit(main())
