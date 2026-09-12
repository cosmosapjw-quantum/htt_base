#!/usr/bin/env python3
"""Read selected releases, execute usable compressed scenarios, retain refusals."""
from pathlib import Path
from fractions import Fraction as F
import hashlib
import json
import tarfile
import sys
import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from scipy.stats import beta, binom
ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/'htt',ROOT/'htt/src',ROOT/'htt/htt'):sys.path.insert(0,str(p))
from scripts.observed_runs.r8_mocks import write


def decode_union3(matrix):
    """Published README convention: row zero z, column zero mu, rest precision."""
    m=np.asarray(matrix,float)
    if m.ndim!=2 or m.shape[0]!=m.shape[1] or len(m)<3 or not np.isfinite(m).all():raise ValueError('finite square Union3 matrix required')
    z=m[0,1:].copy();mu=m[1:,0].copy();precision=m[1:,1:].copy()
    if np.any(z<=0) or np.any(z>=3) or np.any(np.diff(z)<=0):raise ValueError('Union3 released redshift domain/layout failed')
    # The released inverse matrix has ~4e-11 antisymmetry from numerical
    # inversion. r.T P r equals r.T sym(P) r identically; preserve this
    # quadratic rather than treating byte-level symmetry as physical failure.
    precision=(precision+precision.T)/2
    np.linalg.cholesky(precision)
    return z,mu,precision


def flat_distance_modulus(z,omega):
    if not 0<omega<1:raise ValueError('flat LCDM matter density in (0,1) required')
    return np.array([5*np.log10((1+x)*quad(lambda v:1/np.sqrt(omega*(1+v)**3+1-omega),0,x,epsabs=1e-11)[0]) for x in z])


def profile_offset(mu,model,precision):
    one=np.ones(len(mu));r=np.asarray(mu)-np.asarray(model);den=one@precision@one
    if den<=0:raise ValueError('offset information nonpositive')
    offset=float(one@precision@r/den);res=r-offset
    return offset,float(res@precision@res)


def union3_scenario(path):
    from astropy.io import fits
    with fits.open(path,memmap=False) as hdus:matrix=np.array(hdus[0].data)
    z,mu,precision=decode_union3(matrix)
    objective=lambda omega:profile_offset(mu,flat_distance_modulus(z,omega),precision)[1]
    fit=minimize_scalar(objective,bounds=(.01,.99),method='bounded',options={'xatol':1e-11})
    if not fit.success:raise RuntimeError(fit.message)
    model=flat_distance_modulus(z,fit.x);offset,chi2=profile_offset(mu,model,precision)
    grid=np.linspace(.1,.6,101);chi=[objective(v) for v in grid]
    return dict(outcome='RELEASE_COMPRESSED_GAUSSIAN_SCENARIO',nodes=len(z),redshift=z,
                modulus=mu,precision_antisymmetry_max=float(np.max(abs(matrix[1:,1:]-matrix[1:,1:].T))),precision_eigenvalue_range=np.linalg.eigvalsh(precision)[[0,-1]],
                omega_m=float(fit.x),profile_offset_mag=offset,chi2=chi2,
                fitted_modulus=model+offset,residual_mag=mu-model-offset,
                omega_grid=grid,profile_chi2=chi,
                conditional_error_budget='NONE: no exact sampling-law admission',
                limitations=['Public UNITY1.5 compression; finite-sample Gaussian observation law is not established',
                             'Flat LCDM + free common offset; search bounds (0.01,0.99) are numerical domain, not prior',
                             'Released z domain 0<z<3; precision symmetric part used, preserving its quadratic form',
                             'No angular information, no R3 anisotropic distance likelihood, no product independence claim'])


