"""Execute the BF-05 BASS runtime validation evidence bundle."""
from __future__ import annotations

import argparse
import json
import sys

from bass.validation import (
    build_type_i_reionization_probe_evidence,
    build_type_i_runtime_validation_evidence,
    type_i_reionization_probe_payload,
    type_i_runtime_validation_payload,
)


def _check(cutoffs: tuple[int, ...], tier_tol: float, cutoff_tol: float) -> int:
    evidence = build_type_i_runtime_validation_evidence(
        cutoffs=cutoffs,
        tier_compare_tolerance=tier_tol,
        cutoff_delta_tolerance=cutoff_tol,
    )
    if not evidence.passed:
        print(f"[FAIL] BF-05 BASS validation ({evidence.campaign_id})")
        for check in evidence.checks:
            state = "PASS" if check.passed else "FAIL"
            if check.metric_name is None:
                print(f" - [{state}] {check.check_id}: {check.summary}")
                continue
            print(
                f" - [{state}] {check.check_id}: {check.metric_name}="
                f"{check.metric_value:.6e} (threshold={check.threshold:.6e})"
            )
        return 1
    print(
        "[PASS] BF-05 BASS validation "
        f"({evidence.campaign_id}, max_rel_l2={evidence.tier_a_tier_b_max_relative_l2:.6e}, "
        f"max_cutoff_delta={evidence.cutoff_max_relative_delta:.6e})"
    )
    return 0


def _reion_probe_check(z_probe: float, z_final: float) -> int:
    evidence = build_type_i_reionization_probe_evidence(
        z_probe=float(z_probe),
        z_final=float(z_final),
    )
    if not evidence.passed:
        print(f"[FAIL] BF-05 BASS reionization probe ({evidence.campaign_id})")
        for check in evidence.checks:
            state = "PASS" if check.passed else "FAIL"
            if check.metric_name is None:
                print(f" - [{state}] {check.check_id}: {check.summary}")
                continue
            print(
                f" - [{state}] {check.check_id}: {check.metric_name}="
                f"{check.metric_value:.6e} (threshold={check.threshold:.6e})"
            )
        return 1
    print(
        "[PASS] BF-05 BASS reionization probe "
        f"({evidence.campaign_id}, z_probe={z_probe:.1f}, z_final={z_final:.1f})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--reion-probe-check", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--reion-probe-json", action="store_true")
    parser.add_argument("--cutoffs", type=int, nargs="+", default=(4, 6))
    parser.add_argument("--tier-compare-tol", type=float, default=5.0e-2)
    parser.add_argument("--cutoff-delta-tol", type=float, default=7.5e-1)
    parser.add_argument("--z-probe", type=float, default=8.0)
    parser.add_argument("--z-final", type=float, default=4.0)
    args = parser.parse_args(argv)
    cutoffs = tuple(int(value) for value in args.cutoffs)
    if args.check:
        return _check(
            cutoffs=cutoffs,
            tier_tol=float(args.tier_compare_tol),
            cutoff_tol=float(args.cutoff_delta_tol),
        )
    if args.reion_probe_check:
        return _reion_probe_check(
            z_probe=float(args.z_probe),
            z_final=float(args.z_final),
        )
    if args.reion_probe_json:
        payload = type_i_reionization_probe_payload(
            z_probe=float(args.z_probe),
            z_final=float(args.z_final),
        )
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    payload = type_i_runtime_validation_payload(
        cutoffs=cutoffs,
        tier_compare_tolerance=float(args.tier_compare_tol),
        cutoff_delta_tolerance=float(args.cutoff_delta_tol),
    )
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    print(
        "BF-05 BASS validation: "
        f"{payload['campaign_id']} status={payload['status']} "
        f"max_rel_l2={payload['tier_a_tier_b_max_relative_l2']:.6e} "
        f"max_cutoff_delta={payload['cutoff_max_relative_delta']:.6e}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
