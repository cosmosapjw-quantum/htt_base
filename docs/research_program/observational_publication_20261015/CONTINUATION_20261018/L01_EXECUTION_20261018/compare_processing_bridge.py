"""Compare retained raw-child-average and saved-L128 fits on original support."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from analyze_matched_splits import compare, groups, read

EXPECTED = "900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-npz", type=Path, required=True)
    ap.add_argument("--bridge-json", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    source_bytes = args.source_npz.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != EXPECTED:
        raise ValueError("ORIGINAL_SOURCE_COEFFICIENT_IDENTITY")
    bridge, identity = read(args.bridge_json)
    if bridge["selected_support"]["selected_pixels"] != 30021:
        raise ValueError("ORIGINAL_SELECTED_SUPPORT_REQUIRED")
    pairs = {"full": "SMICA_FULL", "hm1": "SMICA_HM1", "hm2": "SMICA_HM2",
             "oe1": "SMICA_OE1", "oe2": "SMICA_OE2"}
    comparisons = {}
    with np.load(args.source_npz, allow_pickle=False) as data:
        names = data["names_EB"].tolist()
        for product, name in pairs.items():
            saved = np.asarray(bridge["saved_L128_projections_on_original_selected_support"][product]["total_K_CMB"])
            original = data["coeff_EB"][names.index(name)]*1e-6
            comparisons[product] = {key: compare(saved[ix], original[ix]) for key, ix in groups().items()}
    result = {"schema": "htt.L01_original_support_processing_comparison/1",
              "owner": "obsstat", "claim_tier": "C0", "status": "DIAGNOSTIC_ONLY",
              "non_claim_bearing": True, "transfer_source": "none",
              "same_selected_support": bridge["selected_support"],
              "left": "Saved W*QU pseudo-alms through ell128 synthesized in RING64 then fit on original selected support",
              "right": "Historical native-child masked-average Q/U fitted on original selected support; retained coefficients only",
              "units": "K_CMB after explicit microK-to-K conversion of original retained coefficients",
              "products": comparisons, "independent_sky_count": 1, "p_value": None,
              "original_data_reprocessed": False, "noise_or_tail_attribution": False,
              "caveats": ["Shared source and selected support do not make the two processing operators identical.",
                          "Difference combines windowing, synthesis/cutoff, grid and child-averaging effects.",
                          "No pure ell>128, physical E/B, noise or significance interpretation."],
              "sources": [{"path": str(args.source_npz), "sha256": EXPECTED, "bytes": len(source_bytes)}, identity],
              "generating_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps({key: {"angle_degrees": row["all"]["angle_degrees"],
                           "distance_nK_CMB": row["all"]["distance_K_CMB"]*1e9}
                      for key, row in comparisons.items()}, indent=2))


if __name__ == "__main__": main()
