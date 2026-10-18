#!/usr/bin/env python3
"""Audit the released Union3 22-node FITS against the PUBLIC NPZ chain.

This is a compression-consistency test, NOT an attestation of the Stan generator
or of the node prior used to create the original MCMC chain.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from astropy.io import fits


class ProductAuditError(ValueError):
    """A source or numerical precondition needed for the audit is not met."""


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def chain_moments(samples: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Follow public read_and_sample.py: median(mu_zbins), inv(cov(mu_zbins.T))."""
    if samples.ndim != 2 or samples.shape[0] <= samples.shape[1]:
        raise ProductAuditError("samples must be N x n with N > n")
    if not np.isfinite(samples).all():
        raise ProductAuditError("samples contain nonfinite values")
    median = np.median(samples, axis=0)
    covariance = np.cov(samples, rowvar=False, ddof=1)
    if not np.isfinite(covariance).all():
        raise ProductAuditError("nonfinite sample covariance")
    eigvals = np.linalg.eigvalsh(covariance)
    if eigvals[0] <= 0:
        raise ProductAuditError("singular or non-positive sample covariance")
    precision = np.linalg.inv(covariance)
    return median, precision, eigvals


def flat_lcdm_reference_modulus(z: np.ndarray) -> np.ndarray:
    """Reference candidate: flat LCDM, Omega_m=.3, H0=70 km/s/Mpc.

    This is independent quadrature, NOT the unreleased original get_mu code.
    """
    nodes, weights = np.polynomial.legendre.leggauss(128)
    z_grid = z[:, None] * (nodes[None, :] + 1.0) / 2.0
    integral = z / 2.0 * (
        weights[None, :] / np.sqrt(0.3 * (1.0 + z_grid) ** 3 + 0.7)
    ).sum(axis=1)
    d_l_mpc = (299792.458 / 70.0) * (1.0 + z) * integral
    return 25.0 + 5.0 * np.log10(d_l_mpc)


def audit_table(
    samples: np.ndarray,
    table: np.ndarray,
    median_tolerance_mag: float = 1e-8,
    precision_relative_tolerance: float = 1e-6,
) -> dict:
    """Compare chain compression, with predeclared diagnostics and no recentering."""
    if median_tolerance_mag < 0 or precision_relative_tolerance < 0:
        raise ProductAuditError("negative tolerance")
    median, precision, cov_eigenvalues = chain_moments(samples)
    n = samples.shape[1]
    if table.shape != (n + 1, n + 1) or not np.isfinite(table).all():
        raise ProductAuditError("FITS table must be finite (n+1) x (n+1)")
    z = table[0, 1:]
    if np.any(np.diff(z) <= 0) or np.any(z <= 0):
        raise ProductAuditError("FITS redshift nodes must be positive and increasing")
    ref_precision = table[1:, 1:]
    if not np.allclose(ref_precision, ref_precision.T, rtol=0, atol=1e-8):
        raise ProductAuditError("FITS precision matrix not symmetric")
    median_residual = median - table[1:, 0]
    prec_residual = precision - ref_precision
    med_max = float(np.max(np.abs(median_residual)))
    p_max = float(np.max(np.abs(prec_residual)))
    relative = float(np.linalg.norm(prec_residual, ord="fro") /
                     np.linalg.norm(ref_precision, ord="fro"))
    precision_pass = relative <= precision_relative_tolerance
    raw_center_pass = med_max <= median_tolerance_mag
    # Public NPZ stores perturbations, whereas FITS reports full modulus values.
    # The physical reference candidate can explain the large raw difference,
    # but its historical get_mu implementation remains unbound to this release.
    flat_ref = flat_lcdm_reference_modulus(z)
    proposed_residual = median + flat_ref - table[1:, 0]
    proposed_max = float(np.max(np.abs(proposed_residual)))
    proposed_rms = float(np.sqrt(np.mean(proposed_residual ** 2)))
    overall_direct_pass = precision_pass and raw_center_pass
    return {
        "source_binding_level": "NPZ_COVARIANCE_RECONSTRUCTED_CENTER_BASIS_UNBOUND",
        "scientific_admission": "HOLD_UNCHANGED",
        "n_samples": int(samples.shape[0]),
        "n_nodes": int(n),
        "released_z_min": float(z[0]),
        "released_z_max": float(z[-1]),
        "chain_cov_min_eigenvalue": float(cov_eigenvalues[0]),
        "chain_cov_max_eigenvalue": float(cov_eigenvalues[-1]),
        "released_precision_min_eigenvalue": float(np.linalg.eigvalsh(ref_precision)[0]),
        "raw_median_max_abs_difference_mag": med_max,
        "precision_max_abs_difference": p_max,
        "precision_relative_frobenius_difference": relative,
        "precision_numerical_match": bool(precision_pass),
        "raw_location_numerical_match": bool(raw_center_pass),
        "full_direct_summary_numerical_match": bool(overall_direct_pass),
        "reference_candidate": {
            "definition": "flat LCDM Omega_m=0.3 H0=70 km/s/Mpc, 128-node Gauss-Legendre",
            "source": "independent analytic background quadrature, not original get_mu",
            "fiducial_shift_max_abs_residual_mag": proposed_max,
            "fiducial_shift_rms_residual_mag": proposed_rms,
            "exact_coordinate_conversion": "UNVERIFIED",
        },
        "declared_raw_median_tolerance_mag": float(median_tolerance_mag),
        "declared_precision_relative_tolerance": float(precision_relative_tolerance),
        "interpretation": (
            "The released precision is reproduced from the public chain, "
            "but its node-centering coordinate conversion and the original "
            "Stan generating prior/configuration remain unbound."
            if precision_pass and not raw_center_pass else
            "Direct sample summary matches the FITS at declared tolerance; "
            "the Stan generator/run still remains unbound."
            if overall_direct_pass else
            "Even the chain precision differs from the FITS beyond tolerance."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", required=True, type=Path)
    parser.add_argument("--fits", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--expected-samples-sha256")
    parser.add_argument("--expected-fits-sha256")
    parser.add_argument("--median-tol", type=float, default=1e-8)
    parser.add_argument("--precision-rel-tol", type=float, default=1e-6)
    args = parser.parse_args()
    hashes = {
        "samples_sha256": sha256_file(args.samples),
        "fits_sha256": sha256_file(args.fits),
    }
    for key, requested in (("samples_sha256", args.expected_samples_sha256),
                           ("fits_sha256", args.expected_fits_sha256)):
        if requested is not None and hashes[key] != requested:
            raise ProductAuditError(f"{key} mismatch: {hashes[key]} != {requested}")
    with np.load(args.samples, allow_pickle=False) as packet:
        if packet.files != ["arr"]:
            raise ProductAuditError(f"unexpected NPZ keys: {packet.files}")
        samples = packet["arr"]
    table = np.asarray(fits.getdata(args.fits), dtype=np.float64)
    report = {
        "schema": "htt.union3.chain-fits-audit/1",
        **hashes,
        "fit_generator_source": "rubind/union3_release/read_and_sample.py@a141f8f6",
        "code_method": "median(mu_zbins,axis=0); inv(cov(mu_zbins.T))",
        "audit": audit_table(samples, table, args.median_tol, args.precision_rel_tol),
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    # A partial covariance-level binding is successful execution, not full science admission.
    return 0 if report["audit"]["precision_numerical_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
