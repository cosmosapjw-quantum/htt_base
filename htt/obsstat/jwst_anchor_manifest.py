"""PR-153: JWST source-table results plus anchor-linkage manifest.

A row-complete manifest of the cited JWST distance anchors (Freedman et al.
2025/2024 CCHP TRGB/JAGB + Riess et al. 2024 SH0ES Cepheids), each carrying the
source DOI/URL, the seed retrieval hash, the object/host name, the J2000
coordinate evidence, the published distance-modulus precision, the
method/calibration group and the deterministic transform.  Each anchor is linked
to the real CF4 group catalogue by a PROBABILISTIC positional-uncertainty-
weighted identity match (never a coordinate radius alone), with an explicit
ambiguity and duplicate policy, and the linkage is exercised by an independent
row replay, a cross-match tolerance sensitivity, a leave-one-match report and a
label-substitution negative test.

The publisher MRT link is unavailable, but the author-submitted arXiv source
archives contain the actual LaTeX tables and are content-verified and hashed by
``dl_pipeline``.  Their host-distance values support a conditional paired
method-consistency result.  The coordinate seed remains a separate supporting
catalogue-linkage product: identity is never confirmed from radius alone and no
CF4-conditioned precision or geometry inference is authorized.
"""
from __future__ import annotations

import math

import numpy as np

SCHEMA_VERSION = "pr153.jwst_anchor_manifest.v3"


class JWSTAnchorError(ValueError):
    """Raised when the JWST anchor-manifest discipline is violated."""


# --------------------------------------------------------------------------
# authoritative-reproduction decision
# --------------------------------------------------------------------------
_REQUIRED_SOURCE_TABLES = {
    "cchp_freedman2025_source_table": ("2408.06153", "Ho2024.tex"),
    "shoes_riess2025_source_table": ("2509.01667", "main.tex"),
    "jwst_trgb_li2024_source_table": ("2408.00065", "sample631.tex"),
    "complete_hst_jwst_trgb_li2025_source_table": ("2504.08921", "main.tex"),
}
_REQUIRED_TRANSCRIPTIONS = {
    "cchp_trgb_jagb": ("cchp_freedman2025_source_table", 7),
    "shoes_jwst_hst": ("shoes_riess2025_source_table", 13),
    "li2024_jwst_trgb_hst_cepheid":
        ("jwst_trgb_li2024_source_table", 1),
    "li2025_complete_trgb_hst_cepheid":
        ("complete_hst_jwst_trgb_li2025_source_table", 1),
}


def _full_sha256(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)


