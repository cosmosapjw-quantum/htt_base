"""PR-180 runner: boost-BiPoSH residual result card (--write / --check)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from obsstat.boost_biposh_residual import (  # noqa: E402
    BoostBiposhConfig,
    run_estimator,
)

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr180_spec.yaml"
CARD = REPO / "docs/generated/pr180_result_card.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_payload() -> dict:
    result = run_estimator()
    baseline = None
    for line in SPEC.read_text().splitlines():
        if line.startswith("baseline_commit:"):
            baseline = line.split(":", 1)[1].strip()
    metadata = {
        "owner": "OBSSTAT",
        "implementation_scope": ["obsstat"],
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C3"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": result["config_hash"],
        "spec_sha256": _sha(SPEC),
        "generating_command": (
            "env PYTHONHASHSEED=0 venv/bin/python -B "
            "scripts/codex_harness/run_pr180_boost_residual.py --write"
        ),
        "git_commit": baseline,
        "sky_support_status": "planck_pr3_smica_compact_cache_masked",
        "mask_status": "pr150_common_mask_window_matched_null",
        "covariance_status": "sim_ensemble_hartlap_leave_one_out",
        "null_mock_status": "boosted_ffp10_999_cmb_plus_300_noise",
        "caveats": [
            "consistency result only; never a boost confirmation",
            "no independence claim (separate registered test required)",
            "boosted-null design per Planck 2018 III FFP10 description",
            "ensemble boost-content measurement non-informative at "
            "128-sim MC power (reported, not gated)",
        ],
    }
    return {
        "schema": "htt.pr180.result_card.v1",
        "pr_id": "PR-180",
        "metadata": metadata,
        "result": result,
        "terminal": result["terminal"],
        "forbidden_claims_reaffirmed": [
            "no boost confirmation or restored-independence claim",
            "no detection, isotropy, or anisotropy statement",
            "no transfer, geometry, native, or Bianchi-family content",
            "kernel never fitted; residual never a geometric estimand",
        ],
    }


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=1) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check and CARD.exists():
        frozen = json.loads(CARD.read_text())
        if (
            frozen.get("metadata", {}).get("config_hash")
            != BoostBiposhConfig().config_hash()
        ):
            print(
                json.dumps(
                    {
                        "mode": "check",
                        "ok": False,
                        "read_only": True,
                        "reason": "config_hash_mismatch",
                    },
                    sort_keys=True,
                )
            )
            return 1
    payload = build_payload()
    if args.write:
        CARD.write_bytes(_render(payload))
        print(f"wrote {CARD.relative_to(REPO)}")
        return 0
    if not CARD.exists() or CARD.read_bytes() != _render(payload):
        print(f"artifact differs under --check: {CARD.relative_to(REPO)}")
        return 1
    print(json.dumps({"mode": "check", "ok": True, "read_only": True,
                      "terminal": payload["terminal"],
                      "rank_p": payload["result"]["rank_p"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
