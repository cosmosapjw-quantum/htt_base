"""Create-only published-source replay for six-paper P3/H01.

Source is an *immutable existing CF4 group NPZ*. No physical velocity-field,
selection likelihood, independent-window or Bianchi inference is constructed.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from hubble_window import (SOURCE_SHA, load_cf4, radial_weights,window_hubble,
                           dipole_bulk_principal_cosines,cross_window_covariance)

HERE=Path(__file__).resolve().parent
ARCHIVE_SOURCE=HERE.parent/'source/selected_source_observables.npz'
# Same path in the owner's existing worktree. Never modify this source.
LOCAL_SOURCE=(HERE.parents[4]/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz') if len(HERE.parents)>4 else Path('/UNAVAILABLE_OWNER_SOURCE')


def compute(source:Path) -> dict:
    x=load_cf4(source)
    windows=[];linear=[];sig=None
    for name,ang in [('source_window',0.),('north_weighted',.6)]:
        for center in (.025,.04,.06,.08):
            w,d,s=radial_weights(x,center,.012,ang_alpha=ang)
            h,m=window_hubble(d,x.n,x.z,w)
            windows.append({'model':name,'z_center':center,'H_W_km_s_Mpc':h,
                'effective_distance_Mpc':m['effective_distance_mpc'],
                'angular_moment':m['angular_moment'].tolist(),
                'bulk_inverse_Mpc':m['bulk_inverse_mpc'].tolist(),
                'dipole_bulk_principal_cosines':dipole_bulk_principal_cosines(d,x.n,w).tolist(),
                'method_denominator_fractions':{
                   method:float(np.sum((w*d*d)[x.method==method])/np.sum(w*d*d))
                   for method in np.unique(x.method)}})
            linear.append(m['alpha'])
            if sig is None:sig=s
    C,R=cross_window_covariance(linear,sig)
    return {'schema':'htt.sixpaper.P3_H01_published_source_replay/1',
      'source_sha256':SOURCE_SHA,'n_groups':len(x.z),
      'working_model':'cz and published DMzp; Gaussian z windows s=0.012; optional positive ICRS north weight; assumed independent 250 km/s + DM-propagated velocity errors',
      'windows':windows,'conditional_covariance':C.tolist(),'conditional_correlation':R.tolist(),
      'physical_expansion_or_covariant_shear_inferred':False,
      'real_survey_selection_and_method_covariance':'UNKNOWN'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=None)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    source=args.source or (ARCHIVE_SOURCE if ARCHIVE_SOURCE.is_file() else LOCAL_SOURCE)
    if args.output.exists():raise FileExistsError('create-only output required')
    result=compute(source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({'source_sha256':SOURCE_SHA,'n_groups':len(result['windows']),
                      'first_H_W':result['windows'][0]['H_W_km_s_Mpc']}))

if __name__=='__main__':main()
