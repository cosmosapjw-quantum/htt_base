"""Bound the mixed invariant beta.T (K-Qcal) beta on one joint ellipsoid.

The enclosing bounds are analytically global in exact arithmetic. Evaluation is
ordinary floating point with a roundoff guard, NOT formal interval arithmetic.
Local optimization supplies feasible witnesses only; branch-and-bound supplies
the enclosing endpoints and the explicitly reported remaining optimality gaps.
"""
from __future__ import annotations

import heapq
import itertools
import time
import numpy as np
from scipy.optimize import minimize


def standard_stf_basis():
    """R54/R58 order: xx-yy, xx+yy-2zz, xy, xz, yz; unit Frobenius norm."""
    s2, s6 = 1 / np.sqrt(2.), 1 / np.sqrt(6.)
    return np.array([np.diag([s2, -s2, 0]), np.diag([s6, s6, -2*s6]),
                     [[0,s2,0],[s2,0,0],[0,0,0]],
                     [[0,0,s2],[0,0,0],[s2,0,0]],
                     [[0,0,0],[0,0,s2],[0,s2,0]]])


class _Problem:
    def __init__(self, center8, cov8, stf_basis, cutoff, rho):
        h, C, E = np.asarray(center8, float), np.asarray(cov8, float), np.asarray(stf_basis, float)
        if h.shape != (8,) or C.shape != (8,8) or E.shape != (5,3,3):
            raise ValueError('Expected center8 (8,), cov8 (8,8), stf_basis (5,3,3).')
        if not all(np.isfinite(a).all() for a in (h,C,E)):
            raise ValueError('Inputs must be finite.')
        if not np.isfinite(cutoff) or cutoff < 0 or not np.isfinite(rho) or rho < 0:
            raise ValueError('cutoff and rho must be finite and nonnegative.')
        if np.any(np.diag(C) <= 0):
            raise ValueError('cov8 must be SPD.')
        scales = np.sqrt(np.diag(C))
        corr = C / scales[:,None] / scales[None,:]
        if not np.allclose(corr, corr.T, rtol=0, atol=1e-12):
            raise ValueError('cov8 must be symmetric.')
        C = (C+C.T)/2
        np.linalg.cholesky(C)
        if (not np.allclose(E, E.transpose(0,2,1), rtol=0, atol=1e-12)
                or not np.allclose(np.trace(E,axis1=1,axis2=2),0,rtol=0,atol=1e-12)
                or not np.allclose(np.einsum('aij,bij->ab',E,E),np.eye(5),rtol=0,atol=1e-12)):
            raise ValueError('stf_basis must be symmetric, trace-free and Frobenius orthonormal.')
        self.h,self.C,self.E,self.cutoff,self.rho=h,C,E,float(cutoff),float(rho)
        self.hb,self.hk=h[:3],h[3:]
        self.L=np.linalg.cholesky(C[:3,:3])
        self.B=np.sqrt(cutoff)*self.L
        self.R=np.linalg.solve(C[:3,:3],C[:3,3:]).T
        self.D=C[3:,3:]-self.R@C[:3,3:]
        self.D=(self.D+self.D.T)/2
        np.linalg.cholesky(self.D)
        self.A=self.R@self.B
        self.M=np.einsum('ji,ajk,kl->ail',self.B,E,self.B)
        self.gamma=np.sqrt(cutoff)
        self.a=np.sqrt(5.)*rho
        bm=np.linalg.norm(self.hb)+np.linalg.norm(self.B,2)
        km=np.linalg.norm(self.hk)+np.linalg.norm(self.A,2)
        self.scale=max(np.finfo(float).tiny,bm*bm*(km+self.gamma*np.sqrt(np.linalg.norm(self.D,2))+self.a))
        self.guard=256*np.finfo(float).eps*self.scale

    def evaluate(self,x,sign,gradient=False):
        b=self.hb+self.B@x
        k=self.hk+self.A@x
        v=np.einsum('i,aij,j->a',b,self.E,b)
        q=max(float(v@self.D@v),0.)
        u=max(1-float(x@x),0.)
        p=sign*float(v@k)+self.a*float(b@b)
        val=p+self.gamma*np.sqrt(u*q)
        if not gradient:
            return val
        J=2*np.einsum('i,aij,jk->ak',b,self.E,self.B)
        grad=sign*(J.T@k+self.A.T@v)+2*self.a*self.B.T@b
        if u>0 and q>0:
            grad+=self.gamma*(np.sqrt(u/q)*(J.T@self.D@v)-np.sqrt(q/u)*x)
        return val,grad

    def bound(self,lo,hi,sign):
        """Global upper enclosure on [lo,hi] intersect unit ball, exact-arithmetic formula."""
        nearest=np.maximum(lo,np.minimum(hi,0.))
        if nearest@nearest > 1+32*np.finfo(float).eps:
            return -np.inf
        m=(lo+hi)/2; d=(hi-lo)/2
        b=self.hb+self.B@m; k=self.hk+self.A@m
        v=np.einsum('i,aij,j->a',b,self.E,b)
        J=2*np.einsum('i,aij,jk->ak',b,self.E,self.B)
        v2=np.einsum('i,aij,j->a',d,np.abs(self.M),d)
        vabs=np.abs(v)+np.abs(J)@d+v2
        kabs=np.abs(k)+np.abs(self.A)@d
        babs=np.abs(b)+np.abs(self.B)@d
        umax=max(1-nearest@nearest,0.)
        qmax=max(float(vabs@np.abs(self.D)@vabs),0.)
        # Direct range bound remains valid at the ball boundary and beta=0.
        p0=sign*float(v@k)+self.a*float(b@b)
        pg=sign*(J.T@k+self.A.T@v)+2*self.a*self.B.T@b
        pQ=sign*(np.einsum('a,aij->ij',k,self.M)+(J.T@self.A+self.A.T@J)/2)+self.a*(self.B.T@self.B)
        pcubic=float(v2@(np.abs(self.A)@d))
        pupper=p0+_quad_upper(pg,pQ,d)+pcubic
        direct=pupper+self.gamma*np.sqrt(umax*qmax)
        q=float(v@self.D@v); u=1-float(m@m)
        best=direct
        if self.gamma>0 and q>0:
            # Young: sqrt(u*q) <= (t*u+q/t)/2 for any t>0.
            # At an interior center t=sqrt(q/u) gives value and gradient contact.
            t=np.sqrt(q/max(u,umax*.25,1e-30))
            U0=p0+self.gamma/2*(t*u+q/t)
            Ug=pg+self.gamma*(-t*m+(J.T@self.D@v)/t)
            UQ=pQ+self.gamma/(2*t)*(J.T@self.D@J+2*np.einsum('a,aij->ij',self.D@v,self.M))-self.gamma*t/2*np.eye(3)
            cubic=pcubic+self.gamma/t*float((np.abs(J)@d)@np.abs(self.D)@v2)
            quartic=self.gamma/(2*t)*float(v2@np.abs(self.D)@v2)
            young=U0+_quad_upper(Ug,UQ,d)+cubic+quartic
            best=min(best,young)
        return float(best+self.guard)

    def witness(self,x,sign):
        x=np.asarray(x,float).copy()
        norm=np.linalg.norm(x)
        if norm>1:
            x*=np.nextafter(1.,0.)/norm
        b=self.hb+self.B@x
        v=np.einsum('i,aij,j->a',b,self.E,b)
        q=max(float(v@self.D@v),0.)
        remainder=max(self.cutoff*(1-float(x@x)),0.)
        k=self.hk+self.A@x
        if q>0:
            k=k+sign*np.sqrt(remainder/q)*(self.D@v)
        Q=np.zeros((3,3))
        bn=float(b@b)
        if bn>0 and self.rho>0:
            # sign=+ seeks max phi, hence Qcal opposes STF(beta beta).
            stf=np.outer(b,b)-bn*np.eye(3)/3
            Q=-sign*np.sqrt(15/2)*self.rho*stf/np.linalg.norm(stf,'fro')
        K=np.einsum('a,aij->ij',k,self.E)
        z=np.r_[b,k]; dz=z-self.h
        mahal=float(dz@np.linalg.solve(self.C,dz))
        phi=float(b@(K-Q)@b)
        return {'beta':b.tolist(),'kappa':k.tolist(),'Qcal':Q.tolist(),
                'phi':phi,'ellipsoid_quadratic':mahal,'cutoff':self.cutoff,
                'calibration_frobenius':float(np.linalg.norm(Q,'fro')),
                'calibration_fullsky_rms':float(np.sqrt(2/15)*np.linalg.norm(Q,'fro')),
                'normalized_beta_coordinates':x.tolist()}


