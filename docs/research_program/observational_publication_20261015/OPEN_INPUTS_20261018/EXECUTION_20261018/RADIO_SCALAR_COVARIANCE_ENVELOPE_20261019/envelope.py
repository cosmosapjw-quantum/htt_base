"""104 scalar-diagonal PSD variance maxima for eight frozen D05 radio maps."""
import hashlib
import importlib.util
import json
from pathlib import Path
import platform

import numpy as np

HERE = Path(__file__).resolve().parent
D05 = HERE.parent/'D05_GAIA_RADIO'
RAW = Path('/mnt/extdrive/workdir/htt_open_data/vlba/233_3')
KEEP = np.array([0,1,2,6,7,8,9,10,11,12,13,14,15])
FRAME = np.array([3,4,5])
CONVENTIONS = ('published_pmRA_is_tangent','published_pmRA_is_coordinate_rate')
RHOS = (-.9,-.5,.5,.9)
EXPECTED = {
    D05/'observable_vsh.py': ('318acb829f163eedda76a136a0edc4d247c17a6893f2faf24681e34fd79822b5',None),
    D05/'RESULTS.json': ('386bfa19ff1f0c24ec836f2e3e471717edf38c3c10da6d119d70548cf062baa0',None),
    RAW/'table6.dat': ('5358da3b6233194cad556010259400b729b7472c5037e39facf1f413e2aa3bff',99085),
    RAW/'ReadMe': ('cb6d18077090e27b803924068c2c9a8b52e2991d61882ff6cc502cefe0274b98',13460),
    HERE/'CONTRACT.md': ('9964c9bf246e6acb2ab3fcaed2d21e3a45dcf5fea522f1f386aebb86b3e3d882',None),
}
CAVEATS = [
    'Published marginal errors are a working hypothesis, not established total physical variances.',
    'Centered-variance envelopes; bias unmeasured and no MSE bound.',
    'Frame/NNR constraints may exclude maximizing covariances; physical B1 UNKNOWN.',
    '104 coordinatewise maxima need not be jointly attained; their diagonal is not a joint covariance or a Loewner upper bound.',
    'Eight conditional estimator maps do not cover all weights or resolve the RA convention.',
    'No confidence coverage, p-value, Gaia-radio independence, cosmic curl, matter vorticity, native solver, family identification or K03 admission.',
]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def error(a,b):
    return float(np.max(np.abs(np.asarray(a)-b))/(1+np.max(np.abs(b))))


def check_finite(*values):
    require(all(np.all(np.isfinite(v)) for v in values),'Nonfinite numerical field')