def authoritative_reproduction_decision(fetch_manifest: dict) -> dict:
    """Decide whether both registered author-source analysis tables exist.

    Abstract HTML never qualifies.  A table qualifies only when the acquisition
    manifest records a verified LaTeX member and marks it as ingested by the
    committed source-checked transcription.
    """
    violations = []
    if fetch_manifest.get("schema") != "htt.jwst_source_table_acquisition.v4":
        violations.append("manifest_schema")
    missing = [m.get("label") for m in fetch_manifest.get("missing", [])]
    if missing:
        violations.append("missing_sources")
    fetched_rows = list(fetch_manifest.get("fetched", []))
    fetched = [f.get("label") for f in fetched_rows]
    by_label = {str(row.get("label")): row for row in fetched_rows}
    if len(by_label) != len(fetched_rows):
        violations.append("duplicate_source_label")
    source_ok = {}
    for label, (arxiv, member) in _REQUIRED_SOURCE_TABLES.items():
        row = by_label.get(label) or {}
        verification = row.get("verification") or {}
        ok = bool(
            row.get("arxiv") == arxiv
            and row.get("path") == f"arxiv_{arxiv}.src.tar.gz"
            and row.get("content_verified_data_table") is True
            and row.get("analysis_table_ingested") is True
            and _full_sha256(row.get("sha256"))
            and verification.get("ok") is True
            and verification.get("member") == member
            and not verification.get("missing_markers")
            and not verification.get("missing_cell_markers")
            and verification.get("cell_markers_verified") is True
            and _full_sha256(verification.get("member_sha256"))
            and _full_sha256(verification.get("cell_receipt_sha256"))
        )
        source_ok[label] = ok
        if not ok:
            violations.append(f"source:{label}")
    cchp_verified = source_ok["cchp_freedman2025_source_table"]
    shoes_verified = source_ok["shoes_riess2025_source_table"]
    li2024_verified = source_ok["jwst_trgb_li2024_source_table"]
    li2025_verified = source_ok[
        "complete_hst_jwst_trgb_li2025_source_table"]

    receipt_rows = fetch_manifest.get("transcription_receipts")
    if not isinstance(receipt_rows, list):
        receipt_rows = []
    receipts = {str(row.get("dataset")): row for row in receipt_rows}
    if len(receipts) != len(receipt_rows):
        violations.append("duplicate_transcription_dataset")
    for dataset, (source_label, count) in _REQUIRED_TRANSCRIPTIONS.items():
        row = receipts.get(dataset) or {}
        ok = bool(
            row.get("source_label") == source_label
            and row.get("registered_row_count") == count
            and row.get("observed_row_count") == count
            and row.get("verified") is True
            and _full_sha256(row.get("source_archive_sha256"))
            and _full_sha256(row.get("source_member_sha256"))
            and _full_sha256(row.get("source_cell_receipt_sha256"))
            and _full_sha256(row.get("transcription_csv_sha256"))
            and _full_sha256(row.get("exact_cells_sha256"))
            and isinstance(row.get("exact_cells"), list)
            and len(row["exact_cells"]) == count
        )
        if not ok:
            violations.append(f"transcription:{dataset}")
    comparison_csv = fetch_manifest.get("source_checked_comparison_csv")
    comparison_hash = fetch_manifest.get("source_checked_comparison_csv_sha256")
    aggregate_csv = fetch_manifest.get("source_checked_aggregate_csv")
    aggregate_hash = fetch_manifest.get("source_checked_aggregate_csv_sha256")
    if not (_full_sha256(comparison_hash) and _full_sha256(aggregate_hash)):
        violations.append("transcription_csv_hash")
    reproduced = bool(not violations and cchp_verified and shoes_verified
                      and li2024_verified
                      and li2025_verified and comparison_csv and comparison_hash
                      and aggregate_csv and aggregate_hash)
    return {
        "authoritative_table_reproduced": reproduced,
        "source_tables_reproduced": reproduced,
        "authentication_level": ("AUTHOR_SOURCE_TABLES_REPRODUCED" if reproduced
                                 else "SOURCE_TABLES_INCOMPLETE"),
        "jwst_lane_status": ("published_table_conditional_result" if reproduced
                             else "source_table_blocked"),
        "cchp_table_content_verified": cchp_verified,
        "shoes_table_content_verified": shoes_verified,
        "li2024_expansion_content_verified": li2024_verified,
        "li2025_expansion_content_verified": li2025_verified,
        "source_checked_comparison_csv": comparison_csv,
        "source_checked_comparison_csv_sha256": comparison_hash,
        "source_checked_aggregate_csv": aggregate_csv,
        "source_checked_aggregate_csv_sha256": aggregate_hash,
        "missing_authoritative_tables": missing,
        "verification_violations": violations,
        "fetched_products": fetched,
        "cf4_conditioned_forecast_authorized": False,
        "note": ("all four registered author-submitted LaTeX sources and both hashed "
                 "source-checked transcriptions are present" if reproduced else
                 "one or more registered source tables are incomplete; no numerical "
                 "distance result may be emitted"),
        "claim_boundary": "host-distance method consistency only; no H0 fit or CF4-conditioned inference"}


# --------------------------------------------------------------------------
# row-complete anchor manifest
# --------------------------------------------------------------------------
# The seed cites its sources at the source-year granularity; the per-anchor
# authoritative DOI is NOT verified for this separate coordinate-seed lane.
# The four author-source distance tables used by the numerical result are
# reproduced independently; that does not promote the seed's per-anchor
# coordinate/identity provenance.
_SOURCE_CITATION = {
    "Freedman2025": "Freedman et al. 2025, ApJ 985, 203 "
                    "(CCHP JWST TRGB/JAGB, doi 10.3847/1538-4357/adce78)",
    "Freedman2024": "Freedman et al. 2024 (CCHP JWST; authoritative DOI "
                    "not verified in this cited-seed lane)",
    "Riess2024": "Riess et al. 2024 (SH0ES JWST Cepheids; authoritative DOI "
                 "not verified in this cited-seed lane)",
}


