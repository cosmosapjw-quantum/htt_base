"""Finite spin-2 E/B pixel maps and masked simultaneous least-squares response.

This is a declared parity-covariant mathematical basis, not a qualified
Planck beam/component-separation transfer or a replacement for healpy.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.linalg import qr, solve_triangular


def _d_small(ell:int, mp:int,m:int, theta):
    """Wigner small-d d^ell_{mp,m}(theta), Condon-Shortley convention."""
    if not isinstance(ell,(int,np.integer)) or ell<0 or abs(mp)>ell or abs(m)>ell:
        raise ValueError('integer ell and allowed m,mp required')
    theta=np.asarray(theta,float)
    if not np.all(np.isfinite(theta)):raise ValueError('finite colatitude')
    c=np.cos(theta/2);s=np.sin(theta/2)
    fac=math.factorial
    coeff=math.sqrt(fac(ell+m)*fac(ell-m)*fac(ell+mp)*fac(ell-mp))
    out=np.zeros_like(theta,dtype=float)
    for k in range(2*ell+1):
        v=(ell+m-k,k,mp-m+k,ell-mp-k)
        if min(v)<0:continue
        a=2*ell+m-mp-2*k; b=mp-m+2*k
        if a<0 or b<0:continue
        out+=((-1)**(k-mp+m))*coeff/np.prod([fac(i) for i in v])*c**a*s**b
    return out


def spin_y(ell:int,m:int,s:int,theta,phi):
    """{}_sY_lm in the declared local polar frame, s=-2,0,+2."""
    if s not in (-2,0,2) or ell<abs(s):raise ValueError('allowed spins/ell')
    theta=np.asarray(theta,float);phi=np.asarray(phi,float)
    if theta.shape!=phi.shape or not np.isfinite(phi).all():raise ValueError('theta phi shape')
    return ((-1)**s)*np.sqrt((2*ell+1)/(4*np.pi))*_d_small(ell,m,-s,theta)*np.exp(1j*m*phi)


def spin2_shell(theta,phi,ell:int):
    """2*N x 2(2ell+1) joint real Q/U map for E/B coefficients.

    Column order: all E (m0,cos,sin), then all B (m0,cos,sin).
    Uses a_{+2}=-(a_E+i a_B), a_{-2}=-(a_E-i a_B).
    """
    if ell<2 or ell>14:raise ValueError('bounded finite mathematical shell 2..14')
    theta=np.asarray(theta,float);phi=np.asarray(phi,float)
    if theta.ndim!=1 or theta.shape!=phi.shape or not np.isfinite(theta).all() or not np.isfinite(phi).all() or np.any(theta<0) or np.any(theta>np.pi):raise ValueError('theta/phi')
    yp={m:spin_y(ell,m,2,theta,phi) for m in range(-ell,ell+1)}
    ym={m:spin_y(ell,m,-2,theta,phi) for m in range(-ell,ell+1)}
    columns=[]
    for kind in ('E','B'):
        for m in range(0,ell+1):
            for phase in (('m0',) if m==0 else ('cos','sin')):
                a=np.zeros(2*ell+1,dtype=complex)
                coef=1. if m==0 else (1/np.sqrt(2) if phase=='cos' else -1j/np.sqrt(2))
                a[m+ell]=coef
                if m>0:a[-m+ell]=((-1)**m)*np.conj(coef)
                mult_p=-1. if kind=='E' else -1j
                mult_m=-1. if kind=='E' else 1j
                p=sum(mult_p*a[j+ell]*yp[j] for j in range(-ell,ell+1))
                q=sum(mult_m*a[j+ell]*ym[j] for j in range(-ell,ell+1))
                Q=(p+q)/2; U=(p-q)/(2j)
                if max(float(np.max(abs(Q.imag))),float(np.max(abs(U.imag))))>3e-12:
                    raise ArithmeticError('Stokes Q/U not real: spin convention mismatch')
                columns.append(np.r_[Q.real,U.real])
    return np.column_stack(columns)


def block_design(theta,phi,l0=2,l1=5):
    if l0<2 or l1<l0:raise ValueError('ell bounds')
    return np.column_stack([spin2_shell(theta,phi,l) for l in range(l0,l1+1)])


def response_from_design(S_low,S_high,mask):
    """Finite Q/U joint OLS; no source-specific mask is ever synthesized here."""
    A=np.asarray(S_low,float);H=np.asarray(S_high,float);m=np.asarray(mask)
    if A.ndim!=2 or H.ndim!=2 or A.shape[0]!=H.shape[0] or A.shape[0]%2 or m.dtype!=bool or len(m)*2!=len(A) or m.sum()*2<=A.shape[1]:raise ValueError('paired Q/U rows and selected mask required')
    rows=np.r_[m,m];L=A[rows];G=H[rows]
    q,r=qr(L,mode='economic',check_finite=False)
    z=np.linalg.svd(r,compute_uv=False)
    if z[-1]<=0 or z[0]/z[-1]>1e6:raise ValueError('rank/condition failure')
    response=solve_triangular(r,q.T@G,check_finite=False)
    residual=float(np.max(np.abs(solve_triangular(r,q.T@L,check_finite=False)-np.eye(L.shape[1]))))
    if residual>1e-9:raise ValueError('low identity violation')
    return response,{'low_condition':float(z[0]/z[-1]),'low_identity_residual':residual,'selected_spatial_pixels':int(m.sum()),'retained_coefficients':A.shape[1]}
