"""R107 cloud: gap register of the open nodes of the R78 60-node DAG (theory loop output).

Reads the R105 node record (60 nodes, 129 edges; R106 added evidence without new
acceptances) and joins a hand-written classification of every open node: what is
missing (DATA, THEORY, CODE, COMPUTE, DEPENDENCY, DECISION), the route, the owner
(cloud work done in R107 or local work) and the acceptance that closes it.  The script
fails closed when an open node is not classified, a classification names an unknown
node or acquisition item, or a dependency claim disagrees with the DAG.

Usage: python -m scripts.r107_cloud.gap_register --output GAP_REGISTER.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from scripts.r107_cloud.acquisition import ITEMS

ROOT = Path(__file__).resolve().parents[2]
NODE60 = ROOT / "docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124/NODE60_EXECUTION.json"
TYPES = {"DATA", "THEORY", "CODE", "COMPUTE", "DEPENDENCY", "DECISION"}

# R107 cloud artefacts referenced by routes
LOS = "htt/bass/transport/hybrid_los_transfer.py"
BJS = "htt/bass/transport/bjs_bianchi_vii_h.py"
REI = "htt/bass/recombination/rei_lowz_continuation.py"
TF = "R107 THEORY_FOUNDATIONS.md"

G = {
    "SQ-CMB-NULL": (["DATA", "COMPUTE"], ["D06", "D07"], "Commander pairs 7-299 and HM/OE splits through the existing R105 estimator; split-difference null.",
                    "local", "same-release null with >= 300 matched pairs and a split-difference zero-signal check"),
    "SQ-LIE-FLUX": (["THEORY", "DATA", "COMPUTE"], ["D08", "D11"], f"{TF} TF5: Codazzi relation q_a = 3 sigma_ab a^b - eps_abc sigma^b_d n^cd fixes the identifiable flux; supply q from independent frames (CMB dipole, radio dipole, CF4 bulk flow) with covariance.",
                    "local", "rank-aware Codazzi residual with independently sourced q and shear covariance"),
    "SQ-NATIVE": (["CODE", "COMPUTE"], ["D00"], f"{LOS} and BASS Rust _rustcore (R109-R111 native SDIRK2+congruence+LoS): C1 z=1600 FLRW depth<=5.83e-7, C3 12-family l<=128 convergence<=1e-3, C4 VII_h l<=64 vs BJS corr>=0.9996 (1.0000 w/ Doppler), C6 l=256 96.5s/65.2MiB. Open: T1-T3 physics specs & SQ-CMB-NULL calibrated null.",
                  "R111 local native runs complete (C1-C6); null needs SQ-CMB-NULL", "provenance-bound native vs independent comparator agreement and calibrated null (needs SQ-CMB-NULL for the null part)"),
    "B02": (["DEPENDENCY", "CODE", "COMPUTE"], ["D00"], f"{LOS} & BASS _rustcore R111 C3/C4/C6: 12-family all-m T/E/B to l<=128 (61 runs, types & h preserved, <=1e-3 convergence) and l=256 timing (89.0s LoS). Open: SQ-NATIVE/T1-T3 physical closures and qualified nulls.",
            "R111 local native l<=128/256 runs done; T1-T3 & nulls open", "Einstein/Boltzmann/recombination/constraint/IC/mode tests on actual runs plus LoS-vs-native and BJS agreement"),
    "SQ-PHOTON-FLUX": (["CODE", "COMPUTE"], [], f"{LOS}.history_window: independent line-of-sight photon moments q/E, pi/E at matched solver times; compare with the hierarchy and fluid moments.",
                       "cloud code done; local runs", "P - f f^T PSD and Einstein-Codazzi checks with independently computed photon moments"),
    "PHY-02": (["DEPENDENCY"], [], "after SQ-CMB-NULL, SQ-PHOTON-FLUX, SQ-LIE-FLUX", "local", "as in the DAG"),
    "L03": (["DEPENDENCY", "DATA", "COMPUTE"], ["D06", "D07"], "release-matched Commander null bank; residual foreground and weight-selection law.", "local", "simulation IDs independent; same mask/beam/foreground law"),
    "SQ-CF4": (["DATA", "COMPUTE"], ["D01", "D02", "D03"], "CF3 table3 overlap, 6dFGSv IDs and non-2MRS K magnitudes; calibrated method/selection holdout.", "local",
               "source-level C = N + S_PV + J Sigma J^T + C_sel with held-out coverage and explicit missing-source remainder"),
    "H02": (["DEPENDENCY", "DATA", "COMPUTE"], ["D01", "D04", "D05"], "independent field (2M++ C15) or posterior ensemble (Manticore); CF3-independent calibration window.", "local", "method-group overlap and correlated errors with reproduced source nulls"),
    "H04": (["DEPENDENCY", "COMPUTE"], [], "after H02 and H03", "local", "false-positive calibration and shared-calibration posterior predictive checks"),
    "SQ-FRAME": (["CODE", "COMPUTE"], [], "catalogue frame registry (position frame, epoch, redshift frame, velocity reference) on top of htt.obsstat.publication_frame_kinematics; boost/inverse validation on the same release.",
                 "local", "unit-tested frame dictionary per catalogue; no unmeasured beta"),
    "SQ-GAIA": (["DATA", "COMPUTE"], ["D08", "D09", "D10"], "ICRF3 centroid control, scan-law mocks and AGN cross-identification nulls.", "local", "16D fit reproduced on registered subset with source-specific null"),
    "K03": (["DEPENDENCY", "COMPUTE"], [], "after SQ-GAIA", "local", "independent source qualification and nonradial response"),
    "SQ-OPTICAL": (["DEPENDENCY", "COMPUTE"], [], "finite_redshift_optics / position_drift_optics exist; needs SQ-FRAME then held-out prediction on CF4/Gaia samples.", "local",
                   "z->0 local H, same-tensor scalar/E2 consistency, T_C, T_G and finite-z remainder with held-out prediction"),
    "B03": (["DEPENDENCY", "CODE", "COMPUTE"], [], f"after B02, L03, SQ-CMB-NULL, SQ-OPTICAL; R111 C5 projected native BASS l<=128 los_modes.tsv through R108 Commander lmax=256 kernel (up to 13.55% l>4 E-leakage into cut-sky l=2); R109 exact repro 0.0. Open: dependencies and scoring.",
            "R111 C5 projection done; scoring blocked on SQ-CMB-NULL/L03", "no fake T/E/B source or forged full-sky score"),
    "B04": (["DEPENDENCY", "COMPUTE"], [], "after B03; injection-recovery and family equivalence classes (compare Saadeh et al. 2016).", "local", "degenerate families reported as equivalence classes"),
    "K04": (["DEPENDENCY"], [], "after K02, H04, SQ-OPTICAL", "local", "unbounded output for null sectors; no zero fill"),
    "PHY-01": (["DEPENDENCY"], [], "after SQ-CF4, SQ-OPTICAL, SQ-LIE-FLUX", "local", "as in the DAG"),
    "PHY-05": (["DEPENDENCY"], [], "after SQ-LIE-FLUX, SQ-OPTICAL", "local", "as in the DAG"),
    "PHY-06": (["DEPENDENCY"], [], "after SQ-CMB-NULL, SQ-PHOTON-FLUX, SQ-LIE-FLUX, SQ-OPTICAL", "local", "as in the DAG"),
    "SQ-P1-ANCHOR": (["THEORY", "COMPUTE"], [], f"{TF} TF6: physical anchor = calibrated template response d a_lm / d(sigma/H)_0 from B02 (LoS) per family; R111 C1-C5 delivered deterministic z=1600+REI native pipeline & Commander projections (z<4 REI remains T3 HOLD placeholder). Proposed route (not a DAG edge): join to 274 rows once B02/B03 & independent covariances close.",
                     "R111 deterministic templates ready; covariance/T3 open", "one identified physical x with source covariance and partial identified interval"),
    "S02": (["DEPENDENCY"], [], "after SQ-P1-ANCHOR", "local", "as in the DAG"),
    "S03": (["DEPENDENCY"], [], "after S02", "local", "as in the DAG"),
    "SQ-RADIO": (["THEORY", "DATA", "COMPUTE"], ["D11"], f"{TF} TF7: C1 prior from LSS clustering theory (dN/dz, bias bracket) plus RACS-low cross-survey C1; feed the R106 closed-form p(C1) curve.",
                 "cloud spec; local compute", "one physically selected k, kappa with paired covariance and C1 fixed by independent input"),
    "PHY-03": (["DEPENDENCY"], [], "after SQ-RADIO, SQ-PHOTON-FLUX, SQ-FRAME", "local", "as in the DAG"),
    "PHY-04": (["DEPENDENCY"], [], "after SQ-GAIA, SQ-RADIO, SQ-OPTICAL, SQ-FRAME", "local", "as in the DAG"),
    "PHY-07": (["DEPENDENCY"], [], "after SQ-CF4, SQ-RADIO, SQ-OPTICAL, SQ-FRAME", "local", "as in the DAG"),
    "SQ-CROSS-COV": (["DEPENDENCY", "COMPUTE"], [], "after SQ-CF4, SQ-GAIA, SQ-RADIO, SQ-FRAME, SQ-OPTICAL", "local", "source-level cross-covariance and calibrated held-out prediction"),
    "K05": (["DEPENDENCY"], [], "after K03, K04, V03, SQ-CROSS-COV", "local", "as in the DAG"),
    "V04": (["DEPENDENCY", "COMPUTE"], [], "after V02, V03, H04, SQ-FRAME, SQ-RADIO", "local", "identified singular modes; no identification from a null column"),
    "B05": (["DEPENDENCY", "DECISION"], [], "after B04 and X02", "local", "real Planck likelihood and calibrated family modes, else HOLD"),
    "H05": (["COMPUTE", "DEPENDENCY"], [], "start now from R105 CF4_LITERATURE_H05.md and CF4_H05_AXES.json; formal acceptance after H04.", "local", "novel difference is covariance/window/calibration robustness"),
    "H06": (["DEPENDENCY", "DECISION"], [], "after H05", "local", "full law with competing models or an informative null"),
    "K06": (["DEPENDENCY", "DECISION"], [], "after K05 and X02", "local", "identified combinations with independent error budget"),
    "L04": (["DEPENDENCY", "COMPUTE"], [], "after L03", "local", "finite-MC ranks, nuisance sensitivity, look-elsewhere"),
    "L05": (["DEPENDENCY"], [], "after L04", "local", "no independent-sky multiplication"),
    "L06": (["DEPENDENCY", "DECISION"], [], "after L05", "local", "qualified simulations and reported null results"),
    "S04": (["DEPENDENCY"], [], "after S03 and X03", "local", "actual selected likelihood or justified outer interval"),
    "S05": (["DEPENDENCY", "DECISION"], [], "after S04", "local", "distinct from standard pushforward"),
    "S06": (["DEPENDENCY", "DECISION"], [], "after S05", "local", "all P1 gates with evidence or HOLD"),
    "V05": (["DEPENDENCY", "COMPUTE"], [], "after V04 and X03; injections on independent mocks", "local", "calibrated null and prior family"),
    "V06": (["DEPENDENCY", "DECISION"], [], "after V05 and X02", "local", "distinct transfer or non-identifiability statement"),
}


def build() -> dict:
    raw = NODE60.read_bytes()
    rec = json.loads(raw)
    nodes = {n["id"]: n for n in rec["nodes"]}
    open_ids = [n["id"] for n in rec["nodes"] if n["canonical_state"] != "completed_scoped"]
    missing = sorted(set(open_ids) - set(G))
    extra = sorted(set(G) - set(open_ids))
    if missing or extra:
        raise SystemExit(f"classification mismatch: missing {missing}, not open or unknown {extra}")
    items = {it["id"] for it in ITEMS}
    rows = []
    for nid in open_ids:
        types, data, route, owner, acceptance = G[nid]
        if not set(types) <= TYPES or not set(data) <= items:
            raise SystemExit(f"bad classification for {nid}")
        open_deps = [d for d in nodes[nid]["hard_dependencies"] if nodes[d]["canonical_state"] != "completed_scoped"]
        if ("DEPENDENCY" in types) != bool(open_deps):
            raise SystemExit(f"{nid}: DEPENDENCY flag disagrees with open hard dependencies {open_deps}")
        rows.append({"id": nid, "paper": nodes[nid]["paper"], "canonical_state": nodes[nid]["canonical_state"],
                     "gap_types": types, "open_hard_dependencies": open_deps, "acquisition_items": data,
                     "route": route, "owner": owner, "acceptance_to_close": acceptance,
                     "dag_acceptance": nodes[nid]["canonical_acceptance"]})
    counts = Counter(t for r in rows for t in r["gap_types"])
    return {"schema": "htt.r107.gap_register/1", "source": str(NODE60.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(raw).hexdigest(), "n_nodes": len(nodes), "n_open": len(rows),
            "gap_type_counts": dict(sorted(counts.items())),
            "unblocked_without_dependencies": sorted(r["id"] for r in rows if not r["open_hard_dependencies"]),
            "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args(argv)
    out = build()
    a.output.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_open", "gap_type_counts", "unblocked_without_dependencies")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
