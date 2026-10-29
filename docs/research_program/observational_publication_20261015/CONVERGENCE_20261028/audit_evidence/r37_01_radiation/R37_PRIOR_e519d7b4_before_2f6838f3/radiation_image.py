"""R37-01 finite synthetic radiation/shear image. Read-only R36 sources."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
R36 = ROOT / "docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-05-RADIATION-RESPONSE"
GOAL = ROOT / "docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/imports/four_goals/lanes/GOAL1_NUMERICS.json"
CONV = ROOT / "docs/research_program/observational_publication_20261015/CONVERGENCE_20261028"
NPZ = R36 / "source_backup/derived/sample_arrays.npz"
CASE = "a0.02_b0.3"
GAMMA = 0.4  # inverse declared toy time
POL_AMP = 0.12
SHEAR_TRUE = np.array([0.014, -0.008, 0.006, 0.002, -0.003])
TOL = 2e-10  # normalized-rho operator and shear coordinates; fixed before comparison
SOURCE_HASHES = {
    "radiation_core.py": "a1eca64b2964529872faf9da5089074e68215f13432079287a364bbc631d844d",
    "RESULT.json": "074b49cc8ce3edcfb8dc106a83858ecf5bb5c08c824952d748377b911879529d",
    "GOAL1_NUMERICS.json": "c500fd2dbdd11f3ff7d331abf90a69189e56d738ae8984f8b6816364aaf3ce7b",
    "DEVELOPMENT_PLAN.md": "771e3415d0d7ff7dca5dacbd269723d6cc14bb9f9d1fac75673b82534ad9d4aa",
    "DATA_ANALYSIS_CONTRACTS.md": "11f8d3870c929202de785bcbc66805e6ff33000178a5d6bd2f29683e1eef10e0",
    "SOURCE_REUSE.json": "f3a79443086652a4e2eb53a9cb3030db18f16a38568f4a13bc062174bc653616",
    "JOINT_REMAINDER.json": "cc9f7c92b73f2193b018e438fea5851a24d6a0d8ca3b0d493af9ecf0892373a6",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_core():
    spec = importlib.util.spec_from_file_location("r36_radiation_core", R36 / "radiation_core.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sky(core, n):
    """Pure R36 boosted positive temperature sky, without old producer main()."""
    v = 0.3 * np.array([0.6, 0., 0.8])
    b2 = float(v @ v)
    g = 1 / np.sqrt(1 - b2)
    boost = np.eye(4)
    boost[0, 0] = g
    boost[0, 1:] = boost[1:, 0] = -g * v
    boost[1:, 1:] += (g - 1) * np.outer(v, v) / b2
    e = -n
    p0 = boost[0, 0] + e @ boost[0, 1:]
    pspace = boost[1:, 0] + e @ boost[1:, 1:].T
    zrest = -pspace[:, 2] / p0
    bright_rest = 1 + .02 * (3 * zrest**2 - 1) / 2
    if bright_rest.min() <= 0:
        raise ValueError("source positivity failure")
    return bright_rest**.25 / p0


def operators(core, n, w):
    e = -n
    s = core.STF_BASIS
    se = np.einsum("aij,nj->nai", s, e)
    ese = np.einsum("ni,nai->na", e, se)
    k = 2 * np.einsum("nai,nbi->nab", se, se) - np.einsum("na,nb->nab", ese, ese)
    p = np.eye(3) - np.einsum("ni,nj->nij", n, n)
    ps = np.einsum("nij,jk,nkl->nil", p, s[0], p)
    pol = ps - .5 * p * np.trace(ps, axis1=1, axis2=2)[:, None, None]
    screen = p / 2 + POL_AMP * pol
    screen_min = float(np.min(np.linalg.eigvalsh(screen)[:, 1]))
    if screen_min <= 0:
        raise ValueError("screen source not positive")
    # STF of the integrated real, screen trace-free contribution.
    polcoord = np.einsum("aij,nij->na", s, POL_AMP * pol)
    pic = np.einsum("aij,ni,nj->na", s, e, e)
    return (w[:, None, None] * k).reshape(len(n), 25), w[:, None] * pic, w[:, None] * polcoord, screen_min


def responses(core, n, w, temp, eta, chunk=256):
    basis = np.column_stack([n, np.einsum("aij,ni,nj->na", core.STF_BASIS, n, n)])
    tbar = float(w @ temp)
    theta = temp / tbar - 1
    matrix, pic, polc, _ = operators(core, n, w)
    L, pi, pol = [], [], []
    for start in range(0, len(eta), chunk):
        noisy = tbar * (1 + theta[None, :] + eta[start:start+chunk] @ basis.T)
        if np.any(noisy <= 0):
            raise ValueError("saved draw violates positive temperature")
        bright = noisy**4
        L.append((bright @ matrix).reshape(-1, 5, 5))
        pi.append(bright @ pic)
        pol.append(bright @ polc)
    return np.concatenate(L), np.concatenate(pi), np.concatenate(pol)


def shear(L, pi, pol, R, mode):
    p = np.zeros_like(pol) if mode == "unpolarized" else pol
    C = -GAMMA * (.9 * pi + .2 * p)
    return np.linalg.solve(L, -(R - C)[..., None])[..., 0]


def gain_response(core, rho, pi):
    """Same rho/pi and P_star gain carrier; omitted H4 set to zero."""
    s = core.STF_BASIS
    pit = np.einsum("...a,aij->...ij", pi, s)
    out = []
    for sj in s:
        # Batch STF, retaining the exact quadrupole contribution.
        x = np.einsum("ij,...jk->...ik", sj, pit)
        x = (x + np.swapaxes(x, -1, -2)) / 2
        x -= np.trace(x, axis1=-2, axis2=-1)[..., None, None] * np.eye(3) / 3
        y = 8 * rho[..., None, None] / 15 * sj + 10 / 7 * x
        out.append(np.einsum("aij,...ij->...a", s, y))
    mat = np.stack(out, axis=-1)
    return (mat + np.swapaxes(mat, -1, -2)) / 2


def main():
    start = time.time()
    core = load_core()
    result36 = json.loads((R36 / "RESULT.json").read_text())
    status36 = json.loads((R36 / "PUBLICATION_STATUS.json").read_text())
    goal = json.loads(GOAL.read_text())
    for path, expected in [(R36 / "radiation_core.py", SOURCE_HASHES["radiation_core.py"]),
                           (R36 / "RESULT.json", SOURCE_HASHES["RESULT.json"]),
                           (GOAL, SOURCE_HASHES["GOAL1_NUMERICS.json"]),
                           *[(CONV/name, SOURCE_HASHES[name]) for name in ("DEVELOPMENT_PLAN.md","DATA_ANALYSIS_CONTRACTS.md","SOURCE_REUSE.json")],
                           (CONV/"imports/four_goals/lanes/JOINT_REMAINDER.json", SOURCE_HASHES["JOINT_REMAINDER.json"])]:
        if sha(path) != expected:
            raise RuntimeError(f"immutable source mismatch: {path}")
    if result36["claim_tier"] != "conditional_synthetic_method_experiment" or not status36["acceptance_met"]:
        raise RuntimeError("R36 qualified synthetic source mismatch")
    if goal["joint_response"]["rank"] != 23 or goal["joint_response"]["shear_scalar_rank"] != 15:
        raise RuntimeError("common carrier rank source mismatch")
    n, w = core.sphere_rule(24, 49)
    temp = sky(core, n)
    L0, pi0, P0 = responses(core, n, w, temp, np.zeros((1, 8)))
    L0, pi0, P0 = L0[0], pi0[0], P0[0]
    m = core.moments(n, w, temp**4, 1.)
    Lm = core.response_from_moments(m)
    Ld = core.response_direct(n, w, temp**4, 1.)
    carrier_error = float(max(np.max(abs(L0-Lm)), np.max(abs(Ld-Lm))))
    if carrier_error > TOL:
        raise RuntimeError(f"full/common response mismatch {carrier_error}")
    eig = np.linalg.eigvalsh(L0)
    if eig[0] <= 0:
        raise RuntimeError("noncoercive positive sky")
    rho0 = m.rho
    Lg0 = gain_response(core, np.array([rho0]), pi0[None])[0]
    C0 = -GAMMA*(.9*pi0+.2*P0)
    # Construct a conditional central derivative, explicitly unmeasured.
    R0 = C0 - L0 @ SHEAR_TRUE
    central = {"full": shear(L0, pi0, P0, R0, "full"),
               "common_carrier": shear(Lm, pi0, P0, R0, "common_carrier"),
               "gain_only": shear(Lg0, pi0, P0, R0, "full"),
               "unpolarized": shear(L0, pi0, P0, R0, "unpolarized")}
    if np.max(abs(central["full"]-SHEAR_TRUE)) > TOL or np.max(abs(central["common_carrier"]-central["full"])) > TOL:
        raise RuntimeError("central shear preservation failure")
    with np.load(NPZ) as archive:
        eta_cal = archive[f"{CASE}_eta_cal"]
        eta_test = archive[f"{CASE}_eta_test"]
    # Reuse the exact saved paired R36 draws; no RNG or old producer invocation.
    law = {}
    for label, eta in [("cal", eta_cal), ("test", eta_test)]:
        LL, pp, pol = responses(core, n, w, temp, eta)
        bright_rho = np.trace(LL, axis1=1, axis2=2) * (3/8)  # tr L = 8 rho/3
        Lgain = gain_response(core, bright_rho, pp)
        law[label] = {"full": shear(LL, pp, pol, R0, "full"),
                      "gain_only": shear(Lgain, pp, pol, R0, "full"),
                      "unpolarized": shear(LL, pp, pol, R0, "unpolarized")}
    # Inference-only timing on identical precomputed test arrays. This does not
    # include sky acquisition or extraction of the method-specific carrier.
    timing = {}
    for mode, matrix, polarization in (("full", LL, pol),
                                       ("common_carrier", LL, pol),
                                       ("gain_only", Lgain, pol),
                                       ("unpolarized", LL, np.zeros_like(pol))):
        trials = []
        for _ in range(5):
            tick = time.perf_counter()
            shear(matrix, pp, polarization, R0, "full")
            trials.append(time.perf_counter()-tick)
        timing[mode] = {"median_seconds_for_4096_test_draws":float(np.median(trials)),
                        "scope":"inference-only; precomputed carrier; five local trials"}
    law["cal"]["common_carrier"] = law["cal"]["full"]
    law["test"]["common_carrier"] = law["test"]["full"]
    directions = np.eye(5)
    direction_names = [f"STF{i+1}" for i in range(5)]
    # One joint primitive z in the Euclidean unit disk. Its two columns drive
    # both derivative and polarization; support is a row norm after one map.
    U = np.array([[1., .1], [.2, .8], [.3, -.4], [0., .5], [-.2, .3]])
    V = np.array([[.5, .2], [.1, -.6], [-.3, .2], [.4, .1], [0., -.2]])
    U /= np.linalg.norm(U, 2)
    V /= np.linalg.norm(V, 2)
    budgets_R = [0., .002, .005, .01, .02]
    budgets_P = [0., .01, .03]
    rows = []
    coverage = []
    for mode in ("full", "common_carrier", "gain_only", "unpolarized"):
        for j, name in enumerate(direction_names):
            cal = law["cal"][mode][:, j]
            test = law["test"][mode][:, j]
            radius = float(np.quantile(abs(cal-central[mode][j]), .95, method="higher"))
            hit = np.mean(abs(test-SHEAR_TRUE[j]) <= radius)
            coverage.append({"method":mode,"direction":name,"radius":radius,"width":2*radius,
                             "coverage_test":float(hit),"cal_N":len(cal),"test_N":len(test),
                             "signed_bias":float(central[mode][j]-SHEAR_TRUE[j])})
        Lmode = Lg0 if mode == "gain_only" else L0
        for er in budgets_R:
            for ep in budgets_P:
                joint = -np.linalg.solve(Lmode, er*U+GAMMA*ep/5*V)
                for j,name in enumerate(direction_names):
                    support = float(np.linalg.norm(directions[j] @ joint))
                    rows.append({"method":mode,"direction":name,"epsilon_R":er,"epsilon_P":ep,
                                 "center":float(central[mode][j]),"physical_support":support,
                                 "statistical_radius":coverage[("full","common_carrier","gain_only","unpolarized").index(mode)*5+j]["radius"],
                                 "total_half_width_triangle":support+coverage[("full","common_carrier","gain_only","unpolarized").index(mode)*5+j]["radius"]})
    omission = central["full"]-central["unpolarized"]
    omission_bound = GAMMA*np.linalg.norm(P0)/(5*eig[0])
    if np.linalg.norm(omission) > omission_bound + TOL:
        raise RuntimeError("polarization omission bound failure")
    gain_bias = central["gain_only"]-central["full"]
    if np.linalg.norm(gain_bias) < 1e-6:
        raise RuntimeError("gain information-loss control too weak")
    with (HERE/"SHEAR_SUPPORT.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with (HERE/"MATCHED_COVERAGE.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(coverage[0]));writer.writeheader();writer.writerows(coverage)
    meta={"owner":"htt","claim_tier":"conditional_synthetic_method_experiment","artifact_mode":"finite_methods_image",
          "allowed_use":"conditional response and shear sensitivity only","transfer_source":"none",
          "null_status":"saved R36 oracle synthetic draws; no empirical sky null",
          "covariance_status":"same saved R36 eight-coordinate correlated temperature law; physical remainder is one shared two-dimensional body",
          "forbidden_uses":["empirical shear", "Bianchi family identification", "native solver validation"]}
    def plot(name, fn):
        fig,ax=plt.subplots(figsize=(6.4,4.1));fn(ax);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(HERE/name);plt.close(fig)
    plot("radiation_response_spectrum.pdf",lambda ax:(ax.plot(range(1,6),eig,"o-",label="full/common"),ax.plot(range(1,6),np.linalg.eigvalsh(Lg0),"s--",label="gain closure"),ax.set(xlabel="STF eigenvalue index",ylabel="response / reference energy density",title="Positive synthetic sky response"),ax.legend()))
    plot("shear_support_vs_transport_budget.pdf",lambda ax:([ax.plot(budgets_R,[r["physical_support"] for r in rows if r["method"]==mode and r["direction"]=="STF1" and r["epsilon_P"]==.01],label=mode) for mode in ("full","gain_only","unpolarized")],ax.set(xlabel="declared derivative remainder budget",ylabel="STF1 shear support / toy time",title="One joint physical-error image; polarization budget 0.01"),ax.legend()))
    plot("polarization_omission_bias.pdf",lambda ax:(ax.bar(range(1,6),omission),ax.axhline(omission_bound,color="red",ls="--",label="norm bound"),ax.axhline(-omission_bound,color="red",ls="--"),ax.set(xlabel="STF coordinate",ylabel="full minus unpolarized shear / toy time",title="Calculated polarization omission"),ax.legend()))
    plot("matched_coverage_width.pdf",lambda ax:([ax.errorbar(range(1,6),[x["coverage_test"] for x in coverage if x["method"]==mode],yerr=None,marker=mark,label=mode) for mode,mark in [("full","o"),("gain_only","s"),("unpolarized","^")]],ax.axhline(.95,color="black",ls="--"),ax.set(xlabel="STF coordinate",ylabel="test coverage of same physical target",ylim=(0,1.02),title="Matched saved draws; oracle calibration"),ax.legend()))
    out={"schema":"htt.r37_radiation_image/1","task_id":"R37-01-RADIATION","case":CASE,"source_metadata":meta,
         "source_bindings":{"R36_RESULT_sha256":sha(R36/"RESULT.json"),"R36_PUBLICATION_STATUS_sha256":sha(R36/"PUBLICATION_STATUS.json"),"R36_qualification":status36["status"],"R36_CORE_sha256":sha(R36/"radiation_core.py"),"R36_ARRAYS_sha256":sha(NPZ),"GOAL1_sha256":sha(GOAL),"DEVELOPMENT_PLAN_sha256":sha(CONV/"DEVELOPMENT_PLAN.md"),"DATA_ANALYSIS_CONTRACTS_sha256":sha(CONV/"DATA_ANALYSIS_CONTRACTS.md"),"SOURCE_REUSE_sha256":sha(CONV/"SOURCE_REUSE.json"),"JOINT_REMAINDER_sha256":sha(CONV/"imports/four_goals/lanes/JOINT_REMAINDER.json")},
         "conventions":{"metric":"(-,+,+,+)","observer":"R36 local observer; e=-n","energy":"rho_ref normalized","time":"declared toy time unit","gamma_T":GAMMA,"temperature_to_intensity":"positive Planckian ray I/I0=(T/T0)^4","polarization":"integrated real screen STF P_star; V=0","R_tau":"constructed central value plus declared two-dimensional remainder, not measured"},
         "predeclared_tolerance":TOL,"full_common_max_error":carrier_error,
         "carrier":{"joint_rank":23,"linear_no_V_rank":20,"shear_rank":15,"positive_screen_min_eigenvalue":operators(core,n,w)[3],
                    "positive_intensity_minimum":float(np.min(temp**4)),
                    "saved_equal_gain_different_shear_control":goal["equal_gain_different_shear"]},
         "response":{"full_eigenvalues":eig.tolist(),"full_condition":float(eig[-1]/eig[0]),"gain_eigenvalues":np.linalg.eigvalsh(Lg0).tolist(),"gain_condition":float(np.linalg.cond(Lg0)),"minimum_coercivity":float(eig[0])},
         "target":{"STF5_shear":SHEAR_TRUE.tolist(),"R_tau_center":R0.tolist(),"C_pi_center":C0.tolist(),"P_star_center":P0.tolist(),"pi_center":pi0.tolist()},
         "centers":{k:v.tolist() for k,v in central.items()},"gain_only_bias_norm":float(np.linalg.norm(gain_bias)),
         "polarization_omission":{"difference_full_minus_unpolarized":omission.tolist(),"norm":float(np.linalg.norm(omission)),"coercive_upper_bound":float(omission_bound)},
         "physical_error":{"primitive":"one shared z in unit Euclidean disk","U":U.tolist(),"V":V.tolist(),"epsilon_R_grid":budgets_R,"epsilon_P_grid":budgets_P,"map":"-L_inverse (epsilon_R U + gamma_T epsilon_P V/5) z; applied once"},
         "matched_law":{"cal_draws":len(eta_cal),"test_draws":len(eta_test),"calibration":"95% higher quantile of absolute centered method error from saved oracle draws","coverage_target":"same declared STF5 shear for every method","statistical_cost":{"full_kernel_rows":len(n),"common_carrier_components":20,"gain_only_components":9,"unpolarized_components":15,"inference_only_timing":timing},"coverage_rows":coverage},
         "limits":"Conditional synthetic complete sky only. Central R_tau manufactured from declared target; derivative remainder sensitivity unmeasured. Fixed polarization profile and oracle noise. No empirical shear, native transfer, or family claim.","elapsed_seconds":time.time()-start}
    (HERE/"RADIATION_IMAGE_RESULT.json").write_text(json.dumps(out,indent=2)+"\n")
    report=f"""# R37-01 radiation and STF5 shear sensitivity\n\nThe positive synthetic R36 {CASE} temperature sky and saved paired R36 noise draws determine this conditional methods image. The same sky, local observer, nuisance, correlated eight-coordinate temperature law, and constructed central derivative target are used for every method. The derivative is an **assumption**, not a measured radiation history.\n\nFull direct quadrature and exact (rho, pi, H4) common-carrier response differ by {carrier_error:.3g} in normalized energy units, below the preregistered {TOL:g} tolerance. The full response eigenvalues are {np.array2string(eig,precision=6)} and its condition number is {eig[-1]/eig[0]:.5g}. The joint gain/shear carrier has rank 23, or 20 at V=0; these ranks are reused from the executed Goal 1 source. The screen remains positive with minimum physical eigenvalue {operators(core,n,w)[3]:.5g}.\n\nThe gain-only closure discards H4 while retaining rho, pi and P_star; its central STF5 bias norm is {np.linalg.norm(gain_bias):.5g}. Omitting P_star with the exact intensity response gives full-minus-unpolarized bias norm {np.linalg.norm(omission):.5g}, bounded by gamma_T ||P_star||/(5 lambda_min) = {omission_bound:.5g}. This is a calculated information-loss consequence on the same physical target.\n\nThe physical image uses a single two-coordinate unit-disk primitive z. The same z drives derivative and polarization errors through the displayed U,V matrices in the JSON result; their effects are summed before one inverse map. SHEAR_SUPPORT.csv gives directional support for five STF directions over the declared derivative and polarization budgets. The statistical radii use the saved 8191 calibration and 4096 test draws, with matched oracle calibration for each adapter. MATCHED_COVERAGE.csv reports target coverage, width and signed bias. Structural cost counts and five-trial median inference-only timings on the 4096 identical test arrays are in the JSON; the timings exclude carrier extraction and are not a throughput claim.\n\nThe figures and tables have owner htt, claim tier conditional_synthetic_method_experiment, artifact mode finite_methods_image, transfer source none, synthetic null status and the same R36 correlated noise law. Allowed use is a conditional response/shear sensitivity image. Empirical shear, native solver validation and Bianchi family identification are forbidden uses. Original 42-node acceptance remains 17/42; analytic alternate remains 18/42.\n"""
    (HERE/"REPORT_DELTA.md").write_text(report)
    print(json.dumps({"case":CASE,"carrier_error":carrier_error,"gain_bias_norm":float(np.linalg.norm(gain_bias)),"omission_norm":float(np.linalg.norm(omission)),"omission_bound":float(omission_bound),"rows":len(rows),"coverage_rows":len(coverage),"seconds":time.time()-start}))


if __name__ == "__main__":
    main()
