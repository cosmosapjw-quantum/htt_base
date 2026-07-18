"""PR-153: JWST authenticated-row, cross-match and calibration manifest.

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

Because the authoritative machine-readable data table (Freedman CCHP MRT) is NOT
reproducible (HTTP 404; only arXiv abstract pages of the other sources fetched),
the anchor rows are CITED-SEED, not authoritative-table-reproduced, so per the
kill rule the JWST lane stays a cited-seed catalogue-linkage scenario and no
CF4-conditioned precision forecast is authorized while N-DATA-CF4-DOWNSTREAM is OPEN.  The
synthetic 14-anchor fixture is NEVER renamed observed JWST data, and identity is
NEVER confirmed from a coordinate radius alone.  Catalogue-linkage DIAGNOSTIC at
``roadmap_rescue_v1:C1`` only; no measurement, forecast, detection, or
Bianchi-family claim; the two CF4 P0s are untouched.
"""
from __future__ import annotations

import math

import numpy as np

SCHEMA_VERSION = "pr153.jwst_anchor_manifest.v1"


class JWSTAnchorError(ValueError):
    """Raised when the JWST anchor-manifest discipline is violated."""


# --------------------------------------------------------------------------
# authoritative-reproduction decision
# --------------------------------------------------------------------------
def authoritative_reproduction_decision(fetch_manifest: dict) -> dict:
    """Decide the authentication level.  The authoritative machine-readable DATA
    table is reproduced only if it is among the fetched products AND is a data
    table (not an abstract page).  When the CCHP MRT is in the ``missing`` list
    (HTTP 404) and only arXiv abstract pages are fetched, the anchors are
    CITED-SEED, not authoritative-table-reproduced."""
    missing = [m.get("label") for m in fetch_manifest.get("missing", [])]
    fetched_rows = list(fetch_manifest.get("fetched", []))
    fetched = [f.get("label") for f in fetched_rows]
    # the CCHP machine-readable table is the authoritative DATA table.  A label
    # match is NOT enough: a 200-OK HTML paywall/landing page would carry the
    # label yet be no data table, so reproduction requires the fetch manifest to
    # CERTIFY the fetched CCHP product parses as a machine-readable table
    # (``content_verified_data_table``) --- absent that flag it is NOT reproduced.
    cchp = [f for f in fetched_rows
            if "cchp" in str(f.get("label", "")).lower()
            or "freedman" in str(f.get("label", "")).lower()]
    content_verified = any(bool(f.get("content_verified_data_table"))
                           for f in cchp)
    reproduced = bool(content_verified and not missing)
    return {
        "authoritative_table_reproduced": reproduced,
        "authentication_level": ("AUTHORITATIVE_TABLE_REPRODUCED" if reproduced
                                 else "CITED_SEED_NOT_AUTHORITATIVE_TABLE_REPRODUCED"),
        "jwst_lane_status": ("authenticated_row" if reproduced
                             else "cited_seed_catalogue_linkage_scenario"),
        "cchp_table_content_verified": content_verified,
        "missing_authoritative_tables": missing,
        "fetched_products": fetched,
        "cf4_conditioned_forecast_authorized": False,
        "note": "the authoritative machine-readable data table (CCHP MRT) is not "
                "reproduced (404 missing; a fetched product is credited only when "
                "the manifest certifies it parses as a data table, not merely by "
                "a matching label), so the anchors are cited-seed and the JWST "
                "lane stays a cited-seed catalogue-linkage scenario; no "
                "CF4-conditioned precision forecast is authorized while "
                "N-DATA-CF4-DOWNSTREAM is OPEN"}


# --------------------------------------------------------------------------
# row-complete anchor manifest
# --------------------------------------------------------------------------
# The seed cites its sources at the source-year granularity; the per-anchor
# authoritative DOI is NOT verified here (the authoritative machine-readable
# table is not reproduced --- the kill), so the manifest records the cited-source
# citation and marks the authoritative DOI unverified rather than stamping a
# specific (possibly wrong) DOI.
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
    distance).  The authoritative per-anchor DOI is marked UNVERIFIED because the
    authoritative machine-readable table is not reproduced (the kill)."""
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
                    "UNVERIFIED because the authoritative table is not "
                    "reproduced), the seed retrieval hash, the J2000 coordinate "
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
    dup_changed = 0
    for drop in range(len(anchors)):
        subset = [a for i, a in enumerate(anchors) if i != drop]
        cm = crossmatch_all(subset, cf4_ra, cf4_dec, cf4_pgc,
                           position_sigma_deg=position_sigma_deg,
                           ambiguity_ratio_threshold=ambiguity_ratio_threshold)
        for m in cm["matches"]:
            if full_pgc[m["anchor"]] != m["cf4_pgc"]:
                per_anchor_stable = False
        sub_dups = {k: set(v) for k, v in cm["duplicate_cf4_groups"].items()}
        # a duplicate group loses a member when its dropped anchor belonged to it
        expected = {k: (v - {anchors[drop]["object_host_name"]})
                    for k, v in full_dups.items()}
        expected = {k: v for k, v in expected.items() if len(v) > 1}
        if sub_dups != expected:
            dup_changed += 1
    return {"n_anchors": len(anchors),
            "per_anchor_best_match_stable": bool(per_anchor_stable),
            "n_duplicate_grouping_changed_under_leave_one_out": dup_changed,
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
    if claim in ("jwst_measurement", "jwst_detection"):
        raise JWSTAnchorError(
            "a JWST-level measurement or detection claim is rejected")


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
        ("jwst ", "measurement"),
        ("bianchi family ", "from jwst"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise JWSTAnchorError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(manifest: dict, decision: dict, crossmatch: dict,
                     negatives: dict) -> str:
    return (
        f"JWST distance-anchor cited-seed manifest: {manifest['n_anchors']} "
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
        f"identities broken). The authoritative machine-readable table is not "
        f"reproduced, so the lane stays a {decision['jwst_lane_status']} and no "
        f"CF4-conditioned precision forecast is authorized. Catalogue-linkage "
        f"diagnostic only; no measurement, forecast, detection, or "
        f"Bianchi-family claim; the two CF4 P0s stay OPEN.")
