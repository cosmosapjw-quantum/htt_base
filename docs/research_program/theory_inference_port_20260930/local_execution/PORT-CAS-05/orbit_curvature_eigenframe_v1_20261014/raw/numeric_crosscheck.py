"""P05-A numeric cross-check (not a proof): Lean definitions re-implemented in numpy vs repo code.

Compares, on seeded random samples,
  (1) scal(Cna n a) from the Lean formulas (Cna, koszul, riem, scal) with
      htt.src.common.relativistic_kinematics.homogeneous_scalar_curvature(n, a),
      for symmetric n and a in ker n (Jacobi);
  (2) koszul(Cna n a) with homogeneous_connection(Cna n a);
  (3) structure reconstruction from DT(koszul C)(diag lam) with invariant_eigenframe_structure;
  (4) collision branch: invariant_eigenframe_structure raises NumericalUnresolved for repeated lam;
  (5) Lean witness values (T4n, T7w, T10a-c).
Writes raw/numeric_crosscheck.json next to this script.
"""
import hashlib, json, pathlib, sys
import numpy as np

REPO = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
import importlib.util, types  # noqa: E402
# Load the two repo files directly (the htt package shim pulls unrelated optional modules).
_pkg = types.ModuleType("p05a_common"); _pkg.__path__ = [str(REPO / "htt/src/common")]
sys.modules["p05a_common"] = _pkg


def _load(name):
    spec = importlib.util.spec_from_file_location(f"p05a_common.{name}", REPO / f"htt/src/common/{name}.py")
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    return mod


_load("r7_contracts")
rk = _load("relativistic_kinematics")

HERE = pathlib.Path(__file__).resolve().parent
EPS = np.zeros((3, 3, 3))
EPS[0, 1, 2] = EPS[1, 2, 0] = EPS[2, 0, 1] = 1
EPS[0, 2, 1] = EPS[2, 1, 0] = EPS[1, 0, 2] = -1
I3 = np.eye(3)


def Cna(n, a):  # C[k,i,j] = sum_l eps[i,j,l] n[l,k] + a_i d_kj - a_j d_ki
    return (np.einsum('ijl,lk->kij', EPS, n) + np.einsum('i,kj->kij', a, I3)
            - np.einsum('j,ki->kij', a, I3))


def koszul(C):
    G = np.empty_like(C)  # explicit loop, identical index order to Lean `koszul`
    for k in range(3):
        for i in range(3):
            for j in range(3):
                G[k, i, j] = (C[k, i, j] - C[i, j, k] + C[j, k, i]) / 2
    return G


def riem(C):  # R[i,l,j,k]
    G = koszul(C)
    return (np.einsum('mkl,ijm->iljk', G, G) - np.einsum('mjl,ikm->iljk', G, G)
            - np.einsum('mjk,iml->iljk', C, G))


def scal(C):
    return float(np.einsum('ijij->', riem(C)))


def DT(G, T):
    return -np.einsum('mki,mj->kij', G, T) - np.einsum('mkj,im->kij', G, T)


def closed(n, a):
    return float(-np.trace(n @ n) + np.trace(n) ** 2 / 2 - 6 * a @ a)


rng = np.random.default_rng(20261014)
res = {"schema": "htt.p05-a.numeric-crosscheck.v1", "seed": 20261014,
       "repo_module": "htt/src/common/relativistic_kinematics.py",
       "repo_module_sha256": hashlib.sha256((REPO / "htt/src/common/relativistic_kinematics.py").read_bytes()).hexdigest()}
d1 = d1b = d2 = d3 = 0.0
N = 200
for t in range(N):
    m = rng.normal(size=(3, 3)); n = (m + m.T) / 2
    # a in ker n: make n singular along a random unit vector u, a = s*u
    u = rng.normal(size=3); u /= np.linalg.norm(u)
    P = I3 - np.outer(u, u); n = P @ n @ P
    a = rng.normal() * u if t % 2 else np.zeros(3)
    C = Cna(n, a)
    d1 = max(d1, abs(scal(C) - rk.homogeneous_scalar_curvature(n, a)))
    d1b = max(d1b, abs(scal(C) - closed(n, a)))
    d2 = max(d2, float(np.max(np.abs(koszul(C) - rk.homogeneous_connection(C)))))
    lam = np.sort(rng.normal(size=3)) + np.array([0, 1, 2])
    dt = DT(koszul(C), np.diag(lam))
    Crec = rk.invariant_eigenframe_structure(lam, dt, invariant_on_homogeneous_neighborhood=True)
    d3 = max(d3, float(np.max(np.abs(Crec - C))))
res["samples"] = N
res["max_abs_scal_lean_minus_repo"] = d1
res["max_abs_scal_lean_minus_closed_form"] = d1b
res["max_abs_koszul_lean_minus_repo_connection"] = d2
res["max_abs_C_reconstructed_minus_C"] = d3
# scal without Jacobi (T4'): symmetric n, arbitrary a
d4 = 0.0
for t in range(N):
    m = rng.normal(size=(3, 3)); n = (m + m.T) / 2; a = rng.normal(size=3)
    d4 = max(d4, abs(scal(Cna(n, a)) - closed(n, a)))
res["max_abs_scal_minus_closed_form_symmetric_n_arbitrary_a"] = d4
# collision branch
try:
    rk.invariant_eigenframe_structure([1.0, 1.0, 2.0], DT(koszul(Cna(I3, np.zeros(3))), np.diag([1.0, 1.0, 2.0])),
                                      invariant_on_homogeneous_neighborhood=True)
    res["collision_branch"] = "NO_RAISE"
except rk.NumericalUnresolved as e:
    res["collision_branch"] = f"NumericalUnresolved: {e}"
# witnesses
n0 = np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], float)
res["T4n_scal_nonsymm"] = scal(Cna(n0, np.zeros(3)))
res["T4n_closed_form"] = closed(n0, np.zeros(3))
lam = np.array([0.0, 1.0, 2.0]); G = koszul(Cna(I3, np.zeros(3)))
res["T7w_koszul_2_0_1"] = float(G[2, 0, 1])
res["T7w_DT_0_1_2_over_gap"] = float(DT(G, np.diag(lam))[0, 1, 2] / (lam[1] - lam[2]))
res["T10a_scal_I"] = scal(Cna(np.zeros((3, 3)), np.zeros(3)))
res["T10a_scal_VII0"] = scal(Cna(np.diag([1.0, 1.0, 0.0]), np.zeros(3)))
res["T10b_scal_IX_116"] = scal(Cna(np.diag([1.0, 1.0, 6.0]), np.zeros(3)))
res["T10b_scal_V"] = scal(Cna(np.zeros((3, 3)), np.array([1.0, 0, 0])))
res["T10b_traceform_V_0"] = float(np.einsum('kik->i', Cna(np.zeros((3, 3)), np.array([1.0, 0, 0])))[0])
res["T10c_scal_IX_111"] = scal(Cna(I3, np.zeros(3)))
res["T10c_scal_IX_115"] = scal(Cna(np.diag([1.0, 1.0, 5.0]), np.zeros(3)))
(HERE / "numeric_crosscheck.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(res, indent=1))