def load_d05():
    # Controls load geometry code and cached matrices, never the actual radio rows.
    for path in (D05/'observable_vsh.py',D05/'RESULTS.json',HERE/'CONTRACT.md'):
        require(digest(path)==EXPECTED[path][0],'Immutable identity drift: '+str(path))
    spec = importlib.util.spec_from_file_location('sealed_radio_d05',D05/'observable_vsh.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    require(np.array_equal(mod.KEEP,KEEP) and np.array_equal(mod.FRAME,FRAME),'Frozen coordinate selector mismatch')
    old = json.loads((D05/'RESULTS.json').read_text())['radio']
    require(old['rows']==713,'Cached radio row count mismatch')
    grid = old['sensitivity_grid']
    require(len(grid)==8,'Cached scenario count mismatch')
    for s,(convention,rho) in zip(grid,[(c,r) for c in CONVENTIONS for r in RHOS]):
        validate_scenario(s,convention,rho)
        require(s['frame_projected']['coefficient_order']==[mod.LABELS[i] for i in KEEP],'Retained coordinate order mismatch')
    return mod,grid


def validate_scenario(s,convention,rho):
    require(s['convention']==convention and s['assumed_missing_component_rho']==rho,'Scenario identity/order mismatch')
    v=np.asarray(s['formal_covariance_uas2yr2'],dtype=float)
    q=np.asarray(s['frame_projected']['covariance_uas2yr2'],dtype=float)
    require(v.shape==(16,16) and q.shape==(13,13),'Malformed cached covariance')
    check_finite(v,q)
    require(np.all(np.diag(v)>0),'Nonpositive cached diagonal')
    require(error(v,v.T)<=1e-12,'Cached V symmetry mismatch')
    require(error(v[np.ix_(KEEP,KEEP)],q)<=1e-12,'Cached quotient covariance mismatch')
    return v


def parse_line(line):
    require(len(line)>=99,'Malformed required fields: short row')
    require(line[32] in ('+','-'),'Malformed declination sign')
    try:
        h,m,s = float(line[9:11]),float(line[12:14]),float(line[15:24])
        dd,dm,ds=float(line[33:35]),float(line[36:38]),float(line[39:48])
        sa,sd=float(line[65:72]),float(line[92:99])
    except ValueError as exc:
        raise ValueError('Malformed required geometry/error field') from exc
    check_finite(h,m,s,dd,dm,ds,sa,sd)
    require(0<=h<24 and 0<=m<60 and 0<=s<60,'Invalid RA geometry')
    require(0<=dd<=90 and 0<=dm<60 and 0<=ds<60 and dd+dm/60+ds/3600<=90,'Invalid DE geometry')
    require(sa>0 and sd>0,'Nonpositive motion errors')
    return 15*(h+m/60+s/3600),(-1 if line[32]=='-' else 1)*(dd+dm/60+ds/3600),sa,sd


def transformed_errors(raw_errors,dec,convention):
    require(convention in CONVENTIONS,'Unknown convention')
    errors=np.asarray(raw_errors,dtype=float).copy()
    require(errors.ndim==2 and errors.shape[1]==2,'Error shape mismatch')
    if convention==CONVENTIONS[1]:
        errors[:,0]*=np.cos(np.deg2rad(dec))
    check_finite(errors)
    require(np.all(errors>0),'Transformed errors must be strictly positive')
    return errors


def scalar_stats(ell,sigma,rho=0.):
    """Return l1 radius, diagonal computational sum, working-block variance."""
    ell=np.asarray(ell,dtype=float);sigma=np.asarray(sigma,dtype=float)
    require(ell.shape==sigma.shape,'Scalar kernel shape mismatch')
    check_finite(ell,sigma,rho)
    require(np.all(sigma>0) and abs(rho)<1,'Invalid scalar kernel errors/rho')
    require(ell.ndim==2 and ell.shape[1]==2,'Expected source x 2 scalar weights')
    z=ell.astype(np.longdouble)*sigma.astype(np.longdouble)
    radius=np.sum(np.abs(z),dtype=np.longdouble)
    d=np.sum(z*z,dtype=np.longdouble)
    a,b=z[:,0],z[:,1]
    work=np.sum((a+rho*b)**2+(1-np.longdouble(rho)**2)*b*b,dtype=np.longdouble)
    check_finite(radius,d,work,radius*radius)
    return radius,d,work


def main():
    controls=json.loads((HERE/'CONTROLS.json').read_text())
    require(controls['status']=='PASS','Controls not PASS')
    require(controls['envelope_sha256']==digest(HERE/'envelope.py'),'Controls source drift')
    mod,grid=load_d05()
    identities={}
    for path,(sha,size) in EXPECTED.items():
        actual_sha=digest(path);actual_size=path.stat().st_size
        require(actual_sha==sha and (size is None or actual_size==size),'Immutable source drift: '+str(path))
        identities[str(path)]=dict(sha256=actual_sha,bytes=actual_size)
    # Exactly one source pass. Do not read motions, position errors or unused nulls.
    lines=(RAW/'table6.dat').read_text().splitlines()
    require(len(lines)==713 and all(line.strip() for line in lines),'Published row/order count mismatch')
    geometry=np.array([parse_line(line) for line in lines],dtype=float)
    ra,dec=geometry[:,0],geometry[:,1]
    X=mod.design(ra,dec)
    require(X.shape==(713,2,16),'Full design shape mismatch')
    check_finite(X)
    R=np.eye(16)[KEEP]
    results=[];scenarios=[]
    for index,s in enumerate(grid):
        convention,rho=CONVENTIONS[index//4],RHOS[index%4]
        V=validate_scenario(s,convention,rho)
        sigma=transformed_errors(geometry[:,2:],dec,convention)
        W=mod.precision(sigma[:,0],sigma[:,1],rho)
        WX=np.einsum('nij,njp->nip',W,X)
        N=np.einsum('nip,niq->pq',X,WX)
        check_finite(N)
        np.linalg.cholesky(N)  # nonsingular positive definite, no new fit/RHS
        require(error(N,N.T)<=1e-12,'Normal symmetry mismatch')
        L=np.einsum('kp,nip->nki',R@V,WX)
        map_residual=np.einsum('nki,nip->kp',L,X)-R
        checks=dict(VN_max_abs=float(np.max(np.abs(V@N-np.eye(16)))),
            LX_minus_R_max_abs=float(np.max(np.abs(map_residual))),
            frame_columns_max_abs=float(np.max(np.abs(map_residual[:,FRAME]))),
            quotient_covariance_E=error(V[np.ix_(KEEP,KEEP)],np.array(s['frame_projected']['covariance_uas2yr2'])),
            V_symmetry_E=error(V,V.T),N_symmetry_E=error(N,N.T))
        require(checks['VN_max_abs']<=1e-10 and checks['LX_minus_R_max_abs']<=1e-10,'Frozen map residual failure')
        work_residual=[]
        for k,label in enumerate(s['frame_projected']['coefficient_order']):
            radius,d,work=scalar_stats(L[:,k,:],sigma,rho)
            vmax=radius*radius;oldvar=V[KEEP[k],KEEP[k]]
            rel=abs(work-oldvar)/oldvar
            require(oldvar>0 and rel<=1e-10,'Working variance relative mismatch')
            require(vmax>=0 and d>=0 and work>=0,'Negative variance')
            require(vmax>=(1-1e-10)*work and vmax>=(1-1e-10)*d and vmax<=(1+1e-10)*1426*d,'Scalar envelope inequality failure')
            row=dict(scenario=index,convention=convention,working_rho=rho,coordinate=label,
                l1_radius_uasyr=float(radius),vmax_uas2yr2=float(vmax),
                sqrt_vmax_uasyr=float(np.sqrt(vmax)),diagonal_computational_sum_uas2yr2=float(d),
                vwork_uas2yr2=float(work),old_working_variance_uas2yr2=float(oldvar),
                vmax_over_vwork=float(vmax/work),sqrt_vmax_over_vwork=float(np.sqrt(vmax/work)),
                working_relative_residual=float(rel),scalar_count=1426)
            check_finite(*[v for v in row.values() if isinstance(v,(float,int))])
            results.append(row);work_residual.append(float(rel))
        checks['working_relative_residual_max']=max(work_residual)
        scenarios.append(dict(scenario=index,convention=convention,working_rho=rho,
            normal_matrix=N.tolist(),checks=checks))
    require(len(results)==104,'Incomplete scalar results')
    result=dict(schema='htt.radio.scalar_covariance_envelope/1',owner='obsstat',claim_tier='C0',
        status='DIAGNOSTIC_ONLY',artifact_mode='CONDITIONAL_SCALAR_DIAGONAL_PSD_ENVELOPE',
        scope='713 released radio sources, 8 cached D05 estimator maps, 13 retained coordinates',
        allowed_use='Coordinatewise centered-variance sensitivity under working scalar marginals',
        transfer_source='none',null_status='NOT_AVAILABLE',null_mock_status='NOT_AVAILABLE',
        covariance_status='TRUE_JOINT_COVARIANCE_UNKNOWN; scalar marginals hypothesized',
        sky_support_status='Released J2000 directions at most recent VLBA epoch, held fixed; selected catalogue',
        forbidden_uses=CAVEATS,caveats=CAVEATS,source_identity=identities,
        base_commit='9a56d1eccfb6ab4bd2413f160f971e406e1a7db3',
        worktree_state='Existing checkout; parent RESUME edit and new assigned directory',
        source_epoch='J2000 coordinates measured at most recent VLBA observing epoch; no epoch propagation',
        motion_error_units='microarcsec/year; no factor 15 or 1000 applied to errors',
        retained_order=[mod.LABELS[i] for i in KEEP],source_rows=713,scalar_count=1426,
        scenario_order=[dict(convention=c,working_rho=r) for c in CONVENTIONS for r in RHOS],
        method='Fixed map L=R V X^T W. v_max=(sum |ell_a| sigma_a)^2. Extended-precision accumulation.',
        working_rho_role='Estimator definition only; true PSD correlations range over endpoints +/-1',
        simultaneous_attainment=False,physical_B1='UNKNOWN',bias='UNMEASURED',
        original_nodes_complete='17/42 unchanged',original_six='NOT_READY_TO_SUBMIT',
        independent_review='PENDING_FRESH_READ_ONLY_ASTRA',
        generating_command='.venv/bin/python -B '+str(HERE/'bounded_run.py')+' actual',
        code_sha256=digest(HERE/'envelope.py'),controls_sha256=digest(HERE/'CONTROLS.json'),
        runtime=dict(requested_model='gpt-6.1-sol',requested_effort='high',observed_model='UNKNOWN',observed_effort='UNKNOWN',
            python=platform.python_version(),numpy=np.__version__,accumulator='numpy.longdouble',
            accumulator_mantissa_bits=int(np.finfo(np.longdouble).nmant)),
        scenarios=scenarios,results=results)
    (HERE/'RESULTS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status='PASS_CONDITIONAL_CALCULATION',source_rows=713,maps=8,coordinates=104,
        max_VN_residual=max(s['checks']['VN_max_abs'] for s in scenarios),
        max_LX_residual=max(s['checks']['LX_minus_R_max_abs'] for s in scenarios),
        results_sha256=digest(HERE/'RESULTS.json'))),flush=True)


if __name__=='__main__':
    main()
