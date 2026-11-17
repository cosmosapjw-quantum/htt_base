#!/usr/bin/env python3
"""Reuse the already-qualified R36 SN carrier, without a new fit or raw release.

Tests its STF marginal and difference using exact Gaussian zero witnesses.
This is a bounded historical-reuse closure, not a CF4/SN joint likelihood.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy import linalg, stats

SOURCE = "docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-08-PUBLIC-SN"
SOURCE_SHA = "f1a9246b7e1ab216fd6fb927a3fc2e28360cf2e5626aba5d7a88f2af05f7e82b"
STATUS_SHA = "bb4062b13afc91a59d777fdc4d088211a36ec1b4b7722d757f2ed316c2e23e35"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("refusing to overwrite SN reuse result")
    source, status = root / SOURCE / "RESULT.json", root / SOURCE / "PUBLICATION_STATUS.json"
    if sha(source) != SOURCE_SHA or sha(status) != STATUS_SHA:
        raise ValueError("qualified SN input identity changed")
    qualified = json.loads(status.read_text())
    if qualified["status"] != "FORMALLY_QUALIFIED_RELEASED_MAGNITUDE_CONDITIONAL_COMPARATOR":
        raise ValueError("SN product is not qualified for the stated reuse")
    data = json.loads(source.read_text())
    sys.path[:0] = [str(root / "htt"), str(root / "htt/src")]
    from htt.htt.infer.r62_tensor_classes import CLASS_NAMES, common_offset_contrast
    results = {}
    index = np.r_[np.arange(3, 8), np.arange(11, 16)]
    for name in ("primary", "lower_z_sensitivity"):
        prior = data[name]
        mean16 = np.r_[prior["low_8_mag"], prior["high_8_mag"]]
        covariance16 = np.asarray(prior["full_16x16_covariance_mag2"])
        mean, covariance = mean16[index], covariance16[np.ix_(index, index)]
        delta = common_offset_contrast(mean, covariance)
        if not np.allclose(delta["mean"], np.array(prior["high_minus_low_8_mag"])[3:], rtol=1e-12, atol=1e-15):
            raise ValueError("prior contrast mean parity failed")
        if not np.allclose(delta["covariance"], np.array(prior["high_minus_low_8x8_covariance_mag2"])[3:, 3:], rtol=1e-12, atol=1e-15):
            raise ValueError("prior contrast covariance parity failed")
        item = dict(selection_lower_zHD=prior["selection_lower_zHD"], n_low=prior["n_low"], n_high=prior["n_high"],
                    row_key_sha256=prior["row_key_sha256"], carriers={})
        for kind, h, V in (("two_depth_STF10", mean, covariance), ("difference_STF5", delta["mean"], delta["covariance"])):
            linalg.cholesky(V, lower=True)
            cutoff = float(stats.chi2.ppf(.95, h.size))
            q = float(h @ linalg.solve(V, h, assume_a="pos"))
            inside = q <= cutoff
            # All classes contain zero. An inside zero state suffices for every
            # intersection; no optimizer or extra probability law is needed.
            labels = {c: ("INTERSECTS" if inside else ("EXCLUDED" if c == "ZERO" else "UNRESOLVED")) for c in CLASS_NAMES}
            if h.size == 5:
                labels["SHARED_FRAME"] = "INTERSECTS"
            item["carriers"][kind] = dict(mean=h.tolist(), covariance=V.tolist(), dimension=int(h.size),
                cutoff=cutoff, zero_mahalanobis2=q, zero_nominal_p=float(stats.chi2.sf(q, h.size)),
                zero_witness=[0.] * h.size, zero_inside=inside, class_status=labels,
                witness_reason="The same exact zero tensor state lies in every declared structured class" if inside else "Zero outside; no nonlinear optimization performed",
                shared_frame_scope="Any single real symmetric STF tensor has an eigenframe; a one-tensor contrast has no pairwise common-frame restriction" if h.size == 5 else "Two source-chart tensor estimators; no claim of common physical shear frame")
        results[name] = item
    result = dict(schema="htt.r62.inherited_sn_reuse/1", source_path=str(source.relative_to(root)), source_sha256=sha(source),
        qualification_sha256=sha(status), source_release=data["source"]["release_commit"],
        units=dict(coefficients="mag residual", covariance="mag^2"),
        unknown_sectors=data["unknown_sectors"],
        law="Inherited R36 released-magnitude conditional Gaussian coefficient law; selected total STAT+SYS covariance, global intercept and high-bin offset already profiled",
        stage="R9 bounded closure of concrete historical-reuse omission in the paper plan",
        reuse="No raw-data acquisition, refit, covariance replacement, new survey simulation or optimizer run",
        results=results, CF4_joint_likelihood="NOT_FORMED: frame/physical response, overlap and shared PV law unresolved",
        script_sha256=sha(Path(__file__)))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({n: {k: {z: v[z] for z in ["zero_mahalanobis2", "zero_nominal_p", "zero_inside", "class_status"]} for k,v in x["carriers"].items()} for n,x in results.items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.root, args.output)
