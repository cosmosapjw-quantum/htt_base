"""A separate Decimal polynomial/eigenframe reference for the root MV code.
Host-authored direct verification, not an independent human/agent review.
"""
from pathlib import Path
import sys,itertools,json,hashlib
from decimal import Decimal,localcontext
from fractions import Fraction as F
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
for p in (ROOT/'htt',ROOT/'htt/src',ROOT/'htt/htt'):sys.path.insert(0,str(p))
from obsstat.r8_multipole_vectors import mv_to_tensor,tensor_to_mv

def ref(A,v,l,trace_denominator=None):
    with localcontext() as ctx:
        ctx.prec=100
        D=Decimal.from_float;v=[[D(float(x)) for x in row] for row in v];A=D(float(A))
        dot=lambda a,b:sum(x*y for x,y in zip(a,b))
        out=np.empty((3,)*l)
        for ix in itertools.product(range(3),repeat=l):
            i,j=ix[:2]
            if l==2:
                val=(v[0][i]*v[1][j]+v[1][i]*v[0][j])/2
                if i==j:val-=dot(v[0],v[1])/Decimal(trace_denominator or 3)
            else:
                k=ix[2]
                val=sum(v[p[0]][i]*v[p[1]][j]*v[p[2]][k] for p in itertools.permutations(range(3)))/6
                b=lambda a:(dot(v[0],v[1])*v[2][a]+dot(v[0],v[2])*v[1][a]+dot(v[1],v[2])*v[0][a])/3
                val-=(int(i==j)*b(k)+int(i==k)*b(j)+int(j==k)*b(i))/Decimal(trace_denominator or 5)
            out[ix]=float(A*val)
        return out

def matched(a,b):
    return max(min(abs(np.dot(x,y)) for x,y in zip(a,b[list(p)])) for p in itertools.permutations(range(len(a))))

rng=np.random.default_rng(84004);checks=0;max_stf=0.;max_eigen=0.;max_error=0.
for l in (2,3):
    for _ in range(100):
        v=rng.normal(size=(l,3));v/=np.linalg.norm(v,axis=1)[:,None];A=float(rng.uniform(-3,3))*1e-5
        t=mv_to_tensor(A,v,l);reference=ref(A,v,l)
        residual=float(np.max(abs(t-reference)))
        assert residual<=2e-15*max(abs(A),1e-30)
        max_stf=max(max_stf,residual)
        c=tensor_to_mv(t,l);assert c.reconstruction_enclosure is not None,c.status
        rec=mv_to_tensor(c.amplitude,c.vectors,l)
        sq=sum((F(float(x))-F(float(y)))**2 for x,y in zip(t.flat,rec.flat))
        assert c.reconstruction_enclosure.lo**2<=sq<=c.reconstruction_enclosure.hi**2
        max_error=max(max_error,float(c.reconstruction_enclosure.hi))
        # Distinct eigenframe construction for l2, independent of polynomial roots.
        if l==2:
            vals,e=np.linalg.eigh(t);amp=float(vals[2]-vals[0]);cosine=float(-3*vals[1]/amp)
            assert -1-1e-14<=cosine<=1+1e-14
            u=np.sqrt((1+cosine)/2)*e[:,2]+np.sqrt((1-cosine)/2)*e[:,0]
            w=np.sqrt((1+cosine)/2)*e[:,2]-np.sqrt((1-cosine)/2)*e[:,0]
            eig=ref(amp,[u,w],2);err=float(np.max(abs(eig-t)))
            assert err<1e-18 and matched(c.vectors,np.array([u,w]))>1-1e-10
            max_eigen=max(max_eigen,err)
        # A dropped amplitude and an incorrect STF coefficient must be caught.
        assert np.linalg.norm(ref(1.,v,l)-t)>1e-2
        assert np.linalg.norm(ref(A,v,l,7)-reference)>1e-12
        checks+=1

# Inspect every actual saved row and full distance/score transport, using exact
# Fraction differences rather than the producer's floating residuals.
base=ROOT/'docs/generated/tensor_joint_r8/representations/execution_after_symmetry'
outputs={}
for name in ('mock2','observed_components'):
    d=json.loads((base/(name+'.json')).read_text())
    with np.load(base/(name+'_rows.npz'),allow_pickle=False) as a:
        assert d['M']==len(a['sample_ids'])==len(set(a['sample_ids']))
        row_errors=[]
        for i,r in enumerate(d['rows']):
            sq=F(0)
            for label,rank in [('Q',2),('O',3)]:
                diff=sum((F(float(x))-F(float(y)))**2 for x,y in zip(a[label][i].flat,a['reconstructed_'+label][i].flat))
                rec=r['conversion'][rank-2]['reconstruction_norm_K']
                if rec is None:assert diff==0
                else:
                    b=F(rec['hi']['numerator'],rec['hi']['denominator']);assert diff<=b*b
                sq+=diff*10**10
            row_errors.append(sq)
        bounds=a['mv_error_expanded_pair_bounds'];original=a['tensor_pair_bounds']
        assert np.array_equal(bounds,bounds.swapaxes(0,1)) and np.isfinite(bounds).all()
        assert np.all(np.maximum(bounds[...,0],original[...,0])<=np.minimum(bounds[...,1],original[...,1]))
        # The pair expansion radius e must bound sqrt(e_i^2)+sqrt(e_j^2).
        for i in range(d['M']):
            for j in range(i):
                e=F(float(bounds[i,j,1]))-F(float(a['mv_pair_bounds'][i,j,1]))
                x,y=row_errors[i],row_errors[j]
                assert e>=0 and e*e>=x+y and (e*e-x-y)**2>=4*x*y
        for i,s in enumerate(d['scores']):
            keep=np.arange(d['M'])!=i
            orig=np.sort(original[i,keep],axis=0)[d['k']-1]
            expanded=np.sort(bounds[i,keep],axis=0)[d['k']-1]
            assert np.array_equal(orig,s['tensor_score']) and np.array_equal(expanded,s['mv_error_expanded_score'])
        assert sum(a['full_mv_available'])==d['converted_rows']
        outputs[name]={'rows':d['M'],'pairs':d['pair_checks'],'all_saved_bounds_verified':True}
result={'status':'PASS','verification_role':'HOST_DIRECT_DISTINCT_ALGORITHM_CHECK','seed':84004,'random_cases':checks,
        'mutation_controls':['dropped amplitude','wrong trace denominator'], 'max_decimal_stf_difference_K':max_stf,
        'max_eigenframe_difference_K':max_eigen,'max_conversion_error_bound_K':max_error,'saved_outputs':outputs,
        'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'htt/obsstat/r8_multipole_vectors.py',ROOT/'scripts/observed_runs/run_r8_representation_controls.py',Path(__file__)]},
        'independence':'Host authored after prior axis results; not a blind independent reviewer'}
print(json.dumps(result,indent=2))
