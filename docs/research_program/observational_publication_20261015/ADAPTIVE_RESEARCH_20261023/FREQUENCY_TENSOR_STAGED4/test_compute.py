"""Small synthetic controls; separate from native production results."""
import math,sys
import numpy as np
import healpy as hp
from scipy.special import sph_harm_y
from compute import canonical,canonical_grid,decode,low_sum,spin_y,SQ2


def alms_for_basis(j,amp=1e-5):
    e=np.zeros(hp.Alm.getsize(3),complex);b=e.copy()
    channel=0 if j<12 else 1;k=j%12;l=2 if k<5 else 3;v=k if l==2 else k-5
    m=0 if v==0 else (v+1)//2
    idx=hp.Alm.getidx(3,l,m)
    z=amp if v==0 else (amp/SQ2 if v%2==1 else -1j*amp/SQ2)
    (e if channel==0 else b)[idx]=z
    return e,b


def run():
    nside=16;n=12*nside*nside;idx=np.arange(n)
    theta,phi=hp.pix2ang(nside,idx)
    c=np.cos(theta/2);s=np.sin(theta/2)
    for l in (2,3):
        for m in range(l+1):
            err=np.max(np.abs(spin_y(l,m,0,c,s,np.exp(1j*m*phi))-sph_harm_y(l,m,theta,phi)))
            assert err<1e-14,(l,m,err)
    rng=np.random.default_rng(764)
    mask=rng.random(n)>0.17
    maxerr=0.;maxpar=0.;maxred=0.
    antip=hp.ang2pix(nside,math.pi-theta,np.mod(phi+math.pi,2*math.pi))
    assert np.array_equal(antip[antip],idx)
    for j in range(24):
        e,b=alms_for_basis(j)
        q,u=hp.alm2map_spin([e,b],nside=nside,spin=2,lmax=3,mmax=3)
        qm=np.where(mask,q,0.);um=np.where(mask,u,0.)
        he,hb=hp.map2alm_spin([qm,um],spin=2,lmax=3,mmax=3)
        ie,ib,ae,ab=low_sum(qm,um,nside,chunk=397)
        x=canonical(he,hb);y=canonical_grid(ie,ib)
        maxerr=max(maxerr,float(np.max(np.abs(x-y))))
        maxred=max(maxred,float(np.max(np.abs(y-canonical_grid(ae,ab)))))
        assert np.allclose(x,y,rtol=1e-9,atol=1e-12),(j,x,y)
        # Joint parity of field and support: E has (-1)^l, B has (-1)^(l+1).
        pq=qm[antip];pu=-um[antip]
        pe,pb=hp.map2alm_spin([pq,pu],spin=2,lmax=3,mmax=3)
        xc=canonical(pe,pb);pred=x.copy()
        pred[0:5]*=1;pred[5:12]*=-1;pred[12:17]*=-1;pred[17:24]*=1
        maxpar=max(maxpar,float(np.max(np.abs(xc-pred))))
        assert np.allclose(xc,pred,rtol=1e-8,atol=1e-12),(j,xc,pred)
    # Decoder sign, inverse canonical scale, complete STF symmetry and trace.
    v=np.zeros(24);v[2]=-SQ2
    qyz=decode(v)[0][1,2]
    assert np.isclose(qyz,math.sqrt(15/(8*math.pi)),rtol=0,atol=1e-15),qyz
    for j in range(24):
        v=np.zeros(24);v[j]=1.;d=decode(v)
        for t in d:
            assert np.allclose(t,np.swapaxes(t,0,1),rtol=0,atol=1e-14)
            assert np.max(np.abs(np.trace(t,axis1=0,axis2=1)))<1e-14
    sent=np.float32(-1.63750e30)
    q=np.asarray([1.,float(sent),np.nan,np.inf],dtype=np.float32)
    u=np.asarray([2.,3.,4.,5.],dtype=np.float32)
    valid=np.isfinite(q)&np.isfinite(u)&(q!=sent)&(u!=sent)
    assert valid.tolist()==[True,False,False,False]
    cleaned=np.where(valid,q,0).astype(np.float64)
    assert np.array_equal(cleaned,[1,0,0,0]) and np.isfinite(cleaned).all()
    for nside in (16,1024,2048):
        native=np.asarray([0,1,12*nside*nside//2,12*nside*nside-1])
        assert np.array_equal(hp.ring2nest(nside,hp.nest2ring(nside,native)),native)
    return {'synthetic_nside':16,'basis_cases':24,'max_independent_error_K_CMB':maxerr,
            'max_reduction_error_K_CMB':maxred,'max_joint_parity_error_K_CMB':maxpar,
            'decoder_a21_i_Qyz':qyz,'sentinel_and_nonfinite':'PASS','permutation':'PASS'}

if __name__=='__main__':
    import json
    print(json.dumps(run(),sort_keys=True))
