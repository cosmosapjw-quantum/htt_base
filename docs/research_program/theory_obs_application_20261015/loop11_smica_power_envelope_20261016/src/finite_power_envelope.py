"""Exact finite masked-OLS covariance and ellipsoidal power envelopes.

Applies ONLY to a supplied, SHA-256 source-bound Planck processing-geometry K
matrix for ell 6..16. Real harmonic coefficients use orthonormal real
Y_l0, sqrt(2)Re Y_lm, sqrt(2)Im Y_lm layout. No measured C_ell, source
sky realization covariance, global beta/shear or physical EGS inputs are inferred.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Mapping

import numpy as np

SOURCE_SHA256 = 'a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007'
ELLS = tuple(range(6,17))

class EnvelopeInputError(ValueError):
    pass


def locate_source(stage_dir: str|Path) -> Path:
    """Resolve the exact archived source or read-only existing Loop9 source.

    For an isolated archive, stage_dir/source/ is preferred. For a staged
    GitHub-only checkout that deliberately does not commit binaries, use the
    owner's existing Loop9 source; its SHA is still checked by source_operator.
    No network, copying, generated substitute or arbitrary filename search.
    """
    stage=Path(stage_dir).resolve()
    embedded=stage/'source/baseline_response_matrices.npz'
    if embedded.is_file():
        return embedded
    if len(stage.parents)>3:
        repo=stage.parents[3]
        prior=repo/'docs/research_program/theory_obs_application_20261015/loop9_smica_finite_response/results/response_v1/baseline_response_matrices.npz'
        if prior.is_file():
            return prior
    raise EnvelopeInputError('source-bound PR536 response not found in archive or original Loop9 checkout')


def source_operator(path: str|Path, *, expected_sha256: str=SOURCE_SHA256) -> np.ndarray:
    """Read-only source authentication and 32x253 retained-multipole lock."""
    p = Path(path)
    if not p.is_file():
        raise EnvelopeInputError(f'original Planck source operator unavailable: {p}')
    observed = sha256(p.read_bytes()).hexdigest()
    if observed != expected_sha256:
        raise EnvelopeInputError(f'source identity mismatch, got {observed}')
    with np.load(p, allow_pickle=False) as f:
        required={'K_full_36x253','K_ell23_12x253','K_ell2to5_32x253'}
        if not required.issubset(f.files):
            raise EnvelopeInputError('missing original operator partitions')
        full=np.asarray(f['K_full_36x253'], dtype=np.float64)
        q=np.asarray(f['K_ell23_12x253'],dtype=np.float64)
        k=np.asarray(f['K_ell2to5_32x253'],dtype=np.float64)
    if (full.shape != (36,253) or k.shape != (32,253) or q.shape != (12,253)
        or not np.isfinite(full).all() or not np.isfinite(k).all()
        or not np.isfinite(q).all()):
        raise EnvelopeInputError('invalid operator shapes/nonfinite values')
    if not np.array_equal(k,full[4:36]) or not np.array_equal(q,full[4:16]):
        raise EnvelopeInputError('partition coordinates do not equal original full response')
    return k.copy()


def shell_slice(ell: int) -> slice:
    if type(ell) is not int or ell not in ELLS:
        raise EnvelopeInputError('shell ell must be original integer in 6..16')
    return slice(ell*ell-36,(ell+1)**2-36)


def _operator(k: np.ndarray) -> np.ndarray:
    a=np.asarray(k,dtype=np.float64)
    if a.shape not in {(12,253),(32,253),(36,253)} or not np.isfinite(a).all():
        raise EnvelopeInputError('finite original 12/32/36 by 253 operator needed')
    return a


def _shell_values(params: Mapping[int,float],name:str,*,allow_zero:bool=True)->np.ndarray:
    if not isinstance(params,Mapping) or set(params.keys())!=set(ELLS):
        raise EnvelopeInputError(f'{name}: require all ell6..16 explicitly')
    nums=[]
    for ell in ELLS:
        obj=params[ell]
        if isinstance(obj,(bool,np.bool_)) or np.iscomplexobj(obj):
            raise EnvelopeInputError(f'{name}[{ell}] must be real scalar')
        try: x=float(obj)
        except (TypeError,ValueError,OverflowError) as exc:
            raise EnvelopeInputError(f'{name}[{ell}] invalid') from exc
        if not np.isfinite(x) or x<0 or (not allow_zero and x==0):
            raise EnvelopeInputError(f'{name}[{ell}] finite nonnegative required')
        nums.append(x)
    return np.asarray(nums,dtype=float)


def shell_gram(k:np.ndarray)->dict[int,np.ndarray]:
    op=_operator(k)
    return {ell:(op[:,shell_slice(ell)] @ op[:,shell_slice(ell)].T) for ell in ELLS}


def independent_power_covariance(k: np.ndarray,power: Mapping[int,float])->np.ndarray:
    """EXACT K diag(C_ell I_{2ell+1}) K^T for explicitly supplied C_ell.

    C_ell is a per-real-coefficient variance, not automatically a measured
    Planck Cl; correlations across ell and processing models are excluded.
    """
    c=_shell_values(power,'C_ell')
    acc=np.zeros((_operator(k).shape[0],)*2,dtype=float)
    for value,gram in zip(c,shell_gram(k).values()):
        acc+=value*gram
    acc=(acc+acc.T)/2
    if not np.isfinite(acc).all() or np.linalg.eigvalsh(acc)[0]<-1e-10*max(1,float(np.linalg.norm(acc,2))):
        raise EnvelopeInputError('non PSD covariance from numerical calculation')
    return acc


def sharp_ellipsoid_bound(k:np.ndarray,radii: Mapping[int,float])->dict:
    r=_shell_values(radii,'radii')
    op=_operator(k)
    # Positive semidefinite 32-by-32, no 253-by-253 covariance allocation.
    G=np.zeros((op.shape[0],op.shape[0]),dtype=float)
    for v,mat in zip(r,shell_gram(op).values()):
        G+=(v*v)*mat
    G=(G+G.T)/2
    eig,U=np.linalg.eigh(G)
    lam=float(eig[-1]);u=U[:,-1]
    if lam < -1e-11:
        raise EnvelopeInputError('non PSD ellipsoid image Gram')
    lam=max(lam,0.)
    a=np.zeros(253,dtype=float)
    if lam>0:
        for ell,v in zip(ELLS,r):
            a[shell_slice(ell)]=(v*v)*(op[:,shell_slice(ell)].T@u)/np.sqrt(lam)
        value=sum(float(np.dot(a[shell_slice(ell)],a[shell_slice(ell)])/(v*v)) for ell,v in zip(ELLS,r) if v>0)
        norm=float(np.linalg.norm(op@a))
    else:
        value=0.0;norm=0.0
    sharp=float(np.sqrt(lam))
    if (lam>0 and (not np.isclose(value,1.,atol=1e-10,rtol=1e-10)
                    or not np.isclose(norm,sharp,atol=1e-10,rtol=1e-10))):
        raise EnvelopeInputError('constructed ellipsoid maximizer did not saturate')
    return {'sharp_bound':sharp,'gram':G,'witness':a,
            'ellipsoid_norm_of_witness':value,'achieved_leakage':norm,
            'leading_left_direction':u,
            'contract':'sum_l norm(a_l)^2/R_l^2 <= 1, with zero-radius shells fixed to zero'}


def shared_mode_correlated_covariance(k:np.ndarray,power: Mapping[int,float],rho:float)->np.ndarray:
    """Manufactured cross-ell coupling with exact C_ell I within each shell.

    a_{ell,j} = sqrt(C_ell)(sqrt(rho) z_j + sqrt(1-rho) xi_{ell,j}).
    Index j is an explicit *coordinate-coupling model*, not a physical sky
    isotropy claim. Same-shell coefficients have covariance C_ell I.
    """
    c=_shell_values(power,'C_ell')
    if isinstance(rho,(bool,np.bool_)) or not isinstance(rho,(int,float,np.floating,np.integer)) or not np.isfinite(rho) or rho<0 or rho>1:
        raise EnvelopeInputError('rho in [0,1] required')
    op=_operator(k)
    base=independent_power_covariance(op,power)
    mat=np.zeros((op.shape[0],max(2*ell+1 for ell in ELLS)),dtype=float)
    for ell,var in zip(ELLS,c):
        cols=2*ell+1
        mat[:,:cols]+=np.sqrt(var)*op[:,shell_slice(ell)]
    ans=(1-rho)*base+rho*(mat@mat.T)
    return (ans+ans.T)/2


def correlation_agnostic_bound(k:np.ndarray,power:Mapping[int,float])->float:
    """Upper bound on sqrt(top output variance), arbitrary cross-ell covariance.

    The diagonal ell blocks are assumed to be C_ell I; all cross-ell blocks
    can be arbitrary subject to global PSD. Minkowski on each output u.
    """
    c=_shell_values(power,'C_ell')
    op=_operator(k)
    return float(sum(np.sqrt(v)*np.linalg.norm(op[:,shell_slice(ell)],2) for ell,v in zip(ELLS,c)))


def leak_trace_fractions(k:np.ndarray,power: Mapping[int,float])->dict[int,float]:
    c=_shell_values(power,'C_ell');grams=shell_gram(k)
    values=np.array([float(c[i]*np.trace(grams[ell])) for i,ell in enumerate(ELLS)])
    if not np.isfinite(values).all():
        raise EnvelopeInputError('nonfinite output trace')
    total=float(values.sum())
    return {ell:float(v/total) if total>0 else 0.0 for ell,v in zip(ELLS,values)}


def default_templates()->dict[str,dict[int,float]]:
    return {
        'WHITE_UNIT_VARIANCE_EXPLICIT':{ell:1. for ell in ELLS},
        'RED_Cl_PROP_1_OVER_ELL_ELLPLUS1_NORMALIZED_AT_ELL6':{ell:42./(ell*(ell+1)) for ell in ELLS},
        'BLUE_Cl_PROP_ELL_ELLPLUS1_NORMALIZED_AT_ELL6':{ell:ell*(ell+1)/42. for ell in ELLS}
    }
