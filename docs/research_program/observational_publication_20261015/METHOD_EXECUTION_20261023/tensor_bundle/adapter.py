"""Full-tensor scenario adapter for the reviewed K03 reported-z working experiment.

This module produces conditional computational objects only.  In particular its
ellipsoids have no survey coverage and its Gaussian law is not a physical law.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "htt/src"))
from common.anchor_geometry import (AnchorBodySpec, AnchorGeometryKind, AnchorVector,
                                    evaluate_anchor_gauge)
from common.depth_path import DepthRepresentation, full_covariance_blocks
from common.typefree_functionals import (FunctionalSpec, FunctionalRecord, FiniteJointSource,
                                         finite_joint_pushforward, FiniteFunctionalImage,
                                         ImageAtom, strict_exceedance, ratio_value, UndefinedValue)

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
INPUT = BASE / "R24-TENSOR-BUNDLE_INPUT.json"
INPUT_SHA = "29b5e234b1c8573384d9b41876d1a244014bda1cae2159fff17d5609a4646ed5"
REGION_ID = "K03-full24-common-C-rho-reported-z-scenario"
RADII = (0, 1, 2, 4, 8)
REFERENCE_RADIUS = 10.0  # microarcsec/year, computational convention only
BLOCK_NAMES = tuple(f"bin{b}_{mode}" for b in range(3) for mode in ("E1", "B1")) + ("slope_E1", "slope_B1")
PARITIES = tuple("polar" if name.endswith("E1") else "axial" for name in BLOCK_NAMES)
LABELS = tuple(f"{name}_{axis}" for name in BLOCK_NAMES for axis in "xyz")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_reviewed_state():
    if sha(INPUT) != INPUT_SHA:
        raise ValueError("immutable tensor task input identity mismatch")
    manifest = json.loads(INPUT.read_text())
    for source in manifest["sources"]:
        path = ROOT / source["path"]
        if path.stat().st_size != source["bytes"] or sha(path) != source["sha256"]:
            raise ValueError(f"immutable source identity mismatch: {path}")
    result = json.loads((BASE / "k03_depth_moments/RESULT.json").read_text())
    mean = np.asarray(result["full24_state_uasyr"], dtype=float)
    cov = np.asarray(result["full24_cov_uasyr2"], dtype=float)
    if mean.shape != (24,) or cov.shape != (24, 24) or not np.isfinite(mean).all() or not np.isfinite(cov).all():
        raise ValueError("full24 shape/finite failure")
    if not np.allclose(cov, cov.T, rtol=0, atol=1e-10) or np.linalg.eigvalsh(cov)[0] <= 0:
        raise ValueError("full24 covariance must be symmetric positive definite")
    return result, mean, (cov + cov.T) / 2


def y_map(centers):
    centers = np.asarray(centers, dtype=float)
    if centers.shape != (3,) or not np.isfinite(centers).all():
        raise ValueError("three finite reported-z centers required")
    matrix = np.zeros((18, 24))
    for b in range(3):
        matrix[6*b:6*b+6, 6*b:6*b+6] = np.eye(6)
        matrix[6*b:6*b+6, 18:] = centers[b]*np.eye(6)
    return matrix


def depth_path(mean, cov, centers, *, covariance_blocks=None):
    rep = DepthRepresentation((6, 6, 6), (np.eye(6), np.eye(6)),
                              tuple(f"bin{b}_{mode}_{axis}" for b in range(3)
                                    for mode in ("E1", "B1") for axis in "xyz"),
                              "reported-z-observed-bin-adjacent-identity")
    mapping = y_map(centers)
    y, cy = mapping @ mean, mapping @ cov @ mapping.T
    if covariance_blocks is not None:
        cy = full_covariance_blocks(covariance_blocks, rep.dimensions)
    z = rep.T @ y
    cz = None if cy is None else rep.T @ cy @ rep.T.T
    return rep, mapping, y, cy, z, cz


def computational_reference(mean):
    """Use the common anchor API; this is deliberately not an MES anchor."""
    body = AnchorBodySpec(
        body_id="computational-direct-sum-ball-r10-uasyr", geometry=AnchorGeometryKind.ELLIPSOID,
        coordinate_labels=LABELS, frame="ICRS", normalization="direct-sum-24-uasyr",
        perturbative_order="observed-fit", branch="reported-z-working",
        premise_identity="fixed-computational-reference-only",
        quadratic_form=tuple(tuple(float(v) for v in row) for row in np.eye(24)/(REFERENCE_RADIUS**2)),
        assumptions=("reference radius is a computational convention, not a physical MES ceiling",))
    vector = AnchorVector("K03-fitted-full24", LABELS, tuple(map(float, mean)), "ICRS",
                          "direct-sum-24-uasyr", "observed-fit", "reported-z-working")
    report = evaluate_anchor_gauge(body, vector)
    return float(report.lower), report.status.value


def ellipsoid_support(mean, cov, direction, rho):
    """Exact finite directional support of C_rho for a supplied direction."""
    if rho not in RADII:
        raise ValueError("unregistered common-region radius")
    u = np.asarray(direction, dtype=float)
    if u.shape != (24,) or not np.isfinite(u).all():
        raise ValueError("finite 24-direction required")
    return float(u @ mean + rho * np.sqrt(max(0.0, u @ cov @ u)))


def gaussian_replicates(mean, cov, n=4096, seed=20261023):
    if type(n) is not int or n <= 0:
        raise ValueError("positive replicate count required")
    return np.random.default_rng(seed).multivariate_normal(mean, cov, size=n, method="cholesky")


def block_specs():
    return tuple(FunctionalSpec(
        definition_id=f"K03-full24-{name}", coordinate_labels=LABELS[3*i:3*i+3],
        output_shape=(3,), rank=1, parity=PARITIES[i], basis="ICRS-cartesian",
        units="microarcsec/year", frame="ICRS", epoch="Gaia-reported-epoch-working",
        domain_id="K03-reported-z-full24", normalization="VSH-E1B1",
        perturbative_order="observed-fit", branch="reported-z-working")
        for i, name in enumerate(BLOCK_NAMES))


def sample_pushforward(samples):
    """Retain sample × functional tensors and typed per-block norm images."""
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 2 or samples.shape[1] != 24 or not np.isfinite(samples).all():
        raise ValueError("full24 finite sample matrix required")
    x = samples.reshape(len(samples), 8, 3)
    images = []
    for i, spec in enumerate(block_specs()):
        records = tuple(FunctionalRecord(f"replicate-{j}", spec, x[j, i], np.zeros(3))
                        for j in range(len(samples)))
        source = FiniteJointSource(f"K03-Gaussian-replicates-{i}", records, "SAMPLING",
                                   "K03-reported-z-full24")
        images.append(finite_joint_pushforward(source, lambda r: np.asarray(np.linalg.norm(r.values)),
                                               definition_id=f"norm-{spec.definition_id}",
                                               target_domain_id="nonnegative-uasy-per-year"))
    return x, tuple(images)


def reference_exceedance(samples, observed):
    values = np.linalg.norm(np.asarray(samples), axis=1)/REFERENCE_RADIUS
    atoms = tuple(ImageAtom(f"replicate-{i}", np.asarray(v), 1/len(values), "DEFINED")
                  for i, v in enumerate(values))
    image = FiniteFunctionalImage("K03-Gaussian-replicates", "SAMPLING", "full24",
                                  "computational-Q-ref", "direct-sum-Q-ref", atoms, "DEFINED")
    return strict_exceedance(image, observed)


def parity_transform(x, rotation, *, inversion=False):
    """Proper SO(3) acts on both modes; inversion flips polar E1 only."""
    r = np.asarray(rotation, dtype=float)
    if r.shape != (3, 3) or not np.allclose(r.T @ r, np.eye(3), atol=1e-12) or not np.isclose(np.linalg.det(r), 1, atol=1e-12):
        raise ValueError("proper SO(3) rotation required")
    v = np.asarray(x, dtype=float)
    if v.shape[-2:] != (8, 3):
        raise ValueError("eight rank-one blocks required")
    out = v @ r.T
    if inversion:
        signs = np.asarray([-1 if p == "polar" else 1 for p in PARITIES])
        out = out * (signs[None, :, None] if out.ndim == 3 else signs[:, None])
    return out


def build(n=4096, seed=20261023):
    source, mean, cov = load_reviewed_state()
    rep, mapping, y, cy, z, cz = depth_path(mean, cov, source["depth_c_reported_z_centers"])
    samples = gaussian_replicates(mean, cov, n, seed)
    x, images = sample_pushforward(samples)
    q_observed, q_status = computational_reference(mean)
    pi = reference_exceedance(samples, q_observed)
    d = samples - mean
    mahal = np.einsum("ni,ni->n", d @ np.linalg.inv(cov), d)
    scenario = []
    for rho in RADII:
        supports = []
        for i, label in enumerate(LABELS):
            u = np.eye(24)[i]
            supports.append({"direction": label, "plus": ellipsoid_support(mean, cov, u, rho),
                             "minus": ellipsoid_support(mean, cov, -u, rho)})
        scenario.append({"rho": rho, "region_id": REGION_ID, "type": "full24_joint_ellipsoid",
                         "definition": "(v-mu)^T C24^-1 (v-mu) <= rho^2",
                         "directional_support": supports,
                         "reference_occupancy_exact": float(chi2.cdf(rho*rho, 24)),
                         "reference_occupancy_empirical": float(np.mean(mahal <= rho*rho)),
                         "physical_occupancy": None})
    result = {
        "task_id": "R24-TENSOR-BUNDLE", "scope": "conditional reported-z tensor scenario only",
        "qualified_products": ["tensor_scenario"], "source_candidate": "sha256:68aa65ba81bce4bfa61a2d7c9c302a7c77068325b80ef69d55fcc89f9272a2de",
        "source_result_sha256": sha(BASE / "k03_depth_moments/RESULT.json"),
        "input_sha256": INPUT_SHA, "region_id": REGION_ID,
        "x": {"status": "DEFINED_COMPUTATIONAL_GAUSSIAN_REPLICATES", "shape": list(x.shape),
              "array_file": "SAMPLES.npz", "axes": ["replicate", "functional", "cartesian_component"],
              "functional_blocks": [{"id": b, "rank": 1, "parity": p, "units": "microarcsec/year"}
                                    for b, p in zip(BLOCK_NAMES, PARITIES)],
              "source_law": "N(fitted24,C24), conditional fixed-design reported-independent-row-error working law",
              "sample_seed": seed, "sample_size": n,
              "pushforward": {"type": "typed_per_block_norm_images", "statuses": [im.status for im in images]}},
        "full24": {"mean_uasyr": mean.tolist(), "cov_uasyr2": cov.tolist(),
                   "retained_original_carrier": True},
        "Q": {"physical_MES_anchor": None, "physical_status": "UNAVAILABLE",
              "computational_reference": {"radius_uasyr": REFERENCE_RADIUS,
                                          "direct_sum_Q_ref": q_observed, "status": q_status,
                                          "purpose": "reference_only_no_MES_ceiling"}},
        "F": {"region_family": scenario, "support_kind": "exact_finite_coordinate_directions",
              "sample_pushforward_kind": "typed_empirical_images_under_declared_Gaussian_replicates",
              "physical_occupancy_status": "UNAVAILABLE"},
        "Pi": {"source_law": "conditional_Gaussian_replicates_N(fitted24,C24)",
               "scalarization": "direct_sum_Q_ref", "threshold": q_observed,
               "strict_rule": "value > threshold", "known_exceedance_mass": pi.known_exceedance_mass,
               "undefined_mass": pi.undefined_mass, "interval": [pi.lower, pi.upper],
               "physical_status": "UNKNOWN_MASS_1", "physical_interval": [0.0, 1.0]},
        "G_F": {"depth_representation_id": rep.identity, "Y18_mean_uasyr": y.tolist(),
                "Y18_cov_uasyr2": cy.tolist(), "Z18_definition": "(Y0,Y1-Y0,Y2-Y1)",
                "Z18_mean_uasyr": z.tolist(), "Z18_cov_uasyr2": cz.tolist(),
                "Y18_to_Z18_matrix": rep.T.tolist(), "M24_to_Y18_matrix": mapping.tolist(),
                "full24_retained_alongside": True, "physical_depth_status": "UNAVAILABLE"},
        "strata": {"signed": "RETAINED", "zero": "RETAINED", "undefined": "UNAVAILABLE_NOT_ZERO_FILLED",
                   "unbounded": "UNAVAILABLE_NOT_ZERO_FILLED", "missing_cross_covariance": "UNAVAILABLE_NOT_ZERO_FILLED",
                   "zero_denominator": "UNDEFINED_NOT_ZERO", "physical_anchor": "UNAVAILABLE_NOT_ZERO"},
        "claim_ceiling": "computational scenario interface only; no calibrated survey coverage, R9 alpha, physical probability, MES ceiling, or family identification",
    }
    return result, {"x_sample_functional_uasyr": x, "sample24_uasyr": samples,
                    "sample_Q_ref": np.linalg.norm(samples, axis=1)/REFERENCE_RADIUS}