def build_row_manifest(seed_rows: list, *, seed_sha256: str,
                       fetch_manifest: dict) -> dict:
    """Build the row-complete manifest: per anchor the object/host name, the
    cited-source citation, the seed retrieval hash, the J2000 coordinate
    evidence, the published distance-modulus precision (the ORIGINAL
    uncertainty), the method/calibration group, and the deterministic transform
    (identity --- the seed carries the published precision, NOT a re-derived
    distance).  The authoritative per-anchor DOI remains UNVERIFIED only for
    this coordinate-seed linkage product; the distance-result source tables are
    governed by a separate content-addressed receipt."""
    rows = []
    for r in seed_rows:
        source = str(r["source"])
        rows.append({
            "object_host_name": str(r["name"]),
            "aliases": [],
            "ra_deg_j2000": float(r["ra_deg"]),
            "dec_deg_j2000": float(r["dec_deg"]),
            "coordinate_evidence": "j2000_host_centre_from_cited_source",
            "redshift_evidence": "absent_in_seed",
            "published_distance_modulus_precision_mag": float(r["jwst_e_dm_mag"]),
            "original_uncertainty_kind": "published_distance_modulus_precision",
            "method_calibration_group": str(r["method"]),
            "source_label": source,
            "cited_source_citation": _SOURCE_CITATION.get(source, "unknown"),
            "authoritative_doi_verified": False,
            "deterministic_transform": "identity_precision_only_no_rederived_distance",
        })
    return {"n_anchors": len(rows), "seed_sha256": seed_sha256,
            "fetch_manifest_sha256_of_seed": fetch_manifest.get("seed_sha256"),
            "rows": rows,
            "note": "row-complete cited-seed manifest; each anchor carries the "
                    "cited-source citation (the authoritative per-anchor DOI is "
                    "UNVERIFIED in the separate coordinate-seed lane), the seed "
                    "retrieval hash, the J2000 coordinate "
                    "evidence, the published distance-modulus precision (the "
                    "original uncertainty), the method/calibration group and the "
                    "deterministic transform (identity, precision only)"}


# --------------------------------------------------------------------------
# probabilistic identity match (NOT a coordinate radius alone)
# --------------------------------------------------------------------------
def _angular_sep_deg(ra1, dec1, ra2, dec2):
    r1, d1 = math.radians(ra1), math.radians(dec1)
    r2, d2 = np.radians(ra2), np.radians(dec2)
    cos = (np.sin(d1) * np.sin(d2)
           + np.cos(d1) * np.cos(d2) * np.cos(r1 - r2))
    return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))


_BACKGROUND_RADIUS_DEG = 5.0


