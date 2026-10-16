"""Bounded TEFF spectral-null and local optical-rank witnesses, not observed physics."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import null_space


def thermal_mixture_witness():
    y=np.array([0.7,1.0,1.4,2.0],dtype=float)
    A=np.stack((np.ones(4),y**3,y**4))
    v=null_space(A)[:,0]
    if v[-1]<0:v=-v
    w0=np.array([0.25,0.20,0.55,0.0]);w1=w0+0.45*v
    assert np.min(w1)>=0
    assert np.max(np.abs(A@w0-A@w1))<1e-12
    E=np.array([5.,10.,20.,30.,40.,60.])
    f0=np.exp(-E[:,None]/y[None,:])@w0
    f1=np.exp(-E[:,None]/y[None,:])@w1
    g=2*f0*f1/(f0+f1)
    sharp=np.abs(f1-f0)/(f0+f1)
    worst=np.maximum(np.abs(g/f0-1),np.abs(g/f1-1))
    assert np.allclose(sharp,worst,atol=1e-13,rtol=1e-12)
    return {'class':'MANUFACTURED_MB_MIXTURE_MOMENTS_M0_M3_M4',
            'support_T_over_Tstar':y.tolist(),
            'weights_without_hot_endpoint':w0.tolist(),
            'weights_with_hot_endpoint':w1.tolist(),
            'matched_moments':{str(p):[float(w0@y**p),float(w1@y**p)] for p in [0,3,4]},
            'unidentified_rate_moments':{str(p):[float(w0@y**p),float(w1@y**p)] for p in [5,6]},
            'energy_over_kBTstar':E.tolist(),'pointwise_sharp_minimax_relative_error':sharp.tolist(),
            'cold_spectrum':f0.tolist(),'hot_spectrum':f1.tolist(),
            'observable_claim':'MATHEMATICAL_ONLY_NO_ASTROPHYSICAL_SOURCE'}


def local_optical_rank(seed=190):
    rng=np.random.default_rng(seed)
    n=rng.normal(size=(320,3));n/=np.linalg.norm(n,axis=1,keepdims=True)
    Q=np.stack((n[:,0]**2-n[:,2]**2,n[:,1]**2-n[:,2]**2,
                 2*n[:,0]*n[:,1],2*n[:,0]*n[:,2],2*n[:,1]*n[:,2]),axis=1)
    F=np.column_stack((np.ones(len(n)),n,Q))
    radial=np.column_stack((np.ones(len(n)),Q))
    omega=np.array([[0,-.4,.7],[.4,0,-.8],[-.7,.8,0]])
    vort=np.einsum('ni,ij,nj->n',n,omega,n)
    group=rng.integers(0,4,len(n))
    Z=np.column_stack([(group==i).astype(float) for i in range(4)])
    Fg=np.column_stack((F,Z))
    ranks=(int(np.linalg.matrix_rank(F,tol=1e-10)),int(np.linalg.matrix_rank(radial,tol=1e-10)),int(np.linalg.matrix_rank(Fg,tol=1e-10)))
    assert ranks==(9,6,12),ranks
    assert max(abs(vort))<1e-15
    return {'class':'MANUFACTURED_LOCAL_OPTICAL_RANK','convention':'sourceward n; H(n)=theta/3 - A.n/c+sigma_ij n_i n_j',
            'ranks':{'optical_1_3_5':ranks[0],'radial_scalar_1_5':ranks[1],
                     'optical_plus_4_method_offsets':ranks[2],
                     'number_of_columns_with_offsets':Fg.shape[1]},
            'vorticity_null_absmax':float(max(abs(vort))),
            'observable_claim':'STRUCTURAL_ONLY_NOT_CF4_OPTICAL_TRANSFER'}



def fisher_response_gap():
    """Fixed-reference Fisher projection of E^2 onto {1,E} versus {1,E,E^2}."""
    from numpy.polynomial.legendre import leggauss
    nodes, weights=leggauss(96)
    lo,hi=0.2,10.0
    E=.5*(nodes+1)*(hi-lo)+lo
    w=.5*(hi-lo)*weights*E**2*np.exp(-E)
    target=E**2
    one=np.column_stack((np.ones(len(E)),E))
    enlarged=np.column_stack((one,target))
    def residual(F):
        sw=np.sqrt(w)
        coef=np.linalg.lstsq(sw[:,None]*F,sw*target,rcond=None)[0]
        return float(np.linalg.norm(sw*(target-F@coef)))
    before,after=residual(one),residual(enlarged)
    assert before>1.e-1 and after<1.e-11
    return {"class":"MANUFACTURED_FINITE_ENERGY_FISHER_PROJECTION",
            "energy_over_kBTstar_range":[lo,hi],"score_span_initial":["1","E"],
            "response_kernel":"E**2","unidentified_Fisher_residual":before,
            "residual_after_E2_added":after,"claim":"LOCAL_LINEAR_INFORMATION_ONLY"}

def run(out=None):
    report={'teff':thermal_mixture_witness(),'optical':local_optical_rank(),'fisher':fisher_response_gap()}
    if out is not None:Path(out).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report

if __name__=='__main__':
    p=Path(__file__).parent/'NUMERICAL_WITNESS.json'
    r=run(p)
    print('m0-m3-m4 exact residual',max(abs(v[0]-v[1]) for v in r['teff']['matched_moments'].values()))
    print('tail minimax relative errors E=40,60:',r['teff']['pointwise_sharp_minimax_relative_error'][-2:])
    print('optical ranks',r['optical']['ranks'])
