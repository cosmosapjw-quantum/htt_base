"""v10 B1 runner: even-L BiPoSH rank card (--write / --check)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from obsstat.k1_evenl_biposh_rank import run_estimator  # noqa: E402

CARD = REPO / "docs/generated/k1_evenl_biposh_rank_card.json"


def build_payload() -> dict:
    result = run_estimator()
    sim_scores = result.pop("sim_scores")
    hist, edges = __import__("numpy").histogram(sim_scores, bins=40)
    metadata = {
        "owner": "OBSSTAT",
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": result["config_hash"],
        "generating_command": (
            "env PYTHONHASHSEED=0 venv/bin/python -B "
            "scripts/k1_evenl_biposh_rank_card.py --write"
        ),
        "sky_support_status": "planck_pr3_smica_compact_cache_masked",
        "mask_status": "pr150_common_mask_window_matched_null",
        "covariance_status": "sim_ensemble_hartlap_leave_one_out",
        "null_mock_status": "smica_processed_ffp10_999_cmb_plus_300_noise",
        "caveats": [
            "diagnostic consistency analysis only; E2E-conditional",
            "no detection, isotropy, anisotropy, or Bianchi-family claim",
            "odd-L quotient rests on the alm-independent exchange symmetry",
        ],
    }
    return {
        "schema": "htt.v10.k1_evenl_biposh_rank_card.v1",
        "metadata": metadata,
        "result": result,
        "sim_score_histogram": {
            "counts": hist.tolist(),
            "edges": edges.tolist(),
        },
        "terminal": result["terminal"],
    }


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=1) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
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
                      "rank_p": payload["result"]["pooled"]["rank_p"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