def probabilistic_identity_match(anchor_ra: float, anchor_dec: float,
                                 cf4_ra: np.ndarray, cf4_dec: np.ndarray, *,
                                 position_sigma_deg: float,
                                 ambiguity_ratio_threshold: float) -> dict:
    """A PROBABILISTIC identity match against a NO-MATCH background hypothesis
    (Budavari--Szalay): the signal likelihood of a CF4 group is a 2D Gaussian
    ``exp(-sep^2/(2 sigma^2)) / (2 pi sigma^2)`` (per unit area), the no-match
    hypothesis is the LOCAL surface density of CF4 groups (chance alignment),
    and the posterior match probability is
    ``lik_signal / (lik_signal + rho_background)``.  This is NOT a coordinate
    radius alone and NOT a bare argmin: a distant best neighbour (e.g. a group
    centre 1+ deg away) gets a LOW posterior and is flagged not-credible, and the
    runner-up posterior sets the ambiguity."""
    sep = _angular_sep_deg(anchor_ra, anchor_dec, cf4_ra, cf4_dec)
    # local background surface density (chance-alignment rate) from a wide annulus
    n_local = int(np.sum(sep < _BACKGROUND_RADIUS_DEG))
    rho_bg = max(n_local, 1) / (math.pi * _BACKGROUND_RADIUS_DEG ** 2)
    lik_signal = np.exp(-0.5 * (sep / position_sigma_deg) ** 2) \
        / (2.0 * math.pi * position_sigma_deg ** 2)
    order = np.argsort(sep)                       # nearest first
    best = int(order[0])
    runner = int(order[1]) if order.size > 1 else -1

    def _post(i):
        return float(lik_signal[i] / (lik_signal[i] + rho_bg))
    post_best = _post(best)
    post_runner = _post(runner) if runner >= 0 else 0.0
    # POSITIONAL credibility only (posterior of a positional coincidence with a
    # CF4 group centre) --- NEVER a confirmed physical identity: the seed carries
    # no redshift, so the label/PGC identity is not cross-checked and a chance
    # angular coincidence with a different galaxy's group can be positionally
    # credible.  ``marginal`` flags a posterior within 0.15 of the 0.5 threshold
    # (fragile to the background-density estimate).
    positionally_credible = bool(post_best > 0.5)
    marginal = bool(abs(post_best - 0.5) <= 0.15)
    runner_ratio = float(post_runner / post_best) if post_best > 0 else 0.0
    ambiguous = bool(runner_ratio >= ambiguity_ratio_threshold
                     and post_runner > 0.1)
    return {"best_index": best, "best_separation_deg": float(sep[best]),
            "posterior_positional_match_probability": post_best,
            "positionally_credible": positionally_credible,
            "identity_confirmed": False,
            "marginal": marginal,
            "background_density_per_deg2": float(rho_bg),
            "runner_up_index": runner,
            "runner_up_posterior_ratio": runner_ratio,
            "ambiguous": ambiguous}


def crossmatch_all(anchors: list, cf4_ra: np.ndarray, cf4_dec: np.ndarray,
                   cf4_pgc: np.ndarray, *, position_sigma_deg: float,
                   ambiguity_ratio_threshold: float) -> dict:
    """Cross-match every anchor and apply the DUPLICATE policy (two anchors
    landing on the same CF4 group are flagged, not silently merged)."""
    matches = []
    for a in anchors:
        m = probabilistic_identity_match(
            a["ra_deg_j2000"], a["dec_deg_j2000"], cf4_ra, cf4_dec,
            position_sigma_deg=position_sigma_deg,
            ambiguity_ratio_threshold=ambiguity_ratio_threshold)
        matches.append({"anchor": a["object_host_name"],
                        "cf4_pgc": int(cf4_pgc[m["best_index"]]), **m})
    seen: dict = {}
    for m in matches:
        if m["positionally_credible"]:
            seen.setdefault(m["cf4_pgc"], []).append(m["anchor"])
    duplicates = {int(k): v for k, v in seen.items() if len(v) > 1}
    return {"matches": matches,
            "n_positionally_credible":
                int(sum(m["positionally_credible"] for m in matches)),
            "n_marginal": int(sum(m["marginal"] for m in matches)),
            "n_ambiguous": int(sum(m["ambiguous"] for m in matches)),
            "identity_confirmed_any": False,
            "duplicate_cf4_groups": duplicates,
            "note": "each anchor linked by the probabilistic match against a "
                    "no-match background; POSITIONAL credibility (posterior > 0.5) "
                    "is a positional coincidence with a CF4 group centre, NOT a "
                    "confirmed physical identity (the seed has no redshift, so "
                    "identity is never cross-checked); marginal matches are near "
                    "the threshold and fragile to the background estimate; "
                    "positionally-credible anchors on the same CF4 group are "
                    "flagged as duplicates, never silently merged"}


# --------------------------------------------------------------------------
# independent row replay + sensitivity + negative tests
# --------------------------------------------------------------------------
def row_replay(parsed_rows: list, reparsed_rows: list) -> dict:
    """Independent row replay: a second deterministic parse of the seed must
    yield the identical row set (name + coordinates + precision)."""
    def _key(r):
        return (r["object_host_name"], round(r["ra_deg_j2000"], 6),
                round(r["dec_deg_j2000"], 6),
                round(r["published_distance_modulus_precision_mag"], 6))
    a = sorted(_key(r) for r in parsed_rows)
    b = sorted(_key(r) for r in reparsed_rows)
    return {"n_rows": len(a), "replay_identical": bool(a == b),
            "note": "an independent deterministic re-parse yields the identical "
                    "row set"}


