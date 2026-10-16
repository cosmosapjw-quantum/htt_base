#!/usr/bin/env python3
"""Deterministic scope-limited H02/L03/V03/K03/K04/B02/S04 manufactured diagnostics."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from htt_gate_precursors.selected_sources import (LatentNormal,SelectedMixture,SharedSelectedLatent,
                                                   gaussian_nuisance_projector)
from htt_gate_precursors.shared_sky import simulate_same_sky,matched_scan,heldout_rank_p_values
from htt_gate_precursors.kinematic_bridge import (history_matrix,frame_calibration_design,
                                                  sky_sample,source_matrix_rank)
from htt_gate_precursors.bianchi_i import (log_frequency_ratio,log_redshift_taylor2,
                                          collisionless_temperature)
from htt_gate_precursors.partial_selection import bounded_unknown_exceedance

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'
OUT.mkdir(exist_ok=True)

def main():
    mm=SelectedMixture((LatentNormal(.6,-1,.5),LatentNormal(.4,1.5,.5)),
                       'MANUFACTURED_PARENT_2COMP','MANUFACTURED_YPOS')
    sm=SharedSelectedLatent(mm)
    qs={str(n):sm.posterior_common_latent_after_N_admissions(n).tolist() for n in (1,2,3,4)}
    ys=np.array([.2,.3]);true=float(np.exp(sm.joint_log_density(ys)))
    wrong=float(sm.wrong_held_parent_joint_density(ys))
    M=simulate_same_sky(101,4,.25,seed=20261016)
    c=np.corrcoef(M,rowvar=False)
    stats=matched_scan(M,tuple('sim_sky_'+str(i) for i in range(len(M))))
    ps=heldout_rank_p_values(stats)
    astro_mean=float(np.mean(c[np.triu_indices(4,1)]))

    h=np.array([.5,.7,.9]);n=np.array([.2,.4,np.sqrt(.8)])
    tau=.2
    exact=float(log_frequency_ratio(h,tau,n))
    lin=float(np.sum(h*n*n)*tau)
    taylor=float(log_redshift_taylor2(h,tau,n))
    bic_res={"direction":n.tolist(),"H_i_inverse_t_unit":h.tolist(),
             "lookback_dimensionless_time":tau,"log1pz_exact":exact,"log1pz_first_order":lin,
             "log1pz_second_order":taylor,"finite_window_log1pz_div_tau":exact/tau,
             "local_H_n":lin/tau,"second_order_correction":taylor-lin}

    g=sky_sample(64,12);q=sky_sample(50,201)
    no_q=frame_calibration_design(g)
    with_q=frame_calibration_design(g,q)
    v0,s0=source_matrix_rank(no_q)
    v1,s1=source_matrix_rank(with_q)
    r2,_=source_matrix_rank(history_matrix(.2,.9))
    r3,_=source_matrix_rank(history_matrix(.2,.9,True))
    outer=bounded_unknown_exceedance(.3,.5,2)
    rec={"schema":"htt.sandbox.idle_gate_20261016/1","observational_input":"NONE",
         "scientific_claim":"MATHEMATICAL_AND_MANUFACTURED_ONLY",
         "H02":{"class_parent_weights":[.6,.4],"selected_class_weights_by_slot_count":qs,
                 "joint_selected_density_y02_y03":true,"incorrect_separately_selected_density":wrong,
                 "ratio_wrong_over_right":wrong/true,"proper_joint_selection_required":True},
         "L03":{"latent_independent_sky_count":101,"products_per_sky":4,
                 "mean_processing_correlation":astro_mean,"unique_rank_p_values":len(np.unique(ps)),
                 "min_heldout_rank_p":float(np.min(ps)),"empirical_exact_heldout_le_0_05":float(np.mean(ps<=.05))},
         "V03":{"history_two_window_rank":r2,"with_independent_local_anchor_rank":r3},
         "K03":{"galaxy_gradient_and_frame_cols":15,"rank_without_quasar":v0,
                 "rank_with_independent_quasar_frame_calibrator":v1,
                 "smallest_singular_with_quasar":float(np.min(s1))},
         "K04_B02":bic_res,
         "S04":{"known_tail":.3,"unknown_mass":.5,"assumed_selection_relative_event_odds_Gamma":2,
                 "outer_interval_after_selection":list(outer)}}
    (OUT/'MANUFACTURED_RESULTS.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')

    fig,ax=plt.subplots(figsize=(7.5,4.2))
    count=np.array(list(map(int,qs.keys())))
    w=np.array([qs[str(n)][0] for n in count])
    ax.plot(count,w,marker='o',label='P(latent low-mean | all N admitted)')
    ax.axhline(.6,linestyle='--',label='Parent probability (before selection)')
    ax.set_xticks(count)
    ax.set_xlabel('Number of source slots conditioned on inclusion, N')
    ax.set_ylabel('Probability of low-mean common latent')
    ax.set_title('H02 shared-latent selection reweighting: manufactured')
    ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'H02_SELECTION_COMMON_LATENT.png',dpi=160);plt.close(fig)

    theta=np.linspace(0,np.pi,240)
    sky=np.column_stack((np.sin(theta),np.zeros_like(theta),np.cos(theta)))
    fig,ax=plt.subplots(figsize=(7.5,4.2))
    ax.plot(np.rad2deg(theta),log_frequency_ratio(h,.2,sky)/.2,label=r'Finite-time $\log(1+z)/\tau$')
    ax.plot(np.rad2deg(theta),sky**2@h,label=r'Local $H(\hat n)=\sum H_i n_i^2$',linestyle='--')
    ax.set_xlabel('Sourceward angle from principal z-axis (deg)')
    ax.set_ylabel('Rate [1 / toy time unit]')
    ax.set_title('Bianchi I null-geodesic finite-time versus local response')
    ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'B02_K04_BIANCHI_I_FINITE_TIME.png',dpi=160);plt.close(fig)
    print(json.dumps({"H02_post_selected_prob_N2":qs['2'],
                      "H02_density_ratio_wrong_to_right":wrong/true,
                      "L03_min_sky_p":rec['L03']['min_heldout_rank_p'],
                      "K03_rank_without_quasar":v0,"K03_rank_with_quasar":v1,
                      "V03_two_window_rank":r2,"V03_with_anchor_rank":r3,
                      "K04_log1pz":exact,"S04_outer_gamma2":outer},indent=2))

if __name__=='__main__':main()