def inspect_products(data_root):
    from astropy.io import fits
    data_root=Path(data_root);out={}
    def run(name,fn):
        try:out[name]=fn()
        except Exception as e:out[name]={'outcome':'INPUT_UNAVAILABLE','reason':type(e).__name__+': '+str(e)}
    def cf4():
        p=data_root/'raw/cf4_full';readme=(p/'ReadMe').read_text()
        rows=sum(bool(s.strip()) for s in (p/'table3.dat').read_text().splitlines())
        return {'outcome':'DESCRIPTIVE_ONLY','rows':rows,'source':'J/ApJ/944/94',
                'readme_sha256':hashlib.sha256(readme.encode()).hexdigest(),
                'law_missing':['group-order full covariance','conditioned distance/velocity sampling and selection law'],
                'declared_release_files':[x.name for x in sorted(p.iterdir()) if x.is_file()]}
    def jwst():
        p=data_root/'raw/jwst_anchors';manifest=json.loads((p/'jwst_anchors_manifest.json').read_text());sets=[]
        for r in manifest['transcription_receipts']:
            if not r['exact_cells'] or 'host' not in r['exact_cells'][0]:continue
            src=next(s for s in manifest['fetched'] if s['label']==r['source_label'])
            with tarfile.open(p/src['path']) as t:raw=t.extractfile(r['source_member']).read()
            if 'sha256:'+hashlib.sha256(raw).hexdigest()!=r['source_member_sha256']:raise ValueError('JWST immutable member changed')
            delta=np.array([float(x['mu_a_mag'])-float(x['mu_b_mag']) for x in r['exact_cells']])
            sets.append({'dataset':r['dataset'],'host_count':len(delta),'mean_difference_mag':float(delta.mean()),
                         'rms_difference_mag':float(np.sqrt(np.mean(delta**2))),'source_arxiv':r['source_arxiv'],
                         'source_member_sha256':r['source_member_sha256']})
        return {'outcome':'DESCRIPTIVE_ONLY','datasets':sets,'law_missing':['shared host/calibration covariance',
            'validated marginal sampling law; quoted errors alone do not establish it'],
            'geometry':'same-host shared distance cancels; method comparison is not a tilt measurement'}
    def desi():
        p=data_root/'raw/desi_dr1_mocks/observed/v1.5/BGS_BRIGHT-21.5_NGC_clustering.dat.fits'
        with fits.open(p,memmap=True) as h:columns=h[1].columns.names;rows=len(h[1].data)
        return {'outcome':'RAW_CATALOGUE_CONTROL_ONLY','rows':rows,'columns':columns,
                'law_missing':['bound apparent/absolute magnitude P-sample selection','matched random normalization and covariance'],
                'PR151_numerical_reuse':False}
    run('cf4_full',cf4);run('jwst_anchors',jwst)
    run('union3',lambda:union3_scenario(data_root/'rrss_observational_inputs/union3_release-main/mu_mat_union3_cosmo=2_mu.fits'))
    run('desi_raw',desi)
    return out


def mixture_diagnosis(frozen):
    data=json.loads(Path(frozen).read_text());row=next(r for r in data['cells'] if r['law']=='mixture' and r['mu']==-1)
    n=row['trials'];k=row['rejections'];upper=float(beta.ppf(1-row['failure_budget'],k+1,n-k))
    assert abs(upper-row['binomial_upper'])<1e-14
    return {'fixed_failure':row,'recomputed_upper':upper,'null_tail_probability':float(binom.sf(k-1,n,.05)),
            'analytic_size':str(F(10,200)),
            'argument':'All 200 absolute residuals are iid continuous under each specified location law; the observed descending rank is uniform on 1..200. Reject ranks 1..10.',
            'implementation_inspection':'Mixture sampler uses independent standard normal and Bernoulli variance selector; scales 1 and 3 give variances 1 and 9. No changed seed or rerun.',
            'status':'ADAPTER_HELD_BY_FROZEN_DIAGNOSTIC',
            'inference':'The 64/1000 count is possible under nominal size. This does not prove absence of all defects or override the frozen upper-bound gate.'}

if __name__=='__main__':
    from scripts.observed_runs.run_tensor_joint_r7 import DATA
    out=ROOT/'docs/generated/tensor_joint_r8/law_followup';out.mkdir(parents=True,exist_ok=True)
    write(out/'products.json',{'owner':'HTT','scope':'RELEASE_INTAKE_AND_SCENARIO_ONLY','products':inspect_products(DATA),
        'source_hashes':{str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}})
    write(out/'mixture_diagnosis.json',mixture_diagnosis(ROOT/'docs/generated/tensor_joint_r8/ac/mocks/mock5.json'))