def crossmatch_tolerance_sensitivity(anchors: list, cf4_ra, cf4_dec, cf4_pgc, *,
                                     tolerance_grid_deg: list,
                                     ambiguity_ratio_threshold: float) -> dict:
    """Vary the positional sigma over a grid and report the DECISION-relevant
    sensitivity: the positionally-credible count per tolerance (which genuinely
    varies --- widening sigma deflates the peak signal likelihood ~1/sigma^2 and
    drops near-threshold posteriors) and how many anchors flip credible/
    non-credible across the grid.  The nearest-neighbour PGC is reported too but
    is INVARIANT under sigma by construction (argmin of the separation), so it is
    not a robustness claim."""
    base_pgc = None
    base_cred = None
    rows = []
    total_flips = 0
    for tol in tolerance_grid_deg:
        cm = crossmatch_all(anchors, cf4_ra, cf4_dec, cf4_pgc,
                            position_sigma_deg=tol,
                            ambiguity_ratio_threshold=ambiguity_ratio_threshold)
        pgcs = tuple(m["cf4_pgc"] for m in cm["matches"])
        cred = tuple(m["positionally_credible"] for m in cm["matches"])
        if base_pgc is None:
            base_pgc, base_cred = pgcs, cred
        pgc_changed = int(sum(1 for x, y in zip(pgcs, base_pgc) if x != y))
        cred_flipped = int(sum(1 for x, y in zip(cred, base_cred) if x != y))
        total_flips = max(total_flips, cred_flipped)
        rows.append({"position_sigma_deg": float(tol),
                     "n_positionally_credible": cm["n_positionally_credible"],
                     "n_marginal": cm["n_marginal"],
                     "n_ambiguous": cm["n_ambiguous"],
                     "credible_flipped_vs_tightest": cred_flipped,
                     "nearest_pgc_changed_invariant_by_construction": pgc_changed})
    return {"grid": rows, "max_credible_flips_across_grid": total_flips,
            "note": "the positionally-credible count varies strongly with the "
                    "positional sigma (widening sigma deflates near-threshold "
                    "posteriors), so the credible classification is "
                    "tolerance-dependent; the nearest-neighbour PGC is invariant "
                    "under sigma by construction and is reported only for "
                    "transparency, not as a robustness claim"}


def leave_one_match_report(anchors: list, cf4_ra, cf4_dec, cf4_pgc, *,
                           position_sigma_deg: float,
                           ambiguity_ratio_threshold: float) -> dict:
    """Leave-one-group report.  The per-anchor BEST match is independent by
    construction (expected stable, verified), but the DUPLICATE-group resolution
    is NOT per-anchor independent: dropping one member of a duplicate group
    changes that group's membership.  Report both --- the per-anchor stability
    (a structural check) and how many leave-one-out subsets change the duplicate
    grouping (the interacting quantity)."""
    full = crossmatch_all(anchors, cf4_ra, cf4_dec, cf4_pgc,
                          position_sigma_deg=position_sigma_deg,
                          ambiguity_ratio_threshold=ambiguity_ratio_threshold)
    full_pgc = {m["anchor"]: m["cf4_pgc"] for m in full["matches"]}
    full_dups = {k: set(v) for k, v in full["duplicate_cf4_groups"].items()}
    per_anchor_stable = True
    changed_subsets = []
    for drop in range(len(anchors)):
        subset = [a for i, a in enumerate(anchors) if i != drop]
        cm = crossmatch_all(subset, cf4_ra, cf4_dec, cf4_pgc,
                           position_sigma_deg=position_sigma_deg,
                           ambiguity_ratio_threshold=ambiguity_ratio_threshold)
        for m in cm["matches"]:
            if full_pgc[m["anchor"]] != m["cf4_pgc"]:
                per_anchor_stable = False
        sub_dups = {k: set(v) for k, v in cm["duplicate_cf4_groups"].items()}
        if sub_dups != full_dups:
            changed_subsets.append({
                "dropped_anchor": anchors[drop]["object_host_name"],
                "duplicate_groups_before": {
                    str(k): sorted(v) for k, v in full_dups.items()},
                "duplicate_groups_after": {
                    str(k): sorted(v) for k, v in sub_dups.items()},
            })
    duplicate_status = "evaluated" if full_dups else "not_applicable_no_duplicates"
    return {"n_anchors": len(anchors),
            "per_anchor_best_match_stable": bool(per_anchor_stable),
            "duplicate_leave_one_status": duplicate_status,
            "full_duplicate_groups": {
                str(k): sorted(v) for k, v in full_dups.items()},
            "n_duplicate_grouping_changed_under_leave_one_out":
                len(changed_subsets),
            "duplicate_grouping_changed_subsets": changed_subsets,
            "note": "the per-anchor best match is independent by construction "
                    "(stable, a structural check); the duplicate-group "
                    "resolution DOES interact, so leave-one-out changes the "
                    "duplicate grouping when a duplicate member is dropped"}


