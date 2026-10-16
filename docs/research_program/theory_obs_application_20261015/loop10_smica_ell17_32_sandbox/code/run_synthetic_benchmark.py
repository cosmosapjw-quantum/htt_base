"""Manufactured mask study, NOT the released Planck source selection."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
from finite_shell_stream import prepare_low_fit,response_shells,streaming_injection,combined_bounds


def fibonacci_mask(n):
    p=np.arange(n,dtype=float)+.5
    z=1.-2*p/n
    phi=(np.pi*(3.-np.sqrt(5.))*p)%(2*np.pi)
    r=np.sqrt(1-z*z)
    v=np.column_stack((r*np.cos(phi),r*np.sin(phi),z))
    return v,((z>-.8)&(v[:,0]<.75))


def run(n):
    nside,selected=fibonacci_mask(n)
    t=time.perf_counter()
    fit=prepare_low_fit(nside,selected)
    old,_=response_shells(fit,6,16)
    new,shells=response_shells(fit,17,32)
    injection=streaming_injection(fit,new,17,32,seed=8819)
    result=combined_bounds(old,new,retain=slice(4,36))
    global_bound=fit.condition*np.sqrt(800.)
    assert result['new_ell17_32_norm']<=global_bound*(1+1e-11)
    return {'manufactured_full_sky_points':n,
            'selected_points':int(selected.sum()),
            'condition_low':fit.condition,
            'old_ell6_16_operator_norm':result['old_ell6_16_norm'],
            'new_ell17_32_operator_norm':result['new_ell17_32_norm'],
            'combined_ell6_32_operator_norm':result['combined_ell6_32_norm'],
            'universal_conditional_bound':float(global_bound),
            'injection':injection,
            'elapsed_seconds':time.perf_counter()-t}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    opts=p.parse_args()
    if opts.output.exists():
        raise FileExistsError('no output overwrite')
    results={'schema':'htt.c8.manufactured_ell17_32/1',
             'status':'MANUFACTURED_GEOMETRY_ONLY_NOT_SOURCE_SMICA',
             'experimental_mask':'deterministic Fibonacci equal-area directions, z>-0.8 and x<0.75',
             'conditions':[run(n) for n in (255,401,801,1601)],
             'actual_ell17_32_source_operator':'NOT_COMPUTED',
             'physics_claim':'NONE'}
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'MANUFACTURED_SHELL_PASS','selected':[x['selected_points'] for x in results['conditions']],
                     'new_norms':[x['new_ell17_32_operator_norm'] for x in results['conditions']]}))
if __name__=='__main__':main()
