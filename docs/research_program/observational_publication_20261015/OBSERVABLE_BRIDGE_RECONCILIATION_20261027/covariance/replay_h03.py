"""Replay six saved H03 dipole fits; conditional statistics, not new sky fits."""
from pathlib import Path
import argparse
import hashlib
import json
import platform

import numpy as np
import scipy
from scipy.linalg import solve_triangular, subspace_angles
from scipy.stats import chi2

from covariance_bridge import gls_svd


def icrs_to_galactic(v):
    # ICRS/J2000 -> IAU Galactic Cartesian rotation; rounded at 16 digits.
    R=np.array([[-0.0548755604162154,-0.8734370902348850,-0.4838350155487132],
                [0.4941094278755837,-0.4448296299600112,0.7469822444972189],
                [-0.8676661490190047,-0.1980763734312015,0.4559837761750669]])
    g=R@v/np.linalg.norm(v)
    return [float(np.degrees(np.arctan2(g[1],g[0]))%360),float(np.degrees(np.arcsin(np.clip(g[2],-1,1))))]


def run(source):
    raw=Path(source).read_bytes(); data=json.loads(raw)
    windows=data['monopole_dipole_STF2_windows']
    if len(windows)!=4:
        raise ValueError('this replay binds the saved four-window experiment')
    idx=np.array([9*j+k for j in range(4) for k in [1,2,3]])
    C=np.asarray(data['joint_covariance_36x36'],float)[np.ix_(idx,idx)]
    y=np.concatenate([np.asarray(w['theta9'])[1:4] for w in windows])
    z=np.array([w['z_center'] for w in windows])
    R=np.vstack([np.asarray(w['bulk_velocity_design_response_9x3_per_Mpc'])[1:4,:] for w in windows])
    G=np.tile(np.eye(3),(4,1))
    B=np.vstack([np.eye(3)/zz for zz in z])
    Z=np.vstack([np.eye(3)*zz for zz in z])
    designs=[('bulk',R,["km/s"]*3),('constant',G,["km/s/Mpc"]*3),
             ('bulk_constant',np.column_stack([R,G]),["km/s"]*3+["km/s/Mpc"]*3),
             ('inverse_z_constant',np.column_stack([B,G]),["km/s/Mpc"]*6),
             ('bulk_z',np.column_stack([R,Z]),["km/s"]*3+["km/s/Mpc"]*3),
             ('bulk_constant_z',np.column_stack([R,G,Z]),["km/s"]*3+["km/s/Mpc"]*6)]
    rows=[]
    for name,X,units in designs:
        r=gls_svd(y,X,C)
        row={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in r.items()}
        row.update(name=name,parameter_units=units)
        dof=r['residual_dof']; tau=float(chi2.ppf(.95,dof))
        row['gaussian_working_reference_threshold_95']=tau
        row['gaussian_working_reference_tail']=float(chi2.sf(r['statistic'],dof))
        row['uniform_covariance_scale_to_threshold']=max(1.,r['statistic']/tau)
        rows.append(row)
    L=np.linalg.cholesky(C)
    angles_white=np.degrees(subspace_angles(solve_triangular(L,R,lower=True),solve_triangular(L,B,lower=True)))
    angles_raw=np.degrees(subspace_angles(R,B))
    fit=gls_svd(y,np.column_stack([R,B]),C)
    bulk=np.array(rows[0]['beta']); Vbulk=np.array(rows[0]['beta_covariance']); bhat=bulk/np.linalg.norm(bulk)
    return {
        'schema':'htt.conditional_h03_replay.v1','date':'2026-10-27',
        'source_commit':'a55036ad09c53a9215dee3282e425d37cfb95443',
        'source_sha256':hashlib.sha256(raw).hexdigest(),
        'source_schema':data['schema'],'source_groups':data['source_groups'],
        'source_frame':data['common_directions'],
        'source_covariance_kind':data['full_joint_covariance_kind'],
        'source_weighting':data['weighting'],
        'data_order':'window major, ICRS dipole x/y/z; original theta9 indices 1,2,3',
        'data_units':'km/s/Mpc','covariance_units':'(km/s/Mpc)^2',
        'null_reference':'fixed Gaussian working covariance only; no empirical CF4 null calibrated',
        'new_observed_data_fit':False,'fits':rows,
        'bulk_vector_summary':{'speed_km_s':float(np.linalg.norm(bulk)),
            'delta_method_working_std_speed_km_s':float(np.sqrt(bhat@Vbulk@bhat)),
            'galactic_longitude_latitude_deg':icrs_to_galactic(bulk)},
        'overlap':{'whitened_principal_angles_degrees_descending':angles_white.tolist(),
            'euclidean_principal_angles_degrees_descending':angles_raw.tolist(),
            'joint_bulk_inverse_z_rank':fit['rank'],
            'joint_bulk_inverse_z_scaled_condition':fit['scaled_condition'],
            'interpretation':'small nonzero angles demonstrate near overlap, not exact rank nonidentifiability; 1/z(center) is a proxy, not the source-level observer response'},
        'covariance_scale_interpretation':'lambda scales the entire assumed covariance: T_lambda=T_1/lambda; required lambda is sensitivity, not an estimated cosmic-variance correction',
        'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}


def figure(result,outdir):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    lam=np.linspace(1,6,300)
    labels={'bulk':'Bulk','constant':'Constant','bulk_constant':'Bulk + constant',
            'inverse_z_constant':'1/z + constant','bulk_z':'Bulk + z','bulk_constant_z':'Bulk + constant + z'}
    for row in result['fits']:
        axs[0].plot(lam,row['statistic']/row['gaussian_working_reference_threshold_95']/lam,label=labels[row['name']])
    axs[0].axhline(1,color='black',ls='--',lw=.8)
    axs[0].set(xlabel='Assumed covariance multiplier lambda',ylabel='Conditional T / Gaussian 95% threshold',title='Covariance sensitivity, not empirical calibration')
    axs[0].legend(fontsize=7)
    x=np.arange(6)
    axs[1].bar(x-.18,[r['raw_unit_dependent_condition'] for r in result['fits']],.36,label='Raw (unit dependent)',color='#89949e')
    axs[1].bar(x+.18,[r['scaled_condition'] for r in result['fits']],.36,label='Unit-column scaled',color='#176fa8')
    axs[1].set(yscale='log',ylabel='Whitened design condition number',title='Separate unit scaling from response overlap')
    axs[1].set_xticks(x,[labels[r['name']].replace(' + ','\n+ ') for r in result['fits']],fontsize=7)
    axs[1].legend(fontsize=8)
    for ext in ['png','pdf']:
        fig.savefig(outdir/f'h03_covariance_frontier.{ext}',dpi=180)
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path(__file__).parent)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    result=run(args.source)
    (args.out/'H03_REPLAY.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    figure(result,args.out)
    print(json.dumps({'fits':{r['name']:r['statistic'] for r in result['fits']},'overlap':result['overlap'],'output':str(args.out/'H03_REPLAY.json')},indent=2))
