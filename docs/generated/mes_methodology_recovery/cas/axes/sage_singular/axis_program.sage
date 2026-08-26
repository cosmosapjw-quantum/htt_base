#!/usr/bin/env sage
"""Exact SageMath plus Singular axis for CAS-PR323-MES-METHODOLOGY-CORE-001.

The program is intentionally standalone.  It reads only the registered
contract and governing input identities, performs every check over exact
rings, and writes exactly one runner-compatible JSON document to stdout.
"""

import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from sage.env import SAGE_VERSION
from sage.rings.integer import Integer
from sage.rings.rational import Rational


AXIS = "sage_singular"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
CONTRACT_SHA256 = "910fd4e002e4c5af1be441253e236b4ffa16f6a71815cf6618417b6b5d5b850c"
SCRIPT_REL = Path(
    "docs/generated/mes_methodology_recovery/cas/axes/"
    "sage_singular/axis_program.sage"
)
CONTRACT_REL = Path(
    "docs/generated/mes_methodology_recovery/cas/CAS_CONTRACT.json"
)
EXPECTED_INPUT_HASHES = {
    "docs/codex_handoff/mes_methodology_recovery/RESEARCH_DECISION_LEDGER.yaml":
        "e4d98b5907eb09a13c04658aeee3db23a3d0995a8378e5d4c3e627141ccc0b62",
    "docs/codex_handoff/mes_methodology_recovery/ADVERSARIAL_SCIENCE_AUDIT.md":
        "6ac385bca9dfebbcbf32a746ef6b7c38022313053b4f0df2ab0f7c0c8f17324a",
    "wolfram/mes_methodology_recovery_proofs.wls":
        "738666f3993471dd461b0f07e35783ac3b0604ee10dbe00ba0e2e4477d4b4930",
}
OBLIGATIONS = [
    "scalar_to_vector_no_go",
    "scalar_to_stf2_no_go",
    "directional_dipole_recovery",
    "directional_stf2_recovery",
    "eigenframe_slice_transverse_simple_spectrum",
    "local_global_fisher_factorization",
    "invertible_anchor_fisher_congruence",
    "finite_rank_formula_n1_100",
    "finite_rank_ties_conservative_n1_100",
    "zero_mean_antipodal_construction",
    "second_moment_antipodal_construction",
]


