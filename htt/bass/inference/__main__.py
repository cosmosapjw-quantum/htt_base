"""FB-11.2 skeleton CLI for the inference driver.

The future CLI reads a YAML config plus an explicit seed and dispatches
to `run_posterior`. The skeleton plants that command-line contract only;
it does not parse YAML or emit posterior artifacts yet.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the future FB-11 CLI parser.

    Determinism contract: the future command
    `python -m bass.inference --config <path> --seed 42` must remain the
    reproducible entry point for the same-machine byte-identical
    `run_posterior(..., seed=42)` workflow documented in FB-11.2.

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
    """Reserve the FB-11 inference CLI entry point."""
    build_parser().parse_args(list(argv) if argv is not None else None)
    raise NotImplementedError(
        "FB-11.2 skeleton only: the inference CLI is reserved for the "
        "future emcee-backed driver implementation."
    )


if __name__ == "__main__":
    raise SystemExit(main())