def _quad_upper(g,Q,d):
    """Upper bound of g.delta+delta.T Q delta for |delta_i|<=d_i."""
    Q=(Q+Q.T)/2
    ev=np.linalg.eigvalsh(Q)
    linear=float(np.abs(g)@d)
    eig=linear+max(float(ev[-1]),0.)*float(d@d)
    box=linear+float(np.maximum(np.diag(Q),0.)@(d*d))
    box+=float(d@np.abs(Q)@d-np.abs(np.diag(Q))@(d*d))
    best=min(eig,box)
    if ev[-1]<-32*np.finfo(float).eps*max(np.max(np.abs(ev)),np.finfo(float).tiny):
        unconstrained=float(-.25*g@np.linalg.solve(Q,g))
        best=min(best,unconstrained)
    return best


def _maximize(problem,sign,atol,max_nodes):
    t0=time.monotonic()
    scale=problem.scale
    starts=[np.zeros(3)]
    starts += [np.asarray(p,float)*.45 for p in itertools.product((-1,1),repeat=3)]
    starts += [s*.8*np.eye(3)[j] for j in range(3) for s in (-1,1)]
    best=-np.inf; bestx=None; local_success=0
    for x0 in starts:
        res=minimize(lambda x:-problem.evaluate(x,sign,True)[0]/scale,x0,
                     jac=lambda x:-problem.evaluate(x,sign,True)[1]/scale,
                     method='SLSQP',constraints={'type':'ineq','fun':lambda x:1-float(x@x),
                     'jac':lambda x:-2*x},options={'ftol':1e-12,'maxiter':250})
        x=np.asarray(res.x,float)
        if not np.isfinite(x).all():
            x=x0
        if np.linalg.norm(x)>1:
            x=x/np.linalg.norm(x)*np.nextafter(1.,0.)
        val=problem.evaluate(x,sign)
        if val>best:
            best,bestx=val,x.copy()
        local_success+=int(res.success)
    heap=[]; serial=0
    lo=np.full(3,-1.);hi=np.full(3,1.)
    upper=problem.bound(lo,hi,sign)
    heapq.heappush(heap,(-upper,serial,lo,hi)); generated=1; expanded=0
    pruned_ceiling=-np.inf
    while heap and -heap[0][0]>best+atol and expanded<max_nodes:
        negub,_,lo,hi=heapq.heappop(heap)
        if -negub<=best+atol:
            pruned_ceiling=max(pruned_ceiling,-negub)
            continue
        j=int(np.argmax(hi-lo)); mid=(lo[j]+hi[j])/2
        for half in (0,1):
            l=lo.copy();h=hi.copy()
            if half==0:h[j]=mid
            else:l[j]=mid
            m=(l+h)/2
            if m@m<=1:
                val=problem.evaluate(m,sign)
                if val>best:best,bestx=val,m.copy()
            ub=problem.bound(l,h,sign);generated+=1
            if ub>best+atol:
                serial+=1;heapq.heappush(heap,(-ub,serial,l,h))
            elif np.isfinite(ub):
                pruned_ceiling=max(pruned_ceiling,ub)
        expanded+=1
    witness=problem.witness(bestx,sign)
    # Recompute the feasible value from the lifted tensor and calibration witness.
    feasible=sign*witness['phi']
    enclosing=max(feasible,pruned_ceiling,-heap[0][0] if heap else -np.inf)
    gap=max(enclosing-feasible,0.)
    return {'feasible_maximum':feasible,'enclosing_upper':enclosing,'gap':gap,
            'converged':bool(gap<=atol+problem.guard),'status':'TOLERANCE_MET' if gap<=atol+problem.guard else 'NODE_CAP',
            'expanded_nodes':expanded,'generated_nodes':generated,'active_nodes':len(heap),
            'local_starts':len(starts),'local_successes':local_success,'witness':witness,
            'elapsed_seconds':time.monotonic()-t0}


