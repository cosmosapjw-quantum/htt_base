"""R37-03 retained-coefficient consumer; no catalogue fit or old producer call."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[2] / "OBSERVABLE_BRIDGE_RECONCILIATION_20261027" / "products"
SN_PATH = BASE / "R36-08-PUBLIC-SN" / "RESULT.json"
CF_PATH = BASE / "R36-01-CF4-OPERATOR" / "RESULT.json"
K = math.log(10) / 5
Q95 = 26.296227604864242
C_KM_S = 299792.458
H0_SYNTHETIC = 70.0

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def stf_basis():
    e = np.zeros((5, 3, 3))
    e[0] = np.diag([1., -1., 0.]) / math.sqrt(2)
    e[1] = np.diag([1., 1., -2.]) / math.sqrt(6)
    for k, (i, j) in enumerate(((0, 1), (0, 2), (1, 2)), 2):
        e[k, i, j] = e[k, j, i] = 1 / math.sqrt(2)
    return e

E = stf_basis()

def feature(n):
    n = np.asarray(n, float)
    assert n.shape == (3,) and abs(n @ n - 1) < 1e-14
    return np.r_[n, np.einsum("i,aij,j->a", n, E, n)]

def contrast(n, ref):
    return feature(n) - feature(ref)

def tensor(coeff):
    return np.einsum("a,aij->ij", np.asarray(coeff)[3:], E)

def support(mean, cov, row, q=Q95):
    v = float(row @ cov @ row)
    assert v >= -1e-12
    return float(row @ mean), math.sqrt(max(0, v)), math.sqrt(q * max(0, v))

def write_csv(name, rows):
    with (HERE / name).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

def cbl_control():
    # Flat de Sitter, transparent at the vertex: tau(z)=a*z.
    # The discrete scan is a declared finite opacity family, not a data fit.
    zs = [0.025, 0.04, 0.06, 0.08]
    a_true = .2
    grid = np.linspace(0, .25, 251)
    rows = []
    compat = []
    for z in zs:
        d = C_KM_S*z/H0_SYNTHETIC
        dr = d*math.exp(a_true*z/2)
        drp = (C_KM_S/H0_SYNTHETIC)*math.exp(a_true*z/2)*(1+a_true*z/2)
        def curvature(a):
            return (((H0_SYNTHETIC/C_KM_S)**2)*(drp-a*dr/2)**2-math.exp(a*z))/dr**2
        vals = np.array([curvature(a) for a in grid])
        recovered = curvature(a_true)
        assert abs(recovered) < 1e-12
        rows.append(dict(z=z, d_r_Mpc=dr, d_r_prime_Mpc=drp,
                         naive_kappa_invMpc2=curvature(0),
                         corrected_kappa_invMpc2=recovered,
                         compatible_min_invMpc2=float(vals.min()),
                         compatible_max_invMpc2=float(vals.max())))
        compat.append(vals)
    # One common constant across windows: each fixed a supplies all four values.
    # Zero occurs at the single generating a=0.2 (within floating point tolerance).
    residuals = np.ptp(np.array(compat), axis=0)
    assert residuals[200] < 1e-12
    assert residuals[0] > residuals[200] + 1e-10
    return rows, {"family": "tau(z)=a*z, a in [0,0.25] on a 0.001 grid",
                  "generating_a": a_true, "common_constant_zero_at_a": a_true,
                  "max_cross_window_spread_at_zero_opacity_invMpc2": float(residuals[0]),
                  "spread_at_generating_opacity_invMpc2": float(residuals[200]),
                  "status": "exact finite synthetic control only; no empirical CBL derivative"}

def main():
    sn, cf = json.loads(SN_PATH.read_text()), json.loads(CF_PATH.read_text())
    assert sha(SN_PATH) == "f1a9246b7e1ab216fd6fb927a3fc2e28360cf2e5626aba5d7a88f2af05f7e82b"
    assert sn["source"]["selected_covariance_status"] == "SELECTED_COVARIANCE_VALIDATED_ONLY"
    assert sn["primary"]["covariance"]["dimension"] == 490
    assert sn["lower_z_sensitivity"]["covariance"]["dimension"] == 705
    assert np.allclose(np.einsum("aij,bij->ab", E, E), np.eye(5), atol=1e-14)
    directions = {"x": [1,0,0], "y": [0,1,0], "z": [0,0,1], "minus_x": [-1,0,0]}
    ref = directions["z"]
    rows, cross_rows, tensor_rows, comparator_rows = [], [], [], []
    for cohort in ("primary", "lower_z_sensitivity"):
        d = sn[cohort]
        mean = np.r_[d["low_8_mag"], d["high_8_mag"]]
        cov = np.asarray(d["full_16x16_covariance_mag2"])
        assert cov.shape == (16,16) and np.max(abs(cov-cov.T)) < 1e-12
        assert np.linalg.eigvalsh(cov).min() > 0
        assert abs(d["simultaneous_95pct_16D_ellipsoid_squared_radius"]-Q95) < 1e-10
        for bin_no, depth in enumerate(("low", "high")):
            q = tensor(mean[bin_no*8:(bin_no+1)*8])
            assert abs(np.trace(q)) < 1e-14
            tensor_rows.append(dict(cohort=cohort, depth=depth, signed_dipole_mag=mean[bin_no*8:bin_no*8+3].tolist(),
                                    stf_matrix_mag=q.tolist(), eigenvalues_mag=np.linalg.eigvalsh(q).tolist()))
            for direction in ("x", "y", "minus_x"):
                f = contrast(directions[direction], ref)
                L = np.zeros(16); L[bin_no*8:(bin_no+1)*8] = f
                m, sig, width = support(mean, cov, L)
                # Full simultaneous 16D event, transformed once by the target linear functional.
                apparent = -K*m
                stat = K*width
                dip = -K*float(f[:3] @ mean[bin_no*8:bin_no*8+3])
                quad = -K*float(f[3:] @ mean[bin_no*8+3:bin_no*8+8])
                assert abs(apparent-dip-quad) < 1e-14
                for bg, bt in ((0.,0.), (.01,0.), (.01,.02), (.02,.04)):
                    phys = bg+bt/2
                    rows.append(dict(cohort=cohort, depth=depth, direction=direction, reference="z",
                                     geometric_difference_bound=bg, optical_depth_difference_bound=bt,
                                     delta_m_mag=m, delta_m_se_mag=sig, dipole_delta_logH=dip,
                                     stf_delta_logH=quad, apparent_delta_logH=apparent,
                                     apparent_logH_95sim_low=apparent-stat,
                                     apparent_logH_95sim_high=apparent+stat,
                                     physical_logH_conditional_low=apparent-stat-phys,
                                     physical_logH_conditional_high=apparent+stat+phys,
                                     physical_ratio_conditional_low=math.exp(apparent-stat-phys),
                                     physical_ratio_conditional_high=math.exp(apparent+stat+phys)))
        for direction in ("x", "y", "minus_x"):
            f=contrast(directions[direction],ref)
            L=np.r_[-f,f]
            m,s,w=support(mean,cov,L)
            # Independent-bin approximation is only a diagnostic falsifier.
            independent_var=float(f@cov[:8,:8]@f+f@cov[8:,8:]@f)
            cross_rows.append(dict(cohort=cohort,direction=direction,reference="z",
                                   high_minus_low_delta_m_mag=m, joint_se_mag=s,
                                   independent_bin_se_wrong_mag=math.sqrt(independent_var),
                                   apparent_delta_logH=-K*m,
                                   apparent_95sim_low=-K*m-K*w,
                                   apparent_95sim_high=-K*m+K*w))
        # Correct opacity-aware scalar contrast consumes the identical row and joint law.
        # Algebraic scalar and tensor coordinate routes must agree exactly.
        for direction in ("x", "y"):
            f=contrast(directions[direction],ref); L=np.r_[f,np.zeros(8)]
            direct=support(mean,cov,L)
            matrix=float((np.asarray(d["low_8_mag"][:3])@f[:3])+(tensor(d["low_8_mag"])@np.asarray(directions[direction])@np.asarray(directions[direction])-tensor(d["low_8_mag"])@np.asarray(ref)@np.asarray(ref)))
            assert abs(direct[0]-matrix)<1e-14
            comparator_rows.append(dict(cohort=cohort,depth="low",direction=direction,
                                        scalar_same_input_delta_m_mag=direct[0],
                                        tensor_signed_delta_m_mag=matrix,
                                        scalar_and_tensor_joint_se_mag=direct[1],
                                        mean_difference_mag=direct[0]-matrix,
                                        information_gain_claim="none; same linear target and full covariance"))
    write_csv("LOCAL_H_IDENTIFIED_REGION.csv", rows)
    write_csv("joint_depth_contrasts.csv", cross_rows)
    write_csv("signed_tensor_matrices.csv", tensor_rows)
    write_csv("same_input_scalar_comparator.csv", comparator_rows)
    # CF4 source target stays separate from the SN chart and covariance.
    th=np.asarray(cf["theta4x9"]); cc=np.asarray(cf["covariance36x36"])
    cfrows=[]
    for i,z in enumerate(cf["window_centers"]):
        for direction in ("x","z"):
            f=feature(directions[direction]); L=np.zeros(36);L[i*9:i*9+9]=np.r_[1,f]
            m=float(L@th.ravel());sig=math.sqrt(max(0,float(L@cc@L)))
            cfrows.append(dict(window_z_CMB=z,direction=direction,apparent_H_km_s_Mpc=m,
                               marginal_se_km_s_Mpc=sig,scope="separate CF4 fixed-weight operator"))
    write_csv("CF4_retained_H_windows.csv",cfrows)
    cbl,cbl_summary=cbl_control();write_csv("synthetic_CBL_first_derivative.csv",cbl)
    # Calibrated TNI filter: Q_in=diag(1/9,1/25). Xi is invariant to grey scaling.
    qmax,qmin=1/9,1/25
    trans=[]
    for tmin in (.04,.06,.08,.10):
        tmax=1.; lower=math.sqrt(tmin/qmin);upper=math.sqrt(tmax/qmax)
        trans.append(dict(t_min=tmin,t_max=tmax,distance_lower_length_units=lower,
                          distance_upper_length_units=upper,grey_log_scale_status="externally bounded"))
    write_csv("distance_transmission_interval.csv",trans)
    assert abs(trans[-1]["distance_lower_length_units"]-math.sqrt(2.5))<1e-14
    assert trans[-1]["distance_upper_length_units"]==3.
    plt.rcParams.update({"font.size":9,"pdf.fonttype":42})
    fig,ax=plt.subplots(figsize=(7,4))
    for depth,style in (("low","o-"),("high","s-")):
        rr=[r for r in rows if r["cohort"]=="primary" and r["depth"]==depth and r["direction"]=="x"]
        x=[r["geometric_difference_bound"]+r["optical_depth_difference_bound"]/2 for r in rr]
        ax.plot(x,[r["physical_ratio_conditional_low"] for r in rr],style,label=depth+" lower")
        ax.plot(x,[r["physical_ratio_conditional_high"] for r in rr],style,label=depth+" upper")
    ax.axhline(1,color="gray",lw=.8);ax.set(xlabel="Declared |Δr_g| + |Δτ|/2 budget",ylabel="H_u(x)/H_u(z) conditional 95% outer interval")
    ax.legend(ncol=2,fontsize=8);fig.tight_layout();fig.savefig(HERE/"local_H_region_vs_opacity.pdf");plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,3.5))
    ax.fill_between([r["t_min"] for r in trans],[r["distance_lower_length_units"] for r in trans],
                    [r["distance_upper_length_units"] for r in trans],alpha=.3)
    ax.plot([r["t_min"] for r in trans],[r["distance_lower_length_units"] for r in trans],"o-",label="lower")
    ax.plot([r["t_min"] for r in trans],[r["distance_upper_length_units"] for r in trans],"s-",label="upper")
    ax.set(xlabel="Calibrated minimum transmission",ylabel="Identified distance (synthetic length unit)")
    ax.legend();fig.tight_layout();fig.savefig(HERE/"distance_transmission_identified_interval.pdf");plt.close(fig)
    result={"schema":"R37-03-v1","task_id":"R37-03-HUBBLE","owner":"HTT inference / obsstat retained features",
            "claim_tier":"conditional observational apparent contrast plus finite synthetic method control",
            "scope":"490 selected released SN covariance; overlapping 705-row sensitivity; separate CF4 operator",
            "input_sha256":{"R36-08_RESULT":sha(SN_PATH),"R36-01_RESULT":sha(CF_PATH)},
            "basis":"released RA/DEC Cartesian signed dipole plus normalized Frobenius STF5",
            "reference_direction":[0,0,1],"simultaneous_event":"one chi-square_16 radius 26.296227604864242 under conditional fixed-design Gaussian law",
            "physical_relation":"Delta ln H_u = -(ln 10)/5 Delta m + Delta r_g + Delta tau/2",
            "physical_budget":"declared absolute difference bounds, not measured confidence intervals",
            "same_input_scalar_comparator":"scalar opacity-aware linear contrast from same 16D event equals tensor-coordinate contrast; no extra information",
            "cbl_synthetic":cbl_summary,"empirical_CBL":"HOLD: no overlapping independently qualified H(z), radial distance derivative and joint law",
            "grey_vs_dichroic":"traceless log fixes only relative transmission; grey scale needs external bound",
            "covariance":"selected released total STAT+SYS consumed once; full 1701 covariance not certified",
            "source_chart":"released RA/DEC physical frame unknown; zHD integral, zHEL luminosity factor; no physical boost conversion",
            "absolute_H0":"not identified after intercept profiling","transfer_source":"none/native solver absent",
            "null_status":"conditional Gaussian event only; empirical null coverage unknown",
            "original42_completed":"17/42","analytic_alternate_completed":"18/42",
            "files":["LOCAL_H_IDENTIFIED_REGION.csv","joint_depth_contrasts.csv","signed_tensor_matrices.csv","same_input_scalar_comparator.csv","CF4_retained_H_windows.csv","synthetic_CBL_first_derivative.csv","distance_transmission_interval.csv","local_H_region_vs_opacity.pdf","distance_transmission_identified_interval.pdf"]}
    (HERE/"HUBBLE_OPACITY_RESULT.json").write_text(json.dumps(result,indent=2)+"\n")

if __name__=="__main__": main()
