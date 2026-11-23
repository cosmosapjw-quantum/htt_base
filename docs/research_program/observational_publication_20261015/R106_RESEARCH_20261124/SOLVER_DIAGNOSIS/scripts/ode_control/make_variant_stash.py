"""Second H5 variant: v1 (coupled_h5_variant.py) + a read-only stash of the final-Picard fluid solution.

The stash keeps references to the Radau OdeSolution, the opacity history and the RHS/unpack closures
so that a driver can integrate the *fluid* photon momentum equation with the photon cell's
SDIRK(2,2) substep/stage scheme after the solve. The solver's numerical path is unchanged.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "coupled_h5_variant.py"
OUT = HERE / "coupled_h5_variant_stash.py"

PATCHES = [
    (
        'RADAU_ATOL = 1e-13\n',
        'RADAU_ATOL = 1e-13\n'
        '# Read-only references to the most recent Picard fluid solution (H5 mimic driver).\n'
        '_H5_STASH: dict = {}\n',
    ),
    (
        '        if not sol.success:\n'
        '            raise CodazziProjectionError(f"[{family}] coupled Einstein-Euler ODE failed: {sol.message}")\n',
        '        if not sol.success:\n'
        '            raise CodazziProjectionError(f"[{family}] coupled Einstein-Euler ODE failed: {sol.message}")\n'
        '        _H5_STASH.clear()\n'
        '        _H5_STASH.update(sol=sol, opacity=opacity, ode_rhs=ode_rhs, unpack=_unpack, N_eval=N_eval.copy(),\n'
        '                         photon_idx=photon_idx, baryon_idx=baryon_idx, picard_idx=picard_idx,\n'
        '                         n_species=len(species_specs), N_start=N_start, N_end=N_end)\n',
    ),
]


def main() -> int:
    text = SRC.read_text()
    for old, new in PATCHES:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"anchor found {n} times (expected 1): {old[:80]!r}")
        text = text.replace(old, new)
    OUT.write_text(text)
    print("source", SRC, hashlib.sha256(SRC.read_bytes()).hexdigest())
    print("variant", OUT, hashlib.sha256(OUT.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
