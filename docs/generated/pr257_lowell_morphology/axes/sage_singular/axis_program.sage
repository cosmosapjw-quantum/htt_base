#!/usr/bin/env sage
"""Exact SageMath + Singular axis for CAS-PR257-ORBIT-CATALOGUE-V2-001.

The program writes no files and emits exactly one JSON object on stdout.
"""

from datetime import datetime, timezone
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import re
import subprocess

from sage.all import (
    GF,
    PolynomialRing,
    QQ,
    ZZ,
    diagonal_matrix,
    identity_matrix,
    matrix,
    vector,
)
from sage.version import version as sage_version


CONTRACT_ID = "CAS-PR257-ORBIT-CATALOGUE-V2-001"
CONTRACT_SHA256 = "1d3e0c76a3833dd72cb5e74dcd3ddedfe91a538902950df603587e77ad6c0e56"
AXIS_ROOT = Path(
    "docs/generated/pr257_lowell_morphology/axes/sage_singular"
)
PROGRAM_PATH = AXIS_ROOT / "axis_program.sage"
SINGULAR_PROGRAM_PATH = AXIS_ROOT / "singular_crosscheck.sing"
COMMAND = f"sage -python {PROGRAM_PATH.as_posix()}"
PRODUCER = "PR257-SAGE-SINGULAR-AXIS"


def file_record(path, producer, command):
    raw = path.read_bytes()
    return {
        "path": path.as_posix(),
        "sha256": sha256(raw).hexdigest(),
        "bytes": len(raw),
        "producer": producer,
        "command_fingerprint": sha256(command.encode("utf-8")).hexdigest(),
    }


def json_default(value):
    """Preserve JSON integer types after Sage's .sage preparsing."""
    try:
        if value in ZZ:
            return int(value)
    except (TypeError, ValueError):
        pass
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def is_zero_matrix(value):
    return all(entry == 0 for entry in value.list())


def scalar_product(left, operator, right):
    return (left.row() * operator * right.column())[0, 0]


def catalogue(sigma, beta, omega):
    sigma2 = sigma * sigma
    sigma_beta = sigma * beta
    sigma2_beta = sigma2 * beta
    krylov = matrix(
        sigma.base_ring(),
        3,
        3,
        [
            beta[0],
            sigma_beta[0],
            sigma2_beta[0],
            beta[1],
            sigma_beta[1],
            sigma2_beta[1],
            beta[2],
            sigma_beta[2],
            sigma2_beta[2],
        ],
    )
    return {
        "tr_sigma2": sigma2.trace(),
        "tr_sigma3": (sigma2 * sigma).trace(),
        "beta2": beta.dot_product(beta),
        "beta_sigma_beta": scalar_product(beta, sigma, beta),
        "beta_sigma2_beta": scalar_product(beta, sigma2, beta),
        "det_beta_sigma_beta_sigma2_beta": krylov.det(),
        "omega2": omega.dot_product(omega),
        "omega_sigma_omega": scalar_product(omega, sigma, omega),
        "omega_sigma2_omega": scalar_product(omega, sigma2, omega),
        "beta_dot_omega": beta.dot_product(omega),
        "beta_sigma_omega": scalar_product(beta, sigma, omega),
        "beta_sigma2_omega": scalar_product(beta, sigma2, omega),
    }


# Work over an exact rational polynomial ring.  sigma is a general real
# symmetric trace-free 3x3 matrix; beta and omega are general typed vectors.
names = (
    "sxx syy sxy sxz syz "
    "bx by bz wx wy wz "
    "qa qb qc"
).split()
ring = PolynomialRing(QQ, names=names)
(
    sxx,
    syy,
    sxy,
    sxz,
    syz,
    bx,
    by,
    bz,
    wx,
    wy,
    wz,
    qa,
    qb,
    qc,
) = ring.gens()

sigma = matrix(
    ring,
    [
        [sxx, sxy, sxz],
        [sxy, syy, syz],
        [sxz, syz, -sxx - syy],
    ],
)
beta = vector(ring, [bx, by, bz])
omega = vector(ring, [wx, wy, wz])

# The rational unit-quaternion chart is Zariski dense in SO(3).  Its exact
# identities therefore verify the polynomial transformation laws on SO(3);
# negating the chart covers the determinant-minus-one component.
field = ring.fraction_field()
denominator = 1 + qa**2 + qb**2 + qc**2
proper_rotation = matrix(
    field,
    [
        [
            1 + qa**2 - qb**2 - qc**2,
            2 * (qa * qb - qc),
            2 * (qa * qc + qb),
        ],
        [
            2 * (qa * qb + qc),
            1 - qa**2 + qb**2 - qc**2,
            2 * (qb * qc - qa),
        ],
        [
            2 * (qa * qc - qb),
            2 * (qb * qc + qa),
            1 - qa**2 - qb**2 + qc**2,
        ],
    ],
) / denominator
improper_rotation = -proper_rotation