def label_substitution_negative_test(anchors: list, cf4_ra, cf4_dec, cf4_pgc, *,
                                     position_sigma_deg: float,
                                     ambiguity_ratio_threshold: float,
                                     seed: int) -> dict:
    """Negative control: SHUFFLE the anchor coordinates among the labels.  The
    probabilistic identity match must then link most labels to the WRONG CF4
    group (the coordinate no longer matches the labelled host), so a
    label-substituted linkage is detectably wrong --- identity is coordinate-
    evidenced, not label-assumed."""
    rng = np.random.Generator(np.random.PCG64(seed))
    n = len(anchors)
    true = crossmatch_all(anchors, cf4_ra, cf4_dec, cf4_pgc,
                         position_sigma_deg=position_sigma_deg,
                         ambiguity_ratio_threshold=ambiguity_ratio_threshold)
    true_pgc = [m["cf4_pgc"] for m in true["matches"]]
    true_cred = [m["positionally_credible"] for m in true["matches"]]
    # a DERANGEMENT (no fixed point) so every label really gets another anchor's
    # coordinates --- a plain permutation could leave labels in place
    perm = rng.permutation(n)
    while n > 1 and bool(np.any(perm == np.arange(n))):
        perm = rng.permutation(n)
    shuffled = [{**anchors[i], "ra_deg_j2000": anchors[perm[i]]["ra_deg_j2000"],
                 "dec_deg_j2000": anchors[perm[i]]["dec_deg_j2000"]}
                for i in range(n)]
    sub = crossmatch_all(shuffled, cf4_ra, cf4_dec, cf4_pgc,
                        position_sigma_deg=position_sigma_deg,
                        ambiguity_ratio_threshold=ambiguity_ratio_threshold)
    sub_pgc = [m["cf4_pgc"] for m in sub["matches"]]
    # score ONLY the anchors that were positionally credible in the truth run:
    # for those, the label-substituted linkage must change (a different PGC or
    # lose credibility), so the credible identities are detectably wrong
    cred_idx = [i for i in range(n) if true_cred[i]]
    n_cred_broken = int(sum(
        1 for i in cred_idx
        if sub_pgc[i] != true_pgc[i] or not sub["matches"][i]["positionally_credible"]))
    return {"n_anchors": n, "n_credible_truth": len(cred_idx),
            "n_credible_identity_broken_by_substitution": n_cred_broken,
            "all_credible_identities_broken":
                bool(len(cred_idx) > 0 and n_cred_broken == len(cred_idx)),
            "substitution_detected": bool(n_cred_broken > 0),
            "note": "a derangement of the anchor coordinates among the labels "
                    "breaks the positionally-credible identities (each moves to a "
                    "different PGC or loses credibility), so a label-substituted "
                    "linkage is detectably wrong --- identity is coordinate-"
                    "evidenced, not label-assumed"}


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def refuse_radius_only_identity(method: str) -> None:
    if method in ("coordinate_radius_only", "radius_threshold"):
        raise JWSTAnchorError(
            "confirming an anchor identity from a coordinate radius alone is "
            "rejected; the match must be probabilistic and uncertainty-weighted")


