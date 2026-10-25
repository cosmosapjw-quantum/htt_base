#!/usr/bin/env python3
"""Deterministic consumer of the frozen R32-06-P4-DESIGN finite contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
SCIENCE = HERE.parent / "science"
PACKET = "2a504af3ea3221e2f1ecf03938a5b042296403afb7c07384eafef5847ec8c459"
INPUT = "sha256:263f8707d940df778ea5a6eeef1023cd7784fe5dac5ebe1be2795f0c6e4de450"
CONTRACT_HASH = "cdc26625caf799110f58d101bcde3182134d77aa2e1f8b512112e5ade8aee309"
SOURCE_HASH = "f5640c1ec3c2af4c9c40a9e295de23c2897f89bae84180ebfaa88b0e91d22a12"
OLD_HASH = "92cf81863ce53eb9a0747e87ce8acf386c732ed8fa0876cec6c91c790b633056"
REPLACED = b"The scalar rate is h_* m. STF rate tensor is h_* S, with h_*=v*/R* and S=sum s_a F_a."
INITIAL = b"The scalar rate is h*m. STF rate tensor is h*S, S=sum s_a F_a."
NAMES = ("baseline", "endpoint", "history", "both")
RANKS = {False: (12, 15, 15, 18), True: (8, 11, 11, 14)}
THRESHOLDS = (1e-12, 1e-10, 1e-8)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def close(actual, expected, label, atol=1e-12, rtol=0):
    difference = np.asarray(actual) - np.asarray(expected)
    delta = float(np.max(np.abs(difference))) if difference.size else 0.
    limit = atol + rtol * float(np.max(np.abs(expected)))
    check(delta <= limit, f"{label}: residual {delta:.17g} > {limit:.17g}")
    return delta


def verify_sources():
    contract = SCIENCE / "BUILD_CONTRACT.md"
    sources = SCIENCE / "SOURCE_IDENTITIES.json"
    check(digest(contract) == CONTRACT_HASH, "contract SHA mismatch")
    check(digest(sources) == SOURCE_HASH, "source manifest SHA mismatch")
    b = contract.read_bytes()
    check(b.count(REPLACED) == 1, "notation transition count")
    check(hashlib.sha256(b.replace(REPLACED, INITIAL, 1)).hexdigest() == OLD_HASH,
          "notation inverse SHA mismatch")
    records = json.loads(sources.read_text())["files"]
    check(len(records) == 9, "source count")
    for record in records:
        p = ROOT / record["path"]
        check(p.is_file() and p.stat().st_size == record["bytes"] and
              digest(p) == record["sha256"], f"source mismatch: {p}")
    return records


def basis():
    x, y, z = np.eye(3)
    return np.array([
        np.diag([1., -1., 0.]) / np.sqrt(2),
        np.diag([1., 1., -2.]) / np.sqrt(6),
        (np.outer(x, y) + np.outer(y, x)) / np.sqrt(2),
        (np.outer(x, z) + np.outer(z, x)) / np.sqrt(2),
        (np.outer(y, z) + np.outer(z, y)) / np.sqrt(2),
    ])


F = basis()
DIRECTIONS = np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],
                       [0,0,1],[0,0,-1],[.6,.8,0],[.6,0,.8],[0,.6,.8],
                       [1,0,0],[-1,0,0],[0,1,0],[0,0,1]], dtype=float)


def matrices(q, name, scales=None, sigma_l=1., sigma_g=1.):
    check(name in NAMES and q >= 1 and sigma_l > 0 and sigma_g > 0, "bad design")
    rho = np.r_[np.ones(9), np.full(4, q)]
    e = DIRECTIONS
    quad = np.einsum("ni,aij,nj->na", e, F, e)
    j0 = np.column_stack((-e, e, rho, rho[:,None]*e, rho[:,None]*quad,
                          np.zeros((13, 3))))
    jl = np.zeros((3,18)); jl[:,0:3] = np.eye(3)
    jg = np.zeros((3,18)); jg[:,7:10] = np.eye(3); jg[:,15:18] = np.eye(3)/3
    rows = [j0]
    precisions = [np.ones(13)]
    if name in ("endpoint", "both"):
        rows.append(jl); precisions.append(np.full(3, 1/sigma_l))
    if name in ("history", "both"):
        rows.append(jg); precisions.append(np.full(3, 1/sigma_g))
    j = np.vstack(rows)
    n = np.r_[np.ones(13), np.zeros(len(j)-13)]
    w = np.diag(np.concatenate(precisions))
    wn = w @ n
    p = np.eye(len(j)) - np.outer(wn, wn)/(wn @ wn)
    a0 = p @ w @ j
    l = np.eye(18) if scales is None else scales
    return dict(J=j, N=n, W=w, P=p, L=l, A=a0@l, A_physical=a0)


def physical_null(q, name):
    cols = []
    if q == 1:
        for i in range(3):
            t = np.zeros(18); t[3+i] = -.25; t[7+i] = .25; t[15+i] = -.75
            cols.append(t)
        t = np.zeros(18); t[6] = .25; cols.append(t)
    else:
        if name in ("baseline", "history"):
            for i in range(3):
                t = np.zeros(18); t[i] = t[3+i] = .25; cols.append(t)
        if name in ("baseline", "endpoint"):
            for i in range(3):
                t = np.zeros(18); t[15+i] = .25; cols.append(t)
    if q == 1:
        # At one radius, endpoint/history each remove an independent three-dimensional
        # portion of the ten-dimensional baseline kernel. Obtain the remaining exact
        # kernel from rational design rows via SVD, then compare only dimensions.
        if name != "both":
            return None
    return np.column_stack(cols) if cols else np.zeros((18,0))


def svd_record(m, rank, explicit_null=None):
    a = m["A"]
    u, s, vt = np.linalg.svd(a, full_matrices=True)
    v = vt.T
    pid = v[:,:rank] @ v[:,:rank].T
    pk = v[:,rank:] @ v[:,rank:].T
    close(a @ v[:,rank:], 0, "SVD null residual", atol=1e-12)
    close(pid+pk, np.eye(18), "projector completeness")
    close(pid@pk, 0, "projector orthogonality")
    close(a, (u[:,:len(s)]*s)@vt[:len(s),:], "SVD reconstruction", atol=1e-12)
    if explicit_null is not None:
        nz = np.linalg.inv(m["L"])@explicit_null
        close(a@nz, 0, "analytic null residual", atol=1e-12)
        if nz.shape[1]:
            qn, _ = np.linalg.qr(nz)
            close(qn@qn.T, pk, "analytic/SVD null projectors", atol=1e-12)
    count = {str(t):int(np.sum(s > t*s[0])) for t in THRESHOLDS}
    return dict(singular_values_unscaled=np.linalg.svd(m["A_physical"],compute_uv=False).tolist(),
                singular_values_scaled=s.tolist(), full_right_basis=v.tolist(),
                identified_projector=pid.tolist(), kernel_projector=pk.tolist(),
                identified_physical_combinations=(v[:,:rank].T@np.linalg.inv(m["L"])).tolist(),
                analytic_rank=rank, kernel_dimension=18-rank, numerical_rank_by_cutoff=count,
                s_min_positive=float(s[rank-1]),
                s_min_all_parameters=float(s[rank-1]) if rank==18 else 0.,
                full_vector_inverse_gain=float(1/s[rank-1]) if rank==18 else None,
                full_vector_gain_status="FINITE" if rank==18 else "UNBOUNDED_KERNEL",
                identified_condition=float(s[0]/s[rank-1]))


def matrix_json(m):
    return {k:np.asarray(v).tolist() for k,v in m.items()}


def witness(m, theta, alpha=0.):
    raw_physical = m["J"]@theta
    raw = raw_physical + m["N"]*alpha
    return dict(theta=theta.tolist(), alpha=alpha, raw_physical=raw_physical.tolist(),
                raw_with_nuisance=raw.tolist(), projected=(m["P"]@m["W"]@raw).tolist())


def plots(nominal, radial, precision, errors):
    plt.rcParams.update({"font.size":9, "pdf.fonttype":42})
    fig, ax = plt.subplots(figsize=(7.2,4.2))
    for name in NAMES:
        r = nominal[name]
        vals = r["singular_values_scaled"][:r["analytic_rank"]]
        ax.semilogy(np.arange(1,len(vals)+1), vals, marker="o", ms=2.5,
                    label=f"{name} (kernel {r['kernel_dimension']})")
    ax.set(xlabel="positive singular-value index",ylabel="singular value, fixed scaled coordinates")
    ax.legend(fontsize=8); ax.grid(True, which="both", alpha=.25)
    fig.tight_layout(); fig.savefig(HERE/"figure1_spectra.pdf"); plt.close(fig)
    fig, axs = plt.subplots(1,2,figsize=(9,3.7))
    rr = [r for r in radial if r["delta"]>0]
    axs[0].loglog([r["delta"] for r in rr], [r["both"]["s_min_positive"] for r in rr],"o-")
    axs[0].scatter([3e-5],[radial[0]["both"]["s_min_positive"]],marker="x",color="red",label="equal radius: rank 14")
    axs[0].set(xlabel="radius gap q−1 (equal-radius marker offset)",ylabel="smallest positive singular value")
    axs[0].legend(fontsize=7); axs[0].grid(True,which="both",alpha=.25)
    x = sorted(set(p["sigma_L"] for p in precision)); y = sorted(set(p["sigma_G"] for p in precision))
    z = np.array([[next(p["s_min"] for p in precision if p["sigma_L"]==a and p["sigma_G"]==b) for b in y] for a in x])
    im=axs[1].imshow(z,origin="lower",aspect="auto")
    axs[1].set(xticks=range(4),xticklabels=y,yticks=range(4),yticklabels=x,
               xlabel="history row scale σG",ylabel="endpoint row scale σL")
    fig.colorbar(im,ax=axs[1],label="full-rank minimum singular value")
    fig.tight_layout(); fig.savefig(HERE/"figure2_leverage_precision.pdf"); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.2,4.2))
    certified=[r for r in errors if r["status"]=="CERTIFIED"]
    ax.semilogy([r["eta_ratio"] for r in certified],[r["error_bound"] for r in certified],"o-")
    for ratio in (1,1.1):
        ax.axvline(ratio,color="firebrick",ls="--",alpha=.5)
    ax.text(.99,.95,"uncertified at and above 1",ha="right",va="top",transform=ax.transAxes)
    ax.set(xlabel="operator error η / smin",ylabel="deterministic upper bound on ||ẑ−z||")
    ax.grid(True,which="both",alpha=.25)
    fig.tight_layout(); fig.savefig(HERE/"figure3_error_bound.pdf");plt.close(fig)


def manuscript(nominal, scales):
    source=(SCIENCE/"MANUSCRIPT.md").read_text()
    table="| Design | Rank | Kernel | Positive smin | Identified condition | Full-vector gain |\n|---|---:|---:|---:|---:|---|\n"
    for name in NAMES:
        x=nominal[name]
        gain=f"{x['full_vector_inverse_gain']:.6g}" if x['full_vector_inverse_gain'] is not None else "unbounded"
        table+=f"| {name} | {x['analytic_rank']} | {x['kernel_dimension']} | {x['s_min_positive']:.8g} | {x['identified_condition']:.8g} | {gain} |\n"
    source=source.replace("**Numerical table placement.** Insert the generated nominal table of all scaled singular values, smallest positive singular value and nonzero-subspace condition number here. Include the generated column-scale table in the numerical appendix. Values must come from this construction; raw-coordinate condition numbers from the retained rank example are not values of (21).",table)
    figures={
        "**Figure 1 placement and caption.** Singular spectra of the four responses at \\(q=2\\), using the single frozen normalization (20). Structural null dimensions are marked separately from the nonzero spectrum. Endpoint and weighted-history additions eliminate distinct three-dimensional kernels. The precision metric is stipulated and is not a measured covariance.":("figure1_spectra.pdf","Singular spectra at q=2 with the fixed normalization (20). Legends state structural null dimensions. The row metric is stipulated, not measured covariance."),
        "**Figure 2 placement and caption.** Radial leverage and additional-channel precision for the complete response. The radial panel displays the smallest positive singular value and marks the equal-radius loss of four identified coordinates; full-vector inverse gain is infinite there. The precision panel displays the full-rank minimum singular value or condition number on grid (23). Every panel uses (20), so changes reflect the response and declared metric rather than renormalization.":("figure2_leverage_precision.pdf","Radial leverage and additional-channel precision in fixed scaled coordinates. The equal-radius marker is offset horizontally for log display; its full-vector inverse gain is unbounded."),
        "**Figure 3 placement and caption.** Deterministic inverse bound (25) for the nominal complete design, \\(\\epsilon=10^{-3}\\) and \\(\\|z\\|\\le1\\), as a function of the relative operator error \\(\\eta/s_{\\min}\\). Values at and above one are marked uncertified rather than assigned zero error or omitted. The bound describes a prescribed error set, without a sampling law.":("figure3_error_bound.pdf","Deterministic inverse bound (25) for epsilon=0.001 and ||z||<=1. At and above eta/smin=1 the bound is uncertified. No sampling law is supplied.")}
    for marker,(file,caption) in figures.items():
        check(marker in source,f"missing placement {file}")
        source=source.replace(marker,"\\begin{figure}[ht]\n\\centering\n\\includegraphics[width=0.95\\linewidth]{"+file+"}\n\\caption{"+caption+"}\n\\end{figure}")
    source += "\n## Generated numerical appendix tables\n\n"
    source += "| Parameter | Physical coefficient unit | d_j | L_jj |\n|---|---|---:|---:|\n"
    labels=[f"ell_{i}" for i in "xyz"]+[f"b_{i}" for i in "xyz"]+["m"]+[f"g0_{i}" for i in "xyz"]+[f"s_{i}" for i in range(1,6)]+[f"g1_{i}" for i in "xyz"]
    units=["v*=300 km/s"]*6+["h*=3 km/s/Mpc"]+["beta*=300/299792.458"]*3+["h*=3 km/s/Mpc"]*5+["beta*=300/299792.458"]*3
    for label,unit,d in zip(labels,units,scales):
        source+=f"| {label} | {unit} | {d:.10g} | {1/d:.10g} |\n"
    for name in NAMES:
        source+=f"\n### Complete nominal scaled spectrum: {name}\n\n"
        source+="| Index | Singular value |\n|---:|---:|\n"
        s=nominal[name]["singular_values_scaled"]
        for i in range(18):
            source+=f"| {i+1} | {s[i]:.12g} |\n" if i<len(s) else f"| {i+1} | structural zero (right completion) |\n"
    source+="\nAll arrays, complete right bases and source-linked checks are in the companion JSON artifacts. This numerical appendix is generated from the frozen design and does not add observed channels.\n"
    (HERE/"manuscript_generated.md").write_text(source)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--finalize",action="store_true");args=ap.parse_args()
    check(HERE.name=="report" and ROOT.name=="htt_base", "unexpected resolved output/repo path")
    records=verify_sources()
    if args.finalize:
        finalize(records);return
    close(np.einsum("aij,bij->ab",F,F),np.eye(5),"STF orthonormality")
    close(np.trace(F,axis1=1,axis2=2),0,"STF trace")
    check(np.max(np.abs(np.linalg.norm(DIRECTIONS,axis=1)-1))<1e-12,"unit directions")
    mf=matrices(2,"both")
    d=np.linalg.norm(mf["A"],axis=0)
    check(bool(np.all(d>0)),"zero augmented column")
    l=np.diag(1/d)
    close(np.linalg.norm(matrices(2,"both",l)["A"],axis=0),1,"nominal column norms")
    nominal={}; matrices_out={}; checks={}
    for name,rank in zip(NAMES,RANKS[False]):
        m=matrices(2,name,l);a=m["A"]
        checks[name]={"projection_symmetry":close(m["P"],m["P"].T,"P symmetry"),
                      "projection_idempotence":close(m["P"]@m["P"],m["P"],"P idempotence"),
                      "nuisance_annihilation":close(m["P"]@m["W"]@m["N"],0,"PWN")}
        nominal[name]=svd_record(m,rank,physical_null(2,name))
        check(all(x==rank for x in nominal[name]["numerical_rank_by_cutoff"].values()),
              f"nominal cutoff rank {name}: {nominal[name]['numerical_rank_by_cutoff']}")
        matrices_out[name]=matrix_json(m)
    radial=[]
    for gap in (0,1e-4,1e-3,1e-2,1e-1,1,3):
        row={"delta":gap,"q":1+gap}
        for name,rank in zip(NAMES,RANKS[gap==0]):
            row[name]=svd_record(matrices(1+gap,name,l),rank)
            # Full matrices are already kept for nominal cases; grid carries compact spectra.
            for key in ("full_right_basis","identified_projector","kernel_projector","identified_physical_combinations"):
                del row[name][key]
        radial.append(row)
    precision=[]
    for sl in (.5,1.,2.,4.):
        for sg in (.5,1.,2.,4.):
            a=matrices(2,"both",l,sl,sg)["A"]
            s=np.linalg.svd(a,compute_uv=False)
            precision.append(dict(sigma_L=sl,sigma_G=sg,s_min=float(s[-1]),
                                  condition=float(s[0]/s[-1]),spectrum=s.tolist()))
    smin=nominal["both"]["s_min_positive"]
    errors=[]
    for ratio in (0,.1,.25,.5,.75,.9,1,1.1):
        eta=ratio*smin
        errors.append(dict(eta_ratio=ratio,eta=eta,epsilon=.001,z_norm_limit=1.,
                           status="CERTIFIED" if ratio<1 else "NOT_CERTIFIED_BY_THIS_BOUND",
                           error_bound=(.001+eta)/(smin-eta) if ratio<1 else None))
    # Exact finite witnesses in physical coordinates, including nuisance compensation.
    split=np.zeros(18);split[0]=split[3]=.25
    history=np.zeros(18);history[16]=.25
    equal_dip=np.zeros(18);equal_dip[3]=-.25;equal_dip[7]=.25;equal_dip[15]=-.75
    equal_m=np.zeros(18);equal_m[6]=.25
    witnesses={"zero":witness(matrices(2,"both",l),np.zeros(18)),
               "split":witness(matrices(2,"both",l),split),
               "history":witness(matrices(2,"both",l),history),
               "combined":witness(matrices(2,"both",l),split+history),
               "equal_dipole":witness(matrices(1,"both",l),equal_dip),
               "equal_monopole":witness(matrices(1,"both",l),equal_m,-.25)}
    close(witnesses["split"]["raw_with_nuisance"][:13],0,"split baseline")
    close(witnesses["history"]["raw_with_nuisance"][:13],0,"history baseline")
    close(witnesses["equal_dipole"]["raw_with_nuisance"],0,"equal dipole raw")
    close(witnesses["equal_monopole"]["raw_with_nuisance"],0,"equal monopole with nuisance")
    # Reconstruct the full tensor, preserving signed coordinates.
    s_signed=np.array([.1,-.2,.3,-.4,.5]); tensor=np.einsum("a,aij->ij",s_signed,F)
    close(np.einsum("aij,ij->a",F,tensor),s_signed,"STF signed reconstruction")
    close(np.linalg.norm(tensor),np.linalg.norm(s_signed),"STF norm")
    # Explicit full-rank deterministic perturbation fixture.
    a=matrices(2,"both",l)["A"];u,sv,vt=np.linalg.svd(a,full_matrices=False)
    eta=.25*smin;delta=-eta*np.outer(u[:,-1],vt[-1]);z=vt[-1]*.5;e=u[:,-1]*.001
    ah=a+delta;y=a@z+e;zh=np.linalg.lstsq(ah,y,rcond=None)[0]
    actual=float(np.linalg.norm(zh-z)); bound=(.001+eta*np.linalg.norm(z))/(smin-eta)
    check(actual<=bound+1e-12,"full-rank deterministic bound")
    close(np.linalg.norm(delta,2),eta,"operator fixture norm")
    # Fixed deficient operator: the identified projection is bounded, never the kernel.
    a0=matrices(2,"baseline",l)["A"];v=np.asarray(nominal["baseline"]["full_right_basis"])
    z0=v[:,0]*.5+v[:,12]*.25;e0=np.zeros(13);e0[0]=.001
    estimate=np.linalg.pinv(a0,rcond=1e-12)@(a0@z0+e0)
    identified=np.asarray(nominal["baseline"]["identified_projector"])@z0
    deficient_error=float(np.linalg.norm(estimate-identified))
    check(deficient_error<=.001/nominal["baseline"]["s_min_positive"]+1e-12,
          "fixed deficient identified bound")
    fixture=dict(z=z.tolist(),delta=delta.tolist(),projected_error=e.tolist(),
                 eta_actual=float(np.linalg.norm(delta,2)),epsilon_actual=float(np.linalg.norm(e)),
                 z_norm=float(np.linalg.norm(z)),estimated_z=zh.tolist(),actual_error=actual,
                 certified_bound=bound,deficient_z=z0.tolist(),deficient_projected_error=e0.tolist(),
                 deficient_estimate=estimate.tolist(),deficient_identified_target=identified.tolist(),
                 deficient_actual_error=deficient_error,
                 deficient_bound=.001/nominal["baseline"]["s_min_positive"])
    outputs={"matrices.json":matrices_out,"spectra.json":nominal,"radial_grid.json":radial,
             "precision_grid.json":precision,"error_grid.json":errors,
             "witnesses.json":witnesses,"bound_fixture.json":fixture,
             "column_scales.json":{"physical_units":{"c_km_s":299792.458,"R_star_Mpc":100,
               "v_star_km_s":300,"beta_star":300/299792.458,"h_star_km_s_Mpc":3,
               "theta_parameter_order":["ell_x","ell_y","ell_z","b_x","b_y","b_z","m",
               "g0_x","g0_y","g0_z","s1","s2","s3","s4","s5","g1_x","g1_y","g1_z"],
               "measurement_unit":"dimensionless y-equivalent"},"d":d.tolist(),"L_diagonal":(1/d).tolist(),
               "STF_basis":F.tolist(),"example_signed_s":s_signed.tolist(),"example_full_S":tensor.tolist()},
             "checks.json":{"source_count":len(records),"nominal_projection":checks,
                "nominal_rank_cutoffs":{n:nominal[n]["numerical_rank_by_cutoff"] for n in NAMES},
                "basis_orthonormal_max_residual":float(np.max(abs(np.einsum("aij,bij->ab",F,F)-np.eye(5)))),
                "full_rank_actual_error":actual,"full_rank_bound":bound,
                "deficient_actual_error":deficient_error,"deficient_bound":fixture["deficient_bound"],
                "all_required_checks_passed":True}}
    for filename,obj in outputs.items():
        (HERE/filename).write_text(json.dumps(obj,indent=2,allow_nan=False)+"\n")
    plots(nominal,radial,precision,errors)
    manuscript(nominal,d)
    print(json.dumps({"status":"NUMERICAL_PASS","nominal_ranks":{n:nominal[n]["analytic_rank"] for n in NAMES},
                      "nominal_smin":{n:nominal[n]["s_min_positive"] for n in NAMES},
                      "q1_ranks":{n:radial[0][n]["analytic_rank"] for n in NAMES},
                      "figures":3,"sources_verified":len(records)},indent=2))


def finalize(records):
    required=["reproduce.py","build_tex.py","body.tex","matrices.json","spectra.json","radial_grid.json","precision_grid.json",
              "error_grid.json","witnesses.json","bound_fixture.json","column_scales.json","checks.json",
              "manuscript_generated.md","main.tex","main.pdf","main.log","figure1_spectra.pdf",
              "figure2_leverage_precision.pdf","figure3_error_bound.pdf","CLAIM_SOURCE_MAP.md","README.md",
              "raw/numerical.stdout","raw/numerical.stderr","raw/numerical_first_failure.stderr",
              "raw/numerical_second_failure.stderr","raw/tex_generation.stdout","raw/tex_generation.stderr",
              "raw/latexmk.stdout","raw/latexmk.stderr","raw/latexmk_first_failure.stdout",
              "raw/latexmk_second_failure.stdout","raw/commands.json","preview/contact_sheet.png"]
    required += [str(p.relative_to(HERE)) for p in sorted((HERE/"preview").glob("page-*.png"))]
    for file in required:
        check((HERE/file).is_file(),f"missing output {file}")
    manifest={file:{"sha256":digest(HERE/file),"bytes":(HERE/file).stat().st_size} for file in required}
    checks=json.loads((HERE/"checks.json").read_text())
    check(checks["all_required_checks_passed"],"checks file not PASS")
    evidence_by_claim={"P4-C01":["column_scales.json","matrices.json"],
                       "P4-C02":["radial_grid.json","checks.json"],
                       "P4-C03":["matrices.json","spectra.json"],
                       "P4-C04":["matrices.json","spectra.json"],
                       "P4-C05":["radial_grid.json","witnesses.json"],
                       "P4-C06":["spectra.json","column_scales.json"],
                       "P4-C07":["witnesses.json"],
                       "P4-C08":["error_grid.json","bound_fixture.json"],
                       "P4-C09":[],"P4-C10":[],"P4-C11":[]}
    claim_map={}
    for line in (SCIENCE/"CLAIM_SOURCE_MAP.md").read_text().splitlines():
        if line.startswith("| P4-C"):
            fields=[x.strip() for x in line.strip("|").split("|")]
            check(len(fields)==4,f"claim map row {line}")
            claim_map[fields[0]]={"claim_and_location":fields[1],"retained_source_and_locator":fields[2],
                                  "construction_and_scope":fields[3],"status":"DERIVED_CONDITIONAL",
                                  "generated_evidence":evidence_by_claim[fields[0]]}
    check(len(claim_map)==11,"claim map row count")
    info=subprocess.run(["pdfinfo",str(HERE/"main.pdf")],capture_output=True,text=True,check=True).stdout
    pages=int(next(line.split(":",1)[1].strip() for line in info.splitlines() if line.startswith("Pages:")))
    figures=(HERE/"main.tex").read_text().count("\\includegraphics")
    check(pages>=10 and figures==3 and "\\tag{27}" in (HERE/"main.tex").read_text(),
          "manuscript completeness")
    result={"task_id":"R32-06-P4-DESIGN","attempt":1,"campaign":"R23-whole-42-solver-free",
            "execute_packet_sha256":PACKET,"input_identity":INPUT,
            "scientific_author":"/root/rc_2a504af3ea3221e2",
            "builder_agent":"/root/r35_p4_prescribed_numeric_build","requested_builder_model":"gpt-6-sol",
            "requested_builder_effort":"high","observed_runtime":"UNKNOWN",
            "proposed_product":"response_design_note","candidate_only":True,
            "acceptance_met":False,"original_acceptance_passed":False,
            "original42_acceptance_met":False,"qualified_products":[],
            "independent_review":"PENDING_FRESH_NONAUTHOR_REVIEW",
            "claim_status":"DERIVED_CONDITIONAL_FINITE_DESIGN","transfer_source":"none",
            "full_physical_covariance":"NOT_SUPPLIED","external_history_provider":"NOT_SUPPLIED",
            "vorticity":"NOT_MEASURED",
            "undefined_sectors":{x:"NOT_EVALUABLE_WITH_THIS_RESPONSE" for x in ("x_C","Q","F","Pi","G_F")},
            "V03_original_requirement":"ACTUAL_EXTERNAL_HISTORY_KERNELS_CALIBRATION_COMMON_FRAME_AND_ERROR_MODEL_PENDING",
            "source_manifest_sha256":SOURCE_HASH,"literal_contract_sha256":CONTRACT_HASH,
            "retained_source_files":records,
            "claim_map":claim_map,
            "report_pdf_pages":pages,"vector_figure_count":figures,
            "commands_and_exit_statuses":json.loads((HERE/"raw/commands.json").read_text()),
            "candidate_identity_definition":"SHA-256 of canonical JSON (sorted keys, compact separators) of output_manifest below; RESULT.json and raw/finalize files excluded",
            "output_manifest":manifest,
            "validation":checks,
            "environment":{"python":platform.python_version(),"numpy":np.__version__,"matplotlib":matplotlib.__version__}}
    canonical=json.dumps(manifest,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    result["candidate_manifest_sha256"]=hashlib.sha256(canonical).hexdigest()
    (HERE/"RESULT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"status":"CANDIDATE_ONLY","result":str(HERE/"RESULT.json"),
                      "candidate_manifest_sha256":result["candidate_manifest_sha256"]},indent=2))


if __name__ == "__main__":
    main()
