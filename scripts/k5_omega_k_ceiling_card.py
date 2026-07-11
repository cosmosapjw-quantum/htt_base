#!/usr/bin/env python3
"""K5 anisotropic-Omega_k ceiling card (NEW artifact, REV-R185).

Exit-gate BRANCH 1 of k5_omega_k_higher_order_ceiling: the OMK-REOPEN
slaving transfer (|Delta Omega_k| <= sqrt(Sigma^2_ceiling)/|kappa| on the
LRS-III/Kantowski-Sachs slaved mode, kappa = -1/(2+q) exact) converts
every registered shear ceiling into a FINITE anisotropic-curvature
ceiling. This card carries the labeled attribution x era branches; the
frozen v7/v8/v9 identified-interval cards and the registered T1'
half-width U_k PLUGIN are NOT modified; nothing is promoted;
observational_claim_allowed stays False.

``--check`` regenerates in memory and diffs byte-exactly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
for p in (REPO / "htt/htt", REPO / "htt", REPO):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

OUT = REPO / "docs/generated/k5_omega_k_ceiling_card.json"
FROZEN_REFS = [
    "docs/generated/k5_cf4_identified_interval_card.json",
    "docs/generated/k5_cf4_identified_interval_card_v8.json",
    "docs/generated/k5_cf4_identified_interval_card_v9.json",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_card() -> dict:
    from htt.obsstat.egs3_omega_k_reopening import (
        ceiling_map, slaving_coefficient, structural_null_repair)
    ceil = ceiling_map()
    sl = slaving_coefficient()
    repair = structural_null_repair()
    return {
        "schema": "htt.k5.omega_k_ceiling_card.v1",
        "theorem_id": "OMK-REOPEN",
        "transfer": {
            "slaving": "Sigma = kappa * Delta Omega_k on the slaved mode,"
                       " kappa = -1/(2+q) exact"
                       " (kappa(w) = -2/(5+3w); dust -2/5, radiation"
                       " -1/3; vacuum anchor ratio -2/3)",
            "kappa_exact": sl["kappa_exact"],
            "two_sided": ceil["two_sided"],
            "instantaneous_null_untouched": repair[
                "instantaneous_null_still_certified"],
        },
        "ceiling_rows": ceil["rows"],
        "conservative_note": ceil["conservative_note"],
        "class_conditional": ceil["class_conditional"],
        "frozen_surfaces_untouched": {
            "registered_T1p_half_width_U_k": "PLUGIN value NOT modified"
                                             " (frozen-card and signed-box"
                                             " surfaces intact)",
            "frozen_card_hashes": {p: _sha(REPO / p) for p in FROZEN_REFS
                                   if (REPO / p).exists()},
        },
        "plugin_coherence_remark": (
            "the saadeh_model_conditional ceilings (<=1.5e-6 / <=1.8e-6, two-significant-figure ceilings) sit"
            " at the same order as the historical U_k PLUGIN placeholder"
            " 1e-6 -- a comparison-only coherence remark, not a"
            " promotion"),
        "observational_claim_allowed": False,
        "sources": {
            "seal": "docs/generated/omega_k_reopening_seal.json",
            "wolfram_seal": "docs/generated/"
                            "omega_k_reopening_wolfram_seal.json",
            "module": "htt/obsstat/egs3_omega_k_reopening.py",
        },
    }


def _render(card: dict) -> str:
    return json.dumps(card, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    text = _render(build_card())
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print("stale omega_k ceiling card", file=sys.stderr)
            return 1
        print("omega_k ceiling card current")
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
