"""L2-W1-B probe: (1) run the existing exact rational polytope adapter on the frozen instance;
(2) sympy exact inequalities for the curved (parabola-arc) counterexample.
Read-only use of repository code; writes only the JSON given as argv[1]."""
import json, sys, hashlib, pathlib
from fractions import Fraction as Fr
REPO = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
sys.path.insert(0, str(REPO / "htt" / "src"))
from common.typefree_fibers import BoundedRationalPolytope, rational_polytope_fiber_support
import sympy as sp

out = {"sources": {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in
       ["htt/src/common/typefree_fibers.py", "htt/src/common/joint_feasible_set.py"]}}
# K = {x0 + x1 <= 1, 0 <= x <= 1}, B = [1, -1], y = 0, P = [1, 2], direction u = 1 -> c = P^T u = (1, 2)
K = BoundedRationalPolytope(matrix=((1, 1),), bounds=(1,), lower=(0, 0), upper=(1, 1))
r = rational_polytope_fiber_support(K, [[1, -1]], [0], [1, 2])
out["polytope_instance"] = {"status": r.status, "lower": str(r.lower), "upper": str(r.upper),
                            "enumerated_vertex_count": r.enumerated_vertex_count}
# Empty-slice control: y = 3 is outside B(K) = [-1, 1]
r2 = rational_polytope_fiber_support(K, [[1, -1]], [3], [1, 2])
out["polytope_empty_control"] = {"status": r2.status}
# Dual certificates (rows in adapter order: A row, then box rows, then B, -B)
# max: 3/2 * (x0 + x1 <= 1) + 1/2 * (-(x0 - x1) <= 0) gives (1, 2).x <= 3/2
# min: 1 * (-x0 <= 0) + 2 * (-x1 <= 0) gives -(1, 2).x <= 0
lam_max = {"A0": Fr(3, 2), "negB0": Fr(1, 2)}
lam_min = {"lo0": Fr(1), "lo1": Fr(2)}
chk_max = (Fr(3, 2) * 1 + Fr(1, 2) * -1, Fr(3, 2) * 1 + Fr(1, 2) * 1)
out["dual_certificates"] = {"max": {k: str(v) for k, v in lam_max.items()}, "max_combination": [str(v) for v in chk_max],
                            "max_bound": "3/2", "min": {k: str(v) for k, v in lam_min.items()}, "min_bound": "0"}
# Curved counterexample: F = {(t, t^2) : -1 <= t <= 1}, B = first coordinate, P = second.
t, s = sp.symbols("t s", real=True)
diff = sp.factor(t**2 - s**2)
out["curved"] = {
    "t2_minus_s2_factor": str(diff),
    "abs_t_plus_s_le_2_on_box": str(sp.simplify(sp.Abs(t + s) <= 2)),
    "max_abs_t_plus_s_on_box": str(sp.Max(*[abs(a + b) for a in (-1, 1) for b in (-1, 1)])),
    "kernel_direction": "(0,1): B(0,1)=0, P(0,1)=1",
    "unbounded_parabola_ratio_at_s=0": str(sp.simplify((t**2 - 0) / (t - 0))),
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
