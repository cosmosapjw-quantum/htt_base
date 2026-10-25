"""One-use R30 controls and actual fixed-cohort band-PV consumer.

No calculation occurs at import. The controller must bind INPUT.json and start
this only through runner.py after its explicit GO.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import time

import numpy as np
from scipy.integrate import quad

import science as s


class Hold(RuntimeError):
    pass


def atomic_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    with open(tmp, 'w') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def atomic_npz(path, **arrays):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp.npz')
    np.savez_compressed(tmp, **arrays)
    with open(tmp, 'rb') as f:
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def atomic_text(path,value):
    path=Path(path)
    tmp=path.with_name(path.name+'.tmp')
    with open(tmp,'w') as f:
        f.write(value);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def demand(condition, detail):
    if not condition:
        raise Hold(detail)


def controls(data, amp, norm, deadline):
    start = time.monotonic()
    if not np.isclose(s.transfer(0.), 1., atol=1e-15):
        raise Hold('TRANSFER_ZERO_LIMIT')
    demand(np.all(s.power(np.geomspace(1e-6, 1e2, 20), amp) >= 0), 'NEGATIVE_POWER')
    demand(abs(math.sqrt(amp*norm[1][0])-s.SIGMA8) <= 1e-12, 'SIGMA8_RECONSTRUCTION')
    demand(abs(s.BANDS[0][0] / s.H - .005) <= 1e-15, 'K_UNIT_CONVERSION')
    demand(abs(s.RADII[0] / s.H * s.H - 5) <= 1e-15, 'R_UNIT_CONVERSION')
    # In EdS, I_D(a)=(2/5)a^(5/2), D=a and f=1.
    a = np.array([.25, .5, 1.])
    eds_ia = 2*a**2.5/5
    eds_d = a**(-1.5)*eds_ia/(2/5)
    eds_f = -1.5 + 1/(a*a * a**(-4.5) * eds_ia)
    demand(max(np.max(abs(eds_d-a)), np.max(abs(eds_f-1))) < 1e-14, 'EDS_CONTROL')
    z = data['z']
    c32, g32, j32, _, _ = s.background(z, 32)
    c64, g64, j64, _, _ = s.background(z, 64)
    growth_diff = float(np.max(abs(g32/g64-1)))
    distance_diff = float(np.max(abs(c32/c64-1)))
    demand(growth_diff <= 1e-9 and distance_diff <= 1e-9, f'BACKGROUND_32_64 {growth_diff} {distance_diff}')
    # Check the inherited H0=74.6 distance modulus derivative, at spaced real rows.
    pick = np.linspace(0, len(z)-1, 11, dtype=int)
    zz = z[pick]
    step = np.minimum(1e-5*zz, 1e-6)
    def mu(x):
        i = s.distance_integral(x, 64)
        return 25+5*np.log10(s.C/74.6*(1+x)*i)
    derivative = (mu(zz+step)-mu(zz-step))/(2*step)
    expected = -s.C*j64[pick]/(1+zz)
    demand(np.max(abs(derivative/expected-1)) <= 2e-7 and np.all(j64[pick] < 0), 'J_FINITE_DIFFERENCE')
    for order in (35, 53):
        pts, wt, paired, pwt = s.angular_rule(order)
        demand(abs(np.sum(wt)-4*math.pi) < 1e-12, f'ANGULAR_CONSTANT_{order}')
        demand(np.max(abs(wt@pts)) < 1e-12, f'ANGULAR_LINEAR_{order}')
        demand(np.max(abs(np.einsum('n,ni,nj->ij',wt,pts,pts)-np.eye(3)*4*math.pi/3)) < 1e-12,
               f'ANGULAR_QUADRATIC_{order}')
        demand(abs(np.sum(pwt)-4*math.pi) < 1e-12 and len(paired)*2 == len(pts), f'ANGULAR_PAIR_{order}')
    for lo, hi in s.BANDS:
        for n in (16, 32):
            k,w = s.cc_rule(n,lo,hi)
            demand(abs(sum(w)-(hi-lo)) <= 1e-12*(hi-lo), 'CC_CONSTANT')
            demand(abs(w@k**2-(hi**3-lo**3)/3) <= 1e-12*(hi**3-lo**3)/3, 'CC_QUADRATIC')
    f = data['factor']
    demand(np.array_equal(f['group_id'], data['ids']), 'GROUP_IDS')
    demand(int(np.sum(f['mixed_zero_leverage_mask'])) == 944 and
           int(np.sum(f['exact_zero_leverage_mask'])) == 945 and
           bool(f['exact_zero_leverage_mask'][1484]) and int(data['ids'][1484]) == 11274,
           'CORRECTED_MASKS')
    demand(np.all(f['exact_zero_leverage_mask'][f['mixed_zero_leverage_mask']]), 'MASK_SUBSET')
    demand(np.all(f['difference_reference_row_index'] ==
                  f['reference_row_by_channel'][f['nonreference_channel']]), 'DIFFERENCE_REFERENCE_MAP')
    # Every within-channel constant cancels before L.
    offsets = np.arange(7., dtype=float)
    support=f['selected_support_7']
    nonref=f['nonreference_row_index']; refs=f['difference_reference_row_index']
    channel_i=np.argmax(support[nonref],axis=1)
    channel_r=np.argmax(support[refs],axis=1)
    demand(np.all(np.sum(support[nonref],axis=1)==1) and
           np.all(np.sum(support[refs],axis=1)==1) and
           np.array_equal(channel_i,channel_r) and
           np.array_equal(channel_i,f['nonreference_channel']) and
           np.array_equal(offsets[channel_i]-offsets[channel_r],np.zeros(len(nonref))),
           'CHANNEL_OFFSET_CONTRAST')
    # Constant field through actual redshift-only j,n against saved nuisance bulk response.
    m = len(np.unique(data['method']))
    with np.load(data['carrier_path'], allow_pickle=False) as carrier:
        saved_bulk = carrier['N'][:, 2*m:2*m+3]
    bulk = j64[:,None] * data['n']
    demand(np.max(abs(bulk-saved_bulk)) <= 1e-10, 'SAVED_BULK_RESPONSE_ROWS')
    direct = f['L_binary64'] @ (bulk[f['nonreference_row_index']]-bulk[f['difference_reference_row_index']])
    saved = np.asarray(data['result']['response_numerical']['KN'])[:, 2*m:2*m+3]
    err = abs(direct-saved)
    demand(np.max(err) <= 1e-10 and np.all(err <= 1e-8*np.maximum(abs(saved),abs(direct))+1e-10),
           'SAVED_BULK_RESPONSE_COEFFICIENTS')
    fixture = fixture_controls(amp, deadline)
    demand(time.monotonic() < deadline, 'CONTROL_DEADLINE')
    return {'status':'PASS', 'seconds':time.monotonic()-start, 'normalization':norm,
            'amplitude':amp, 'sigma8_reconstructed':math.sqrt(amp*norm[1][0]),
            'transfer_spots_k_mpc_inv':[0.,.003,.02,.1],
            'transfer_spots':[float(s.transfer(k)) for k in (0.,.003,.02,.1)],
            'growth_32_64_max_relative':growth_diff, 'chi_32_64_max_relative':distance_diff,
            'redshift_j_finite_difference_max_relative':float(np.max(abs(derivative/expected-1))),
            'fixture': fixture}, (c64,g64,j64)


def fixture_controls(amp, deadline):
    # Smooth, nontrivial signed fixture with a duplicate-position pair.
    x = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,1,0],
                  [0,0,0],[1,0,1],[0,1,1]],float)
    n = np.array([[1,1,1],[1,0,1],[0,1,1],[1,1,0],[-1,1,1],
                  [1,1,1],[1,-1,1],[1,1,-1]],float)
    n /= np.linalg.norm(n,axis=1)[:,None]
    jg = np.array([-.7,-.8,-.9,-.65,-1.1,-.75,-.95,-.85])
    nonref = np.arange(1,8)
    refs = np.array([0,0,0,0,0,0,0])
    L = np.array([[1,-2,0,.5,0,0,1],[-.5,0,1,0,2,0,-1],
                  [0,1,-1,0,0,2,.5],[1,0,0,-1,1,-1,0],
                  [0,.5,.4,.2,-.7,1,-.2]],float)
    pts, wt, paired, pwt = s.angular_rule(53)
    kk, wk = s.cc_rule(32,*s.BANDS[0])
    spectral = np.array([s.gram(k,paired,pwt,x,n,jg,L,nonref,refs) for k in kk])
    angular = s.joint_from_spectral(spectral,kk,wk,amp)
    # Independent scalar pair-kernel route; N=8 only.
    K = np.zeros((5,8))
    for p,i in enumerate(nonref):
        K[:,i] += L[:,p]
        K[:,refs[p]] -= L[:,p]
    def pair_at(k):
        mat = (jg[:,None]*jg[None,:]) * s.pair_kernel(k,x,n)
        return K@mat@K.T
    pair = np.zeros((15,15))
    for r in range(3):
        for t in range(3):
            for a in range(5):
                for b in range(5):
                    def integrand(k):
                        smooth = math.exp(-.5*(k*s.RADII[r]/s.H)**2-.5*(k*s.RADII[t]/s.H)**2)
                        return float(s.power(k,amp))*smooth*pair_at(k)[a,b]/(2*math.pi**2)
                    val,_ = quad(integrand,*s.BANDS[0],epsrel=1e-10,epsabs=1e-12)
                    pair[5*r+a,5*t+b] = val
    delta = angular-pair
    scale = np.sqrt(np.maximum(np.diag(pair),0))
    demand(np.all(scale > 0), 'FIXTURE_ZERO_VARIANCE')
    fro = float(np.linalg.norm(delta)/np.linalg.norm(pair))
    entry = float(np.max(abs(delta)/np.outer(scale,scale)))
    demand(fro <= 1e-5 and entry <= 1e-6 and abs(pair[0,1]) > 0, f'FIXTURE_PAIR_KERNEL {fro} {entry}')
    # Paired and unpaired comparison, row permutation, simultaneous spatial rotation.
    first = s.gram(kk[8],paired,pwt,x,n,jg,L,nonref,refs)
    unpaired = s.gram(kk[8],pts,wt,x,n,jg,L,nonref,refs)
    demand(np.max(abs(first-unpaired)) <= 1e-11*np.max(abs(first)), 'PAIRED_UNPAIRED')
    perm = np.array([3,5,1,7,2,0,6,4])
    inv = np.argsort(perm)
    permuted = s.gram(kk[8],paired,pwt,x[perm],n[perm],jg[perm],L,inv[nonref],inv[refs])
    demand(np.max(abs(first-permuted)) <= 1e-11*np.max(abs(first)), 'FIXTURE_ROW_PERMUTATION')
    rot = np.array([[0,-1,0],[1,0,0],[0,0,1]])
    rotated = s.gram(kk[8],paired,pwt,x@rot.T,n@rot.T,jg,L,nonref,refs)
    demand(np.max(abs(first-rotated)) <= 1e-11*np.max(abs(first)), 'FIXTURE_ROTATION')
    scaled = s.joint_from_spectral(4*spectral,kk,wk,amp)
    demand(np.max(abs(scaled-4*angular)) <= 1e-11*np.max(abs(angular)), 'POWER_SCALING')
    sym, diag = s.matrix_diagnostics(angular)
    basis = np.array([np.diag([1,-1,0])/math.sqrt(2),np.diag([1,1,-2])/math.sqrt(6),
                      [[0,1/math.sqrt(2),0],[1/math.sqrt(2),0,0],[0,0,0]],
                      [[0,0,1/math.sqrt(2)],[0,0,0],[1/math.sqrt(2),0,0]],
                      [[0,0,0],[0,0,1/math.sqrt(2)],[0,1/math.sqrt(2),0]]])
    transformed = np.einsum('aij,ik,jl,bkl->ab',basis,rot,rot,basis)
    block = sym[:5,:5]
    covariance_rotated = transformed @ block @ transformed.T
    tensor=np.einsum('ab,aij,bkl->ijkl',block,basis,basis)
    tensor_rotated=np.einsum('ip,jq,kr,ls,pqrs->ijkl',rot,rot,rot,rot,tensor)
    tensor_from_coeff=np.einsum('ab,aij,bkl->ijkl',covariance_rotated,basis,basis)
    demand(np.max(abs(transformed@transformed.T-np.eye(5))) <= 1e-12 and
           np.max(abs(tensor_rotated-tensor_from_coeff)) <= 1e-11*np.max(abs(tensor)) and
           np.max(abs(covariance_rotated-covariance_rotated.T)) <= 1e-11*np.max(abs(block)),
           'STF_BASIS_ROTATION')
    demand(time.monotonic() < deadline, 'CONTROL_DEADLINE')
    return {'pair_relative_frobenius':fro, 'pair_max_normalized_entry':entry,
            'joint_minimum_eigenvalue':diag['minimum_eigenvalue'],
            'paired_unpaired_max_abs':float(np.max(abs(first-unpaired))),
            'rotation_matrix':transformed.tolist(),
            'pair_band1_r10':pair[5:10,5:10].tolist(),
            'angular_band1_r10':angular[5:10,5:10].tolist()}


def source_data(bindings):
    p = {k:v['path'] for k,v in bindings['immutable_numeric_inputs'].items()}
    with np.load(p['corrected_factor'],allow_pickle=False) as z:
        factor = {k:z[k] for k in z.files}
    with np.load(p['selected_source'],allow_pickle=False) as z:
        ids,zobs,n,method = (z[k] for k in ('group_id','z_CMB','n_J2000','method_family'))
    with open(p['corrected_result']) as f:
        result = json.load(f)
    demand(ids.shape == (35970,) and n.shape == (35970,3), 'SOURCE_SHAPE')
    demand(s.sha256(p['selected_source']) == bindings['immutable_numeric_inputs']['selected_source']['sha256'], 'SOURCE_SHA')
    demand(__import__('hashlib').sha256(np.asarray(ids,dtype='<i8').tobytes()).hexdigest() ==
           'f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88', 'ID_ORDER_SHA')
    demand(np.array_equal(ids,factor['group_id']) and np.all(np.isfinite(zobs)) and
           np.all((zobs > 0) & (zobs <= .5)) and np.all(np.isfinite(n)) and
           np.max(abs(np.linalg.norm(n,axis=1)-1)) <= 2e-13, 'SOURCE_DOMAINS')
    return {'ids':ids,'z':zobs,'n':n,'method':method,'factor':factor,'result':result,
            'carrier_path':p['inherited_carrier']}


def stage(order, radial_n, name, data, amp, background, output, deadline, timing):
    f = data['factor']
    _,_,paired,pwt = s.angular_rule(order)
    positions = background[0][:,None]*data['n']
    jg = background[1]*background[2]
    matrices=[]; joints=[]
    for bi,(lo,hi) in enumerate(s.BANDS):
        k,radial = s.cc_rule(radial_n,lo,hi)
        spectral=[]
        for node,kk in enumerate(k):
            path = output/'spectral'/f'o{order}_b{bi}_k{float(kk).hex()}.npz'
            if path.exists():
                with np.load(path,allow_pickle=False) as z:
                    matrix=z['A']
            else:
                start=time.monotonic()
                matrix=s.gram(kk,paired,pwt,positions,data['n'],jg,f['L_binary64'],
                              f['nonreference_row_index'],f['difference_reference_row_index'])
                demand(np.all(np.isfinite(matrix)), f'NONFINITE_SPECTRAL {order} {bi} {node}')
                sample_u=paired[:4]
                phase=positions@sample_u.T
                amplitude=jg[:,None]*(data['n']@sample_u.T)
                signal=amplitude*np.exp(1j*kk*phase)
                sample_w=f['L_binary64']@(signal[f['nonreference_row_index']]-
                                           signal[f['difference_reference_row_index']])
                atomic_npz(path,A=matrix,k=np.array(kk),order=np.array(order),band=np.array(bi),
                           sample_u=sample_u,sample_w=sample_w)
                timing.append({'order':order,'band':bi,'node':node,'seconds':time.monotonic()-start,
                               'directions':len(pwt),'path':str(path)})
                atomic_json(output/'PROGRESS.json',{'last_completed_spectral':timing[-1],
                            'completed_spectral_count':len(timing),'stage':name,'utc_unix':time.time()})
                # Forecast all still-declared mandatory work, using actual measured rate.
                if len(timing) >= 3:
                    rates=[t['seconds']/t['directions'] for t in timing]
                    conservative=max(np.median(rates)*1.25,max(rates[-3:]))
                    mandatory=0
                    for oo,nn in ((35,16),(53,32)):
                        directions={35:217,53:487}[oo]
                        for bb in (0,1):
                            nodes,_=s.cc_rule(nn,*s.BANDS[bb])
                            for jj in range(nn+1):
                                key=output/'spectral'/f'o{oo}_b{bb}_k{float(nodes[jj]).hex()}.npz'
                                if not key.exists():
                                    mandatory += directions
                    forecast=mandatory*conservative + 8
                    if forecast > deadline-time.monotonic():
                        raise Hold(f'BUDGET_CONVERGENCE_HOLD forecast={forecast:.3f} remaining={deadline-time.monotonic():.3f}')
            spectral.append(matrix)
            if time.monotonic() > deadline:
                raise Hold(f'BUDGET_CONVERGENCE_HOLD deadline after spectral {order} {bi} {node}')
        a=np.stack(spectral)
        joint,diag=s.matrix_diagnostics(s.joint_from_spectral(a,k,radial,amp))
        matrices.append((k,radial,a))
        joints.append(joint)
    both,diag=s.matrix_diagnostics(joints[0]+joints[1])
    atomic_npz(output/f'STAGE_{name}.npz',band1=joints[0],band2=joints[1],total=both,
               k1=matrices[0][0],w1=matrices[0][1],A1=matrices[0][2],
               k2=matrices[1][0],w2=matrices[1][1],A2=matrices[1][2])
    atomic_json(output/f'STAGE_{name}.json',{'order':order,'radial_intervals':radial_n,
                'joint_diagnostics':diag,'source':'conditional band-PV component'})
    return joints


def summarize(joints, basis):
    results=[]
    for joint in (joints[0],joints[1],joints[0]+joints[1]):
        blocks=joint.reshape(3,5,3,5).transpose(0,2,1,3)
        corr=joint/np.outer(np.sqrt(np.diag(joint)),np.sqrt(np.diag(joint)))
        tensor=np.empty((3,3,3,3,3,3))
        for r in range(3):
            for t in range(3):
                tensor[r,t]=np.einsum('ab,aij,bkl->ijkl',blocks[r,t],basis,basis)
        eig=[]
        for r in range(3):
            val,vec=np.linalg.eigh(blocks[r,r])
            for col in range(vec.shape[1]):
                pivot=np.argmax(abs(vec[:,col]))
                if vec[pivot,col] < 0:vec[:,col]*=-1
            eig.append({'eigenvalues':val.tolist(),'signed_eigenvectors_columns':vec.tolist(),
                        'basis_labels':s.BASIS_LABELS})
        results.append((blocks,corr,tensor,eig))
    return results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    args=parser.parse_args()
    with open(args.input) as f:
        packet=json.load(f)
    output=Path(packet['output_dir'])
    output.mkdir(parents=True,exist_ok=True)
    (output/'spectral').mkdir(exist_ok=True)
    deadline=float(os.environ['R30_CHILD_DEADLINE_MONOTONIC'])
    timing=[]
    status={'status':'STARTED','scientific_admission':False,'original_H02_H04':'HOLD',
            'component':'conditional fixed-band five-coordinate apparent STF error only'}
    try:
        demand(packet.get('controller_go') is True, 'MISSING_CONTROLLER_GO')
        bindings=json.load(open(packet['input_bindings']))
        demand(s.sha256(packet['input_bindings']) == packet['input_bindings_sha256'], 'BINDINGS_SHA')
        s.verify_bindings(bindings)
        data=source_data(bindings)
        amp,norm=s.power_amplitude()
        control,background=controls(data,amp,norm,deadline)
        atomic_json(output/'CONTROLS.json',control)
        a=stage(35,16,'A',data,amp,background,output,deadline,timing)
        b=stage(53,16,'B',data,amp,background,output,deadline,timing)
        c=stage(53,32,'C',data,amp,background,output,deadline,timing)
        angular_ok,angular_findings=s.convergence(a,b)
        radial_ok,radial_findings=s.convergence(b,c)
        status.update({'angular_A_B':angular_findings,'radial_B_C':radial_findings,
                       'angular_A_B_pass':angular_ok,'radial_B_C_pass':radial_ok})
        if not radial_ok:
            raise Hold('RADIAL_CONVERGENCE_HOLD')
        final=c; final_stage='C'; refinement=None; d=None
        if not angular_ok:
            rates=[t['seconds']/t['directions'] for t in timing if t['directions'] in (217,487)]
            if not rates:
                raise Hold('ANGULAR_CONVERGENCE_HOLD no timing for optional refinement')
            optional_forecast=727*33*2*max(np.median(rates)*1.25,max(rates[-3:]))+8
            if optional_forecast > deadline-time.monotonic():
                raise Hold(f'ANGULAR_CONVERGENCE_HOLD optional_D_forecast={optional_forecast:.3f} '
                           f'remaining={deadline-time.monotonic():.3f}')
            d=stage(65,32,'D',data,amp,background,output,deadline,timing)
            refinement,angular_findings=s.convergence(c,d)
            status.update({'angular_C_D':angular_findings,'angular_C_D_pass':refinement})
            if not refinement:
                raise Hold('ANGULAR_CONVERGENCE_HOLD')
            final=d;final_stage='D'
        summaries=summarize(final,data['factor']['STF_basis_5x3x3'])
        blocks=np.stack([v[0] for v in summaries]); corr=np.stack([v[1] for v in summaries])
        tensor=np.stack([v[2] for v in summaries])
        joint_values=[];joint_vectors=[]
        for joint in (final[0],final[1],final[0]+final[1]):
            values,vectors=np.linalg.eigh(joint)
            for col in range(vectors.shape[1]):
                pivot=np.argmax(abs(vectors[:,col]))
                if vectors[pivot,col] < 0:vectors[:,col]*=-1
            joint_values.append(values);joint_vectors.append(vectors)
        basis=data['factor']['STF_basis_5x3x3']
        with np.load(output/f'STAGE_{final_stage}.npz',allow_pickle=False) as final_spectral:
            spectra={key:final_spectral[key] for key in ('k1','w1','A1','k2','w2','A2')}
        stage_products={'joint_stage_A':np.stack(a),'joint_stage_B':np.stack(b),'joint_stage_C':np.stack(c)}
        if d is not None:stage_products['joint_stage_D']=np.stack(d)
        atomic_npz(output/'PRODUCT.npz',group_id=data['ids'],mixed_zero_leverage_mask=data['factor']['mixed_zero_leverage_mask'],
                   exact_zero_leverage_mask=data['factor']['exact_zero_leverage_mask'],
                   additional_zero_leverage_mask=data['factor']['extra_zero_leverage_mask'],
                   b_fact=np.asarray(data['result']['display_b_fact']),STF_basis_5x3x3=basis,
                   positions=background[0][:,None]*data['n'],n_J2000=data['n'],j=background[2],g=background[1],
                   band_joint=np.stack(final),total_joint=final[0]+final[1],
                   covariance_blocks=blocks,coordinate_correlations=corr,tensor_covariance=tensor,
                   joint_eigenvalues=np.stack(joint_values),joint_signed_eigenvectors=np.stack(joint_vectors),
                   radii_hinv_mpc=s.RADII,bands_physical=np.asarray(s.BANDS),
                   angular_order=np.array(65 if d is not None else 53),
                   angular_rule_id=np.array('scipy.integrate.lebedev_rule'),
                   **spectra,**stage_products)
        status.update({'status':'CONDITIONAL_NUMERICAL_PASS_PENDING_INDEPENDENT_REVIEW',
                       'final_stage':final_stage,'controls':control,'angular_A_B':angular_findings,
                       'radial_B_C':radial_findings,'optional_C_D_pass':refinement,
                       'eigensystems':[v[3] for v in summaries],
                       'joint_eigenbasis_labels':[f'R{r:g}:{label}' for r in s.RADII for label in s.BASIS_LABELS],
                       'full_tensor_images':{q:'UNDEFINED/HOLD' for q in ('x','F','Pi','Q','G_F')},
                       'source_bindings':bindings,'spectral_evaluations':timing,
                       'claim_ceiling':'declared conditional band-PV error component, no empirical total law or H02/H04 acceptance'})
        lines=['# R30 conditional band-PV numerical component','',
               'Fixed 35,970-row K_fact=L D_diff apparent STF error component; observed signed center is separate.',
               'EH98 no-wiggle fixed-parameter common Gaussian field, redshift-only inherited j; CMB observer metadata held fixed.',
               f'Final deterministic integration stage: {final_stage}. Angular A/B pass: {angular_ok}; radial B/C pass: {radial_ok}.',
               'Bands are q=[0.005,0.02] and [0.02,0.05] h/Mpc; smoothing radii 5,10,20 h^-1 Mpc.',
               'Full signed 5x5 blocks, 15x15 cross-smoothing matrices, correlations, rank diagnostics, and tensor covariance are in PRODUCT.npz.',
               '']
        for bi,label in enumerate(('B1','B2','B1+B2')):
            lines.append(f'## {label}')
            for r,rh in enumerate(s.RADII):
                ev=summaries[bi][3][r]['eigenvalues']
                vec=np.asarray(summaries[bi][3][r]['signed_eigenvectors_columns'])[:,-1]
                lines.append(f'R={rh:g}: eigenvalues '+', '.join(f'{v:.9g}' for v in ev))
                lines.append('  leading signed STF direction '+', '.join(f'{label}={v:.6g}' for label,v in zip(s.BASIS_LABELS,vec)))
            off=corr[bi].copy();np.fill_diagonal(off,0)
            lines.append(f'Maximum absolute off-diagonal 15x15 correlation: {np.max(abs(off)):.6g}')
            lines.append('')
        lines.extend(['x,F,Pi,Q,G_F: UNDEFINED/HOLD; missing physical response, total law, support, and denominator.',
                      'Original empirical H02/H04 acceptances remain HOLD. This component requires independent numeric review.',''])
        atomic_text(output/'REPORT.md','\n'.join(lines))
    except Exception as exc:
        status.update({'status':'HOLD','first_failure':f'{type(exc).__name__}: {exc}'})
        raise
    finally:
        status['spectral_evaluations']=timing
        status['utc_unix']=time.time()
        atomic_json(output/'RESULT.json',status)


if __name__ == '__main__':
    main()
