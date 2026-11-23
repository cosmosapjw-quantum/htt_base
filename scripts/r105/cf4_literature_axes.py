"""Project the measured 2MRS field and exact bounded missing-row support on two published axes."""
import argparse
import json
from pathlib import Path

import numpy as np

from scripts.r103 import manticore_cf4_pv as pv
from scripts.r104 import cf4_2mrs_field as field
from scripts.r105.cross_routes import missing_support

AXES = {"Boubel_2025_fig4": (142., 52.), "Stiskalek_2026_sec4_1": (127., 10.)}


def analyze():
    _, directions, distances, weights = pv.geometry()
    galactic = field.to_galactic(directions)
    velocity, covered = field.interpolate(field.load_field(), galactic * (distances * field.H_LITTLE)[:, None])
    radial = np.sum(velocity[covered] * galactic[covered], axis=1)
    measured = weights[:, covered] @ radial
    rows = {}
    for label, (lon, lat) in AXES.items():
        l, b = np.deg2rad((lon, lat))
        gal_axis = np.array([np.cos(l)*np.cos(b), np.sin(l)*np.cos(b), np.sin(b)])
        eq_axis = field.to_galactic(np.eye(3)) @ gal_axis
        if not np.allclose(directions @ eq_axis, galactic @ gal_axis, atol=2e-15, rtol=0):
            raise ArithmeticError("axis rotation is inconsistent")
        op = np.einsum("a,wan->wn", eq_axis, weights.reshape(4, 9, -1)[:, 1:4])
        known = op[:, covered] @ radial
        check = measured.reshape(4, 9)[:, 1:4] @ eq_axis
        np.testing.assert_allclose(known, check, rtol=1e-12, atol=1e-15)
        box, coherent = missing_support(op[:, ~covered], galactic[~covered])
        if np.any(box <= 0.) or np.any(coherent <= 0.) or np.any(coherent > box + 1e-15):
            raise ArithmeticError("unexpected missing-row supports")
        rows[label] = {"galactic_lb_deg": [lon, lat], "unit_icrs": eq_axis.tolist(),
                       "known_log_dipole_projection": known.tolist(),
                       "independent_width_per_kms": box.tolist(), "coherent_width_per_kms": coherent.tolist(),
                       "independent_sign_cancellation_speed_kms": (np.abs(known)/box).tolist(),
                       "coherent_sign_cancellation_speed_kms": (np.abs(known)/coherent).tolist()}
    return {"schema": "htt.r105.h05_literature_axes.v1", "source_sha256": pv.SOURCE_SHA,
            "field_axes_sha256": field.FIELD_SHA, "windows_z": [.025,.040,.060,.080],
            "total_groups": len(covered), "field_covered": int(sum(covered)), "field_missing": int(sum(~covered)),
            "quantity": "2MRS contribution to R98 natural-log expansion-ratio dipole along each external direction",
            "scope": "Exact one-dimensional conditional support for each window separately. No prior or measured maximum speed for missing galaxies; no physical H0 fit.",
            "axes": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    path = parser.parse_args().output
    path.write_text(json.dumps(analyze(), indent=2, allow_nan=False) + "\n")
