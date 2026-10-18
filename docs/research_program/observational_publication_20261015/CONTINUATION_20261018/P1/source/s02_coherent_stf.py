"""Source-conditioned coherent-STF nuisance cancellation for four CF4 windows.

This is a certified conservative lower *event* bound for a common additive
STF5 systematic on all windows, |delta|<=b, and per-window |deltaH|<=a.
The four source windows have one shared coordinate basis and one joint draw ID.
No physical shear/tilt/curvature posterior is constructed.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from s02_interval_coupled_original import original_source_draws, ratio_intervals, sharp_event_bounds


def lower_certificates(draws, threshold, stf_radius, mono_radius, *, transfer_gap=0.):
    d=np.asarray(draws,dtype=float)
    if d.ndim!=3 or d.shape[1:]!=(4,9) or not np.isfinite(d).all():raise ValueError('one 4x9 joint array per draw')
    if not np.isfinite(threshold) or threshold<=0:raise ValueError('positive threshold')
    H=d[:,:,0]
    a=np.asarray(mono_radius,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all() or (a<0).any() or (H<=a[None,:]).any():raise ValueError('finite positive denominator')
    b=float(stf_radius)
    if not np.isfinite(b) or b<0:raise ValueError('common STF error ball')
    eta=float(transfer_gap)
    if not np.isfinite(eta) or eta<0:raise ValueError('transfer gap must be nonnegative')
    # Physical model: delta_s_j=T_j delta, ||T_j|| <= 1, ||delta|| <= b,
    # ||T_i-T_j|| <= eta. Equality eta=0 is a perfectly coherent common
    # additive STF5 error. For eta>0 pairwise thresholds incur eta*b.
    s=d[:,:,4:9]
    lo,_=ratio_intervals(d,np.full(4,b),a)
    solo=(lo>threshold).any(axis=1)
    pair=[];events=[]
    for i in range(4):
        for j in range(i+1,4):
            delta=np.linalg.norm(s[:,i]-s[:,j],axis=1)
            # If both corrected ratios <=threshold, triangle inequality gives
            # ||s_i-s_j||<=threshold*(H_i+H_j+deltaH_i+deltaH_j).
            # Since deltaH_i+deltaH_j <=a_i+a_j, strict greater forces
            # at least one event, independent of b or the unknown common ds.
            forced=delta>threshold*(H[:,i]+H[:,j]+a[i]+a[j])+eta*b
            pair.append((i,j));events.append(forced)
    forced_by_difference=np.logical_or.reduce(events)
    all_forced=np.logical_or(solo,forced_by_difference)
    return {
     'n_joint_draws':len(d),'threshold':float(threshold),
     'monopole_bound_per_window':a.tolist(),'common_STF_radius':b,'max_interwindow_transfer_gap':eta,
     'rectangular_lower_count':int(solo.sum()),
     'coherent_pairwise_lower_count':int(all_forced.sum()),
     'pairwise_only_count':int((~solo&forced_by_difference).sum()),
     'rectangle_lower_mass':float(solo.mean()),
     'coherent_certified_lower_mass':float(all_forced.mean()),
     'fraction_of_draws_forced_from_some_pair_alone':float(forced_by_difference.mean()),
     'pair_ids':[list(x) for x in pair],
     'claim':'CONDITIONAL_CONSERVATIVE_LOWER_NOT_SHARP_FULL_SOCP',
     'nuisance_scope':'NORM_T_J_LE_ONE; NORM_T_I_MINUS_T_J_LE_TRANSFER_GAP; COMMON_DELTA_NORM_LE_B',
    }


def run(root, output):
    d=original_source_draws(Path(root))
    results={}
    for b in [0.5,1.,2.,3.,4.]:
      for threshold in [.015,.02,.025,.03,.05]:
        key=f'b_{b:g}_threshold_{threshold:g}'
        results[key]=lower_certificates(d,threshold,b,[.2]*4)
    transfer_sensitivity={}
    for eta in [0.,.1,.25,.5,1.]:
        key=f'b3_t0p02_transfer_gap_{eta:g}'
        transfer_sensitivity[key]=lower_certificates(d,.02,3.,[.2]*4,transfer_gap=eta)
    o={'schema':'htt.S02_true_source_draws_common_STF_nuisance_pair_certificate/2',
       'transfer_gap_sensitivity':transfer_sensitivity,
       'source_sha256':'f73fa930809731e69193ea3f0876efe73c499d1e1ca7af05221d3a004247a404',
       'joint_draw_ids':2048,'four_windows_not_independent':True,
       'physical_x_C_Q_F_G_F':'UNMEASURED; UNKNOWN_PHYSICAL_PROBABILITY_MASS_ONE',
       'external_radius_b':'HARD_ASSUMPTION_NOT_CALIBRATED',
       'results':results}
    dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
    return o

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--source',default='source');p.add_argument('--output',default='results/S02_COHERENT_STF_SOURCE_BOUNDS.json');a=p.parse_args();o=run(a.source,a.output)
 print(json.dumps(o['results']['b_3_threshold_0.02'],indent=2))
