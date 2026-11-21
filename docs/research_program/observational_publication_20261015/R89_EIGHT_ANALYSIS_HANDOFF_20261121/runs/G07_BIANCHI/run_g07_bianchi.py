#!/usr/bin/env python3
"""R89 G07_BIANCHI group execution (create-only).

Reuses B01 11-family Lie/Jacobi/Codazzi algebra, verifies fail-closed gates for
missing external all-m polarized Bianchi solver / flux source, inspects the
retained external McEwen Bianchi v1.1 VIIh T-only test FITS map on /mnt/extdrive/workdir,
and runs R85 Fortran K02 32D shape parity without implementing an external solver.
"""
from __future__ import annotations

import hashlib
import json
import platform
import resource
import sys
import time
from pathlib import Path

import healpy as hp
import numpy as np

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import p4_bianchi_fast, p5p6_fast, phy_fast

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "RESULT.json"

PROG = ROOT / "docs/research_program/observational_publication_20261015"
B01_REG = PROG / "READY_20261016/B01_BIANCHI_ATLAS_REGISTRY.json"
R75_RES = PROG / "R75_P5_LIE_TILT_FIVEVIEW_20261119/RESULTS.json"
CF4_SEL = ROOT / "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
BIANCHI_DIR = Path("/mnt/extdrive/workdir/htt_open_data/external_transfer/bianchi_v1_1_1c90b98")
BIANCHI_TEST_FITS = BIANCHI_DIR / "test/sky_bianchi_test.fits"
BIANCHI_PAR = BIANCHI_DIR / "param.par"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    # 1. Reuse B01 11-family Bianchi Lie/Jacobi/Codazzi algebra
    reg = p4_bianchi_fast.validate_bianchi_registry()
    bk_hist = p5p6_fast.historical_BK_statuses()
    assert reg["canonical_count"] == 11 and reg["all_Jacobi_N_a_zero"] is True
    assert bk_hist["science_gates_modified"] is False

    r75 = json.loads(R75_RES.read_text(encoding="utf-8"))

    # 2. Verify fail-closed external polarized Bianchi solver gates
    fail_closed_b02 = False
    try:
        p5p6_fast.inspect_external_Bianchi_atlas(OUT_DIR / "__missing_external_polarized_atlas__.json")
    except FileNotFoundError:
        fail_closed_b02 = True
    assert fail_closed_b02

    fail_closed_phy = False
    try:
        phy_fast.inspect_external_native(OUT_DIR / "__missing_external_native__.json")
    except FileNotFoundError:
        fail_closed_phy = True
    assert fail_closed_phy

    # 3. Inspect retained external Bianchi v1.1 VII_h T-only test map (NOT all-m polarized atlas)
    t_map = hp.read_map(str(BIANCHI_TEST_FITS), field=0)
    cl_tt = hp.anafast(t_map, lmax=12)
    b11_diag = {
        "nside": int(hp.get_nside(t_map)),
        "npix": int(len(t_map)),
        "map_min_max_std": [float(np.min(t_map)), float(np.max(t_map)), float(np.std(t_map))],
        "cl_TT_ell2_to_6": [float(x) for x in cl_tt[2:7]],
        "polarized_E_B_present": False,
        "all_11_families_covered": False,
        "param_par_summary": [ln.strip() for ln in BIANCHI_PAR.read_text().splitlines() if ln.strip() and not ln.strip().startswith("#")],
        "scope_note": "Single McEwen Bianchi v1.1 Type VII_h temperature-only test fixture (Barrow et al. 1985, zero Lambda, omega0=0.50); does NOT supply SQ-NATIVE all-m E/B polarization or 11-family transfer.",
    }

    # 4. Run R85 Fortran 12-thread K02 32D shape parity & conditional subspace overlap check
    k02_src = p5p6_fast.prepare_cf4_method_source(CF4_SEL)
    k02_np = p5p6_fast.k02_method_profiled(k02_src, native_lib=None)
    k02_ft = p5p6_fast.k02_method_profiled(k02_src, native_lib="auto", threads=12)
    k02_rec = p5p6_fast.last_p5p6_receipt()
    k02_maxdiff = float(
        max(
            np.max(np.abs(k02_ft["shape8"] - k02_np["shape8"])),
            np.max(np.abs(k02_ft["joint_cov32"] - k02_np["joint_cov32"])),
        )
    )
    assert k02_ft["physical_shear"] is None and k02_ft["physical_Pi"] is None

    # Illustrative algebraic subspace overlap check on working covariance
    sub_ov = p5p6_fast.conditional_template_subspace_overlap(
        np.eye(8, 3), np.eye(8, 5, k=-3), k02_ft["joint_cov32"][:8, :8]
    )
    assert sub_ov["physical_family_evidence"] is None

    elapsed = time.perf_counter() - t0
    input_paths = (B01_REG, R75_RES, CF4_SEL, BIANCHI_TEST_FITS, BIANCHI_PAR)
    out = {
        "schema": "htt.r89.g07_bianchi_result/1",
        "group_id": "G07_BIANCHI",
        "node_ids": ["B01", "SQ-LIE-FLUX", "SQ-NATIVE", "B02", "B03", "B04", "B05"],
        "source_sha256": {str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p): _sha256(p) for p in input_paths},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "reused_B01_lie_algebra": {
            "registry_summary": reg,
            "r75_max_SO3_equivariance_err": r75["SO3_covariance"]["max_rotation_equivariance_error"],
            "historical_BK_science_nodes": bk_hist["science_nodes"],
        },
        "fail_closed_external_gates": {
            "p5p6_inspect_external_Bianchi_atlas_missing": "FileNotFoundError (fail-closed)",
            "phy_inspect_external_native_missing": "FileNotFoundError (fail-closed)",
        },
        "external_bianchi_v1_1_workdir_fixture": b11_diag,
        "r85_k02_fortran_parity": {
            "backend_used": k02_rec["used"],
            "source_certified": k02_rec["source_certified"],
            "fortran_vs_numpy_maxabs": k02_maxdiff,
            "condition_F": k02_ft["condition_F"],
            "working_subspace_overlap_singular_cosines": sub_ov["singular_cosines"],
            "physical_shear": k02_ft["physical_shear"],
            "physical_Pi": k02_ft["physical_Pi"],
        },
        "node_verdicts": {
            "B01": "REUSED_SCOPED",
            "SQ-LIE-FLUX": "BLOCKED_INPUT",
            "SQ-NATIVE": "BLOCKED_INPUT",
            "B02": "BLOCKED_DEPENDENCY",
            "B03": "BLOCKED_DEPENDENCY",
            "B04": "BLOCKED_DEPENDENCY",
            "B05": "BLOCKED_DEPENDENCY",
        },
        "missing_physics_and_next_action": {
            "missing": [
                "External native polarized all-m Bianchi transfer atlas across all 11 canonical types (T, E, B)",
                "Physical initial-condition normalization, recombination history, and Planck likelihood interface",
                "Independent normal-frame energy-flux and stress source closure (SQ-LIE-FLUX)",
            ],
            "next_action": "Await external native all-m polarized Bianchi solver handoff and independent normal-frame flux inputs; do not simulate solver or promote B02-B05.",
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G07_BIANCHI",
        "elapsed_s": round(elapsed, 3),
        "canonical_families": reg["canonical_count"],
        "k02_backend": k02_rec["used"],
        "k02_maxdiff": k02_maxdiff,
        "bianchi_v1_1_cl2_TT": cl_tt[2],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