def sha256_path(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_default(value):
    if isinstance(value, Integer):
        return int(value)
    if isinstance(value, Rational):
        return str(value)
    raise TypeError("not JSON serializable: %r" % (value,))


def canonical_sha256(value):
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=json_default,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def find_repo_root():
    start = Path.cwd().resolve()
    for candidate in (start,) + tuple(start.parents):
        if (candidate / CONTRACT_REL).is_file() and (candidate / SCRIPT_REL).is_file():
            return candidate
    raise RuntimeError("cannot resolve repository root from the registered paths")


def zero_matrix_entries(mat):
    return all(entry == 0 for entry in mat.list())


repo = find_repo_root()
contract_path = repo / CONTRACT_REL
script_path = repo / SCRIPT_REL

contract = json.loads(contract_path.read_text(encoding="utf-8"))

domain_assumption_diff = []
contract_sha = sha256_path(contract_path)
if contract_sha != CONTRACT_SHA256:
    domain_assumption_diff.append(
        "contract sha256 mismatch: expected %s, observed %s"
        % (CONTRACT_SHA256, contract_sha)
    )
contract_obligations = contract.get("target", {}).get("exact_test_obligations")
if contract_obligations != OBLIGATIONS:
    domain_assumption_diff.append(
        "contract obligation order or membership differs from the registered axis"
    )

observed_input_hashes = {}
for rel, expected_hash in EXPECTED_INPUT_HASHES.items():
    observed_hash = sha256_path(repo / rel)
    observed_input_hashes[rel] = observed_hash
    if observed_hash != expected_hash:
        domain_assumption_diff.append(
            "input sha256 mismatch for %s: expected %s, observed %s"
            % (rel, expected_hash, observed_hash)
        )

# ---------------------------------------------------------------------------
# 1-2. Fixed subspaces of the vector and STF2 representations.
# Groebner bases are computed by Sage's Singular polynomial backend over QQ.
# ---------------------------------------------------------------------------
Pvec = PolynomialRing(
    QQ, names=("vx", "vy", "vz"), order="degrevlex", implementation="singular"
)
vx, vy, vz = Pvec.gens()
Jx_vec = Matrix(Pvec, [[0, 0, 0], [0, 0, -1], [0, 1, 0]])
Jy_vec = Matrix(Pvec, [[0, 0, 1], [0, 0, 0], [-1, 0, 0]])
Jz_vec = Matrix(Pvec, [[0, -1, 0], [1, 0, 0], [0, 0, 0]])
v_fixed = vector(Pvec, [vx, vy, vz])
vector_equations = []
for generator in (Jx_vec, Jy_vec, Jz_vec):
    vector_equations.extend(list(generator * v_fixed))
vector_fixed_ideal = Pvec.ideal(vector_equations)
vector_origin_ideal = Pvec.ideal(Pvec.gens())
vector_groebner = vector_fixed_ideal.groebner_basis()
scalar_to_vector_no_go = vector_fixed_ideal == vector_origin_ideal

Pstf = PolynomialRing(
    QQ,
    names=("ta", "tb", "tc", "td", "te", "tf"),
    order="degrevlex",
    implementation="singular",
)
ta, tb, tc, td, te, tf = Pstf.gens()
Jx_stf = Matrix(Pstf, [[0, 0, 0], [0, 0, -1], [0, 1, 0]])
Jy_stf = Matrix(Pstf, [[0, 0, 1], [0, 0, 0], [-1, 0, 0]])
Jz_stf = Matrix(Pstf, [[0, -1, 0], [1, 0, 0], [0, 0, 0]])
T_fixed = Matrix(Pstf, [[ta, td, te], [td, tb, tf], [te, tf, tc]])
tensor_equations = [ta + tb + tc]
for generator in (Jx_stf, Jy_stf, Jz_stf):
    tensor_equations.extend((generator * T_fixed - T_fixed * generator).list())
tensor_fixed_ideal = Pstf.ideal(tensor_equations)
tensor_origin_ideal = Pstf.ideal(Pstf.gens())
tensor_groebner = tensor_fixed_ideal.groebner_basis()
scalar_to_stf2_no_go = tensor_fixed_ideal == tensor_origin_ideal

# ---------------------------------------------------------------------------
# 3-4. Exact normalized full-sky moments.  The helper encodes
# E[n_i n_j] and E[n_i n_j n_k n_l] for E = (4*pi)^-1 integral dOmega;
# odd moments vanish by antipodal symmetry.
# ---------------------------------------------------------------------------
Pmom = PolynomialRing(
    QQ,
    names=("v1", "v2", "v3", "s11", "s22", "s12", "s13", "s23"),
    order="degrevlex",
    implementation="singular",
)
v1, v2, v3, s11, s22, s12, s13, s23 = Pmom.gens()
v_components = [v1, v2, v3]
S_stf = Matrix(
    Pmom,
    [[s11, s12, s13], [s12, s22, s23], [s13, s23, -s11 - s22]],
)


def delta(i, j):
    return QQ.one() if i == j else QQ.zero()


def sphere_moment(indices):
    degree = len(indices)
    if degree % 2 == 1:
        return QQ.zero()
    if degree == 2:
        i, j = indices
        return delta(i, j) / 3
    if degree == 4:
        i, j, k, ell = indices
        return (
            delta(i, j) * delta(k, ell)
            + delta(i, k) * delta(j, ell)
            + delta(i, ell) * delta(j, k)
        ) / 15
    raise ValueError("only the registered degree 1-4 moments are used")


V_reconstructed = []
for a_index in range(3):
    value = 3 * sum(
        v_components[b_index] * sphere_moment((b_index, a_index))
        for b_index in range(3)
    )
    value += 3 * sum(
        S_stf[i_index, j_index]
        * sphere_moment((i_index, j_index, a_index))
        for i_index in range(3)
        for j_index in range(3)
    )
    V_reconstructed.append(Pmom(value))
dipole_residual = vector(Pmom, V_reconstructed) - vector(Pmom, v_components)
directional_dipole_recovery = all(entry == 0 for entry in dipole_residual)

T_reconstructed = Matrix(Pmom, 3, 3)
for a_index in range(3):
    for b_index in range(3):
        vector_part = sum(
            v_components[k_index]
            * (
                sphere_moment((k_index, a_index, b_index))
                - delta(a_index, b_index)
                * sphere_moment((k_index,))
                / 3
            )
            for k_index in range(3)
        )
        tensor_part = sum(
            S_stf[i_index, j_index]
            * (
                sphere_moment((i_index, j_index, a_index, b_index))
                - delta(a_index, b_index)
                * sphere_moment((i_index, j_index))
                / 3
            )
            for i_index in range(3)
            for j_index in range(3)
        )
        T_reconstructed[a_index, b_index] = QQ(15) / 2 * (
            vector_part + tensor_part
        )
stf_residual = T_reconstructed - S_stf
directional_stf2_recovery = zero_matrix_entries(stf_residual)

# ---------------------------------------------------------------------------
# 5. Exact eigenframe-slice transversality determinant.
# ---------------------------------------------------------------------------
Peig = PolynomialRing(
    QQ,
    names=("ell1", "ell2", "ell3", "a12", "a13", "a23"),
    order="degrevlex",
    implementation="singular",
)
ell1, ell2, ell3, a12, a13, a23 = Peig.gens()
S_eigen = diagonal_matrix(Peig, [ell1, ell2, ell3])
A_rotation = Matrix(
    Peig, [[0, a12, a13], [-a12, 0, a23], [-a13, -a23, 0]]
)
commutator = A_rotation * S_eigen - S_eigen * A_rotation
off_diagonal = [commutator[0, 1], commutator[0, 2], commutator[1, 2]]
orbit_jacobian = Matrix(
    Peig,
    [[entry.derivative(parameter) for parameter in (a12, a13, a23)]
     for entry in off_diagonal],
)
transversality_determinant = orbit_jacobian.det()
simple_spectrum_product = (ell1 - ell2) * (ell1 - ell3) * (ell2 - ell3)
eigenframe_slice_transverse_simple_spectrum = (
    transversality_determinant == -simple_spectrum_product
    and simple_spectrum_product != Peig.zero()
)

# ---------------------------------------------------------------------------
# 6. Kronecker Fisher factorization and the registered depth vectors.
# ---------------------------------------------------------------------------
Pfisher = PolynomialRing(
    QQ,
    names=("k11", "k12", "k22", "dirp", "dirq", "dirr"),
    order="degrevlex",
    implementation="singular",
)
k11, k12, k22, dirp, dirq, dirr = Pfisher.gens()
K_depth = Matrix(Pfisher, [[k11, k12], [k12, k22]])
S_direction = diagonal_matrix(Pfisher, [dirp, dirq, dirr])
Fisher = K_depth.tensor_product(S_direction)
fisher_determinant = Fisher.det()
expected_fisher_determinant = (
    (k11 * k22 - k12**2) ** 3 * (dirp * dirq * dirr) ** 2
)

K_independent = Matrix(QQ, [[1, 0], [0, 1]])
S_numeric = diagonal_matrix(QQ, [2, 3, 5])
F_independent = K_independent.tensor_product(S_numeric)
K_one_shell = Matrix(QQ, [[4, 6], [6, 9]])
F_one_shell = K_one_shell.tensor_product(S_numeric)
local_global_fisher_factorization = (
    fisher_determinant == expected_fisher_determinant
    and F_independent.det() == QQ(900)
    and F_independent.rank() == 6
    and K_one_shell.det() == 0
    and K_one_shell.rank() == 1
    and F_one_shell.det() == 0
    and F_one_shell.rank() == 3
)

# ---------------------------------------------------------------------------
# 7. General 2x2 Fisher congruence plus invertible fixed-anchor witness.
# ---------------------------------------------------------------------------
Panchor = PolynomialRing(
    QQ,
    names=(
        "r11", "r12", "r21", "r22", "c11", "c12", "c22",
        "d11", "d12", "d21", "d22",
    ),
    order="degrevlex",
    implementation="singular",
)
(
    r11, r12, r21, r22, c11, c12, c22, d11, d12, d21, d22
) = Panchor.gens()
response = Matrix(Panchor, [[r11, r12], [r21, r22]])
covariance_inverse = Matrix(Panchor, [[c11, c12], [c12, c22]])
normalizer = Matrix(Panchor, [[d11, d12], [d21, d22]])
F0 = response.transpose() * covariance_inverse * response
FD = (
    (response * normalizer).transpose()
    * covariance_inverse
    * (response * normalizer)
)
congruence_residual = FD - normalizer.transpose() * F0 * normalizer
determinant_congruence_residual = (
    FD.det() - normalizer.det() ** 2 * F0.det()
)
normalizer_adjugate = Matrix(Panchor, [[d22, -d12], [-d21, d11]])
adjugate_left_residual = (
    normalizer_adjugate * normalizer
    - normalizer.det() * identity_matrix(Panchor, 2)
)
adjugate_right_residual = (
    normalizer * normalizer_adjugate
    - normalizer.det() * identity_matrix(Panchor, 2)
)

fixed_U = QQ(5)
fixed_v = vector(QQ, [1, 2, 3])
fixed_T = diagonal_matrix(QQ, [1, -1, 0])
scaled_v = fixed_v / fixed_U
scaled_T = fixed_T / fixed_U
fixed_anchor_witness = (
    scaled_v == vector(QQ, [QQ(1) / 5, QQ(2) / 5, QQ(3) / 5])
    and scaled_T == diagonal_matrix(QQ, [QQ(1) / 5, -QQ(1) / 5, 0])
    and Matrix(QQ, [fixed_v, scaled_v]).rank() == 1
    and fixed_T.rank() == scaled_T.rank()
)
invertible_anchor_fisher_congruence = (
    zero_matrix_entries(congruence_residual)
    and determinant_congruence_residual == 0
    and zero_matrix_entries(adjugate_left_residual)
    and zero_matrix_entries(adjugate_right_residual)
    and fixed_anchor_witness
)

# ---------------------------------------------------------------------------
# 8-9. Observation-inclusive exact finite ranks, alpha = 1/20.
# ---------------------------------------------------------------------------
alpha = QQ(1) / 20
rank_formula_failures = []
tie_failures = []
rank_sizes = {}
for m in range(1, 101):
    count_rejecting_positions = sum(
        1 for position in range(m + 1)
        if QQ(1 + position) / (m + 1) <= alpha
    )
    expected_count = floor(alpha * (m + 1))
    actual_size = QQ(count_rejecting_positions) / (m + 1)
    expected_size = QQ(expected_count) / (m + 1)
    rank_sizes[str(m)] = str(actual_size)
    if actual_size != expected_size:
        rank_formula_failures.append(
            {"m": m, "actual": str(actual_size), "expected": str(expected_size)}
        )
    base_count = count_rejecting_positions
    for ties in range(m + 1):
        tied_count = sum(
            1 for position in range(m + 1)
            if QQ(1 + position + ties) / (m + 1) <= alpha
        )
        if tied_count > base_count:
            tie_failures.append(
                {"m": m, "ties": ties, "base": base_count, "tied": tied_count}
            )
finite_rank_formula_n1_100 = not rank_formula_failures
finite_rank_ties_conservative_n1_100 = not tie_failures
first_nonzero_rank_rejection = next(
    m for m in range(1, 101) if floor(alpha * (m + 1)) > 0
)

# ---------------------------------------------------------------------------
# 10-11. Spectral antipodal construction over an exact polynomial ring.
# ---------------------------------------------------------------------------
Pantipodal = PolynomialRing(
    QQ,
    names=("lambda1", "lambda2", "lambda3"),
    order="degrevlex",
    implementation="singular",
)
lambda1, lambda2, lambda3 = Pantipodal.gens()
weights = [lambda1, lambda2, lambda3]
basis = [
    vector(Pantipodal, [1, 0, 0]),
    vector(Pantipodal, [0, 1, 0]),
    vector(Pantipodal, [0, 0, 1]),
]
antipodal_mean = vector(Pantipodal, [0, 0, 0])
antipodal_second_moment = Matrix(Pantipodal, 3, 3)
for weight, axis_vector in zip(weights, basis):
    negative_axis = -axis_vector
    antipodal_mean += weight * (axis_vector + negative_axis) / 2
    positive_outer = Matrix(
        Pantipodal,
        3,
        3,
        lambda i, j: axis_vector[i] * axis_vector[j],
    )
    negative_outer = Matrix(
        Pantipodal,
        3,
        3,
        lambda i, j: negative_axis[i] * negative_axis[j],
    )
    antipodal_second_moment += weight * (positive_outer + negative_outer) / 2
expected_second_moment = diagonal_matrix(
    Pantipodal, [lambda1, lambda2, lambda3]
)
zero_mean_antipodal_construction = all(entry == 0 for entry in antipodal_mean)
second_moment_antipodal_construction = (
    antipodal_second_moment == expected_second_moment
)

checks = {
    "scalar_to_vector_no_go": bool(scalar_to_vector_no_go),
    "scalar_to_stf2_no_go": bool(scalar_to_stf2_no_go),
    "directional_dipole_recovery": bool(directional_dipole_recovery),
    "directional_stf2_recovery": bool(directional_stf2_recovery),
    "eigenframe_slice_transverse_simple_spectrum": bool(
        eigenframe_slice_transverse_simple_spectrum
    ),
    "local_global_fisher_factorization": bool(local_global_fisher_factorization),
    "invertible_anchor_fisher_congruence": bool(
        invertible_anchor_fisher_congruence
    ),
    "finite_rank_formula_n1_100": bool(finite_rank_formula_n1_100),
    "finite_rank_ties_conservative_n1_100": bool(
        finite_rank_ties_conservative_n1_100
    ),
    "zero_mean_antipodal_construction": bool(
        zero_mean_antipodal_construction
    ),
    "second_moment_antipodal_construction": bool(
        second_moment_antipodal_construction
    ),
}

host_singular = subprocess.run(
    ["Singular", "--version"], capture_output=True, text=True, check=False
)
host_singular_first_line = (
    (host_singular.stdout + host_singular.stderr).splitlines() or [""]
)[0]
embedded_singular_version_code = singular.eval('system("version");').strip()

transcript = {
    "axis": AXIS,
    "arithmetic": "exact QQ and QQ polynomial rings; no numerical tolerance",
    "toolchain": {
        "sage": SAGE_VERSION,
        "sage_singular_backend_version_code": embedded_singular_version_code,
        "host_singular_command": "Singular --version",
        "host_singular_exit": host_singular.returncode,
        "host_singular_first_line": host_singular_first_line,
    },
    "rings": {
        "vector_fixed_subspace": str(Pvec),
        "stf2_fixed_subspace": str(Pstf),
        "directional_moments": str(Pmom),
        "eigenframe_slice": str(Peig),
        "fisher_factorization": str(Pfisher),
        "anchor_congruence": str(Panchor),
        "antipodal_construction": str(Pantipodal),
    },
    "obligation_evidence": {
        "scalar_to_vector_no_go": {
            "singular_groebner_basis": [str(item) for item in vector_groebner],
            "solution_ideal": "origin ideal (vx, vy, vz)",
        },
        "scalar_to_stf2_no_go": {
            "singular_groebner_basis": [str(item) for item in tensor_groebner],
            "solution_ideal": "origin ideal in the six symmetric tensor coordinates",
        },
        "directional_dipole_recovery": {
            "normalized_second_moment": "delta_ij/3",
            "residual": [str(item) for item in dipole_residual],
        },
        "directional_stf2_recovery": {
            "normalized_fourth_moment":
                "(delta_ij delta_kl + delta_ik delta_jl + delta_il delta_jk)/15",
            "residual": [str(item) for item in stf_residual.list()],
        },
        "eigenframe_slice_transverse_simple_spectrum": {
            "determinant": str(transversality_determinant.factor()),
            "registered_form": "-(ell1-ell2)(ell1-ell3)(ell2-ell3)",
            "assumption": "ell1, ell2, ell3 pairwise distinct",
        },
        "local_global_fisher_factorization": {
            "determinant": str(fisher_determinant.factor()),
            "registered_form": "det(K)^3 det(S)^2",
            "independent_depth_rank": F_independent.rank(),
            "independent_fisher_determinant": str(F_independent.det()),
            "one_shell_depth_determinant": str(K_one_shell.det()),
            "one_shell_depth_rank": K_one_shell.rank(),
            "one_shell_fisher_rank": F_one_shell.rank(),
        },
        "invertible_anchor_fisher_congruence": {
            "matrix_residual": [str(item) for item in congruence_residual.list()],
            "determinant_residual": str(determinant_congruence_residual),
            "invertibility_localization": "det(D) != 0 via exact adjugate identities",
            "fixed_anchor_U": str(fixed_U),
            "scaled_vector": [str(item) for item in scaled_v],
            "scaled_tensor": [str(item) for item in scaled_T.list()],
        },
        "finite_rank_formula_n1_100": {
            "alpha": str(alpha),
            "failures": rank_formula_failures,
            "first_nonempty_m": first_nonzero_rank_rejection,
            "m19_size": rank_sizes["19"],
            "m100_size": rank_sizes["100"],
        },
        "finite_rank_ties_conservative_n1_100": {
            "failures": tie_failures,
            "enumerated_m": [1, 100],
            "ties_per_m": "0 through m inclusive",
        },
        "zero_mean_antipodal_construction": {
            "mean": [str(item) for item in antipodal_mean],
        },
        "second_moment_antipodal_construction": {
            "second_moment": [str(item) for item in antipodal_second_moment.list()],
            "probability_conditions": "lambda_i >= 0 and sum lambda_i = 1",
        },
    },
}

failed_obligations = [name for name in OBLIGATIONS if not checks[name]]
counterexample = (
    None if not failed_obligations else {"failed_obligations": failed_obligations}
)
all_pass = not failed_obligations and not domain_assumption_diff
if all_pass:
    axis_status = "PASS"
elif domain_assumption_diff:
    axis_status = "MISALIGNED_ASSUMPTIONS"
else:
    axis_status = "FAIL"

binding_material = {
    "checks": checks,
    "counterexample": counterexample,
    "domain_assumption_diff": domain_assumption_diff,
    "transcript": transcript,
}
completed_at = datetime.datetime.now(datetime.timezone.utc).replace(
    microsecond=0
).isoformat()
command = "sage %s" % SCRIPT_REL.as_posix()
result_envelope = {
    "schema_version": 1,
    "axis": AXIS,
    "status": axis_status,
    "evidence_class": "exact",
    "contract_sha256": contract_sha,
    "context_version": CONTEXT_VERSION,
    "completed_at": completed_at,
    "commands": [{"cmd": command, "exit": 0 if all_pass else 1}],
    "reproducible_command": command,
    "artifact_hashes": {
        SCRIPT_REL.as_posix(): sha256_path(script_path),
        CONTRACT_REL.as_posix(): contract_sha,
        **observed_input_hashes,
    },
    "evidence_payload_sha256": canonical_sha256(binding_material),
    "assumptions": list(contract.get("semantics", {}).get("assumptions", [])),
    "positivity_nonzero_conditions": list(
        contract.get("semantics", {}).get("positivity_nonzero_conditions", [])
    ),
    "claim_ceiling": contract.get("identity", {}).get("claim_ceiling"),
    "scope": "diagnostic-only exact CAS methodology receipt; one blind axis only",
    "caveats": list(contract.get("semantics", {}).get("exclusions", [])),
}

payload = {
    "schema": "htt.cas.runner_payload.sage_singular.v1",
    "checks": checks,
    "domain_assumption_diff": domain_assumption_diff,
    "counterexample": counterexample,
    "transcript": transcript,
    "result_envelope": result_envelope,
}
print(
    json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=json_default,
    )
)
if not all_pass:
    sys.stdout.flush()
    os._exit(int(1))