def refuse_synthetic_renamed_observed(label: str) -> None:
    if label in ("synthetic_fixture_as_observed", "rename_synthetic_observed"):
        raise JWSTAnchorError(
            "renaming the synthetic fixture observed JWST data is rejected")


def refuse_authoritative_without_table(reproduced: bool, claim: str) -> None:
    if claim in ("authoritative_reproduced", "authoritative_table") \
            and not reproduced:
        raise JWSTAnchorError(
            "claiming authoritative-table reproduction without the machine-"
            "readable table is rejected")


def refuse_cf4_forecast_downstream_open(claim: str) -> None:
    if claim in ("cf4_conditioned_forecast", "global_tilt_forecast",
                 "precision_forecast"):
        raise JWSTAnchorError(
            "a CF4-conditioned precision forecast while N-DATA-CF4-DOWNSTREAM is OPEN is "
            "rejected")


def refuse_jwst_measurement(claim: str) -> None:
    """Legacy guard retained for callers; published table consistency is allowed."""
    if claim in ("jwst_detection", "h0_fit_from_host_offsets",
                 "cosmological_inference_from_host_offsets"):
        raise JWSTAnchorError(
            "a detection or cosmological inference from the host offsets is rejected")


def refuse_bianchi_from_jwst(claim: str) -> None:
    if claim in ("bianchi_family", "geometry"):
        raise JWSTAnchorError(
            "a Bianchi-family claim from the JWST anchors is rejected")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("identity from ", "coordinate radius alone"),
        ("synthetic fixture ", "renamed observed"),
        ("authoritative reproduction ", "without"),
        ("cf4-conditioned ", "forecast"),
        ("jwst ", "detection"),
        ("bianchi family ", "from jwst"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise JWSTAnchorError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(manifest: dict, decision: dict, crossmatch: dict,
                     negatives: dict, distance_result: dict | None = None) -> str:
    result_text = ""
    if distance_result is not None:
        c = distance_result["cchp_trgb_minus_jagb_consistency"]["primary_host_level"]
        s = distance_result["shoes_jwst_minus_hst_consistency"]["primary_host_level"]
        shift = distance_result["shoes_jwst_minus_hst_consistency"]["registered_shift_comparison"]
        result_text = (
            f" Published-table results: CCHP JAGB-TRGB mean offset "
            f"{c['mean_delta_mag']:.3f} +/- {c['standard_error_mag']:.3f} mag "
            f"over 7 unique hosts (two-sided p={c['two_sided_p_for_zero_mean']:.3f}); "
            f"SH0ES JWST-HST mean offset {s['mean_delta_mag']:.3f} +/- "
            f"{s['standard_error_mag']:.3f} mag over 13 hosts "
            f"(two-sided p={s['two_sided_p_for_zero_mean']:.3f}). The registered "
            f"+{shift['comparison_shift_mag']:.3f}-mag displacement is inconsistent "
            f"with the host-level mean (one-sided p="
            f"{shift['one_sided_p_mean_at_least_comparison']:.3g}).")
    return (
        f"JWST source-table and distance-anchor manifest: {manifest['n_anchors']} "
        f"row-complete anchors (Freedman CCHP + Riess SH0ES) each carrying the "
        f"cited-source citation (authoritative DOI unverified), seed retrieval "
        f"hash, J2000 coordinate evidence, published distance-modulus precision, "
        f"method/calibration group and deterministic transform, linked to the "
        f"real CF4 groups by a probabilistic no-match-background match: "
        f"{crossmatch['n_positionally_credible']} POSITIONALLY credible "
        f"(a positional coincidence with a CF4 group centre, NOT a confirmed "
        f"identity --- the seed has no redshift), {crossmatch['n_marginal']} "
        f"marginal, {crossmatch['n_ambiguous']} ambiguous. Exercised by a row "
        f"replay, a credible-count tolerance sensitivity, a leave-one-group "
        f"report and a derangement label-substitution negative test "
        f"({negatives['n_credible_identity_broken_by_substitution']} credible "
        f"identities broken). The content-verified author-source tables set the "
        f"lane to {decision['jwst_lane_status']}.{result_text} No H0 fit, "
        f"CF4-conditioned precision forecast, detection, or Bianchi-family "
        f"claim; the two CF4 P0s stay OPEN.")