def mixed_shear_range(center8,cov8,stf_basis,cutoff,rho=0.,atol=1e-10,max_nodes=100000):
    """Enclose global min/max phi, preserving joint beta-kappa covariance.

    Inputs z=(beta[3],kappa[5]); beta is dimensionless V/c. The caller owns
    the simultaneous ellipsoid cutoff (e.g. chi2.ppf(.95,11), even after
    projecting to 8 coordinates). rho is the full-sky RMS of n.Qcal.n.
    The domain is (z-center8).T inv(cov8) (z-center8)<=cutoff and independent
    ||Qcal||_F<=sqrt(15/2)*rho. All returned phi quantities are dimensionless.

    max_nodes is an expansion cap PER endpoint. A cap is a valid enclosing
    result with an explicit unresolved gap, never a sharpness assertion.
    """
    if not np.isfinite(atol) or atol<=0:
        raise ValueError('atol must be finite and strictly positive.')
    if isinstance(max_nodes,bool) or int(max_nodes)!=max_nodes or max_nodes<0:
        raise ValueError('max_nodes must be a nonnegative integer.')
    p=_Problem(center8,cov8,stf_basis,cutoff,rho)
    if cutoff==0:
        wlo=p.witness(np.zeros(3),-1);whi=p.witness(np.zeros(3),1)
        low,high=wlo['phi'],whi['phi']
        return {'minimum_bracket':[low,low],'maximum_bracket':[high,high],
                'outer_range':[low,high],'feasible_range':[low,high],
                'minimum_witness':wlo,'maximum_witness':whi,'max_gap':0.,
                'converged':True,'status':'TOLERANCE_MET','cutoff':float(cutoff),'rho':float(rho),
                'arithmetic':'FLOAT64_ANALYTIC_ENCLOSURE_NOT_FORMAL_INTERVAL_PROOF'}
    plus=_maximize(p,1,atol,int(max_nodes));minus=_maximize(p,-1,atol,int(max_nodes))
    return {'minimum_bracket':[-minus['enclosing_upper'],-minus['feasible_maximum']],
            'maximum_bracket':[plus['feasible_maximum'],plus['enclosing_upper']],
            'outer_range':[-minus['enclosing_upper'],plus['enclosing_upper']],
            'feasible_range':[-minus['feasible_maximum'],plus['feasible_maximum']],
            'minimum_witness':minus['witness'],'maximum_witness':plus['witness'],
            'max_gap':max(plus['gap'],minus['gap']),
            'converged':plus['converged'] and minus['converged'],
            'status':'TOLERANCE_MET' if plus['converged'] and minus['converged'] else 'NODE_CAP',
            'cutoff':float(cutoff),'rho':float(rho),'atol':float(atol),
            'max_nodes_per_endpoint':int(max_nodes),'endpoints':{'maximum':plus,'negative_minimum':minus},
            'arithmetic':'FLOAT64_ANALYTIC_ENCLOSURE_NOT_FORMAL_INTERVAL_PROOF',
            'roundoff_guard_per_bound':p.guard,'full_beta_kappa_cross_covariance':True}
