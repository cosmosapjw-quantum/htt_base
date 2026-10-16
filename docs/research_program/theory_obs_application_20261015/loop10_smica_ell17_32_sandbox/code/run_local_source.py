#!/usr/bin/env python3
"""Local-source exact NSIDE64 Planck SMICA ell17..32 geometry-only continuation.

This is intentionally not run in the ChatGPT sandbox, which does not hold the
raw official Planck 2048 masks or HTT K1 reduced cache. The owner's existing
htt_base checkout contains these hash-locked source inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PREVIOUS=ROOT/'docs/research_program/theory_obs_application_20261015/loop9_smica_finite_response'
SOURCE=PREVIOUS/'results/response_v1/baseline_response_matrices.npz'
SOURCE_JSON=PREVIOUS/'results/response_v1/result.json'
SOURCE_HASH='a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007'
SOURCE_JSON_HASH='85b82fac9e108280d1386bee0ba24cceb8e3e3d7a6a3bb4b4ca5559d285f9248'
from finite_shell_stream import prepare_low_fit,response_shells,streaming_injection,combined_bounds,real_harmonic_shell


def digest(path:Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):
            h.update(block)
    return h.hexdigest()


def execute(output:Path)->dict:
    if output.exists():
        raise FileExistsError('create-only output requested, refusing overwrite')
    if digest(SOURCE)!=SOURCE_HASH or digest(SOURCE_JSON)!=SOURCE_JSON_HASH:
        raise ValueError('PR536 source result identity changed')
    sys.path.insert(0,str(PREVIOUS))
    prior_file=PREVIOUS/'run.py'
    spec=importlib.util.spec_from_file_location('htt_c8_prior_mask_source',prior_file)
    if spec is None or spec.loader is None:
        raise ImportError('readable PR536 local runner required')
    prior=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    checks={}
    # Geometry-only: hash mask and K1 cache inputs. The 2 GB SMICA map
    # is not read by this independent geometry operator; its prior
    # checksum is preserved only as historical predecessor provenance.
    for path in (prior.COMMON,prior.HM,prior.OE,prior.CACHE):
        old=prior.EXPECTED[path]
        new=digest(path)
        if old!=new:
            raise ValueError(f'source mask/cache hash mismatch: {path}')
        checks[str(path)]=new
    fine,coverage,confidence=prior.selection()
    selected=(confidence>.5)&(coverage>=.995)
    if selected.shape!=(49152,) or int(selected.sum())!=26846:
        raise ValueError('fixed Loop5/PR536 mask selection has drifted')
    directions,orig_design=prior.pixel_fit_geometry()
    fit=prepare_low_fit(directions,selected)
    low=np.column_stack([real_harmonic_shell(fit.selected_directions,ell) for ell in range(6)])
    orig_err=float(np.max(abs(low-orig_design[selected,:36])))
    if orig_err>1e-12 or abs(fit.condition-3.6013785311890616)>1e-8:
        raise ValueError('PR536 source low harmonic design mismatch')
    with np.load(SOURCE,allow_pickle=False) as z:
        old=np.asarray(z['K_full_36x253'],float)
    old_new,old_shells=response_shells(fit,6,16)
    old_err=float(np.max(abs(old-old_new)))
    if old_err>1e-9:
        raise ValueError(f'PR536 published K6..16 cannot be reproduced: {old_err}')
    new,new_shells=response_shells(fit,17,32)
    inj=streaming_injection(fit,new,17,32)
    bound32=combined_bounds(old,new,retain=slice(4,36))
    bound12=combined_bounds(old,new,retain=slice(4,16))
    certificate=fit.condition*np.sqrt(800.)
    for bound in (bound12,bound32):
        if bound['new_ell17_32_norm']>certificate*(1+2e-12):
            raise AssertionError('addition theorem universal norm bound fails')
    payload={
        'schema':'htt.C8_SMICA_ELL17_32_ACTUAL_MASK_FINITE_TAIL/1',
        'science':'SOURCE_CONDITIONAL_FINITE_HARMONIC_GEOMETRY_ONLY',
        'source_pr536_head':'37db458319fd10e353a722345cb9a4ea6a39c698',
        'source_file_sha256':{str(SOURCE):SOURCE_HASH,str(SOURCE_JSON):SOURCE_JSON_HASH,**checks},
        'same_source_replay_old_6_16_max_abs_error':old_err,
        'harmonic_sign_and_order_max_abs_error':orig_err,
        'nside64_ring_pixels':49152,'source_selected_pixels':int(selected.sum()),
        'old_design_condition':fit.condition,
        'low_fit_identity_error':fit.identity_residual,
        'new_shell_ell_range':[17,32],'new_coefficient_count':800,
        'per_shell_ell17_32':new_shells,
        'ell2_3_operator':bound12,
        'ell2_5_operator':bound32,
        'new_universal_conservative_bound':float(certificate),
        'manufactured_source_geometry_injection':inj,
        'assumption':'same exact Loop5/PR536 source mask; unweighted simultaneous ell0..5 OLS; real Condon-Shortley orthonormal harmonics',
        'claims_withheld':['actual high-mode sky amplitude','ell>=33 remainder','beam/systematics/E2E covariance','physical covariant MES epsilon and derivatives','Bianchi geometry shear and tilt'],
        'raw_full_SMICA_temperature_not_used':'geometry-only projector; 2GB map validated previously in PR536, not rehashed here',
        'environment':{'python':sys.version.split()[0],
                       'numpy':np.__version__,
                       'openblas_threads':os.environ.get('OPENBLAS_NUM_THREADS','UNSET')}
    }
    output.mkdir(parents=True)
    np.savez_compressed(output/'ell17_32_mask_response.npz',
        K_full_36x800=new,K_ell23_12x800=new[4:16],K_ell2to5_32x800=new[4:36])
    (output/'result.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    return payload

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps({'status':'ACTUAL_SOURCE_FINITE_SHELL_ONLY',
                     'ell2_5_norm':execute(args.output)['ell2_5_operator']['new_ell17_32_norm']}))
