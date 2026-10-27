"""Bounded independent review of saved R36-07 partial products.

No producer or all-native-pixel stream is called. Repository and candidate
files are read only. Each check returns raw numerical evidence, not admission.
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import time
import traceback

import numpy as np
import mpmath as mp
from astropy.io import fits
import healpy as hp
from scipy.linalg import block_diag
from scipy.spatial import cKDTree

OUT = Path(__file__).resolve().parent
ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE = ROOT/'docs/research_program/observational_publication_20261015'
PRODUCT = BASE/'OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-07-FOREGROUND-BUDGET'
EXT = Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_budget_actual')
CONTRACT = Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_contract_preparation/IMPLEMENTATION_CONTRACT.json')
BANDS = (30, 44, 70, 100, 143, 217, 353)
R32 = BASE/'PUBLICATION_ACCELERATION_20261025/products/R32-04-BANDPASS-BOUNDS/repair_05'
EXPECTED = '34ac36b0a774589c213d33943e4a4c25678d4e095e9b9f6062081118a2129cc9'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def identity_check():
    receipt = read(EXT/'RAW_RECEIPT.json')
    manifest = receipt['source_manifest']
    identity = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert identity == EXPECTED == receipt['candidate_identity']
    mismatches = []
    for item in manifest:
        p = Path(item['path'])
        if p.stat().st_size != item['bytes'] or digest(p) != item['sha256']:
            mismatches.append(str(p))
    assert not mismatches, mismatches
    assert digest(CONTRACT) == 'ca09bcbcba470c7712a34c69c793703181b99836f4cb51febdd7471435121089'
    contract = read(CONTRACT)
    for item in contract['inputs']:
        assert digest(item['path']) == item['sha256'], item['path']
    for p, item in read(PRODUCT/'RESULT.json')['source_bindings']['FIRAS_files'].items():
        assert digest(p) == item['sha256']
    return {'candidate_identity': identity, 'manifest_count': len(manifest),
            'contract_input_count': len(contract['inputs']), 'all_exact_small_inputs_and_candidate_members_match': True}

def geometry_check():
    actual = np.load(EXT/'ACTUAL_GEOMETRY.npz', allow_pickle=False)
    carrier = np.load('/mnt/extdrive/workdir/htt_open_data/r26_delivered_seven_frequency_numeric/FULL7_CARRIER.npz', allow_pickle=False)
    Y = actual['Y']
    assert np.array_equal(Y, carrier['frequency_canonical_7x24'])
    assert Y.shape == (7, 24)
    D = actual['D']
    branches = read(EXT/'BRANCH_SENSITIVITY.json')
    checks = []
    for br in branches:
        z = np.load(R32/'report/generated'/f"{br['branch']}_full24.npz", allow_pickle=False)
        F, a = z['F'], z['a']
        # Rectangular SVD, avoiding the producer's normal-matrix inverse.
        B = F / D
        u, singular, vt = np.linalg.svd(B, full_matrices=False)
        Binv = (vt.T / singular) @ u.T
        direction = Binv @ a
        ywhite = Binv @ Y
        ell2 = direction @ direction
        center = direction @ ywhite / ell2
        V = ywhite - np.outer(direction, center)
        J0 = np.sum(V*V)
        reconstructed = F @ (V/D[:, None]) + np.outer(a, center)
        rho = math.sqrt(J0)
        assert abs(rho-br['rho_min_algebraic_K_CMB']) < 1e-12
        assert abs(math.sqrt(ell2)-br['ell']) < 1e-9
        assert abs(np.linalg.norm(center[12:])-br['center_B_norm_K_CMB']) < 1e-12
        checks.append({'branch': br['branch'], 'rank': int((singular > 1e-12*singular[0]).sum()),
                       'condition_F_over_D': float(singular[0]/singular[-1]),
                       'rho_min_K_CMB_svd': rho, 'ell_svd': math.sqrt(ell2),
                       'center_B_norm_K_CMB_svd': float(np.linalg.norm(center[12:])),
                       'reconstruction_Frobenius_K_CMB_svd': float(np.linalg.norm(reconstructed-Y))})
    # Exact stored binary64 inputs interpreted at 70 decimal digits.
    mp.mp.dps = 70
    m = lambda x: mp.matrix(np.asarray(x).tolist())
    F, a = m(actual['F']), m(actual['a'])
    Dm = mp.diag([mp.mpf(float(x)) for x in D])
    Ym = m(Y)
    Cm = (F * Dm**-2 * F.T)**-1
    ell2 = (a.T * Cm * a)[0]
    sm = Ym.T*Cm*a/ell2
    resid = Ym-a*sm.T
    Vm = Dm**-1*F.T*Cm*resid
    J0 = sum(x*x for x in Vm)
    high_center = np.asarray(list(sm), float)
    g = read(EXT/'GEOMETRY.json')
    center_error = float(np.max(np.abs(high_center-actual['s0'])))
    assert center_error < 1e-12
    assert abs(float(J0)-g['J0_K_CMB_squared']) < 1e-16
    c, v, U0, s0 = (actual[k] for k in ('compensator_c','compensation_direction_v','U0','s0'))
    compensators=[]
    for amplitude in (0, 1e-6, 1e-5, 1e-4, 1):
        ss=s0+amplitude*v; UU=U0-amplitude*np.outer(c,v)
        residual=actual['F']@UU+np.outer(actual['a'],ss)-Y
        compensators.append({'amplitude_K_CMB':amplitude,'residual_K_CMB':float(np.linalg.norm(residual)),
                             'budget_K_CMB':float(np.linalg.norm(D[:,None]*UU))})
        assert np.linalg.norm(residual) < max(1e-12, amplitude*1e-9)
    assert abs(np.linalg.norm(v)-1)<1e-14 and np.all(v[:12]==0)
    # Arbitrary rotations in the retained real coordinate representation transport
    # both data and center, preserving the metric and the available radius.
    q,_=np.linalg.qr(np.random.default_rng(2707).normal(size=(24,24)))
    C=actual['C']; aa=actual['a']; ell2f=aa@C@aa
    rotated=(Y@q).T@C@aa/ell2f
    assert np.max(np.abs(rotated-q.T@s0))<1e-14
    for row in g['conditional_curves'][1:]:
        expected=math.sqrt((row['rho_K_CMB']**2-float(J0))/float(ell2))
        assert abs(expected-row['s_ball_radius_K_CMB'])<1e-12
    return {'branches': checks, 'high_precision_decimal_digits':70,
            'high_precision_ell':str(mp.sqrt(ell2)), 'high_precision_J0_K_CMB_squared':str(J0),
            'high_precision_rho_min_K_CMB':str(mp.sqrt(J0)),
            'max_center_absolute_error_K_CMB': center_error, 'compensators':compensators,
            'orthogonal_coordinate_transport': 'PASS'}

def load_candidate():
    spec=importlib.util.spec_from_file_location('r36_candidate',PRODUCT/'compute.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def spin_check():
    candidate=load_candidate()
    # Compare the analytic weights to libsharp/healpy rather than to the same
    # retained explicit spin function used by the producer's own test.
    nside=16
    ring=np.array([0,17,191,800,1500,2401,2900,3071])
    rng=np.random.default_rng(27)
    q=rng.normal(size=ring.size)*1e-6
    u=rng.normal(size=ring.size)*1e-6
    wq,wu=candidate.coordinate_weights(ring,nside,hp,candidate.load_spin_math())
    measured=wq@q+wu@u
    qmap=np.zeros(hp.nside2npix(nside));umap=qmap.copy()
    qmap[ring]=q;umap[ring]=u
    e,b=hp.map2alm_spin([qmap,umap],2,lmax=3)
    ref=[]
    for alm in (e,b):
        for ell in (2,3):
            ref.append(alm[hp.Alm.getidx(3,ell,0)].real)
            for m in range(1,ell+1):
                z=alm[hp.Alm.getidx(3,ell,m)]
                ref.extend([math.sqrt(2)*z.real,-math.sqrt(2)*z.imag])
    error=np.max(np.abs(measured-np.array(ref)))
    assert error < 1e-20, (error, measured, ref)
    return {'independent_library': 'healpy.map2alm_spin/libsharp', 'healpy_version':hp.__version__,
            'native_like_sparse_map_nside':nside,'tested_pixel_count':len(ring),
            'all_24_coordinates_max_error_K_CMB':float(error)}

def covariance_check():
    covs=[np.array([[2.,.3],[.3,1.]]),np.array([[.8,-.2],[-.2,3.]]),np.array([[1.,0.],[0.,0.]])]
    weights=[np.array([.4,-.6]),np.array([-.2,.7]),np.array([.8,-2.])]
    sig=np.array([math.sqrt(w@S@w) for w,S in zip(weights,covs)])
    common=np.concatenate([S@w/s for S,w,s in zip(covs,weights,sig)])
    residuals=[S-np.outer(S@w,S@w)/(s*s) for S,w,s in zip(covs,weights,sig)]
    full=block_diag(*residuals)+np.outer(common,common)
    ell=np.concatenate(weights)
    minimum=float(np.linalg.eigvalsh(full).min())
    attained=float(ell@full@ell)
    assert minimum>-1e-13
    for i,S in enumerate(covs): assert np.allclose(full[2*i:2*i+2,2*i:2*i+2],S,rtol=0,atol=1e-15)
    assert abs(attained-sig.sum()**2)<1e-13
    n=read(EXT/'NOISE.json')
    perband=np.array([n['per_band_sigma_worst_coordinate_K_CMB'][str(b)] for b in BANDS])
    z=np.load(EXT/'ACTUAL_GEOMETRY.npz',allow_pickle=False)
    F=z['F'];D=z['D'];a=z['a']
    G=np.linalg.pinv(F/D)
    direction=G@a
    h=G.T@direction/(direction@direction)
    sigma=(np.abs(h[:,None])*perband).sum(axis=0)
    assert np.max(np.abs(sigma-n['center_24_sigma_worst_coordinate_K_CMB']))<1e-12
    raw_sum=float(np.sum(perband*perband));center_sum=float(sigma@sigma)
    for alpha in (.1,.05,.01):
        assert abs(math.sqrt(raw_sum/alpha)-n['actual_Y_168_simultaneous_Euclidean_Chebyshev_radii_K_CMB'][str(alpha)])<1e-12
        assert abs(math.sqrt(center_sum/alpha)-n['center_24_simultaneous_Euclidean_Chebyshev_radii_K_CMB'][str(alpha)])<1e-10
    return {'full_6x6_PSD_completion_min_eigenvalue':minimum,
            'full_block_completion_variance':attained,'sharp_variance_formula':float(sig.sum()**2),
            'released_per_band_entries_checked':int(perband.size),
            'raw_168_trace_upper_K_CMB_squared':raw_sum,'center_24_trace_upper_K_CMB_squared':center_sum,
            'center_95pct_Euclidean_radius_K_CMB':math.sqrt(center_sum/.05),
            'center_weights_SVD':h.tolist(),
            'meaning':'Each coordinate maximum may use a different completion; their summed variances remain a valid uniform trace upper bound, not a joint covariance.'}

def native_samples_check():
    frozen=read('/mnt/extdrive/workdir/htt_open_data/r26_streamed_spin2_numeric/FROZEN_INPUT.json')['products']
    S7=np.load('/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/run/COMMON_SUPPORT_S7.npz',allow_pickle=False)
    mask=S7['s7_mask_nest64'].astype(bool)
    ring=S7['retained_ring64']
    assert np.array_equal(np.sort(hp.nest2ring(64,np.flatnonzero(mask))),np.sort(ring))
    parents=np.flatnonzero(mask)[[0,len(ring)//2,len(ring)-1]]
    rows=[]
    for band in BANDS:
        meta=frozen[str(band)];path=Path(meta['path']);nside=meta['nside'];child=(nside//64)**2
        idx=np.concatenate([p*child+np.array([0,child//2,child-1]) for p in parents])
        with fits.open(path,memmap=True) as f:
            hd=f[1].header
            assert hd['NSIDE']==nside and hd['ORDERING']=='NESTED' and hd[meta['pol_keyword']]=='COSMO'
            assert f[1].columns['QQ_COV'].unit in ('K_CMB^2','(K_CMB)^2')
            data=f[1].data[idx]
            qq,qu,uu=(data[k].astype(float) for k in ('QQ_COV','QU_COV','UU_COV'))
            blocks=np.array([[qq,qu],[qu,uu]]).transpose(2,0,1)
            eig=np.linalg.eigvalsh(blocks)
            assert np.isfinite(blocks).all() and eig.min()>0
            assert np.all(data['Q_STOKES']!=np.array(hd['BAD_DATA'],dtype=data['Q_STOKES'].dtype))
            assert np.all(data['U_STOKES']!=np.array(hd['BAD_DATA'],dtype=data['U_STOKES'].dtype))
            rows.append({'band':band,'sample_native_nest_indices':idx.tolist(),'sample_cov_min_eigen_K_CMB_squared':float(eig.min()),
                         'actual_bytes':path.stat().st_size,'expected_bytes':meta['size_bytes'],
                         'units':{k:f[1].columns[k].unit for k in ('Q_STOKES','U_STOKES','QQ_COV','QU_COV','UU_COV')},
                         'sample_QU_nonzero':bool(np.any(qu!=0))})
    recorded=read(EXT/'NOISE.json')['receipts']
    count=sum(r['selected_native_pixels'] for r in recorded.values())
    assert count==146022144
    return {'original_S7_mask_and_ring_set_match':True,'native_sample_count':63,'rows':rows,
            'recorded_full_stream_rows':count,'full_stream_repeated':False,
            'large_file_hashes':'Inherited frozen terminal identities; not rehashed in this bounded review.'}

def firas_check():
    source=EXT/'source'
    with fits.open(source/'FIRAS_DESTRIPED_SKY_SPECTRA_LOWF.FITS') as f:
        header=f[0].header;nf=header['NUM_FREQ'];tab=f[1].data
        lon,lat=tab['GAL_LON'].astype(float),tab['GAL_LAT'].astype(float)
        spectra=tab['SPECTRUM'].astype(float)
        frequencies=header['NU_ZERO']+header['DELTA_NU']*np.arange(nf)
        assert f[1].columns['SPECTRUM'].unit=='MJy/sr'
    with fits.open(source/'FIRAS_C_VECTOR_LOWF.FITS') as f: c=f[1].data['C_VECTOR'][0][:nf].astype(float)
    with fits.open(source/'FIRAS_COVARIANCE_MATRIX_LOWF.FITS') as f: cov=f[1].data['ROW_COVR'][:,:nf].astype(float)
    sr=np.column_stack((np.cos(np.deg2rad(lat))*np.cos(np.deg2rad(lon)),np.cos(np.deg2rad(lat))*np.sin(np.deg2rad(lon)),np.sin(np.deg2rad(lat))))
    s7=np.load('/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/run/COMMON_SUPPORT_S7.npz',allow_pickle=False)['retained_ring64']
    tx=np.array(hp.pix2vec(64,s7)).T
    ds,ix=cKDTree(sr).query(tx)
    angles=np.rad2deg(np.arccos(np.clip(np.einsum('ij,ij->i',tx,sr[ix]),-1,1)))
    stored=read(EXT/'FIRAS_FEASIBILITY.json')
    count=int(np.sum(spectra[:,:nf]<0));gt=int(np.sum(angles>3.5))
    relation=float(np.max(np.abs(np.diag(cov)-c*c)/(c*c)))
    assert nf==43 and spectra.shape==(6067,182) and np.all(spectra[:,43:]==0)
    assert count==621 and gt==31 and abs(angles.max()-stored['nearest_FIRAS_centre_angle_deg_quantiles'][-1])<1e-9
    assert abs(relation-3.815836032363304e-5)<1e-14
    return {'rows':len(sr),'valid_frequency_count':nf,'padding_columns':139,
            'valid_negative_entries':count,'nominal_GHz_minmax':frequencies[[0,-1]].tolist(),
            'nearest_centre_max_deg':float(angles.max()),'target_centres_beyond_3p5deg':gt,
            'C_squared_cov_diagonal_relative_max':relation,
            'inference':'Centre distances establish neither actual holes nor an angular lower-response certificate; C diagonal difference does not block partial geometry/noise.'}

def main():
    started=time.monotonic()
    out={'schema':'R36-07-independent-bounded-checks-v1','candidate_identity':EXPECTED,'checks':{},'failures':[]}
    for name,fn in [('identities',identity_check),('geometry',geometry_check),('spin_libsharp',spin_check),
                    ('PSD_completion_and_noise_summaries',covariance_check),('native_source_samples',native_samples_check),('FIRAS',firas_check)]:
        t=time.monotonic()
        try:
            value=fn();out['checks'][name]={'status':'PASS','elapsed_seconds':time.monotonic()-t,'evidence':value}
        except Exception as exc:
            failure={'check':name,'exception_type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
            out['failures'].append(failure)
            first=OUT/'FIRST_FAILURE.json'
            if not first.exists(): first.write_text(json.dumps(failure,indent=2)+'\n')
            out['checks'][name]={'status':'FAIL','elapsed_seconds':time.monotonic()-t}
        print(name,out['checks'][name]['status'],flush=True)
    out.update(elapsed_seconds=time.monotonic()-started,maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               python=sys.version,numpy=np.__version__,reproducer_sha256=digest(__file__),all_checks_pass=not out['failures'])
    (OUT/'NUMERIC_CHECKS.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'all_checks_pass':out['all_checks_pass'],'elapsed_seconds':out['elapsed_seconds'],'failures':out['failures']}))

if __name__=='__main__':main()
