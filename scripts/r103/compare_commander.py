"""Check the new per-index reduction against the independently transformed R102 pair."""
import argparse
import json
from pathlib import Path

import numpy as np

from .commander_ensemble import atomic_json, CHANNELS, _sha256_file

BASE = Path("docs/research_program/observational_publication_20261015")
PREVIOUS = BASE / "R102_CF4_HOLDOUT_NATIVE_SOLVER_20261123/COMMANDER_PAIR_00000_CHECK.json"


def compare(new, previous):
    new_data = json.loads(new.read_text())
    old = json.loads(previous.read_text())
    if new_data["index"] != 0 or new_data["config"]["lmax"] != 64:
        raise ValueError("R102 comparison requires index 00000, ell_max 64")
    metadata = old["file_metadata"]
    if new_data["raw_sha256"]["noise"] != metadata["noise_mc_00000"]["sha256"]:
        raise ValueError("R102 noise identity mismatch")
    if new_data["config"]["mask_sha256"] != [metadata[key]["sha256"] for key in ("mask_int", "mask_pol")]:
        raise ValueError("R102 mask identities differ")
    target = old["pseudo_cl_uK2"]["signal_plus_noise_00000"]
    result = {}
    for ch in CHANNELS:
        vals = np.asarray(new_data["pseudo_cl_ell2_up_uK2"][ch])
        local_err = np.max(np.abs(vals[:7] - target["ell_2_to_8"][ch]))
        mean_err = abs(vals.mean() - target["mean_ell_2_to_64"][ch])
        if not (local_err < 1e-9 and mean_err < 1e-9):
            raise ArithmeticError(f"R102 replay mismatch in {ch}: {local_err}, {mean_err}")
        result[ch] = dict(max_abs_ell_2_to_8_uK2=float(local_err), abs_mean_difference_uK2=float(mean_err))
    return {"index":0, "status":"real_pair_R102_replay", "input_sha256":new_data["raw_sha256"],
            "spectrum_sha256":_sha256_file(new), "reference_sha256":_sha256_file(previous),
            "config":new_data["config"], "errors":result, "n_pairs":1, "physical_Pi":None,
            "commander_null_qualified":False}


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("reduction",type=Path)
    p.add_argument("--reference",type=Path,default=PREVIOUS)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    atomic_json(args.output,compare(args.reduction,args.reference))
