#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np

try:
    import astropy.units as u
    from astropy.coordinates import SkyCoord
except Exception as e:
    raise SystemExit("astropy is required: pip install astropy") from e

CLIGHT = 299792.458
GRID_BOX_SIZE_MPC = 1000.0


def to_grid_index(coord, delta, N=128, L=GRID_BOX_SIZE_MPC):
    coord = coord + L / 2.0
    index = np.floor(coord / delta).astype(int)
    return np.clip(index, 0, N - 1)


def load_grid(npz_path: Path):
    x = np.load(npz_path)
    needed = [
        "d_mean_CF4pp", "d_std_CF4pp",
        "v_mean_CF4pp", "v_std_CF4pp",
        "vr_mean_CF4pp", "vr_std_CF4pp",
    ]
    out = {}
    for k in needed:
        if k not in x:
            raise KeyError(f"Missing key in CF4 grid file: {k}")
        out[k] = np.asarray(x[k])
    return out


def coords_to_supergalactic(coord1, coord2, distance, coord_type="equatorial", unit_type="degrees", distance_type="redshift"):
    units = u.deg if unit_type == "degrees" else u.rad
    distance_mpc = np.asarray(distance, dtype=float).copy()
    if distance_type == "redshift":
        distance_mpc = distance_mpc * CLIGHT / 100.0
    elif distance_type == "velocity":
        distance_mpc = distance_mpc / 100.0
    else:
        raise ValueError("distance_type must be 'redshift' or 'velocity'")

    if coord_type == "galactic":
        gc = SkyCoord(l=coord1 * units, b=coord2 * units, distance=distance_mpc * u.Mpc, frame="galactic")
    elif coord_type in ("equatorial", "equitorial", "fk5"):
        gc = SkyCoord(ra=coord1 * units, dec=coord2 * units, distance=distance_mpc * u.Mpc, frame="fk5", equinox="J2000.000")
    else:
        raise ValueError("coord_type must be 'galactic' or 'equatorial'")

    sg = gc.supergalactic
    sgc = SkyCoord(sgl=sg.sgl, sgb=sg.sgb, distance=distance_mpc * u.Mpc, frame="supergalactic")
    return sgc.cartesian.x.value, sgc.cartesian.y.value, sgc.cartesian.z.value


def query_loaded_grid(grid, coord1, coord2, distance, coord_type="equatorial", unit_type="degrees", distance_type="redshift"):
    sgx, sgy, sgz = coords_to_supergalactic(coord1, coord2, distance, coord_type, unit_type, distance_type)

    n_grid = int(np.asarray(grid["d_mean_CF4pp"]).shape[0])
    delta = GRID_BOX_SIZE_MPC / float(n_grid)
    ix = to_grid_index(np.asarray(sgx), delta, N=n_grid, L=GRID_BOX_SIZE_MPC)
    iy = to_grid_index(np.asarray(sgy), delta, N=n_grid, L=GRID_BOX_SIZE_MPC)
    iz = to_grid_index(np.asarray(sgz), delta, N=n_grid, L=GRID_BOX_SIZE_MPC)

    d_mean = grid["d_mean_CF4pp"][ix, iy, iz]
    d_std = grid["d_std_CF4pp"][ix, iy, iz]
    v_mean = grid["v_mean_CF4pp"][:, ix, iy, iz].T
    v_std = grid["v_std_CF4pp"][:, ix, iy, iz].T
    vr_mean = grid["vr_mean_CF4pp"][ix, iy, iz]
    vr_std = grid["vr_std_CF4pp"][ix, iy, iz]

    return {
        "delta_mean": np.asarray(d_mean),
        "delta_std": np.asarray(d_std),
        "vxyz_mean": np.asarray(v_mean),
        "vxyz_std": np.asarray(v_std),
        "vr_mean": np.asarray(vr_mean),
        "vr_std": np.asarray(vr_std),
        "sgx": np.asarray(sgx),
        "sgy": np.asarray(sgy),
        "sgz": np.asarray(sgz),
        "grid_index": np.stack([ix, iy, iz], axis=-1),
    }


def query_grid(grid_npz: Path, coord1, coord2, distance, coord_type="equatorial", unit_type="degrees", distance_type="redshift"):
    grid = load_grid(grid_npz)
    return query_loaded_grid(
        grid, coord1, coord2, distance,
        coord_type=coord_type, unit_type=unit_type, distance_type=distance_type,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", required=True, help="Path to CF4pp_mean_std_grids.npz")
    ap.add_argument("--coord1", type=float)
    ap.add_argument("--coord2", type=float)
    ap.add_argument("--distance", type=float)
    ap.add_argument("--coord-type", choices=["equatorial", "galactic"], default="equatorial")
    ap.add_argument("--unit-type", choices=["degrees", "radians"], default="degrees")
    ap.add_argument("--distance-type", choices=["redshift", "velocity"], default="redshift")
    ap.add_argument("--input-csv", help="CSV with columns coord1,coord2,distance or ra,dec,z or l,b,v")
    ap.add_argument("--out")
    args = ap.parse_args()

    if args.input_csv:
        import csv
        rows = []
        with open(args.input_csv, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                c1 = float(row.get("coord1", row.get("ra", row.get("l"))))
                c2 = float(row.get("coord2", row.get("dec", row.get("b"))))
                dist = float(row.get("distance", row.get("z", row.get("v"))))
                rows.append((c1, c2, dist))
        coord1 = np.array([r[0] for r in rows], dtype=float)
        coord2 = np.array([r[1] for r in rows], dtype=float)
        distance = np.array([r[2] for r in rows], dtype=float)
    else:
        if args.coord1 is None or args.coord2 is None or args.distance is None:
            raise SystemExit("Provide either --input-csv or --coord1 --coord2 --distance")
        coord1 = np.array([args.coord1], dtype=float)
        coord2 = np.array([args.coord2], dtype=float)
        distance = np.array([args.distance], dtype=float)

    out = query_grid(
        Path(args.grid), coord1, coord2, distance,
        coord_type=args.coord_type, unit_type=args.unit_type, distance_type=args.distance_type
    )

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.suffix == ".npz":
            np.savez(out_path, **out)
        else:
            serial = {k: np.asarray(v).tolist() for k, v in out.items()}
            out_path.write_text(json.dumps(serial, indent=2, ensure_ascii=False))
        print(out_path)
    else:
        serial = {k: np.asarray(v).tolist() for k, v in out.items()}
        print(json.dumps(serial, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
