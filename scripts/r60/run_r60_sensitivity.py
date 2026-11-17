#!/usr/bin/env python3
"""Reanalyse the owned R58 CF4 tensor carrier under explicit sensitivity laws.

The covariance amplitude is a conditional sensitivity coordinate, not a
measured cosmological growth parameter. The calibration body is a deterministic
full-sky RMS budget, not an inferred prior or a survey-estimated covariance.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy import optimize, stats

SOURCE_DIR = 'docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117'
BASELINE = '6fe19c5139004a1f281ec85c592e5ab4c7590d5f'
G_MAG = 5.0 / np.log(10.0)
B8 = np.diag([3.0]*3+[7.5]*5)
B5 = 7.5*np.eye(5)
B3 = 3.0*np.eye(3)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [clean(v) for v in x]
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,(np.bool_,)):return bool(x)
    if isinstance(x,(np.integer,)):return int(x)
    if isinstance(x,(float,np.floating)):
        return float(x) if np.isfinite(x) else ('inf' if x>0 else '-inf')
    return x


def run(root, output):
    root,output=Path(root).resolve(),Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('refusing to overwrite an existing result directory')
    output.mkdir(parents=True,exist_ok=True)
    sys.path[:0]=[str(root/'htt'),str(root/'htt/src')]
    from htt.htt.infer.r58_mixed_tensor_likelihood import fit_linear
    from htt.htt.infer.r60_covariance_calibration import (
        block_wald,calibration_breakdown,calibrated_support,
        fixed_mean_amplitude,residual_contrast_amplitude,
    )
    source=root/SOURCE_DIR/'RESULTS/OWNED_TENSOR_CARRIERS.npz'
    reference=root/SOURCE_DIR/'RESULTS/OWNED_TENSOR_RESULT.json'
    old=json.loads(reference.read_text())
    if sha(source)!=old['carrier_sha256']:
        raise ValueError('R58 carrier no longer matches its published source identity')
    z=np.load(source,allow_pickle=False)
    rows=z['row_indices32'];scales=z['parameter_scale']
    names=sorted(k[:-5] for k in z.files if k.endswith('__y32'))
    models={}
    for name in names:
        models[name]=dict(y=z[name+'__y32'].copy(),x=z[name+'__response32x11'].copy(),
                         n=z[name+'__white36'][np.ix_(rows,rows)],
                         s=z[name+'__body36'][np.ix_(rows,rows)])
    targets={'all11':np.arange(11),'angular8':np.arange(3,11),
             'quadrupole5':np.arange(6,11),'dipole3':np.arange(3,6),
             'velocity3':np.arange(3)}
    def evaluate(name,a):
        m=models[name]
        return fit_linear(m['y'],m['n']+a*m['s'],m['x'],scales)
    def pvalues(f):
        return {key:block_wald(f,indices)['p'] for key,indices in targets.items()}
    grid=np.unique(np.r_[0.,np.linspace(.05,3.,60),np.geomspace(3.1,20.,21),1.])
    grid_rows=[]; fits_at_one={}
    for a in grid:
        for name in names:
            f=evaluate(name,float(a))
            pv=pvalues(f)
            grid_rows.append(dict(model=name,cosmic_variance_amplitude=float(a),
                                 **{'p_'+k:v for k,v in pv.items()},
                                 p_omnibus32=f['null_p'],p_residual21=f['adequacy_p'],
                                 residual_chi2=f['residual_chi2'],logdet=f['logdet_cov']))
            if abs(a-1.)<1e-14:fits_at_one[name]=f
    baseline={};parity={}; amplitudes={}
    # A residual-contrast amplitude fit has an amplitude-independent mean
    # annihilator. The global fixed-mean amplitude bound therefore applies.
    for name in names:
        f=fits_at_one[name];h=f['estimate'];c=f['covariance'];m=models[name]
        parity[name]=dict(estimate_max_abs=float(np.max(np.abs(h-z[name+'__estimate11']))),
                          covariance_relative_max=float(np.max(np.abs(c-z[name+'__cov11']))/
                                                        np.max(np.abs(z[name+'__cov11']))))
        baseline[name]=dict(tests={key:block_wald(f,v) for key,v in targets.items()},
            estimate11=h,covariance11=c,
            rms_angular_log_distance=float(np.sqrt(h[3:]@np.linalg.solve(B8,h[3:]))),
            calibration_breakdown={
                'angular8':calibration_breakdown(h[3:],c[3:,3:],B8),
                'quadrupole5':calibration_breakdown(h[6:],c[6:,6:],B5),
                'dipole3':calibration_breakdown(h[3:6],c[3:6,3:6],B3)},
            covariance_eigenvalue_checks={'noise_min':float(np.linalg.eigvalsh(m['n']).min()),
                                         'body_min':float(np.linalg.eigvalsh(m['s']).min())})
        print('amplitude fits:',name,flush=True)
        amplitudes[name]=dict(
            zero_mean=fixed_mean_amplitude(m['y'],m['n'],m['s']),
            residual_contrast=residual_contrast_amplitude(m['y'],m['n'],m['s'],m['x']))
    if max(v['estimate_max_abs'] for v in parity.values())>1e-7 or max(v['covariance_relative_max'] for v in parity.values())>1e-10:
        raise ValueError('unchanged lambda=1 R58 reference parity failed')
    curves=[]
    for a in [0.,.25,.5,.75,1.,1.25,1.5,2.,3.,5.]:
        for name in names:
            f=evaluate(name,a);h,c=f['estimate'],f['covariance']
            for key,ix,body in [('angular8',slice(3,11),B8),('quadrupole5',slice(6,11),B5),('dipole3',slice(3,6),B3)]:
                br=calibration_breakdown(h[ix],c[ix,ix],body)
                curves.append(dict(model=name,cosmic_variance_amplitude=a,target=key,
                                   critical_rms_log_distance=br['radius'],critical_rms_magnitude=G_MAG*br['radius'],
                                   distance2=br['distance2'],threshold=br['threshold'],witness=br['witness']))
    # Wald statistics are generally NOT monotone under PSD covariance growth.
    # Enumerate all sign changes on this declared grid, refine each crossing,
    # retain the grid and avoid claiming exhaustive roots between its nodes.
    crossings={}
    for target in targets:
        def envelope(a):
            return max(block_wald(evaluate(name,a),targets[target])['p'] for name in names)
        values=np.array([max(r['p_'+target] for r in grid_rows
                            if r['cosmic_variance_amplitude']==a) for a in grid])
        roots=[]
        for lo,hi,vl,vh in zip(grid[:-1],grid[1:],values[:-1]-.05,values[1:]-.05):
            if vl*vh<0:
                rt=optimize.brentq(lambda a:envelope(a)-.05,float(lo),float(hi),xtol=1e-10)
                vals={n:block_wald(evaluate(n,rt),targets[target])['p'] for n in names}
                roots.append(dict(amplitude=rt,bracket=[lo,hi],p_max=envelope(rt),
                                  attaining_model=max(vals,key=vals.get),per_model_p=vals))
        crossings[target]=dict(roots=roots,p_at_zero=values[0],p_at_one=envelope(1.),
            p_at_twenty=values[-1],nondecreasing_on_tested_grid=bool(np.all(np.diff(values)>=-1e-12)),
            scope='all sign changes found on the declared finite grid; no global monotonicity or exhaustive continuous-root claim')
    # F_support of the angular log-H response, in a single simultaneous set.
    # Explicit directions provide concrete functionals without axis selection.
    from htt.htt.infer.r54_distance_estimators import multipole_basis
    directions={'ICRS_x':np.array([1.,0.,0.]),'ICRS_y':np.array([0.,1.,0.]),'ICRS_z':np.array([0.,0.,1.])}
    support={}
    for label,n in directions.items():
        u=multipole_basis(n[None,:])[0,1:]
        support[label]={}
        for rho in [0.,.001,.005,.01]:
            per={name:calibrated_support(f['estimate'][3:],f['covariance'][3:,3:],B8,u,rho)
                 for name,f in fits_at_one.items()}
            support[label][str(rho)]=dict(lower=min(v['lower'] for v in per.values()),
                                         upper=max(v['upper'] for v in per.values()),
                                         budget_rms_magnitude=G_MAG*rho,per_model=per)
    # G_F-compatible residual tomography: fixed orthonormal contrasts remove
    # the declared constant mean response but retain the full window covariance.
    result=dict(schema='htt.r60.covariance_calibration/1',baseline=BASELINE,
        source_read_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        source={'carrier_path':str(source.relative_to(root)),'sha256':sha(source),
                'reference_path':str(reference.relative_to(root)),'reference_sha256':sha(reference),
                'n_groups':35970,'n_observed':32,'n_mean_parameters':11,'n_models':len(names)},
        conventions={'frame':'ICRS/J2000, sourceward n, input z_CMB fixed',
            'mean':'alpha=(V[km/s],dH[dimensionless],kappa_STF[dimensionless])',
            'covariance':'C_m(lambda)=N_m+lambda*S_m; lambda multiplies variance, not standard deviation',
            'physical_map':'dH=-A/(cH)+d_cal; kappa=sigma/H+q_cal; V=c*beta_MR under the inherited CONST_V response',
            'calibration_metric':'rho^2=|d_cal|^2/3+2||q_cal||_F^2/15 = full-sky mean square angular log-distance bias',
            'rms_magnitude_factor':G_MAG,'body_shape_B8':B8,
            'angular8_test':'dH=kappa=0 with V profiled; fixed-C chi-square_8',
            'calibration_test':'confidence-ellipsoid intersection, not a chi-square law for optimized distance',
            'calibration_guarantee':'if one included model, supplied covariance and stated deterministic budget are valid; post-hoc selection remains uncalibrated'},
        baseline_results=baseline,reference_parity=parity,covariance_grid=grid_rows,
        crossings_of_model_max_p_0_05=crossings,calibration_frontier=curves,
        amplitude_likelihoods=amplitudes,angular_logH_support=support,
        five_views={'x':'joint signed alpha and full covariance; physical pullback with calibration coordinates',
            'Q':'minimum sky-RMS calibration gauge over the simultaneous confidence ellipsoid',
            'Pi':'fixed-lambda, explicitly targeted chi-square tails and finite-model maximum',
            'F_support':'support of the confidence ellipsoid plus deterministic calibration body',
            'F_occupancy':'UNAVAILABLE: no specified physical occupancy measure/ceiling',
            'G_F':'cross-window residual contrasts; full transformed covariance; residual-contrast amplitude likelihood'},
        limitations=[
            'Conditional reanalysis of the existing selected CF4 experiment; no new catalogue or end-to-end survey mocks.',
            'The seven nuisance operators are correlated transforms of the same data; no model-odds comparison or probability multiplication.',
            'Cosmic-amplitude fits are not measurements of cosmological growth: they can absorb misspecification and unmodelled covariance.',
            'No p-value is obtained by substituting a fitted amplitude into the known-covariance chi-square law.',
            'Finite covariance-grid roots describe tested sensitivity, not a universal monotonicity theorem.',
            'The full-sky RMS calibration body is a declared deterministic sensitivity family, not measured survey calibration.',
            'Pointwise shear, acceleration and arbitrary tilt remain unbounded when their calibration or transfer is left unrestricted; omega has no distance column.',
            'Neither scalar nor tensor morphology identifies a Bianchi Lie algebra without additional geometry and transfer information.'],
        implementation={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
                        'runner_sha256':sha(__file__),
                        'module_sha256':sha(root/'htt/htt/htt/infer/r60_covariance_calibration.py'),
                        'amplitude_module_sha256':sha(root/'htt/src/common/covariance_amplitude.py')})
    (output/'SENSITIVITY_RESULT.json').write_text(json.dumps(clean(result),indent=2,allow_nan=False)+'\n')
    with (output/'COVARIANCE_SCAN.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(grid_rows[0]));writer.writeheader();writer.writerows(grid_rows)
    with (output/'CALIBRATION_FRONTIER.csv').open('w',newline='') as f:
        keys=[k for k in curves[0] if k!='witness'];writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        writer.writerows({k:r[k] for k in keys} for r in curves)
    plot(result,output)
    return result


def plot(result,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    rows=result['covariance_grid'];grid=sorted(set(r['cosmic_variance_amplitude'] for r in rows))
    fig,axs=plt.subplots(1,2,figsize=(11.5,4.3),layout='constrained')
    for target,label in [('all11','All 11 apparent coefficients'),('angular8','Dipole + STF; velocity free'),('quadrupole5','STF; other coefficients free')]:
        y=[max(r['p_'+target] for r in rows if r['cosmic_variance_amplitude']==a) for a in grid]
        axs[0].plot(grid,y,label=label)
    axs[0].axhline(.05,color='black',ls='--',lw=1);axs[0].axvline(1.,color='.6',ls=':',lw=1)
    axs[0].set(xlim=(0,3),ylim=(0,1),xlabel='Cosmic covariance variance multiplier',ylabel='Maximum p across seven nuisance models')
    axs[0].legend(fontsize=8);axs[0].set_title('Conditional sensitivity of distinct null hypotheses')
    curves=result['calibration_frontier']
    for target,label in [('angular8','Dipole + STF'),('quadrupole5','STF only')]:
        ag=sorted(set(r['cosmic_variance_amplitude'] for r in curves if r['target']==target))
        yy=[min(r['critical_rms_magnitude'] for r in curves if r['target']==target and r['cosmic_variance_amplitude']==a) for a in ag]
        axs[1].plot(ag,yy,marker='o',label=label)
    axs[1].set(xlim=(0,3),xlabel='Cosmic covariance variance multiplier',ylabel='Minimum full-sky RMS calibration (mag)')
    axs[1].legend(fontsize=8);axs[1].set_title('Budget making the 95% confidence union contain zero')
    fig.suptitle('Owned CF4 tensor carrier: fixed-law sensitivity, not discovery significance',fontsize=11)
    for ext in ['png','pdf']:fig.savefig(output/('COVARIANCE_CALIBRATION.'+ext),dpi=180)
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=run(args.root,args.output)
    print(json.dumps(clean({'model_max_p_at_lambda1':{k:v['p_at_one'] for k,v in result['crossings_of_model_max_p_0_05'].items()},
                           'crossings':{k:v['roots'] for k,v in result['crossings_of_model_max_p_0_05'].items()},
                           'amplitudes':{k:{m:q['amplitude'] for m,q in v.items()} for k,v in result['amplitude_likelihoods'].items()}}),indent=2))
