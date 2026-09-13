#!/usr/bin/env python3
"""Real SDSS PV depth execution; estimated moments never become a Gaussian law."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import tarfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "htt/src", ROOT / "htt"):
    sys.path.insert(0, str(path))

from obsstat.sdss_pv_depth import (BASIS, read_catalogue, mock_identity, extract_depth,
                                  representation, ensemble_summary)
from common.r9_product import ProductIntake, SharedStateEmbedding

DATA_MD5 = "b5b6e31caf7ea469c2ac2cb775fa8d14"
MOCK_MD5 = "9ba3e8876f6f08a2af00d30cbf1c6cd9"


def hashes(path):
    digests = {name: hashlib.new(name) for name in ("md5", "sha256")}
    with path.open("rb") as handle:
        while chunk := handle.read(8*1024*1024):
            for digest in digests.values():
                digest.update(chunk)
    return {name: digest.hexdigest() for name, digest in digests.items()}


def dump(path, value):
    def encode(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
        raise TypeError(type(obj).__name__)
    path.write_text(json.dumps(value, default=encode, indent=2, allow_nan=False) + "\n")


def shared_eta_state(config, response):
    """Bind the actual shell response and its unidentifiable shared offset."""
    depths = len(config["redshift_maxima"])
    shell_names = tuple(f"shell{k}:{name}" for k in range(depths) for name in BASIS)
    n = len(shell_names)
    embedding = SharedStateEmbedding(config["product_id"]+":phenomenological_state",
        shell_names+("additive_eta_zero_point",), ("dex",)*(n+1),
        ("OBSERVABLE",)*n+("SHARED_NUISANCE",), config["frame"],
        "release light-cone redshifts; no common physical epoch asserted",
        shell_names, ("dex",)*n, ("additive_eta_zero_point",), ("dex",),
        np.eye(n+1)[:n], np.eye(n+1)[n:])
    response = np.asarray(response, dtype=float)
    if response.shape != (n, n) or not np.all(np.isfinite(response)):
        raise ValueError("complete finite shell response required")
    offset = response @ np.tile([1.]+[0.]*8, depths)
    return embedding, np.column_stack((response, offset))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--mocks", type=Path)
    parser.add_argument("--analysis", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new directory; preserve earlier execution")
    config = json.loads(args.analysis.read_text())
    if config["product_id"] != "SDSS_PV_ZENODO_6824749_SINGLE_FP_DEPTH_DIAGNOSTIC":
        raise ValueError("unsupported release analysis")
    if (config["distance_field"] != "logdist" or config["data_mask"] != "in_mask == 1"
            or config["inference"] != "DIAGNOSTIC_ONLY" or config["alpha_consumed"] != 0
            or config["basis"] != list(BASIS)
            or config["redshift_field_data"] != "zcmb" or config["redshift_field_mock"] != "z_obs"):
        raise ValueError("this runner implements only the uncorrected diagnostic procedure")
    args.output.mkdir(parents=True)
    source = {str(path.relative_to(ROOT)): hashes(path)["sha256"] for path in
              (Path(__file__).resolve(), ROOT / "htt/obsstat/sdss_pv_depth.py",
               ROOT / "htt/src/common/depth_path.py", ROOT / "htt/src/common/r9_product.py")}
    provenance = {"release": config["release"], "analysis": config,
                  "analysis_sha256": hashes(args.analysis)["sha256"], "sources": source,
                  "data": {"path": str(args.data), **hashes(args.data)},
                  "environment": {"python": sys.version, "numpy": np.__version__}}
    dump(args.output / "provenance.json", provenance)
    if provenance["data"]["md5"] != DATA_MD5:
        raise ValueError("official v1.1.0 catalogue checksum mismatch")
    options = dict(z_min=config["redshift_min"], maxima=config["redshift_maxima"],
                   rank_tol=config["rank_relative_tolerance"])
    rep = representation(options["maxima"])
    observed = extract_depth(read_catalogue(args.data.read_bytes()), **options)
    observed.update(feature_ids=rep.feature_ids, H=rep.H, T=rep.T,
                    r=rep.H @ observed["Y"], initial_and_contrasts=rep.T @ observed["Y"],
                    contrast_response=rep.H @ observed["response"],
                    anchored_response=rep.T @ observed["response"])
    embedding, observed["shared_state_response"] = shared_eta_state(config, observed["response"])
    n = len(embedding.local_parameter_names)
    observed["state_names"] = embedding.state_names
    observed["state_roles"] = embedding.state_roles
    dump(args.output / "embedding.json", {**asdict(embedding), "identity": embedding.identity})
    intake = ProductIntake(config["product_id"], config["release"],
        (config["release"]+":data:sha256:"+provenance["data"]["sha256"],),
        rep.feature_ids, ("dex",)*n, config["frame"], embedding.epoch,
        "unit-weight angular projection; "+rep.procedure_id,
        "published post-selection catalogue; in_mask=1; fixed CMB-redshift cumulative windows",
        "individual rows; group-richness control not calibrated with mocks",
        "free additive eta zero point; CF3 anchor law unavailable",
        "NYU-VAGC DR7 mask flag; source paper sections 2.5 and 3.2.1",
        None, None, "UNAVAILABLE")
    dump(args.output / "intake.json", {**asdict(intake), "identity": intake.identity})
    dump(args.output / "observed.json", observed)
    summary = {"owner": "obsstat", "product_id": config["product_id"],
               "status": "OBSERVED_FEATURES_ONLY", "law_status": "INPUT_UNAVAILABLE",
               "covariance_status": "UNAVAILABLE", "claim_tier": "DIAGNOSTIC_ONLY",
               "physical_response": "UNAVAILABLE; eta-shell response is phenomenological",
               "state_jet_anchor_coverage": "UNAVAILABLE", "probability": None,
               "alpha_consumed": 0, "observed_counts": observed["counts"],
               "mock_count": 0, "source_sha256": source}
    dump(args.output / "result.json", summary)
    print("OBSERVED", observed["counts"].tolist(), flush=True)
    if args.mocks is None:
        return
    provenance["mocks"] = {"path": str(args.mocks), **hashes(args.mocks)}
    dump(args.output / "provenance.json", provenance)
    if provenance["mocks"]["md5"] != MOCK_MD5:
        raise ValueError("official complete mock archive checksum mismatch")
    records, features, truths, responses, counts, spectra, failures = [], [], [], [], [], [], []
    identities = set()
    with tarfile.open(args.mocks, "r|gz") as archive:
        for member in archive:
            if not member.isfile():
                continue
            box, observer = mock_identity(member.name)
            if (box, observer) in identities:
                raise ValueError("duplicate mock identity")
            identities.add((box, observer))
            payload = archive.extractfile(member).read()
            record = {"member": member.name, "box": box, "observer": observer,
                      "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            try:
                catalogue = read_catalogue(payload, mock=True)
                record.update(released_row_count=len(catalogue.ids),
                              unique_source_id_count=len(set(catalogue.source_ids)))
                result = extract_depth(catalogue, **options)
            except ValueError as error:
                failures.append({**record, "error": str(error)})
                continue
            records.append(record)
            features.append(result["Y"])
            truths.append(result["truth"])
            responses.append(result["response"])
            counts.append(result["counts"])
            spectra.append(result["singular_values"])
            if len(records) % 64 == 0:
                print("MOCKS", len(records), member.name, flush=True)
    dump(args.output / "mock_members.json", {"complete": records, "failed": failures})
    if features:
        np.savez_compressed(args.output / "mock_features.npz", Y=features, truth=truths,
                            response=responses, counts=counts, singular_values=spectra,
                            box=[r["box"] for r in records], observer=[r["observer"] for r in records])
    boxes = np.array([r["box"] for r in records], dtype=int)
    complete = (not failures and len(records) == config["expected_mock_count"]
                and len(set(boxes)) == config["expected_box_count"]
                and all({o for b, o in identities if b == box} == set(range(8)) for box in set(boxes)))
    if not complete:
        summary.update(status="INCOMPLETE_ENSEMBLE", mock_count=len(records), failed_count=len(failures))
        dump(args.output / "result.json", summary)
        raise ValueError("incomplete ensemble; no failed or missing mock silently discarded")
    y, truth = np.array(features), np.array(truths)
    moments = ensemble_summary(y, boxes, rep)
    train = moments["training_mask"]
    # Separate fitted-minus-truth errors from total mock variation. Neither is
    # the unknown covariance of individual observed catalogue measurements.
    error_moments = ensemble_summary(y-truth, boxes, rep)
    response = np.array(responses)
    np.savez_compressed(args.output / "moments.npz",
                        **{key: value for key, value in moments.items() if isinstance(value, np.ndarray)},
                        error_mean=error_moments["mean"], error_covariance=error_moments["covariance"],
                        mean_response=response[train].mean(axis=0),
                        contrast_mean_response=rep.H @ response[train].mean(axis=0),
                        anchored_mean_response=rep.T @ response[train].mean(axis=0))
    intake = ProductIntake(**{**asdict(intake),
        "source_ids": intake.source_ids+(config["release"]+":mocks:sha256:"+provenance["mocks"]["sha256"],),
        "covariance_source": "moments.npz:sha256:"+hashes(args.output / "moments.npz")["sha256"],
        "covariance_row_ids": rep.feature_ids, "law_kind": "ESTIMATED_REQUIRES_CALIBRATION"})
    dump(args.output / "intake.json", {**asdict(intake), "identity": intake.identity})
    c = moments["covariance"]
    diagonal_blocks = np.zeros_like(c)
    for j in range(len(options["maxima"])):
        sl = slice(9*j, 9*(j+1)); diagonal_blocks[sl, sl] = c[sl, sl]
    transformed = y[train] @ rep.T.T
    residual = observed["Y"] - moments["mean"]
    summary.update(status="RELEASE_FEATURE_REPLAY_COMPLETE", law_status="ESTIMATED_MOMENTS_ONLY",
        covariance_status="FULL_CJK_FROM_SHARED_TRAINING_CATALOGUES; not known population covariance",
        mock_count=len(records), box_count=len(set(boxes)), training_count=int(train.sum()),
        evaluation_count=int((~train).sum()), training_box_count=len(set(boxes[train])),
        evaluation_box_count=len(set(boxes[~train])), failed_count=0,
        observed_residual=residual, observed_contrast_residual=rep.H @ residual,
        preferred_minus_single_FP=observed["control"]-observed["Y"],
        cross_depth_covariance_frobenius=float(np.linalg.norm(c-diagonal_blocks)),
        omitted_cross_terms_change_V_frobenius=float(np.linalg.norm(rep.H @ diagonal_blocks @ rep.H.T - moments["contrast_covariance"])),
        direct_covariance_transform_max_error=float(np.max(np.abs(np.cov(transformed, rowvar=False)-moments["anchored_covariance"]))),
        restore_max_error=float(np.max(np.abs(rep.restore(rep.T @ observed["Y"])-observed["Y"]))),
        covariance_rank=int(np.linalg.matrix_rank(c)),
        covariance_dimension=len(c),
        shared_state_response_rank=int(np.linalg.matrix_rank(observed["shared_state_response"])),
        shared_state_dimension=n+1,
        limitations=["Single-FP data is non-preferred and retains documented group-richness systematics.",
            "Public mocks do not repeat the preferred group correction or CF3 zero-point calibration.",
            "Only post-selection catalogues and fitted FP outputs are replayed; no upstream fit/generator code is supplied.",
            "Generator parameters, error/colour relations and redshift selection were fitted to the observed survey; this tuning is not repeated here.",
            "Simulation-box split prevents shared-box leakage; it does not prove iid sampling or survey coverage.",
            "Mean and covariance estimates are fitted once on training boxes; no calibrated size, coverage or p-value is computed.",
            "Additive eta-shell responses do not supply physical local/global or state-jet-anchor responses.",
            "No raw galaxy C_ik has been inferred from marginal errors; saved C is the feature-vector covariance estimate."])
    dump(args.output / "result.json", summary)
    print(summary["status"], len(records), "mocks; physical law remains unavailable", flush=True)


if __name__ == "__main__":
    main()
