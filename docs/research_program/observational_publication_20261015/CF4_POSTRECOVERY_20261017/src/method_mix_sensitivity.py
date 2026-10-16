"""Sharp componentwise finite-method-composition weight-box bounds.

A declared *assumption* about method weight ratios, NOT estimated selection
or physical dipole. For N_m counts and mean feature f_m, the ratio
  T(w) = sum_m N_m w_m f_m / sum_m N_m w_m
is fractional affine and extrema on closed weight-box vertices.
"""
import itertools, json, argparse
from pathlib import Path
import numpy as np

def method_mixture_bound(count,mean, gamma=2.):
    count=np.asarray(count,float);mean=np.asarray(mean,float)
    if count.ndim!=1 or mean.ndim!=2 or len(count)!=len(mean) or len(count)<2 or (count<=0).any() or not np.isfinite(count).all() or not np.isfinite(mean).all() or not np.isfinite(gamma) or gamma<1:
        raise ValueError('positive method counts, finite feature means and gamma >=1 required')
    weights=np.asarray(list(itertools.product([1/gamma,gamma],repeat=len(count))),float)
    vals=((weights*count)@mean)/(weights@count)[:,None]
    return {'gamma':float(gamma),'lower':vals.min(axis=0).tolist(),'upper':vals.max(axis=0).tolist(),
            'max_corner_norm':float(np.linalg.norm(vals,axis=1).max()),
            'no_correction_mean':(count@mean/count.sum()).tolist(),
            'balanced_equal_method_mean':mean.mean(axis=0).tolist(),
            'vertices_checked':len(weights)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-result',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--gamma',type=float,default=2.);args=p.parse_args()
    src=json.loads(args.source_result.read_text());t=src['methods'];names=sorted(t)
    a=method_mixture_bound([t[k]['n_groups'] for k in names],[t[k]['sky_mean_n_J2000'] for k in names],args.gamma)
    a.update({'schema':'htt.CF4_35970_method_composition_sensitivity/1','source_sha256':src['source_npz_sha256'],
              'methods':names,'meaning':'ASSUMED_METHOD_WEIGHT_BOX_NOT_ACTUAL_SURVEY_SELECTION','H02':'HOLD'})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(a,indent=2,sort_keys=True)+'\n')
    print(json.dumps(a,sort_keys=True))
if __name__=='__main__':main()
