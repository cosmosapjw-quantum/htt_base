"""Generate the finite L01 shared-anchor result from pinned committed summaries."""
from pathlib import Path
import hashlib
import json
import math
import platform
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from l01_anchor_geometry import shared_anchor_bounds

HEAD = "967ef7c8f0b132ecaaba343045d333d4ebf299c1"
PREFIX = "docs/research_program/observational_publication_20261015/L01_SMICA_QU_BAND_ACCOUNTING_20261017/"
PINS = {
    "MATCHED_SPLIT_STREAM_PROGRESS_20261018.json": "bca4231760c9b19faef9d0da9bb445288faea3ce",
    "NATIVE_RESIDUAL_VISIBILITY_PROGRESS.json": "17d67c6466ab78df998a8eb9e37ae8c58c4726f4",
}


def main():
    data, sources = {}, []
    for name, expected in PINS.items():
        raw = (ROOT / "inputs" / name).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if blob != expected:
            raise ValueError("PINNED_SUMMARY_CHANGED_" + name)
        data[name] = json.loads(raw)
        sources.append({"repo_path": PREFIX + name, "git_commit": HEAD,
                        "git_blob": blob, "sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw)})
    matched = data["MATCHED_SPLIT_STREAM_PROGRESS_20261018.json"]["user_evidence"]["components"]
    native = data["NATIVE_RESIDUAL_VISIBILITY_PROGRESS.json"]["user_evidence"]["components"]
    groups = {}
    for group in ("all", "E", "B"):
        m, n = matched[group], native[group]
        a = m["original_norm"]
        if not math.isclose(a, n["direct_norm_K_CMB"], rel_tol=1e-12, abs_tol=0):
            raise ValueError("SHARED_ANCHOR_NORM_MISMATCH_" + group)
        lengths = {"anchor_norm": a, "matched_norm": m["matched_norm"],
                   "reconstructed_norm": n["reconstructed_norm_K_CMB"],
                   "anchor_matched_distance": m["estimator_change_norm"],
                   "anchor_reconstructed_distance": n["measured_residual_norm_K_CMB"]}
        result = shared_anchor_bounds(**lengths)
        result["input_lengths_K_CMB"] = lengths
        result["estimator_change_over_native_L128_residual"] = lengths["anchor_matched_distance"] / lengths["anchor_reconstructed_distance"]
        cu = result["shared_anchor_cosines"]["matched"]
        result["matched_energy_orthogonal_to_original_fraction"] = (1 - cu) * (1 + cu)
        result["best_scalar_original_to_matched_gain"] = lengths["matched_norm"] / a * max(0., cu)
        groups[group] = result
    # E/B are orthogonal blocks in the archived real-coefficient convention.
    # Their separately attainable endpoints tighten the total 64-dimensional
    # interval. Check additive lengths before using that extra information.
    additivity = {}
    for key, total in groups["all"]["input_lengths_K_CMB"].items():
        e, b = (groups[g]["input_lengths_K_CMB"][key] for g in ("E", "B"))
        error = abs((e / total)**2 + (b / total)**2 - 1)
        if error > 2e-12:
            raise ValueError("NONADDITIVE_EB_LENGTHS_" + key)
        additivity[key] = error
    distance = [math.hypot(*(groups[g]["matched_reconstructed_distance_interval"][i]
                            for g in ("E", "B"))) for i in (0, 1)]
    b = groups["all"]["input_lengths_K_CMB"]["matched_norm"]
    c = groups["all"]["input_lengths_K_CMB"]["reconstructed_norm"]
    cosines = [(1 + (b / c)**2 - (d / c)**2) / (2 * b / c) for d in distance]
    block_refined = {
        "matched_reconstructed_distance_interval_K_CMB": distance,
        "matched_reconstructed_angle_degrees_interval": [math.degrees(math.acos(x)) for x in cosines],
        "best_nonnegative_scalar_residual_fraction_lower": math.sqrt((1-cosines[0])*(1+cosines[0])),
        "E_B_energy_additivity_relative_errors": additivity,
        "meaning": "Sharp total interval after imposing all available E/B summary constraints; one common scalar for the total vector",
    }
    result = {
        "schema": "htt.L01_shared_anchor_processing_geometry/1",
        "date_utc": "2026-10-18", "owner": "obsstat", "claim_tier": "C0",
        "status": "DIAGNOSTIC_ONLY", "non_claim_bearing": True,
        "scope": "New deterministic postprocessing of real-data summary norms; no map execution",
        "transfer_source": "none", "sources": sources,
        "data_origin": "USER_NATIVE_OUTPUT_SUMMARIES_COMMITTED_AT_PINNED_HEAD",
        "raw_arrays_available": False, "raw_native_report_read_here": False,
        "shared_anchor_basis": "Same full-product direct native two-mask contrast, real ell2..5 coefficients; 64 total, E32/B32",
        "shared_anchor_identity_evidence": "Linked committed reports, same native report path and direct norms. Native bytes not independently replayed here.",
        "groups": groups, "all_refined_using_orthogonal_E_B_blocks": block_refined,
        "interpretation": "For these finite estimates, no nonnegative scalar rescaling of the original native-L128 reconstruction can approximate the matched raw contrast more closely than the reported lower residual. Native-L128 truncation diagnostics cannot be reassigned as matched-estimator error diagnostics.",
        "limitations": [
            "Intervals vary over missing cross orientation, not a stochastic ensemble or confidence distribution.",
            "Bounds are conditional on reported shared-anchor identities and lengths; not formally outward-rounded.",
            "Different source support objectives define different estimators; disagreement does not attribute cosmic B, noise, foregrounds, or contamination.",
            "Single shared sky; same-sky split covariance including cross terms is still required.",
            "Matched native HM/OE data scan and matched null calibration remain NOT_RUN here.",
            "No infinite harmonic-tail, continuum quadrature, physical transfer or family-identification claim."
        ],
        "native_solver_or_ODE_called": False,
        "publication_DAG_recommendation": {"node": "L01", "status": "PENDING_UNCHANGED", "completed": 14, "total": 42},
        "runtime": {"python_version": platform.python_version(),
                    "native_worker_dispatched": True, "requested_model": "INHERITED_PARENT_SETTINGS",
                    "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN",
                    "primary_checkout_status": "UNKNOWN", "RDC_retry": False},
        "generating_command": "python analyze_planck_anchor.py",
    }
    target = ROOT / "results" / "PLANCK_ANCHOR_GEOMETRY_20261018.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    for group, r in groups.items():
        print(group, json.dumps({k: r[k] for k in (
            "matched_reconstructed_angle_degrees_interval", "matched_reconstructed_distance_interval",
            "best_nonnegative_scalar_residual_fraction_lower",
            "estimator_change_over_native_L128_residual", "matched_energy_orthogonal_to_original_fraction")}))
    print("all_EB_refined", json.dumps(block_refined))


if __name__ == "__main__":
    main()
