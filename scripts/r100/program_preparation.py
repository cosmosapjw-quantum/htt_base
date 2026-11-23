"""R100 Part F: Strict 60-node execution preparation overlay inheriting frozen R78/R99 contracts."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Sequence

from scripts.r99 import program_preparation as r99_prep

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/research_program/observational_publication_20261015"
R78_DIR = BASE / "R78_UNIFIED_SCIENCE_DAG_20261119"
R99_DIR = BASE / "R99_FIFTH_BLOCKER_RESOLUTION_20261123"
OUT = BASE / "R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123"
FILE = "NODE60_EXECUTION_PREPARATION.json"

R78_DAG_SHA256 = "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
R99_OVERLAY_SHA256 = "7bcf01630318b4701ac0a8973a0180de727c527aa2ba542e8660b2a5d84a235e"
ORIGINAL_42_SHA256 = "e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _pin(path: Path) -> dict[str, object]:
    p = Path(path)
    rel = str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
    return {
        "path": rel,
        "exists": p.exists(),
        "sha256": sha256(p) if p.exists() else None,
        "bytes": p.stat().st_size if p.exists() else None,
    }


R100_BLOCKER_DELTAS: dict[str, dict[str, object]] = {
    "D01": {
        "delta": (
            "R100 ingested bounded SDSS_PV_public.dat (34,059 rows, 20,231,640 B, MD5 verified) and "
            "6dFGSv table1.txt (8,885 rows incl. 6,219 -1 sentinels, 696,070 B, MD5 verified), matched "
            "34,045 SDSS PGCs + 8,885 6dFGSv IDs to CF4 table2/table3/table4, proved native SDSS ldc "
            "and 6dF delta_d agree positively (+0.7733 on 45 shared galaxies), yet discovered table2 DMfp "
            "assigns +4.978*ldc to SDSS vs -5.027*delta_d to 6dFGSv (Dec>0 dipole reversal sensitivity quantified)."
        ),
        "remaining_block": "Pre-intercalibration unshifted SNIa/TF/SBF/TRGB/Cepheid/maser tables, zero-point covariance, and authoritative CF4 pipeline sign provenance for SDSS vs 6dF.",
        "lane_tag": "BLOCKED_DATA",
        "evidence_packages": ["SOURCE_INTAKE", "CF4_KBAND_GENEALOGY"],
    },
    "D02": {
        "delta": (
            "Constructed 6-stage SDSS (34,059 -> 28,285/z-cut/table2) and 6dFGSv (8,885 -> 2,666 grouped -> "
            "matched) population ledgers, fitted empirical probit inclusion laws, and evaluated normalized "
            "joint_selected_logpdf on matched 6dFGSv."
        ),
        "remaining_block": "Full-union CF4 pre-selection rejected parent denominators across TF, SNIa, and SBF.",
        "lane_tag": "BLOCKED_DATA",
        "evidence_packages": ["CF4_KBAND_GENEALOGY"],
    },
    "M01": {
        "delta": (
            "Computed full 3-band [1e-4, 1.0] h/Mpc correlated PV S_PV matrices matrix-free via per-panel FINUFFT "
            "across R={5,10,20} Mpc/h and all 4 observables (WF_log, background_proxy, native_comoving, bolometric), "
            "assembled 4-term C_36 trace budget (N_meas + N_nl150 + S_PV + J_cal Sigma_cal J_cal^T + C_sel), and octant CV."
        ),
        "remaining_block": "Authoritative uncalibrated zero-point/selection physical generative law and independent physical holdout.",
        "lane_tag": "MODEL_CONDITIONAL",
        "evidence_packages": ["CF4_KBAND_GENEALOGY"],
    },
    "M02": {
        "delta": (
            "Derived and verified exact finite-z position drift dn/dtau_o across FLRW, I, V, VII_h, VI_h "
            "(Bianchi I coordinate-ray oracle 4.41e-9, Milne Type V zero drift, SO(3) equivariance 1.50e-12, "
            "secular aberration 3.11e-15 uas/yr), separated observer vs emitter T_C(z) and T_G(z) kernels, and "
            "quantified VI_h finite-z E2/B2 helical proper motion (B2/E2=4.62% at z=2.461; 15.06% z=2 remainder)."
        ),
        "remaining_block": "Release-qualified physical Gaia/CF4 joint astrometric+PV likelihood calibration and source-frame closure.",
        "lane_tag": "MODEL_CONDITIONAL",
        "evidence_packages": ["OPTICAL_DRIFT", "GAIA_OPTICAL_JOINT"],
    },
    "D03": {
        "delta": "Verified exact SHA-256 preservation of R98 PR3 CMB_GROUPED_FULL_CACHE.json and CMB_OBSERVED_SPLITS.json without altering noise genealogy.",
        "remaining_block": "PR4/NPIPE component-separated maps and independent FFP12-style paired noise ensemble remain external.",
        "lane_tag": "BLOCKED_EXTERNAL",
        "evidence_packages": ["BIANCHI_SELFCONSISTENT_PHY"],
    },
    "M04": {
        "delta": "Preserved grouped noise cross-fitting guard (commander_null_qualified=false, physical_Pi=None).",
        "remaining_block": "Matched component-separation/foreground null ensemble for PR4/PR3 splits.",
        "lane_tag": "BLOCKED_EXTERNAL",
        "evidence_packages": ["BIANCHI_SELFCONSISTENT_PHY"],
    },
    "D04": {
        "delta": "Audited pmra/pmdec provenance (zero parallax substitution) and isolated separate 15/30/60 deg C_sys outside rank-47 C_jk.",
        "remaining_block": "Gaia release-calibrated AGIS spatial scan error law and independent AGN host/centroid controls.",
        "lane_tag": "BLOCKED_DATA",
        "evidence_packages": ["GAIA_OPTICAL_JOINT"],
    },
    "M05": {
        "delta": (
            "Executed rank-47 positive eigenspace whitening (avoiding 64D/160D inversion), separated constant 16D floor + "
            "beta_o + beta_e + VI_h finite-z across 4 Quaia shells, and quantified joint CF4+Gaia profiled Fisher SV gain."
        ),
        "remaining_block": "Uncalibrated AGIS scan+AGN+physical Bianchi normal-frame covariance closure.",
        "lane_tag": "MODEL_CONDITIONAL",
        "evidence_packages": ["GAIA_OPTICAL_JOINT"],
    },
    "D05": {
        "delta": (
            "Audited all 1,580 LoTSS DR3 mosaics (4.04e11 px, 1.62 TB primary FITS metadata) and proved unmasked "
            "LoTSS_DR3_outer_b15 adds 112 zero-count cells elevating 50 mJy NB1 dipole from 0.0110 (legacy966) to 0.8469."
        ),
        "remaining_block": "Per-mosaic weight holes & local RMS/completeness maps reside in SURF tape HP-misc-*.tar (HTTP 202 deferred).",
        "lane_tag": "BLOCKED_EXTERNAL",
        "evidence_packages": ["RADIO_EXPOSURE_SELECTION"],
    },
    "M06": {
        "delta": (
            "Fitted fixed-offset Poisson, NB1_Pearson, NB1_MLE, NB2_CoxLSS GLMs across all 5 radio surveys (19 cuts) "
            "with zero-cell retention and exact scale invariance, plus exact finite-boost Doppler/aberration/SED reselection."
        ),
        "remaining_block": "Physical shared-source Cox/LSS mocks calibrated against LoTSS completeness & PyBDSF RMS maps.",
        "lane_tag": "MODEL_CONDITIONAL",
        "evidence_packages": ["RADIO_EXPOSURE_SELECTION"],
    },
    "M07": {
        "delta": (
            "Constructed matched position-drift T_G(z) and luminosity-distance T_C(z) kernels separating beta_o vs beta_e, "
            "exposing single-survey FLRW near-collinearity vs joint CF4+Gaia profiled Fisher SV separation."
        ),
        "remaining_block": "Independent physical normal-frame velocity calibration across optical+radio+PV.",
        "lane_tag": "MODEL_CONDITIONAL",
        "evidence_packages": ["OPTICAL_DRIFT", "GAIA_OPTICAL_JOINT", "RADIO_EXPOSURE_SELECTION"],
    },
    "D06": {
        "delta": "Preserved exact normal-frame species stress-energy book-keeping; derived optical drift + Thomson momentum constraints.",
        "remaining_block": "Independent external normal-frame photon/matter flux measurements.",
        "lane_tag": "BLOCKED_DATA",
        "evidence_packages": ["BIANCHI_SELFCONSISTENT_PHY"],
    },
    "M08": {
        "delta": (
            "Implemented Radau iterated k=0..4 coupled radiation-shear-baryon Thomson drag + pi_gamma(N) backreaction "
            "across FLRW, I, V, VII_h, VI_h preserving Hamiltonian/Codazzi < 1e-6, zero 4-momentum defect, and full contraction."
        ),
        "remaining_block": "All-family native linear Boltzmann perturbation transfer atlas (SQ-NATIVE) remains external.",
        "lane_tag": "MODEL_CONDITIONAL",
        "evidence_packages": ["BIANCHI_SELFCONSISTENT_PHY"],
    },
    "M09": {
        "delta": "Preserved coupled baryon-photon recombination/reionization opacity timeline without tuning physical thermal parameters.",
        "remaining_block": "Self-consistent anisotropic recombination chemistry solved simultaneously on curved Bianchi hypersurfaces.",
        "lane_tag": "BLOCKED_EXTERNAL",
        "evidence_packages": ["BIANCHI_SELFCONSISTENT_PHY"],
    },
    "A01": {
        "delta": "Completed CF4 octant CV & 4-term C_36 decomposition across full [1e-4, 1.0] h/Mpc k-band.",
        "remaining_block": "Physical source-law validation once upstream unshifted tables/sign provenance resolve D01/D02.",
        "lane_tag": "MODEL_CONDITIONAL",
        "evidence_packages": ["CF4_KBAND_GENEALOGY"],
    },
    "A02": {"delta": "Preserved P2 SHA guard & raw SMICA fold-0 tail provenance.", "remaining_block": "Matched PR4/FFP12 calibration.", "lane_tag": "BLOCKED_EXTERNAL", "evidence_packages": ["BIANCHI_SELFCONSISTENT_PHY"]},
    "A03": {"delta": "Verified Radau vs DOP853 parity & k=0..4 convergence across 5 canonical Bianchi families + AniLoS near-FLRW.", "remaining_block": "Full external native all-m solver atlas.", "lane_tag": "BLOCKED_EXTERNAL", "evidence_packages": ["BIANCHI_SELFCONSISTENT_PHY"]},
    "A04": {"delta": "Computed rank-47 Gaia+CF4 joint profiled Fisher SVD and 5-survey 48-patch radio GLS sensitivity.", "remaining_block": "Common physically calibrated mock lightcone covariance across CF4+Gaia+Radio+CMB.", "lane_tag": "MODEL_CONDITIONAL", "evidence_packages": ["GAIA_OPTICAL_JOINT", "RADIO_EXPOSURE_SELECTION", "BIANCHI_SELFCONSISTENT_PHY"]},
    "A05": {"delta": "Quantified SDSS vs 6dF DMfp sign flip, empty-cell LoTSS exposure effect, and NB2 vs NB1 likelihood gain.", "remaining_block": "Calibrated completeness-aware physical mock injection campaigns.", "lane_tag": "MODEL_CONDITIONAL", "evidence_packages": ["CF4_KBAND_GENEALOGY", "RADIO_EXPOSURE_SELECTION"]},
    "A06": {"delta": "Updated R100 manifest, claim firewalls (physical_Pi=None, physical_GF=None, calibrated_p=None), and zero gate promotions.", "remaining_block": "Upstream D01-D05, M01-M09 resolutions required prior to manuscript claim promotion.", "lane_tag": "MODEL_CONDITIONAL", "evidence_packages": ["PROGRAM_PREPARATION"]},
    "M03": {"delta": "Preserved exact correlated four-window P1 signed weights alongside full-k 4-term C_36.", "remaining_block": "Physical body/anchor calibration for P1 finite-law likelihood.", "lane_tag": "BLOCKED_DATA", "evidence_packages": ["CF4_KBAND_GENEALOGY"]},
}


def build() -> dict[str, object]:
    """Assemble strict R100 60-node execution preparation payload without relaxing R78 or R99 pins."""
    dag_path = R78_DIR / "INTEGRATED_DAG.json"
    r99_path = R99_DIR / FILE
    pub_path = BASE / "PUBLICATION_DAG.json"
    if sha256(dag_path) != R78_DAG_SHA256:
        raise ValueError(f"R78 INTEGRATED_DAG.json SHA mismatch: {sha256(dag_path)}")
    if sha256(r99_path) != R99_OVERLAY_SHA256:
        raise ValueError(f"R99 {FILE} SHA mismatch: {sha256(r99_path)}")

    dag = r99_prep.read(dag_path)
    old_r99 = r99_prep.read(r99_path)
    original_nodes = r99_prep.read(pub_path)["nodes"]

    data = copy.deepcopy(old_r99)
    data["schema"] = "htt.r100.exact60_preparation/1"
    data["inherited_overlay_sha256"] = R99_OVERLAY_SHA256
    data["r78_authority_sha256"] = R78_DAG_SHA256
    data["original_42_payload_sha256"] = ORIGINAL_42_SHA256
    data["interpretation"] = (
        "R100 solver-free source intake, full-k CF4 S_PV/selection, exact finite-z optical drift, "
        "radio exposure/reselection GLMs, Gaia/Quaia rank-47 joint identifiability, and iterated coupled "
        "Bianchi+radiation evolution; original 42 science gates and SQ-CF4 entry remain unpromoted."
    )

    data["packages"] = {
        **old_r99["packages"],
        "SOURCE_INTAKE": {
            "command": [".venv/bin/python", "-B", "-m", "scripts.r100.source_intake"],
            "script": _pin(ROOT / "scripts/r100/source_intake.py"),
            "outputs": [_pin(OUT / "SOURCE_INTAKE_RECEIPT.json")],
            "lane_tag": "SOURCE_QUALIFIED",
        },
        "CF4_KBAND_GENEALOGY": {
            "command": [".venv/bin/python", "-B", "-m", "scripts.r100.cf4_upstream_and_kband"],
            "script": _pin(ROOT / "scripts/r100/cf4_upstream_and_kband.py"),
            "outputs": [_pin(OUT / "CF4_UPSTREAM_KBAND_RESULTS.json"), _pin(OUT / "CF4_FULL_KBAND_COVARIANCES.npz")],
            "lane_tag": "SOURCE_QUALIFIED",
        },
        "OPTICAL_DRIFT": {
            "command": [".venv/bin/python", "-B", "-m", "scripts.r100.optical_drift"],
            "script": _pin(ROOT / "scripts/r100/optical_drift.py"),
            "transport_module": _pin(ROOT / "htt/bass/transport/position_drift_optics.py"),
            "outputs": [_pin(OUT / "OPTICAL_DRIFT_RESULTS.json"), _pin(OUT / "OPTICAL_DRIFT_TEMPLATES.npz")],
            "lane_tag": "MODEL_CONDITIONAL",
        },
        "RADIO_EXPOSURE_SELECTION": {
            "command": [".venv/bin/python", "-B", "-m", "scripts.r100.radio_exposure_selection"],
            "script": _pin(ROOT / "scripts/r100/radio_exposure_selection.py"),
            "outputs": [_pin(OUT / "RADIO_EXPOSURE_SELECTION_RESULTS.json")],
            "lane_tag": "MODEL_CONDITIONAL",
        },
        "GAIA_OPTICAL_JOINT": {
            "command": [".venv/bin/python", "-B", "-m", "scripts.r100.gaia_optical_joint"],
            "script": _pin(ROOT / "scripts/r100/gaia_optical_joint.py"),
            "outputs": [_pin(OUT / "GAIA_OPTICAL_JOINT_RESULTS.json")],
            "lane_tag": "MODEL_CONDITIONAL",
        },
        "BIANCHI_SELFCONSISTENT_PHY": {
            "command": [".venv/bin/python", "-B", "-m", "scripts.r100.bianchi_selfconsistent_and_phy"],
            "script": _pin(ROOT / "scripts/r100/bianchi_selfconsistent_and_phy.py"),
            "outputs": [_pin(OUT / "BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json")],
            "lane_tag": "MODEL_CONDITIONAL",
        },
        "PROGRAM_PREPARATION": {
            "command": [".venv/bin/python", "-B", "-m", "scripts.r100.program_preparation", "prepare"],
            "script": _pin(Path(__file__).resolve()),
            "lane_tag": "MODEL_CONDITIONAL",
        },
    }

    pkg_outputs = {
        "SOURCE_INTAKE": str((OUT / "SOURCE_INTAKE_RECEIPT.json").relative_to(ROOT)),
        "CF4_KBAND_GENEALOGY": str((OUT / "CF4_UPSTREAM_KBAND_RESULTS.json").relative_to(ROOT)),
        "OPTICAL_DRIFT": str((OUT / "OPTICAL_DRIFT_RESULTS.json").relative_to(ROOT)),
        "RADIO_EXPOSURE_SELECTION": str((OUT / "RADIO_EXPOSURE_SELECTION_RESULTS.json").relative_to(ROOT)),
        "GAIA_OPTICAL_JOINT": str((OUT / "GAIA_OPTICAL_JOINT_RESULTS.json").relative_to(ROOT)),
        "BIANCHI_SELFCONSISTENT_PHY": str((OUT / "BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json").relative_to(ROOT)),
    }

    for bid, blk in data["blockers"].items():
        if bid in R100_BLOCKER_DELTAS:
            binfo = R100_BLOCKER_DELTAS[bid]
            blk["r100_cycle_delta"] = binfo["delta"]
            blk["r100_remaining_block"] = binfo["remaining_block"]
            blk["r100_lane_tag"] = binfo["lane_tag"]
            blk["r100_evidence_packages"] = list(binfo["evidence_packages"])

    for node in data["nodes"]:
        all_b = node.get("all_blockers_including_dependencies", [])
        updated_b = [b for b in all_b if b in R100_BLOCKER_DELTAS]
        added_res: list[str] = []
        tags: list[str] = []
        for b in updated_b:
            binfo = R100_BLOCKER_DELTAS[b]
            if binfo["lane_tag"] not in tags:
                tags.append(str(binfo["lane_tag"]))
            for pk in binfo["evidence_packages"]:
                if pk in pkg_outputs and pkg_outputs[pk] not in added_res:
                    added_res.append(pkg_outputs[pk])
        if node["id"] == "SQ-NATIVE":
            tags = ["BLOCKED_EXTERNAL"]
        node["r100_lane_tags"] = tags if tags else (["SOURCE_QUALIFIED"] if node["science_status"] == "INHERITED_COMPLETED_SCOPED" else ["BLOCKED_DATA"])
        node["r100_updated_blockers"] = updated_b
        existing_res = list(node.get("available_results", []))
        for r in added_res:
            if r not in existing_res:
                existing_res.append(r)
        node["available_results"] = existing_res
        node["r100_new_acceptance_claimed"] = False

    # Enforce strict immutable contract against R78 INTEGRATED_DAG and PUBLICATION_DAG original 42!
    r99_prep.verify_contract(dag, data, original_nodes)
    return data


def render_blocker_markdown(data: dict[str, object]) -> str:
    lines = [
        "# R100 Execution Preparation & Blocker Resolution Ledger",
        "",
        f"- Canonical R78 DAG SHA-256: `{R78_DAG_SHA256}` (60 nodes, 129 edges, `next_id={data['next_id']}`)",
        f"- Frozen R99 Overlay SHA-256: `{R99_OVERLAY_SHA256}`",
        f"- Original 42 Gates Payload SHA-256: `{ORIGINAL_42_SHA256}` (`new_science_nodes_promoted={data['counts']['new_science_nodes_promoted']}`)",
        "",
        "| Blocker | Category | Lane Tag | Remaining Physical/External Block | R100 Delta Summary |",
        "|---|---|---|---|---|",
    ]
    for bid, blk in data["blockers"].items():
        lines.append(
            f"| `{bid}` | {blk['category']} | `{blk.get('r100_lane_tag', 'INHERITED')}` | "
            f"{blk.get('r100_remaining_block', blk['current_defect'])} | {blk.get('r100_cycle_delta', blk['cycle_delta'])} |"
        )
    lines.append("")
    lines.append("## Selected Progress Nodes")
    lines.append("")
    lines.append("| Node | Science Status | R100 Lane Tags | Updated Blockers |")
    lines.append("|---|---|---|---|")
    for n in data["nodes"]:
        if n["id"].startswith("SQ-") or n["id"].startswith("PHY-") or n["id"] in {"S02", "L03", "H02", "V04", "B02", "K03"}:
            lines.append(
                f"| `{n['id']}` | `{n['science_status']}` | `{', '.join(n.get('r100_lane_tags', []))}` | `{', '.join(n.get('r100_updated_blockers', [])) or '—'}` |"
            )
    return "\n".join(lines) + "\n"


def write_artifact_manifest(data: dict[str, object]) -> dict[str, object]:
    files = sorted(
        [
            OUT / "SOURCE_INTAKE_RECEIPT.json",
            OUT / "OPTICAL_DRIFT_RESULTS.json",
            OUT / "OPTICAL_DRIFT_TEMPLATES.npz",
            OUT / "CF4_UPSTREAM_KBAND_RESULTS.json",
            OUT / "CF4_FULL_KBAND_COVARIANCES.npz",
            OUT / "RADIO_EXPOSURE_SELECTION_RESULTS.json",
            OUT / "GAIA_OPTICAL_JOINT_RESULTS.json",
            OUT / "BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json",
            OUT / FILE,
            OUT / "BLOCKER_ACTIONS.md",
            OUT / "ARTIFACT_MANIFEST.json",
            OUT / "REPORT_KO.md",
            ROOT / "htt/bass/transport/position_drift_optics.py",
            ROOT / "scripts/r100/source_intake.py",
            ROOT / "scripts/r100/cf4_upstream_and_kband.py",
            ROOT / "scripts/r100/optical_drift.py",
            ROOT / "scripts/r100/radio_exposure_selection.py",
            ROOT / "scripts/r100/gaia_optical_joint.py",
            ROOT / "scripts/r100/bianchi_selfconsistent_and_phy.py",
            ROOT / "scripts/r100/program_preparation.py",
            ROOT / "scripts/r100/validate_cycle.py",
        ],
        key=lambda p: str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),
    )
    manifest = {
        "schema": "htt.r100.artifact_manifest/1",
        "claim_firewall": {
            "physical_Pi": None,
            "physical_GF": None,
            "calibrated_p": None,
            "Bianchi_family_attribution": None,
            "new_science_nodes_promoted": 0,
            "next_science_id": data["next_id"],
        },
        "authorities": {
            "r78_dag_sha256": R78_DAG_SHA256,
            "r99_overlay_sha256": R99_OVERLAY_SHA256,
            "original_42_sha256": ORIGINAL_42_SHA256,
        },
        "artifacts": [_pin(p) for p in files],
    }
    (OUT / "ARTIFACT_MANIFEST.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("prepare")
    sci = sub.add_parser("science")
    sci.add_argument("--node", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    data = build()
    out_file = OUT / FILE
    md_file = OUT / "BLOCKER_ACTIONS.md"
    if args.check:
        if not out_file.exists():
            raise ValueError(f"Missing saved execution preparation: {out_file}")
        saved = json.loads(out_file.read_text())
        if saved != data:
            raise ValueError("Saved execution preparation diverges from deterministic build()")
        if not md_file.exists() or md_file.read_text() != render_blocker_markdown(data):
            raise ValueError("Saved BLOCKER_ACTIONS.md diverges from deterministic render")
        return 0
    if args.cmd == "science":
        row = next((n for n in data["nodes"] if n["id"] == args.node), None)
        if row is None:
            raise SystemExit(2)
        if row["science_status"] == "INHERITED_COMPLETED_SCOPED":
            print(json.dumps({"node": row["id"], "status": row["science_status"]}))
            return 0
        print(json.dumps({
            "node": row["id"],
            "science_status": row["science_status"],
            "r100_lane_tags": row["r100_lane_tags"],
            "direct_blockers": row["direct_blockers"],
            "all_blockers": row["all_blockers_including_dependencies"],
        }, indent=2))
        return 3
    # Default or "prepare"
    OUT.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    md_file.write_text(render_blocker_markdown(data))
    write_artifact_manifest(data)
    print(json.dumps({"status": "PREPARED", "nodes": len(data["nodes"]), "next_id": data["next_id"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
