#!/usr/bin/env python3
"""Explicit ideal Gaussian pixel-model reference, NOT Commander end-to-end MC.

Use the previously archived Planck R3.01 TT theory, a 5-arcmin Gaussian beam,
exact native-averaged quadrupole columns and NSIDE128 pixel-centre l>=3 modes
with the HEALPix128 pixel window. The actual R66 linear estimators, native mask
counts and cross-operator covariance are retained. No foreground/noise/parameter
uncertainty or Commander transfer is claimed. Lref=256; controls 64 and128.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import time
import numpy as np
import healpy as hp

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/r66'))
import extract_r66_commander as ex
from htt.htt.infer import r66_radiation_quotient as rq
OUT=ex.OUT
THEORY=ex.RAW/'COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt'
THEORY_SHA='50eecd4422e22026070bdacf9fa8a7e7ef3badf4fa50fffea040df669715cf51'
N=4096
SEED=6620261117


def run():
    start=time.monotonic();assert ex.sha(THEORY)==THEORY_SHA
    mask=ex.mask2048();moments,count=ex.native_moments(4096,mask)
    n128=hp.nside2npix(128);weight=[];keys=[];native_response=[]
    for nside,lmax in ex.SPECS:
        key=f'n{nside}_l{lmax}';m,cn=ex.downgrade_moments(moments,count,nside)
        n=np.column_stack(hp.pix2vec(nside,np.arange(hp.nside2npix(nside)),nest=True))
        h,labels=rq.harmonic_design(n,lmax);h[:,1:9]=m
        e=rq.estimator(h,cn/((4096//nside)**2)>=.995,labels)
        padded=np.zeros((5,len(cn)));padded[:,e.retained]=e.matrix[4:9]
        f=(128//nside)**2
        w=np.repeat(padded/np.maximum(cn,1),f,axis=1)*count[None,:]
        weight.extend(w);keys.append(key)
        native_response.append(w@moments[:,3:])
    weight=np.array(weight);response=np.vstack(native_response)
    response_error=float(np.max(abs(response-np.tile(np.eye(5),(3,1)))))
    if response_error>1e-10:raise ValueError('native physical quadrupole response failed')
    ell=np.arange(257);cl=np.zeros(257);theory=np.loadtxt(THEORY)
    for row in theory:
        l=int(row[0])
        if l<=256:cl[l]=2*np.pi*row[1]/(l*(l+1))
    beam=hp.gauss_beam(np.deg2rad(5/60),lmax=256)
    pixel=hp.pixwin(128,lmax=256)
    cl[3:]*=beam[3:]**2*pixel[3:]**2
    cl[2]*=beam[2]**2  # exact native-average quadrupole; no duplicate pixel window
    area=hp.nside2pixarea(128)
    transformed=[]
    for k,w in enumerate(weight):
        ring=hp.reorder(w,n2r=True)
        transformed.append(hp.map2alm(ring/area,lmax=256,iter=0,pol=False))
    a=np.array(transformed);le,me=hp.Alm.getlm(256)
    covs={};spectra={}
    quad=15*cl[2]/(8*np.pi)*(response@response.T)
    for lmax in (64,128,256):
        valid=(le>=3)&(le<=lmax)
        factors=cl[le[valid]]*np.where(me[valid]==0,1.,2.)
        av=a[:,valid]
        cov=quad+(av*factors[None,:])@av.conj().T
        cov=np.real(cov);cov=(cov+cov.T)/2
        np.linalg.cholesky(cov)
        covs[str(lmax)]=cov
        spectra[str(lmax)]=np.linalg.eigvalsh(cov)
    cov=covs['256'];rng=np.random.default_rng(SEED)
    samples=rng.normal(size=(N,15))@np.linalg.cholesky(cov).T
    payload={'reference_ids':np.arange(N),'joint_covariance_uK2':cov}
    for i,key in enumerate(keys):payload[f'REF_{key}']=samples[:,i*5:(i+1)*5]
    np.savez_compressed(OUT/'ideal_gaussian_reference.npz',**payload)
    u=rq.quotient_basis(rq.DQ_UK)
    stability={}
    for key,c in covs.items():
        s=u.T@c[:5,:5]@u;s0=u.T@cov[:5,:5]@u
        stability[key]={'primary_quotient_trace_uK2':np.trace(s),
                        'trace_fraction_of_L256':np.trace(s)/np.trace(s0)}
    record={'schema':'htt.r66.ideal_gaussian_pixel_reference/1','status':'COMPLETE_IDEAL_REFERENCE',
        'source_code_sha256':ex.sha(Path(__file__)),'carrier_sha256':ex.sha(OUT/'ideal_gaussian_reference.npz'),
        'theory_path':str(THEORY),'theory_sha256':THEORY_SHA,'theory_columns':'L, Dl_TT, Dl_TE, Dl_EE, Dl_BB, PP',
        'TT_units':'Dl in microkelvin squared; Cl=2pi Dl/[l(l+1)]',
        'N':N,'seed':SEED,'training_ids':[0,2047],'heldout_ids':[2048,4095],
        'covariance_order':keys,'joint_covariance_uK2':cov,'covariance_controls':covs,
        'joint_covariance_eigenvalues':spectra,'band_reference_control':stability,
        'native_quadrupole_response_error':response_error,
        'statistical_model':'zero-mean isotropic Gaussian harmonic coefficients with fixed Planck TT spectrum',
        'quadrupole_model':'native-mask-averaged STF basis; covariance15 Cl2/(8pi), common physical sky across operators',
        'higher_ell_model':'3<=ell<=256 Gaussian pixel-centre sky at NSIDE128, 5arcmin Gaussian beam and HEALPix128 pixel window',
        'adjoint':'iter0 map2alm(weight/pixel_area) evaluates the finite equal-area harmonic sum; real-field m>0 factor2',
        'assumptions':['fixed fiducial spectrum','zero mean','no instrument noise','no foreground residual','no component-separation response',
                       'higher-ell native pixel averaging replaced by declared NSIDE128 pixel-centre/window model','no ell>256'],
        'processed_reference':'same finite R66 extraction weights; explicitly approximate sky-generating model',
        'Commander_end_to_end_MC':False,'physical_PTE_qualified':False,
        'same_sky_cross_covariance_retained':True,'realized_sky_measurement_error':False,
        'elapsed_seconds':time.monotonic()-start}
    ex.save_json(OUT/'IDEAL_REFERENCE.json',record)
    print(json.dumps(ex.plain({'status':record['status'],'N':N,'seconds':record['elapsed_seconds'],
        'response_error':response_error,'band_control':stability,'cov_eigenvalues':spectra}),indent=2),flush=True)

if __name__=='__main__':run()
