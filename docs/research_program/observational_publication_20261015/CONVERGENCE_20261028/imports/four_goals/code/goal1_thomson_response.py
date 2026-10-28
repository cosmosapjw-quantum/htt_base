"""Finite Thomson detector/response union checks. No ODE or catalogue fit."""
from pathlib import Path
import json
import numpy as np
from numpy.polynomial.legendre import leggauss, legval
from scipy.special import sph_harm_y
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]

def sphere(k):
    z,w=leggauss(k);phi=np.arange(2*k)*np.pi/k
    zz,pp=np.meshgrid(z,phi,indexing='ij')
    n=np.stack([np.sqrt(1-zz**2)*np.cos(pp),np.sqrt(1-zz**2)*np.sin(pp),zz],-1).reshape(-1,3)
    return n,np.repeat(w,2*k)*np.pi/k

def cross(v):
    v=np.asarray(v);a=np.zeros(v.shape[:-1]+(3,3));a[...,0,1]=-v[...,2];a[...,0,2]=v[...,1]
    a[...,1,0]=v[...,2];a[...,1,2]=-v[...,0];a[...,2,0]=-v[...,1];a[...,2,1]=v[...,0]
    return a

S=[np.diag([1,-1,0])/np.sqrt(2),np.diag([1,1,-2])/np.sqrt(6)]
for i,j in [(0,1),(0,2),(1,2)]:
    a=np.zeros((3,3));a[i,j]=a[j,i]=1/np.sqrt(2);S.append(a)
S=np.array(S)
HB=np.array([np.eye(3)/np.sqrt(3),*S,*[1j*cross(e)/np.sqrt(2) for e in np.eye(3)]])

