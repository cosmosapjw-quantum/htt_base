#!/usr/bin/env python3
"""Summarize the completed R63 finite experiments without additional fitting."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import linalg, stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def limits(values):
    values=list(values)
    return [float(min(values)),float(max(values))]


def run(folder):
    folder=Path(folder)
    observed=folder/"RESULTS/OBSERVED/FRAME_HISTORY_RESULT.json"
    chart=folder/"RESULTS/CATALOGUE_CHART_TRANSPORT.json"
    d=json.loads(observed.read_text());q=json.loads(chart.read_text())
    rows=[]
    for name,v in d["variants"].items():
        for degree,s in v["models"].items():
            free=q["models"][name+f"__J{degree}__free_history"]
            tied=q["models"][name+f"__J{degree}__rad_tied"]
            w_radius=s["physical_body"]["W_bound_km_s"]
            w_cov=np.asarray(free["target_covariance"])
            w_precision=linalg.inv(w_cov)
            w_score=linalg.solve(w_cov,np.asarray(free["corrected_target"]),assume_a="pos")
            corrected_ball_bound=float(2*w_radius*linalg.norm(w_score)+w_radius**2*linalg.eigvalsh(w_precision)[-1])
            rows.append({"operator":name,"J":int(degree),
                "W_zero_p_original":s["W_zero_test"]["nominal_p"],
                "W_zero_p_catalogue_chart":free["zero_nominal_p"],
                "W_tangent_estimate_km_s":free["corrected_target"],
                "W_sd_km_s":np.sqrt(np.diag(free["target_covariance"])).tolist(),
                "U_tied_corrected_km_s":tied["corrected_target"],
                "U_tied_sd_km_s":np.sqrt(np.diag(tied["target_covariance"])).tolist(),
                "U_zero_p_corrected":tied["zero_nominal_p"],
                "U_chart_shift_km_s":tied["target_shift"],
                "W_rounding_box_support_km_s":free["rounding_box_target_support_km_s"],
                "U_rounding_box_support_km_s":tied["rounding_box_target_support_km_s"],
                "history_rank":s["history_geometry"]["target_rank"],
                "dipole_only_rank":s["history_geometry"]["dipole_only_target_rank"],
                "whole_free_rank":s["free_history"]["rank"],
                "free_adequacy_p_original":s["free_history"]["adequacy_p"],
                "free_adequacy_p_catalogue_chart":float(stats.chi2.sf(free["residual_chi2"],free["dof"])),
                "max_distance_body":s["tied_vs_bulk"]["max_distance_in_matter_radiation_body"],
                "max_power_body":s["tied_vs_bulk"]["oracle_power_alpha_0p1_max_body"],
                "max_power_300":s["tied_vs_bulk"]["oracle_power_alpha_0p1_max_300"],
                "free_W_body_delta_chi2_bound_original":s["physical_body"]["free_W_profile_max_abs_delta_chi2_from_zero_in_body_bound"],
                "free_W_body_delta_chi2_bound":corrected_ball_bound,
                "checks":s["checks"]})
    body=dict(d["variants"]["log"]["models"]["2"]["physical_body"])
    body.pop("free_W_profile_max_abs_delta_chi2_from_zero_in_body_bound")
    j2=[r for r in rows if r["J"]==2];j3=[r for r in rows if r["J"]==3]
    summary={"schema":"htt.r63.interpretation/1","sources":{"observed_sha256":hashlib.sha256(observed.read_bytes()).hexdigest(),"chart_sha256":hashlib.sha256(chart.read_bytes()).hexdigest()},
        "n_sources":d["source"]["groups"],"z_range":d["source"]["z_min_max"],"n_operators":7,"n_source_orders":2,
        "free_history_fits":14,"base_and_physical_fits":42,"J2_depth_calibration_fits":7,"chart_transported_fits":42,
        "W_p_J2_original":limits(r["W_zero_p_original"] for r in j2),"W_p_J3_original":limits(r["W_zero_p_original"] for r in j3),
        "W_p_J2_corrected":limits(r["W_zero_p_catalogue_chart"] for r in j2),"W_p_J3_corrected":limits(r["W_zero_p_catalogue_chart"] for r in j3),
        "W_sd_all_components_km_s":limits(s for r in rows for s in r["W_sd_km_s"]),
        "unphysical_tangent_estimate_count":int(sum(np.linalg.norm(r["W_tangent_estimate_km_s"])>299792.458 for r in rows)),
        "full_history_target_ranks":sorted(set(r["history_rank"] for r in rows)),
        "dipole_only_history_target_ranks":sorted(set(r["dipole_only_rank"] for r in rows)),
        "power_alpha":.1,"max_power_body":max(r["max_power_body"] for r in rows),"max_power_300":max(r["max_power_300"] for r in rows),
        "max_distance_body":max(r["max_distance_body"] for r in rows),"body":body,
        "max_U_chart_shift_norm_km_s":max(np.linalg.norm(r["U_chart_shift_km_s"]) for r in rows),
        "q_additive_fit_rms_km_s":q["q_diagnostic"]["additive_fit"]["residual"]["rms_km_s"],
        "q_fixed_log_vector_fit_rms_km_s":q["q_diagnostic"]["multiplicative_fit"]["residual"]["rms_km_s"],
        "max_affine_parity_error":max(r["affine_GLS_scaled_parity_error"] for r in q["models"].values()),
        "W_rounding_box_support_range_km_s":limits(s for r in rows for s in r["W_rounding_box_support_km_s"]),
        "U_rounding_box_support_range_km_s":limits(s for r in rows for s in r["U_rounding_box_support_km_s"]),
        "max_free_W_physical_ball_likelihood_delta_bound":max(r["free_W_body_delta_chi2_bound"] for r in rows),
        "max_free_W_physical_ball_likelihood_delta_bound_original":max(r["free_W_body_delta_chi2_bound_original"] for r in rows),
        "rows":rows,
        "decision":"No evidence for extra history in this fixed working law. The restricted compensated physical model and constant bulk are practically indistinguishable in the retained distance experiment. Full tensors identify a weak history direction after source/STF nuisance; they do not establish globality.",
        "not_established":["CF4 method-level distance deboost and grouping response","calibrated nonlinear physical remainder","a physically measured superluminal W","global-tilt detection or universal impossibility","independent CMB 3D anchor","adopted kSZ physical limit"],
        "publication_status":"NOT_READY_TO_SUBMIT"}
    (folder/"RESULTS/INTERPRETATION_SUMMARY.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    labels=[r["operator"].replace("log_","").replace("log","base") for r in j2]
    fig,axes=plt.subplots(1,2,figsize=(12.8,4.8),layout="constrained")
    x=np.arange(7)
    colors=["#244b78","#bb7131","#31785a"]
    for k,axis in enumerate("xyz"):
        axes[0].scatter(x+(k-1)*.16,[r["W_sd_km_s"][k] for r in j2],s=45,color=colors[k],label=f"J2, {axis} component")
    axes[0].axhline(body["W_bound_km_s"],color="#a33142",ls="--",lw=1.8,label="Declared matter/radiation speed body")
    axes[0].set_yscale("log");axes[0].set_ylim(.5,3e6)
    axes[0].set_ylabel(r"Tangent coefficient $W$: standard error / body radius [km s$^{-1}$]")
    axes[0].set_title("Algebraic rank does not imply physical sensitivity")
    axes[0].legend(fontsize=8,loc="center right")
    axes[0].grid(True,axis="y",alpha=.25)
    for dataset,label,marker,color in [(j2,"J2","o","#244b78"),(j3,"J3","s","#bb7131")]:
        axes[1].plot(x,[(r["max_power_body"]-.1)*1e7 for r in dataset],marker=marker,label=label,color=color)
    axes[1].set_ylabel(r"Oracle power ceiling minus size $0.1$ [$10^{-7}$]")
    axes[1].set_ylim(0,4.7);axes[1].set_title("Tied global history versus constant bulk")
    axes[1].legend(loc="lower right");axes[1].grid(True,axis="y",alpha=.25)
    for ax in axes:
        ax.set_xticks(x,labels,rotation=28,ha="right",fontsize=8)
        ax.set_xlabel("Correlated nuisance prescriptions; not independent samples")
    fig.suptitle("CF4: 35,970 groups, joint dipole/STF32, fixed Gaussian covariance",fontsize=13)
    for ext in ("png","pdf"):fig.savefig(folder/f"RESULTS/r63_history_sensitivity.{ext}",dpi=180)
    plt.close(fig)
    bins=q["q_diagnostic"]["depth_bins"]
    z=np.array([r["median_z_CMB"] for r in bins])
    fig,ax=plt.subplots(figsize=(8.3,4.8),layout="constrained")
    ax.plot(z,[r["additive_fit"]["vector"]["amplitude_km_s"] for r in bins],"o-",label=r"Fit to $V_{3k}-V_h$",color="#244b78")
    ax.plot(z,[r["multiplicative_fit"]["vector"]["amplitude_km_s"] for r in bins],"s-",label=r"Fit to $c\,\ln[(1+z_{3k})/(1+z_h)]$",color="#bb7131")
    ax.set_xlabel("Median published CMB-frame redshift in each diagnostic bin")
    ax.set_ylabel(r"Deterministic chart-dipole coefficient [km s$^{-1}$]")
    ax.set_title("Published CF4 frame correction: additive and logarithmic charts differ")
    ax.text(.02,.04,"Catalogue-operation fit; not an independent observer-velocity measurement.\nNo stochastic error bars or new catalogue selection.",transform=ax.transAxes,fontsize=9)
    ax.legend();ax.grid(alpha=.25);ax.set_ylim(334,378)
    for ext in ("png","pdf"):fig.savefig(folder/f"RESULTS/r63_published_frame_chart.{ext}",dpi=180)
    plt.close(fig)
    print(json.dumps({k:v for k,v in summary.items() if k not in ("rows","not_established","decision","sources")},indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("folder");run(parser.parse_args().folder)
