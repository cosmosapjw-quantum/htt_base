"""Finite, geometry-only SO(3) profile bounds for deterministic T/E/B skies.

No observational covariance, priors, likelihood, or family identification.
Input ordering is full signed-m, starting at ell=ell_min; shared rotations.
"""
import numpy as np


def rotation_factory(ell_min,ell_max):
    if type(ell_min) is not int or type(ell_max) is not int or not 0<=ell_min<=ell_max:
        raise ValueError("invalid band")
    blocks=[]
    for l in range(ell_min,ell_max+1):
        m=np.arange(-l,l+1)
        jp=np.diag(np.sqrt(l*(l+1)-m[:-1]*(m[:-1]+1)),k=-1)
        jy=(jp-jp.T)/(2j)
        w,v=np.linalg.eigh(jy)
        blocks.append((l,m,w,v))
    def rotate(a,angles):
        x=np.asarray(a,dtype=complex)
        if x.shape[-2:]!=((ell_max+1)**2-ell_min**2,3) or not np.isfinite(x).all():
            raise ValueError("invalid signed TEB shape")
        angles=np.asarray(angles,dtype=float)
        if angles.shape!=(3,) or not np.isfinite(angles).all():
            raise ValueError("invalid Euler angles")
        alpha,beta,gamma=angles
        y=np.empty_like(x)
        for l,m,w,v in blocks:
            d=(v*np.exp(-1j*beta*w))@v.conj().T
            D=np.exp(-1j*alpha*m)[:,None]*d*np.exp(-1j*gamma*m)[None,:]
            s=slice(l*l-ell_min**2,(l+1)**2-ell_min**2)
            y[...,s,:]=D@x[...,s,:]
        return y
    return rotate


def profile_bounds(skies,ell_min,ell_max,seed=119,samples=(64,256)):
    """Nested Haar rotation trials and inverse trials; distances are brackets.

    samples counts random rotations, with identity and inverse also evaluated.
    """
    x=np.asarray(skies,dtype=complex)
    if x.ndim!=3 or x.shape[1:]!=((ell_max+1)**2-ell_min**2,3) or not np.isfinite(x).all():
        raise ValueError("invalid finite sky array")
    if not samples or any(type(n) is not int or n<1 for n in samples) or tuple(sorted(set(samples)))!=tuple(samples):
        raise ValueError("sample counts must be strictly increasing positive integers")
    norms=np.linalg.norm(x.reshape(len(x),-1),axis=1)
    if np.any(norms<=0) or not np.isfinite(norms).all():
        raise ValueError("zero/nonfinite sky cannot be shape normalized")
    x=x/norms[:,None,None]
    flat=x.reshape(len(x),-1)
    blocks=np.concatenate([np.linalg.norm(x[:,l*l-ell_min**2:(l+1)**2-ell_min**2,:],axis=1)
        for l in range(ell_min,ell_max+1)],axis=1)
    def dist(c):
        return np.sqrt(np.maximum(0,1-np.clip(c,0,1)**2))
    lower=dist(blocks@blocks.T)
    best=np.real(flat.conj()@flat.T)
    identity=dist(best)
    rotate=rotation_factory(ell_min,ell_max)
    rng=np.random.default_rng(seed)
    results={}
    for n in range(1,max(samples)+1):
        angles=(rng.uniform(0,2*np.pi),np.arccos(rng.uniform(-1,1)),rng.uniform(0,2*np.pi))
        y=rotate(x,angles).reshape(len(x),-1)
        corr=np.real(flat.conj()@y.T)
        # The transpose represents the inverse rotation, so the bracket is symmetric.
        best=np.maximum(best,np.maximum(corr,corr.T))
        if n in samples:
            upper=dist(best)
            if np.any(lower>upper+2e-7):
                raise ArithmeticError("rotation bracket violated")
            results[n]=upper
    return lower,identity,results
