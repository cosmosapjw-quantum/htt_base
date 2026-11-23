"""Build the H5 control variant of the R105 coupled solver (copy + asserted text patches).

Changes relative to htt/bass/transport/coupled_einstein_boltzmann.py (R105 b234bb0e0):
  1. Radau rtol/atol read from module globals RADAU_RTOL/RADAU_ATOL (defaults equal R105: 1e-10/1e-13).
  2. Extra *read-only* diagnostics recorded per cell when record_history=True:
     - fluid q/E recomputed from the dense output sol.sol(N_end) (same _unpack path) and the raw
       conserved ratio r = y[off+1:off+4]; max |sol.sol(N_end) - sol.y[:, i1]| over the full state;
     - baryon velocity v_b(N_end), opacity.rate(N_end) and recomb opacity_per_efold[i1];
     - fluid-equation decomposition at N_end: full d r_gamma/dN, Thomson part (F[1:]-r F[0])/E,
       gravitational part G = full - Thomson, d v_b/dN (baryon r_b = v_b for K=0).
  No numerical path of the solution is altered: with default tolerances it must reproduce R105 bit-for-bit.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
SRC = REPO / "htt/bass/transport/coupled_einstein_boltzmann.py"
OUT = Path(__file__).resolve().parent / "coupled_h5_variant.py"

PATCHES = [
    (
        'Z_INITIAL = 1600.0\n',
        'Z_INITIAL = 1600.0\n'
        '# H5 control: Radau tolerances as module globals (R105 values by default).\n'
        'RADAU_RTOL = 1e-10\n'
        'RADAU_ATOL = 1e-13\n',
    ),
    (
        '            rtol=1e-10,\n            atol=1e-13,\n',
        '            rtol=RADAU_RTOL,\n            atol=RADAU_ATOL,\n',
    ),
    (
        '                "thomson_force_over_E_sky": np.zeros((n_c, 4)),\n            }\n',
        '                "thomson_force_over_E_sky": np.zeros((n_c, 4)),\n'
        '                # H5 read-only diagnostics\n'
        '                "q_over_E_fluid_dense": np.zeros((n_rad, n_c, 3)),\n'
        '                "r_raw_fluid": np.zeros((n_rad, n_c, 3)),\n'
        '                "y_dense_minus_grid_absmax": np.zeros(n_c),\n'
        '                "y_dense_minus_grid_relmax": np.zeros(n_c),\n'
        '                "v_b_end": np.zeros((n_c, 3)),\n'
        '                "rate_fn_end": np.zeros(n_c),\n'
        '                "rate_grid_end": np.zeros(n_c),\n'
        '                "drgamma_dN_full": np.zeros((n_c, 3)),\n'
        '                "drgamma_dN_thomson": np.zeros((n_c, 3)),\n'
        '                "dvb_dN": np.zeros((n_c, 3)),\n'
        '                "E_gamma_end": np.zeros(n_c),\n'
        '            }\n',
    ),
    (
        '                        record["thomson_force_over_E_sky"][cell] = rate * covariant_thomson_four_force(\n'
        '                            sky_t, vb_end, clock="conserved_anchor")\n',
        '                        record["thomson_force_over_E_sky"][cell] = rate * covariant_thomson_four_force(\n'
        '                            sky_t, vb_end, clock="conserved_anchor")\n'
        '                # ---- H5 read-only diagnostics (no effect on the evolved state) ----\n'
        '                N1 = float(N_eval[i1])\n'
        '                y_grid = sol.y[:, i1]\n'
        '                y_dense = np.asarray(sol.sol(N1), dtype=np.float64)\n'
        '                dyd = np.abs(y_dense - y_grid)\n'
        '                record["y_dense_minus_grid_absmax"][cell] = float(dyd.max())\n'
        '                record["y_dense_minus_grid_relmax"][cell] = float(np.max(dyd / np.maximum(np.abs(y_grid), 1e-300)))\n'
        '                T4_dense = _unpack(N1, y_dense)[11]\n'
        '                for slot, species_idx in enumerate(radiation_indices):\n'
        '                    offr = 16 + 4 * species_idx\n'
        '                    record["q_over_E_fluid_dense"][slot, cell] = T4_dense[species_idx][0, 1:] / T4_dense[species_idx][0, 0]\n'
        '                    record["r_raw_fluid"][slot, cell] = y_grid[offr + 1:offr + 4]\n'
        '                unp = _unpack(N1, y_grid)\n'
        '                T4g, vvg = unp[11], unp[13]\n'
        '                record["v_b_end"][cell] = vvg[baryon_idx]\n'
        '                rate_fn = float(opacity.rate(min(max(N1, N_start), N_end)))\n'
        '                record["rate_fn_end"][cell] = rate_fn\n'
        '                record["rate_grid_end"][cell] = float(recomb_hist.opacity_per_efold[i1])\n'
        '                dy_full = ode_rhs(N1, y_grid)\n'
        '                offg = 16 + 4 * photon_idx\n'
        '                offb = 16 + 4 * baryon_idx\n'
        '                Eg = float(T4g[photon_idx][0, 0])\n'
        '                rg = T4g[photon_idx][0, 1:] / Eg\n'
        '                Fg = _species_thomson_forces(T4g[photon_idx], vvg[baryon_idx], rate_fn,\n'
        '                                             len(species_specs), photon_idx, baryon_idx)[photon_idx]\n'
        '                record["drgamma_dN_full"][cell] = dy_full[offg + 1:offg + 4]\n'
        '                record["drgamma_dN_thomson"][cell] = (Fg[1:] - rg * Fg[0]) / Eg\n'
        '                record["dvb_dN"][cell] = dy_full[offb + 1:offb + 4]\n'
        '                record["E_gamma_end"][cell] = Eg\n',
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