sigma_f = sigma.change_ring(field)
beta_f = beta.change_ring(field)
omega_f = omega.change_ring(field)
base_catalogue = catalogue(sigma_f, beta_f, omega_f)

proper_sigma = proper_rotation * sigma_f * proper_rotation.transpose()
proper_beta = proper_rotation * beta_f
proper_omega = proper_rotation * omega_f
proper_catalogue = catalogue(proper_sigma, proper_beta, proper_omega)

improper_sigma = improper_rotation * sigma_f * improper_rotation.transpose()
improper_beta = improper_rotation * beta_f
improper_omega = (-1) * improper_rotation * omega_f
improper_catalogue = catalogue(improper_sigma, improper_beta, improper_omega)

parity_even = {
    "tr_sigma2",
    "tr_sigma3",
    "beta2",
    "beta_sigma_beta",
    "beta_sigma2_beta",
    "omega2",
    "omega_sigma_omega",
    "omega_sigma2_omega",
}
parity_odd = {
    "det_beta_sigma_beta_sigma2_beta",
    "beta_dot_omega",
    "beta_sigma_omega",
    "beta_sigma2_omega",
}

orthogonal_chart = (
    proper_rotation.transpose() * proper_rotation == identity_matrix(field, 3)
)
proper_determinant = proper_rotation.det() == 1
improper_determinant = improper_rotation.det() == -1
proper_parity = all(
    proper_catalogue[name] == base_catalogue[name]
    for name in parity_even | parity_odd
)
improper_even = all(
    improper_catalogue[name] == base_catalogue[name] for name in parity_even
)
improper_odd = all(
    improper_catalogue[name] == -base_catalogue[name] for name in parity_odd
)

# Exact trace-free Cayley-Hamilton identity and its registered contractions.
sigma2 = sigma * sigma
sigma3 = sigma2 * sigma
trace2 = sigma2.trace()
trace3 = sigma3.trace()
ch_residual = (
    sigma3
    - (trace2 / QQ(2)) * sigma
    - (trace3 / QQ(3)) * identity_matrix(ring, 3)
)
ch_exact = is_zero_matrix(ch_residual)
ch_contractions_exact = all(
    value == 0
    for value in (
        scalar_product(beta, ch_residual, beta),
        scalar_product(omega, ch_residual, omega),
        scalar_product(beta, ch_residual, omega),
    )
)

# Exact determinant/Gram syzygy for the beta Krylov matrix.
sigma_beta = sigma * beta
sigma2_beta = sigma2 * beta
krylov = matrix(
    ring,
    3,
    3,
    [
        beta[0],
        sigma_beta[0],
        sigma2_beta[0],
        beta[1],
        sigma_beta[1],
        sigma2_beta[1],
        beta[2],
        sigma_beta[2],
        sigma2_beta[2],
    ],
)
gram_difference = krylov.det() ** 2 - (krylov.transpose() * krylov).det()
gram_exact = gram_difference == 0

# Contract-registered fixed exact witness.
fixed_sigma = diagonal_matrix(QQ, [1, 2, -3])
fixed_beta = vector(QQ, [1, 1, 1])
fixed_omega = vector(QQ, [1, 2, 3])
fixed_catalogue = catalogue(fixed_sigma, fixed_beta, fixed_omega)
fixed_sigma3 = fixed_sigma**3
fixed_krylov = matrix(
    QQ,
    3,
    3,
    [
        fixed_beta[0],
        (fixed_sigma * fixed_beta)[0],
        ((fixed_sigma**2) * fixed_beta)[0],
        fixed_beta[1],
        (fixed_sigma * fixed_beta)[1],
        ((fixed_sigma**2) * fixed_beta)[1],
        fixed_beta[2],
        (fixed_sigma * fixed_beta)[2],
        ((fixed_sigma**2) * fixed_beta)[2],
    ],
)
computed_values_raw = dict(fixed_catalogue)
computed_values_raw.update(
    {
        "beta_sigma3_beta": scalar_product(
            fixed_beta, fixed_sigma3, fixed_beta
        ),
        "omega_sigma3_omega": scalar_product(
            fixed_omega, fixed_sigma3, fixed_omega
        ),
        "beta_sigma3_omega": scalar_product(
            fixed_beta, fixed_sigma3, fixed_omega
        ),
        "beta_krylov_gram_determinant": (
            fixed_krylov.transpose() * fixed_krylov
        ).det(),
    }
)
computed_values = {
    name: str(computed_values_raw[name])
    for name in (
        "tr_sigma2",
        "tr_sigma3",
        "beta2",
        "beta_sigma_beta",
        "beta_sigma2_beta",
        "det_beta_sigma_beta_sigma2_beta",
        "omega2",
        "omega_sigma_omega",
        "omega_sigma2_omega",
        "beta_dot_omega",
        "beta_sigma_omega",
        "beta_sigma2_omega",
        "beta_sigma3_beta",
        "omega_sigma3_omega",
        "beta_sigma3_omega",
        "beta_krylov_gram_determinant",
    )
}
expected_values = {
    "tr_sigma2": "14",
    "tr_sigma3": "-18",
    "beta2": "3",
    "beta_sigma_beta": "0",
    "beta_sigma2_beta": "14",
    "det_beta_sigma_beta_sigma2_beta": "20",
    "omega2": "14",
    "omega_sigma_omega": "-18",
    "omega_sigma2_omega": "98",
    "beta_dot_omega": "6",
    "beta_sigma_omega": "-4",
    "beta_sigma2_omega": "36",
    "beta_sigma3_beta": "-18",
    "omega_sigma3_omega": "-210",
    "beta_sigma3_omega": "-64",
    "beta_krylov_gram_determinant": "400",
}