def main():
    n,w=sphere(22);P=np.eye(3)-np.einsum('ni,nj->nij',n,n);alpha=3/(8*np.pi)
    Sn=np.einsum('aij,nj->nai',S,n);snn=np.einsum('ni,nai->na',n,Sn)
    LK=2*np.einsum('nai,nbi->nab',Sn,Sn)-np.einsum('na,nb->nab',snn,snn)
    moment=lambda F:np.einsum('n,nij->ij',w,F)
    # Use the invariant real Hilbert--Schmidt pairing explicitly.
    coords=lambda M:np.array([np.trace(b.conj().T@M).real for b in HB])
    L=lambda I:np.einsum('n,n,nab->ab',w,I,LK)
    gain=lambda M:alpha*np.einsum('nij,jk,nkl->nil',P,M,P)
    packL=lambda A:np.array([A[i,j]*(1 if i==j else np.sqrt(2)) for i in range(5) for j in range(i,5)])
    K=np.column_stack([coords(moment(gain(b))) for b in HB])
    spectrum=np.linalg.eigvalsh(K)
    expected=np.array([.5]*3+[.7]*5+[1.])
    spec_error=np.max(abs(spectrum-expected))

    # Positive unpolarized skies with equal Thomson response but unequal MES L.
    p4=legval(n[:,2],[0,0,0,0,1]);amp=.6
    Iplus=1+amp*p4;Iminus=1-amp*p4
    Mplus=moment(Iplus[:,None,None]*P/2);Mminus=moment(Iminus[:,None,None]*P/2)
    Lplus=L(Iplus);Lminus=L(Iminus);Mdiff=np.linalg.norm(Mplus-Mminus)
    Gdiff=np.max(np.abs(gain(Mplus)-gain(Mminus)))
    Ldiff=np.linalg.norm(Lplus-Lminus,2)

    # Exact real-linear carrier for the pair (all Thomson gain, all shear response).
    theta=np.arccos(n[:,2]);phi=np.arctan2(n[:,1],n[:,0]);scalar=[]
    for ell in [0,2,4]:
        scalar.append(sph_harm_y(ell,0,theta,phi).real)
        for m in range(1,ell+1):
            y=sph_harm_y(ell,m,theta,phi)
            scalar.extend([np.sqrt(2)*y.real,np.sqrt(2)*y.imag])
    columns=[]
    for I in scalar:columns.append(np.r_[coords(moment(I[:,None,None]*P/2)),packL(L(I))])
    pol_fields=[]
    for s in S:
        psp=np.einsum('nij,jk,nkl->nil',P,s,P)
        field=psp-.5*P*np.einsum('nii->n',psp)[:,None,None]
        pol_fields.append(field);columns.append(np.r_[coords(moment(field)),np.zeros(15)])
    for j in range(3):
        field=.5j*n[:,j,None,None]*cross(n)
        columns.append(np.r_[coords(moment(field)),np.zeros(15)])
    response=np.column_stack(columns);sv=np.linalg.svd(response,compute_uv=False)
    rank=int(np.linalg.matrix_rank(response,tol=1e-10))
    shear_rank=int(np.linalg.matrix_rank(response[9:,:15],tol=1e-10))

    # Detector effect responses: trace-only loses the imaginary antisymmetric part.
    d=np.array([[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,0,1],[0,1,1]],float)
    d/=np.linalg.norm(d,axis=1)[:,None]
    intensity=[]
    for q in d:
        p=np.eye(3)-np.outer(q,q);intensity.append(coords(alpha*p))
    linear=[];full=[]
    for j in range(3):
        e1=np.eye(3)[(j+1)%3];e2=np.eye(3)[(j+2)%3]
        for v in [e1,e2,(e1+e2)/np.sqrt(2)]:
            row=coords(alpha*np.outer(v,v.conj()));linear.append(row);full.append(row)
        v=(e1+1j*e2)/np.sqrt(2);full.append(coords(alpha*np.outer(v,v.conj())))
    det_ranks={'intensity_six_directions':int(np.linalg.matrix_rank(intensity)),
               'linear_effects_three_screens':int(np.linalg.matrix_rank(linear)),
               'full_Stokes_effects_three_screens':int(np.linalg.matrix_rank(full))}

    # Polarized collision quadrupole and resulting finite inverse bias.
    pol_amp=.12;F=P/2+pol_amp*pol_fields[0]
    M=moment(F);I=np.trace(F,axis1=1,axis2=2).real
    pi=np.einsum('n,n,nij->ij',w,I,np.einsum('ni,nj->nij',n,n)-np.eye(3)/3)
    sp=M.real-np.trace(M).real*np.eye(3)/3
    coll_I=np.trace(gain(M)-F,axis1=1,axis2=2).real
    cp=np.einsum('n,n,nij->ij',w,coll_I,np.einsum('ni,nj->nij',n,n)-np.eye(3)/3)
    cp_expected=-pi-sp/5
    cp_err=np.linalg.norm(cp-cp_expected)
    pmin=float(np.min(np.linalg.eigvalsh(F)))
    polarized_moment=sp+pi/2
    gamma=.4;LL=L(I);B=gamma*np.array([np.sum(s*polarized_moment) for s in S])/5
    bias=np.linalg.solve(LL,B);bias_bound=gamma*np.linalg.norm(polarized_moment)/(5*np.linalg.eigvalsh(LL)[0])
    # The transverse field has one structural zero eigenvalue at each direction.
    screen_min=float(np.min(np.linalg.eigvalsh(F)[:,1]))
    results={'schema':'htt.goal1_thomson_response/1','scope':'Cold-electron fixed-frame one-scatter gain and instantaneous shear response; no ODE and no observed-sky fit',
      'sphere_nodes':len(n),'gain_spectrum':spectrum.tolist(),'spectrum_max_error':float(spec_error),
      'equal_gain_different_shear':{'amplitude':amp,'minimum_intensity':float(min(Iplus.min(),Iminus.min())),
       'analytic_global_intensity_lower_bound':1-amp,'minimum_intensity_scope':'Quadrature grid; analytic global bound is separately recorded.',
       'M_difference':float(Mdiff),'pointwise_gain_max_difference':float(Gdiff),'shear_operator_difference_norm':float(Ldiff),
       'Lplus_eigenvalues':np.linalg.eigvalsh(Lplus).tolist(),'Lminus_eigenvalues':np.linalg.eigvalsh(Lminus).tolist()},
      'joint_response':{'input_components':23,'output_rows':24,'rank':rank,'minimum_singular_value':float(sv[-1]),'shear_scalar_rank':shear_rank,'singular_values':sv.tolist()},
      'detector_ranks':det_ranks,
      'polarized_collision':{'gamma_units':'inverse time; gamma=.4 in declared toy time unit','collision_quadrupole_error_at_gamma1':float(cp_err),'positive_screen_min_eigenvalue':screen_min,
       'structural_full_matrix_min_eigenvalue':pmin,'omitted_polarization_shear_bias_norm':float(np.linalg.norm(bias)),'bound':float(bias_bound)},
      'validation':{'all_pass':bool(spec_error<1e-12 and Mdiff<1e-12 and Gdiff<1e-12 and Ldiff>.1 and rank==23 and shear_rank==15 and cp_err<1e-12 and screen_min>0 and np.linalg.norm(bias)<=bias_bound+1e-12)}}
    assert results['validation']['all_pass'],results
    (ROOT/'lanes/GOAL1_NUMERICS.json').write_text(json.dumps(results,indent=2)+'\n')
    fig,ax=plt.subplots(1,3,figsize=(13,3.7),layout='constrained')
    z=np.linspace(-1,1,400);pp=legval(z,[0,0,0,0,1]);ax[0].plot(z,1+amp*pp,label=r'$I_+$');ax[0].plot(z,1-amp*pp,label=r'$I_-$')
    ax[0].set(xlabel=r'$\cos\theta$',ylabel='Brightness (toy units)',title='Distinct positive skies, identical gain');ax[0].legend()
    ax[1].plot(np.arange(1,6),np.linalg.eigvalsh(Lplus),'o-',label=r'$\mathcal{L}_{I_+}$');ax[1].plot(np.arange(1,6),np.linalg.eigvalsh(Lminus),'s--',label=r'$\mathcal{L}_{I_-}$')
    ax[1].set(xlabel='Sorted eigenmode',ylabel='Shear-response eigenvalue',title='Different kinematic responses');ax[1].legend()
    ax[2].bar(['Intensity','Linear\npolarizers','Full Stokes'],list(det_ranks.values()),color=['#5c84a2','#5c84a2','#c2734a'])
    ax[2].set(ylabel='Identifiable components of M',ylim=(0,10),title='Actual channels set the rank')
    fig.savefig(ROOT/'figures/goal1_thomson_carrier.png',dpi=190);fig.savefig(ROOT/'figures/goal1_thomson_carrier.pdf');plt.close(fig)
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
