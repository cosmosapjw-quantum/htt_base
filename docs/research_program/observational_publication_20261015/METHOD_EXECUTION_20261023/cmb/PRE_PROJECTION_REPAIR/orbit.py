"""Retained PR3 processed E carrier and finite SO(3) orbit experiment.

This is an observer-space diagnostic on one sky, not a physical CMB null law.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / "docs/research_program/observational_publication_20261015"
COUNTER = BASE / "ADVERSARIAL_AUDIT_20261022/continuation/cmb_counterpairs"
PILOT = BASE / "ADVERSARIAL_AUDIT_20261022/continuation/cmb_pilot"
INPUT = HERE.parent / "CMB_INPUT.json"
Q0 = O0 = 1e-5  # K_CMB, fixed for every map and intervention
PACKET = "503086ca39900549c146176289ea3aff406bc9869397f20ae844f2a3dc86c437"
INPUT_ID = "sha256:0ae60cc8f899f3480b3c186f4f5c534989aa125744cde917f1e52f6ce4301e7a"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_inputs():
    if "sha256:" + digest(INPUT) != INPUT_ID:
        raise ValueError("packet input identity drift")
    pin = json.loads(INPUT.read_text())
    for source in pin["sources"]:
        path = Path(source["path"])
        if not path.is_file() or path.stat().st_size != source["bytes"] or digest(path) != source["sha256"]:
            raise ValueError(f"frozen input drift: {path}")
    return pin


def carrier(alm, projection):
    # c_lm,s=-sqrt(2) Im(a_lm), the repository's canonical real-map basis.
    blocks = []
    for ell in (2, 3):
        c = [float(alm[ell, 0].real)]
        for m in range(1, ell + 1):
            a = alm[ell, m]
            c.extend((float(np.sqrt(2) * a.real), float(-np.sqrt(2) * a.imag)))
        blocks.append(np.asarray(c))
    q = projection.real_harmonic_l2_to_stf(blocks[0])
    o = projection.real_harmonic_l3_to_stf(blocks[1])
    for tensor in (q, o):
        if not np.all(np.isfinite(tensor)):
            raise ValueError("nonfinite STF")
    if not np.allclose(projection.stf2_to_real_harmonic(q), blocks[0], rtol=1e-12, atol=1e-20):
        raise ValueError("quadrupole roundtrip")
    if not np.allclose(projection.stf3_to_real_harmonic(o), blocks[1], rtol=1e-12, atol=1e-20):
        raise ValueError("octupole roundtrip")
    return np.concatenate(blocks), q, o


def pilot_alm(packed):
    # The saved cache has E,B packed through ell=4 (15 values per row).
    import healpy as hp
    if packed.shape != (2, 15) or not np.isfinite(packed).all():
        raise ValueError("secondary-window schema")
    a = packed[0]
    out = {}
    for ell in (2, 3):
        for m in range(ell + 1):
            v = complex(a[hp.Alm.getidx(4, ell, m)])
            out[ell, m] = v
            if m:
                out[ell, -m] = (-1) ** m * v.conjugate()
    return out


def norm_decimal(array):
    with localcontext() as ctx:
        ctx.prec = 90
        return sum(Decimal.from_float(float(x)) ** 2 for x in np.ravel(array)).sqrt()


def determinant_decimal(q):
    a=[[Decimal.from_float(float(v)) for v in row] for row in q]
    return (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
            -a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
            +a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))


def downward(value: Decimal) -> float:
    v = float(value)
    return float(np.nextafter(v, -np.inf)) if Decimal.from_float(v) > value else v


def upward(value: Decimal) -> float:
    v = float(value)
    return float(np.nextafter(v, np.inf)) if Decimal.from_float(v) < value else v


def rotation_from_quaternion(q):
    # Treat each binary64 quaternion component as an exact rational. The
    # resulting matrix is exactly in SO(3); float entries below are display.
    x, y, z, w = [Fraction(float(a)) for a in q]
    s = w*w + x*x + y*y + z*z
    if not s:
        raise ValueError("zero quaternion")
    r = (
        (s-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)),
        (2*(x*y+z*w), s-2*(x*x+z*z), 2*(y*z-x*w)),
        (2*(x*z-y*w), 2*(y*z+x*w), s-2*(x*x+y*y)),
    )
    exact = [[v/s for v in row] for row in r]
    display = np.array([[float(v) for v in row] for row in exact])
    if np.max(np.abs(display @ display.T - np.eye(3))) > 1e-12 or abs(np.linalg.det(display)-1) > 1e-12:
        raise ValueError("rotation witness failed SO3 check")
    return exact, display


def exact_distance(q, o, p, t, r):
    # Decimal values preserve the exact stored float inputs and rational
    # rotation witness to 80 digits. A conservative 1e-12 relative inflation
    # covers decimal evaluation, well beyond its 80-digit arithmetic error.
    with localcontext() as ctx:
        ctx.prec = 90
        rd = [[Decimal(a.numerator)/Decimal(a.denominator) for a in row] for row in r]
        scale = Decimal.from_float(Q0)
        sumsq = Decimal(0)
        for i in range(3):
            for j in range(3):
                rotated = sum(rd[i][a]*rd[j][b]*Decimal.from_float(float(p[a,b])) for a in range(3) for b in range(3))
                z = (Decimal.from_float(float(q[i,j]))-rotated)/scale
                sumsq += z*z
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    rotated = sum(rd[i][a]*rd[j][b]*rd[k][c]*Decimal.from_float(float(t[a,b,c]))
                                  for a in range(3) for b in range(3) for c in range(3))
                    z = (Decimal.from_float(float(o[i,j,k]))-rotated)/scale
                    sumsq += z*z
        return upward(sumsq.sqrt() * (Decimal(1) + Decimal("1e-12")))


def orbit_bounds(a, b):
    _, q, o = a
    _, p, t = b
    with localcontext() as ctx:
        ctx.prec = 90
        # SO(3) preserves each Frobenius norm; reverse triangle gives a
        # global bound even on repeated-eigenvalue/zero tensor strata.
        nq,np_ = norm_decimal(q),norm_decimal(p)
        radial2 = abs(nq-np_)/Decimal.from_float(Q0)
        # Determinant is invariant under proper rotations. Multilinearity and
        # Hadamard give |det A-det B| <= 3 M^2 ||A-B||_F for M=max norms.
        m=max(nq,np_)
        det2=abs(determinant_decimal(q)-determinant_decimal(p))/(3*m*m*Decimal.from_float(Q0)) if m else Decimal(0)
        d2=max(radial2,det2)
        d3 = abs(norm_decimal(o)-norm_decimal(t))/Decimal.from_float(O0)
        lower = downward(max(Decimal(0), (d2*d2+d3*d3).sqrt()*(Decimal(1)-Decimal("1e-12"))))
    def objective(v):
        r = Rotation.from_rotvec(v).as_matrix()
        rq = r@p@r.T
        ro = np.einsum("ia,jb,kc,abc->ijk", r, r, r, t)
        return float(np.hypot(np.linalg.norm(q-rq)/Q0, np.linalg.norm(o-ro)/O0))
    starts = [np.zeros(3)]
    _, va = np.linalg.eigh(q)
    _, vb = np.linalg.eigh(p)
    for signs in ((1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)):
        r = va @ np.diag(signs) @ vb.T
        if np.linalg.det(r) > 0:
            starts.append(Rotation.from_matrix(r).as_rotvec())
    candidates = []
    for start in starts:
        fit = minimize(objective, start, method="Powell", options={"maxiter":120,"xtol":1e-9,"ftol":1e-11})
        candidates.append(fit.x)
    best = min(candidates, key=objective)
    exact, display = rotation_from_quaternion(Rotation.from_rotvec(best).as_quat())
    upper = exact_distance(q,o,p,t,exact)
    if upper + 1e-12 < lower:
        raise ArithmeticError("orbit interval inverted")
    return {"lower": lower, "feasible_upper": upper, "witness_rotation": display.tolist(),
            "SO3_orthogonality_residual": float(np.max(np.abs(display@display.T-np.eye(3)))),
            "SO3_determinant_residual": float(abs(np.linalg.det(display)-1))}


def main():
    verify_inputs()
    sys.path.insert(0, str(ROOT))
    morphology = load_module("retained_cmb_morphology", COUNTER / "morphology.py")
    projection = load_module("retained_cmb_irrep_projection", ROOT / "htt/obsstat/planck_lowell_irrep_projection.py")
    experiment = json.loads((COUNTER / "EXPERIMENT.json").read_text())
    primary = {}
    for entry, alm in morphology.load_fields(experiment):
        primary[(entry["product"], entry["lmax"], 0)] = carrier(alm, projection)
    saved = json.loads((PILOT / "RESULT.json").read_text())["raw_processed_output"]
    cache = Path(saved["path"])
    if not cache.is_file() or cache.stat().st_size != saved["bytes"] or digest(cache) != saved["sha256"]:
        raise ValueError("secondary-window cache drift")
    secondary = {}
    with np.load(cache, allow_pickle=False) as z:
        for ell in (32,64,128):
            for product in morphology.PRODUCTS:
                for window in (0,20,30):
                    key = f"{product}_L{ell}_w{window}"
                    secondary[(product,ell,window)] = carrier(pilot_alm(z[key]), projection)
    # The pilot's recomputed w0 is a distinct processing realization; measure
    # its offset rather than silently treating it as byte/number identical.
    parity = max(float(np.max(np.abs(primary[key][0]-secondary[key][0]))) for key in primary)
    bundles = []
    for source, rows in (("hash_pinned_primary",primary),("pilot_cached",secondary)):
      for (product,ell,window), (c,q,o) in rows.items():
        bundles.append({"source":source,"product":product,"lmax":ell,"secondary_window_degrees":window,
                        "harmonic12_K_CMB":c.tolist(),
                        "STF2_components_K_CMB":projection.stf2_tensor_to_components(q).tolist(),
                        "STF3_components_K_CMB":projection.stf3_tensor_to_components(o).tolist(),
                        "STF2_norm_K_CMB":float(np.linalg.norm(q)),"STF3_norm_K_CMB":float(np.linalg.norm(o))})
    # Exact retained phase oracle: equal scalar multipole powers but an
    # information-bearing full-tensor witness.
    observed = next(a for e,a in morphology.load_fields(experiment) if e["product"]=="full" and e["lmax"]==32)
    phased = morphology.intervention(observed, morphology.Factor.PHASE, .37)
    c0 = carrier(observed, projection)
    c1 = carrier(phased, projection)
    phase = {"C2_C3_relative_power_residual":max(abs(sum(abs(observed[ell,m])**2 for m in range(-ell,ell+1)) /
                           sum(abs(phased[ell,m])**2 for m in range(-ell,ell+1))-1) for ell in (2,3)),
             "harmonic12_distance_K_CMB":float(np.linalg.norm(c0[0]-c1[0])),
             "STF2_determinant_difference_K_CMB_cubed":float(abs(determinant_decimal(c0[1])-determinant_decimal(c1[1]))),
             "orbit_interval":orbit_bounds(c0,c1)}
    if phase["C2_C3_relative_power_residual"] > 1e-12 or phase["orbit_interval"]["lower"] > phase["orbit_interval"]["feasible_upper"]:
        raise ArithmeticError("phase control")
    comparisons = []
    for ell in (32,64,128):
        for product in morphology.PRODUCTS[1:]:
            comparisons.append({"comparison":"split_vs_full","product":product,"lmax":ell,"window":0,
                                "interval":orbit_bounds(primary[("full",ell,0)],primary[(product,ell,0)])})
    for ell in (32,64,128):
        for product in morphology.PRODUCTS:
            comparisons.append({"comparison":"primary_vs_pilot_cached_w0","product":product,"lmax":ell,"window":0,
                                "interval":orbit_bounds(primary[(product,ell,0)],secondary[(product,ell,0)])})
    for ell in (32,64,128):
        for product in morphology.PRODUCTS:
            for window in (20,30):
                comparisons.append({"comparison":"same_product_secondary_window","product":product,
                                    "lmax":ell,"window":window,
                                    "interval":orbit_bounds(secondary[(product,ell,0)],secondary[(product,ell,window)])})
    # Finite processing sets in the actual 12 real harmonic coordinates.
    # The 24 directions are exactly the signed coordinate axes; h_K is an
    # observed finite maximum, with no interpolation/stratum reconstruction.
    support = []
    for ell in (32,64,128):
        for window in (0,20,30):
            rows=primary if window==0 else secondary
            vectors=np.array([rows[(product,ell,window)][0]/Q0 for product in morphology.PRODUCTS])
            support.append({"lmax":ell,"secondary_window_degrees":window,"source":"hash_pinned_primary" if window==0 else "pilot_cached",
                            "direction_set":"signed_12_coordinate_axes",
                            "support_plus":np.max(vectors,axis=0).tolist(),
                            "support_minus":np.max(-vectors,axis=0).tolist(),
                            "processing_set_size":5})
    result={"task_id":"R24-CMB-ORBIT","packet_id":PACKET,"input_identity":INPUT_ID,
            "owner":"obsstat","status":"DIAGNOSTIC_ONLY","claim_tier":"C0_PROCESSED_MAP_DIAGNOSTIC",
            "scope":"one observed PR3 sky; 15 retained product/band carriers and secondary 20/30-degree window sensitivity",
            "transfer_source":"none","q0_K_CMB":Q0,"o0_K_CMB":O0,
            "harmonic_basis":"Condon-Shortley (a_l0, sqrt2 Re a_lm, -sqrt2 Im a_lm)",
            "projection_identity":projection.PROJECTION_IDENTITY,
            "source_hashes":{"experiment":digest(COUNTER/"EXPERIMENT.json"),"pilot_cache":digest(cache),
                             "projection":digest(ROOT/"htt/obsstat/planck_lowell_irrep_projection.py")},
            "primary_cached_max_abs_residual_K_CMB":parity,"bundles":bundles,
            "equal_scalar_phase_control":phase,"comparisons":comparisons,"processing_support":support,
            "p_value":None,"matched_total_field_law":"ABSENT",
            "caveats":["Processed E pseudoalm of common masked delivered QU, not cosmic E.",
                       "L32 is primary; L64/L128 and 20/30-degree windows are sensitivity views of one sky.",
                       "Bounds apply to stored projected tensors with fixed scales; feasible upper is not an optimizer certificate.",
                       "Signed-coordinate support is evaluated at exactly 24 directions; the convex hull does not recover nonconvex strata.",
                       "No matched total-field null law or calibrated p; original acceptance remains unchanged."]}
    (HERE/"RESULT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    primary_pairs=[v for v in comparisons if v["comparison"]=="split_vs_full" and v["lmax"]==32]
    for i,row in enumerate(primary_pairs):
        z=row["interval"]
        axes[0].plot((z["lower"],z["feasible_upper"]),(i,i),"o-",color="tab:blue")
    axes[0].set_yticks(range(len(primary_pairs)),[x["product"] for x in primary_pairs])
    axes[0].set_xlabel("fixed-scale SO(3) distance")
    axes[0].set_title("L32 pinned split vs full\nanalytic lower / feasible upper")
    window_pairs=[v for v in comparisons if v["comparison"]=="same_product_secondary_window" and v["lmax"]==32]
    for i,row in enumerate(window_pairs):
        z=row["interval"]
        axes[1].plot((z["lower"],z["feasible_upper"]),(i,i),"o-",color="tab:orange" if row["window"]==20 else "tab:red")
    axes[1].set_yticks(range(len(window_pairs)),[f'{x["product"]} {x["window"]}°' for x in window_pairs],fontsize=7)
    axes[1].set_xlabel("fixed-scale SO(3) distance")
    axes[1].set_title("L32 pilot window response\nrelative to its cached 0°")
    s=[x for x in support if x["lmax"]==32]
    matrix=np.array([x["support_plus"]+x["support_minus"] for x in s])
    im=axes[2].imshow(matrix,aspect="auto",cmap="coolwarm")
    axes[2].set_yticks(range(3),["pinned 0°","pilot 20°","pilot 30°"])
    axes[2].set_xticks(range(24),[f"{j+1}{sign}" for sign in ("+","−") for j in range(12)],rotation=90,fontsize=6)
    axes[2].set_title("L32 finite processing support\n24 sampled coordinate directions")
    fig.colorbar(im,ax=axes[2],fraction=.046,label="hK, harmonic/K0")
    fig.suptitle("One PR3 sky; processed E pseudoalm; no calibrated p")
    fig.tight_layout()
    for ext in ("png","pdf"):
        fig.savefig(HERE/f"PROCESSING_SUPPORT.{ext}",dpi=160)
    plt.close(fig)
    return result


if __name__ == "__main__":
    r=main()
    print(json.dumps({"bundles":len(r["bundles"]),"comparisons":len(r["comparisons"]),
                      "cache_residual":r["primary_cached_max_abs_residual_K_CMB"]}))