# The registered nongeneric pair has identical catalogue values.  The distinct
# eigenvalues force the stabilizer of sigma to diagonal sign matrices; exact
# enumeration shows that none sends axial omega to -omega.
zero_beta = vector(QQ, [0, 0, 0])
opposite_omega = -fixed_omega
left_catalogue = catalogue(fixed_sigma, zero_beta, fixed_omega)
right_catalogue = catalogue(fixed_sigma, zero_beta, opposite_omega)
catalogues_equal = left_catalogue == right_catalogue
stabilizer_maps_pair = False
for signs in product((-1, 1), repeat=3):
    stabilizer = diagonal_matrix(QQ, signs)
    transformed_axial = stabilizer.det() * stabilizer * fixed_omega
    if transformed_axial == opposite_omega:
        stabilizer_maps_pair = True
        break
nongeneric_pair_exact = catalogues_equal and not stabilizer_maps_pair

# Run the separate Singular source and capture its single status line.
singular_version_process = subprocess.run(
    ["Singular", "--version"],
    check=True,
    capture_output=True,
    text=True,
)
singular_version_line = singular_version_process.stdout.splitlines()[0].strip()
singular_match = re.search(r"version ([0-9]+(?:\.[0-9]+)+)", singular_version_line)
singular_version = singular_match.group(1) if singular_match else singular_version_line
singular_process = subprocess.run(
    ["Singular", "-q", SINGULAR_PROGRAM_PATH.as_posix()],
    check=False,
    capture_output=True,
    text=True,
)
singular_status = singular_process.stdout.strip()
singular_exact = (
    singular_process.returncode == 0
    and singular_status == "SINGULAR_EXACT_PASS"
    and singular_process.stderr.strip() == ""
)

checks = {
    "scalar_pseudoscalar_o3": bool(
        orthogonal_chart
        and proper_determinant
        and improper_determinant
        and proper_parity
        and improper_even
        and improper_odd
    ),
    "cayley_hamilton_tracefree_3x3": bool(ch_exact and singular_exact),
    "cayley_hamilton_vector_contractions": bool(
        ch_contractions_exact and singular_exact
    ),
    "beta_krylov_gram_syzygy": bool(gram_exact and singular_exact),
    "fixed_rational_values": computed_values == expected_values,
    "nongeneric_nonseparation_witness": bool(nongeneric_pair_exact),
    "generic_separation_not_promoted": True,
    "completeness_not_promoted": True,
}
status = "PASS" if all(checks.values()) else "FAIL"

payload = {
    "schema_version": 1,
    "axis": "sage_singular",
    "contract_id": CONTRACT_ID,
    "contract_sha256": CONTRACT_SHA256,
    "status": status,
    "commands": [
        {"cmd": COMMAND, "exit": 0},
        {
            "cmd": f"Singular -q {SINGULAR_PROGRAM_PATH.as_posix()}",
            "exit": singular_process.returncode,
        },
    ],
    "tool_versions": {
        "sage": sage_version,
        "singular": singular_version,
    },
    "source_output_hashes": [
        file_record(PROGRAM_PATH, PRODUCER, COMMAND),
        file_record(
            SINGULAR_PROGRAM_PATH,
            PRODUCER,
            f"Singular -q {SINGULAR_PROGRAM_PATH.as_posix()}",
        ),
    ],
    "domain_assumption_diff": [],
    "evidence_class": "exact",
    "counterexample": None,
    "checks": checks,
    "computed": computed_values,
    "nonpromotion_states": {
        "generic_orbit_separation": "UNPROVEN",
        "invariant_ring_completeness": "UNPROVEN",
    },
    "singular_stdout": singular_status,
    "completed_at": datetime.now(timezone.utc)
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z"),
}

print(
    json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=json_default,
    )
)
