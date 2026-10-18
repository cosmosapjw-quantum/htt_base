"""Focused finite controls; no actual radio row access or motion fits."""
import json
import sys
import numpy as np
from envelope import (HERE, KEEP, FRAME, CONVENTIONS, RHOS, digest, error,
    require, scalar_stats, parse_line, transformed_errors, validate_scenario, load_d05)


def close(a,b):
    require(error(a,np.asarray(b))<=1e-12,'Finite control disagreement')


def rejected(function,*args):
    try:
        function(*args)
    except (ValueError,KeyError):
        return
    raise AssertionError('Invalid fixture accepted')


def fixture():
    row=list(' '*139)
    for a,b,s in ((9,11,'12'),(12,14,'30'),(15,24,'12.000000'),
        (32,33,'-'),(33,35,'60'),(36,38,'15'),(39,48,'30.000000'),
        (65,72,'   2.00'),(92,99,'   3.00')):
        require(len(s)==b-a,'Fixture width')
        row[a:b]=s
    return ''.join(row)


def controls():
    names=[]
    z=np.zeros((2,2)); sig=np.array([[2.,3.],[4.,5.]])
    require(all(v==0 for v in scalar_stats(z,sig)),'Zero weights not exactly zero')
    names.append('zero_weights_exact')
    close(scalar_stats([[-2,0]],[[3,1]])[0]**2,36)
    names.append('one_scalar_36')
    ell=np.array([[1.,-2.]])
    sigma=np.array([[2.,3.]])
    close(scalar_stats(ell,sigma)[0]**2,64)
    close(ell[0]@np.array([[4.,1.],[1.,9.]])@ell[0],36)
    names.append('two_scalar_64_not_fixed_block_36')
    ell=np.array([[1.,-2.],[3.,-4.]])
    radius,d,work=scalar_stats(ell,sig,.5)
    close(radius**2,1600);close(d,584)
    names.append('four_scalar_1600_d584')
    # Explicit maximizer including a zero-weight component: positive zero sign.
    e=np.array([1.,-2.,0.,-4.]);s=sig.ravel()
    u=s*np.where(e>=0,1.,-1.);cov=np.outer(u,u)
    close(np.diag(cov),s*s)
    require(np.linalg.eigvalsh(cov).min()>=-1e-12,'Witness not PSD numerically')
    close(e@cov@e,np.sum(np.abs(e)*s)**2)
    names.append('rank_one_PSD_diagonal_attainment_zero_component')
    for ix in ([1,0,3,2],[2,3,0,1],[3,0,2,1]):
        close(scalar_stats(ell.ravel()[ix].reshape(2,2),sig.ravel()[ix].reshape(2,2))[0],radius)
    close(scalar_stats(-ell,sig,.5),[radius,d,work])
    close(sum(scalar_stats(ell[i:i+1],sig[i:i+1])[0] for i in range(2)),radius)
    close(scalar_stats(ell,sig*1000,.5),np.array([radius*1000,d*1000**2,work*1000**2]))
    names.extend(['component_source_permutations','overall_weight_sign','chunk_radius_addition','unit_scaling'])
    raw=np.array([[2.,3.]])
    tangent=transformed_errors(raw,np.array([60.]),CONVENTIONS[1])
    close(tangent,[[1.,3.]])
    close(scalar_stats([[1,-1]],raw)[0]**2,25)
    close(scalar_stats([[2,-1]],tangent)[0]**2,25)
    close(scalar_stats([[2,-1]],raw)[0]**2,49)
    close(np.array([2.,-1.])@np.diag([.5,1.]),[1.,-1.])
    names.append('approved_RA_dual_weight_unit_invariant_25_and_wrong_pair_49')
    row=fixture()
    close(parse_line(row),[187.55,-60.25833333333333,2.,3.])
    rejected(parse_line,row[:70]);rejected(parse_line,row[:32]+'?'+row[33:])
    for invalid in ('    nan','   0.00','  -1.00','       '):
        rejected(parse_line,row[:65]+invalid+row[72:])
    rejected(transformed_errors,[[0,1]],[0],CONVENTIONS[0])
    rejected(transformed_errors,[[np.inf,1]],[0],CONVENTIONS[0])
    rejected(transformed_errors,[[1,1]],[np.nan],CONVENTIONS[1])
    rejected(transformed_errors,[[1,1]],[0],'bad_convention')
    rejected(scalar_stats,[[1,2]],[[1,np.nan]])
    names.append('required_field_parser_and_invalid_nonfinite_errors')
    mod,grid=load_d05()
    rejected(validate_scenario,grid[0],CONVENTIONS[0],RHOS[1])
    names.append('cached_scenario_identity_and_order')
    # Deterministic synthetic sky: only geometry/errors, no observed motions.
    i=np.arange(48,dtype=float)
    ra=np.mod(i*137.50776405,360)
    dec=np.rad2deg(np.arcsin(-.95+1.9*(i+.5)/48))
    X=mod.design(ra,dec)
    W=mod.precision(1+i/100,1.2+i/80,.3)
    flat=X.reshape(96,16)
    WX=np.einsum('nij,njp->nip',W,X)
    N=np.einsum('nip,niq->pq',X,WX)
    V=np.linalg.inv(N)
    R=np.eye(16)[KEEP]
    full=np.einsum('kp,nip->nki',R@V,WX).transpose(1,0,2).reshape(13,96)
    B=N[np.ix_(KEEP,FRAME)]@np.linalg.inv(N[np.ix_(FRAME,FRAME)])
    schur=N[np.ix_(KEEP,KEEP)]-B@N[np.ix_(FRAME,KEEP)]
    q=R.copy();q[:,FRAME]=-B
    explicit=np.linalg.solve(schur,q)@WX.transpose(2,0,1).reshape(16,96)
    close(full,explicit)
    require(np.max(np.abs(full@flat-R))<=1e-12,'Synthetic full map failure')
    require(np.max(np.abs(full@flat[:,FRAME]))<=1e-12,'Frame annihilation failure')
    names.extend(['full16_selected_vs_explicit_Schur_map','synthetic_frame_annihilation'])
    result=dict(status='PASS',controls=names,count=len(names),
        envelope_sha256=digest(HERE/'envelope.py'),test_sha256=digest(HERE/'test_envelope.py'),
        scope='Finite controls and cached D05 schema; actual radio rows NOT_READ',
        geometry_max_map_residual=float(np.max(np.abs(full@flat-R))),
        geometry_Schur_E=error(full,explicit))
    (HERE/'CONTROLS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result),flush=True)


def cached_review():
    result=json.loads((HERE/'RESULTS.json').read_text())
    _,grid=load_d05()
    require(len(result['scenarios'])==8 and len(result['results'])==104,'Incomplete cached results')
    residual=[]
    for s,old in zip(result['scenarios'],grid):
        N=np.array(s['normal_matrix']);V=np.array(old['formal_covariance_uas2yr2'])
        np.linalg.cholesky(N)
        r=float(np.max(np.abs(V@N-np.eye(16))))
        require(r<=1e-10,'Cached N/V failure');residual.append(r)
    for row in result['results']:
        v,w,d=row['vmax_uas2yr2'],row['vwork_uas2yr2'],row['diagonal_computational_sum_uas2yr2']
        close(row['sqrt_vmax_uasyr']**2,v)
        close(row['sqrt_vmax_over_vwork']**2,v/w)
        require(v>=(1-1e-10)*w and v>=(1-1e-10)*d and v<=(1+1e-10)*1426*d,'Cached envelope inequality')
    print(json.dumps(dict(status='PASS_CACHED_ONLY',source_rows_replayed=0,max_VN_residual=max(residual))),flush=True)


if __name__=='__main__':
    cached_review() if '--cached-review' in sys.argv else controls()
