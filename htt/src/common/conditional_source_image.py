"""Conditional finite source image; no MES anchor, likelihood or physical bridge.

The Decimal arithmetic and dyadic support cover are reused from the accepted R7
prototype SHA256 c6bdf504339b36ce0fdbbe33c25d715967e9021ee12629aa8fd50a4975e97951.
They enclose the serialized binary64 L, A and directions, not preprocessing
uncertainty. Only the validated BoxSourceImage facade is the supported API.
"""
from dataclasses import dataclass
from decimal import Decimal, Context, ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_EVEN
import itertools
import numpy as np
from scipy.optimize import minimize

C_KMS = 299792.458

LO=Context(prec=42,rounding=ROUND_FLOOR)
HI=Context(prec=42,rounding=ROUND_CEILING)
NEAR=Context(prec=42,rounding=ROUND_HALF_EVEN)
ZERO=(Decimal(0),Decimal(0)); ONE=(Decimal(1),Decimal(1))

def point(x):
    d=Decimal.from_float(float(x)); return d,d

def add(x,y): return LO.add(x[0],y[0]),HI.add(x[1],y[1])
def neg(x): return x[1].copy_negate(),x[0].copy_negate()
def sub(x,y): return add(x,neg(y))
def mul(x,y):
    return min(LO.multiply(a,b) for a in x for b in y),max(HI.multiply(a,b) for a in x for b in y)
def div(x,y):
    if y[0]<=0<=y[1]: raise ValueError('interval division crosses zero')
    return min(LO.divide(a,b) for a in x for b in y),max(HI.divide(a,b) for a in x for b in y)
def logi(x):
    if x[0]<=0: raise ValueError('nonpositive logarithm domain')
    # Decimal.ln is correctly rounded, half-even. Its adjacent values enclose
    # the exact endpoint logarithms, including when the value is exactly 0.
    return NEAR.next_minus(NEAR.ln(x[0])),NEAR.next_plus(NEAR.ln(x[1]))
def sumi(xs):
    r=ZERO
    for x in xs:r=add(r,x)
    return r
def abshi(x):return max(x[0].copy_abs(),x[1].copy_abs())
def upfloat(x):return float(np.nextafter(float(x),np.inf))
def downfloat(x):return float(np.nextafter(float(x),-np.inf))

def interval_coefficients(L,u):
    return [sumi(mul(point(u[k]),point(L[k,i])) for k in range(len(u))) for i in range(L.shape[1])]

def exact_value_interval(A,dual,xi):
    return sumi(mul(a,neg(logi(sub(ONE,sumi(mul(point(v),point(x)) for v,x in zip(row,xi)))))) for row,a in zip(A,dual))

def node_bounds_interval(A,duals,center,halfwidth):
    """Enclose max on this node by a one-sided Taylor remainder.

    For t=(A delta)/(1-A center), 0 <= -log(1-t)-t
    <= -log(1-rho)-rho; negative dual weights cannot increase the remainder.
    The box-cover maximum is a support bound even for a nonconvex image.
    """
    cv=[point(x) for x in center];hv=[point(x) for x in halfwidth]
    row_f=[];row_inv=[];row_rem=[];row_A=[]
    for row in A:
        av=[point(x) for x in row];row_A.append(av)
        den=sub(ONE,sumi(mul(a,c) for a,c in zip(av,cv)))
        if den[0]<=0:raise ValueError('node center outside log domain')
        radius=sumi(mul(point(abs(x)),h) for x,h in zip(row,hv))
        rho=div(radius,den)
        if rho[1]>=1:raise ValueError('node extends outside log domain')
        row_f.append(neg(logi(den)))
        row_inv.append(div(ONE,den))
        # b(rho) is increasing for rho >= 0. Use upper endpoint as exact input.
        ru=(rho[1],rho[1])
        row_rem.append(sub(neg(logi(sub(ONE,ru))),ru)[1])
    result=[]
    for dual in duals:
        value=sumi(mul(a,f) for a,f in zip(dual,row_f))
        gradient=[sumi(mul(mul(a,ra[j]),inv) for a,ra,inv in zip(dual,row_A,row_inv)) for j in range(A.shape[1])]
        # Avoid Python Decimal sum default-context rounding on the upper bound.
        linear=Decimal(0)
        for g,h in zip(gradient,hv):linear=HI.add(linear,HI.multiply(abshi(g),h[1]))
        rem=Decimal(0)
        for a,b in zip(dual,row_rem):rem=HI.add(rem,HI.multiply(max(a[1],Decimal(0)),b))
        result.append(HI.add(HI.add(value[1],linear),rem))
    return result

def phi(L,A,xi):
    t=A@xi
    if np.any(t>=1):raise ValueError('outside logarithm domain')
    return -L@np.log1p(-t)

def float_node_upper(L,A,u,c,h):
    den=1-A@c;rho=np.abs(A)@h/den
    if min(den)<=0 or max(rho)>=1:raise ValueError('node outside logarithm domain')
    dual=u@L
    grad=(dual/den)@A
    return u@phi(L,A,c)+np.abs(grad)@h+np.maximum(dual,0)@(-np.log1p(-rho)-rho)

def partition(depth):
    """Deterministic dyadic cover. Depth 8 gives 4**4 = 256 boxes."""
    nodes=[(np.zeros(4),np.ones(4))]
    for level in range(depth):
        j=level%4;new=[]
        for c,h in nodes:
            hh=h.copy();hh[j]*=.5
            for sign in (-1,1):
                cc=c.copy();cc[j]+=sign*hh[j];new.append((cc,hh.copy()))
        nodes=new
    return nodes

def support_records(L,A,directions,labels,depth):
    corners=np.array(list(itertools.product((-1.,1.),repeat=4)))
    duals=[interval_coefficients(L,u) for u in directions]
    records=[]
    for u,label,dual in zip(directions,labels,duals):
        g=(u@L)@A
        candidates=[np.zeros(4),*corners,np.sign(g)]
        values=[u@phi(L,A,x) for x in candidates]
        starts=[candidates[i] for i in np.argsort(values)[-3:]]+[np.zeros(4)]
        statuses=[]
        for start in starts:
            res=minimize(lambda x:-u@phi(L,A,x),start,jac=lambda x:-((u@L)/(1-A@x))@A,
                         bounds=[(-1.,1.)]*4,method='SLSQP',options={'ftol':1e-14,'maxiter':200})
            # Clipping produces an explicitly feasible witness even if the
            # optimizer's stopping criterion fails or it crosses a boundary.
            candidates.append(np.clip(res.x,-1,1));values.append(u@phi(L,A,candidates[-1]))
            statuses.append({'success':bool(res.success),'status':int(res.status),'message':str(res.message)})
        best=candidates[int(np.argmax(values))]
        iv=exact_value_interval(A,dual,best)
        if iv[0]<0:
            # Phi(0)=0 algebraically. Keep the lower-bound witness consistent.
            best=np.zeros(4);iv=ZERO
        rowrho=np.sum(np.abs(A),axis=1)
        m=-.5*np.log1p(-rowrho**2);h=np.arctanh(rowrho)
        rowdual=u@L
        records.append({'direction':label,'direction_coefficients':u,'direction_norm':np.linalg.norm(u),
            'coherent_linear_support':np.sum(np.abs(g)),
            'coherent_nonlinear_feasible_lower':max(0.,downfloat(iv[0])),
            'feasible_witness_xi':best,'feasible_witness_interval_decimal':[str(iv[0]),str(iv[1])],
            'optimizer_statuses':statuses,
            'row_decoupled_exact_support':rowdual@m+np.abs(rowdual)@h,
            'row_decoupled_centered_halfwidth':np.abs(rowdual)@h,
            'row_decoupled_comparison':'Same four-parameter coordinate box first mapped to row intervals; parameter coherence discarded. This does not remove or reduce unmodeled residual errors.'})
    nodes=partition(depth)
    upper=[Decimal('-Infinity')]*len(directions)
    root_upper=node_bounds_interval(A,duals,np.zeros(4),np.ones(4))
    # Select no nodes for omission; every member of the full cover is evaluated.
    for c,h in nodes:
        ub=node_bounds_interval(A,duals,c,h)
        upper=[max(a,b) for a,b in zip(upper,ub)]
    for i,r in enumerate(records):
        r['coherent_nonlinear_certified_upper']=upfloat(min(upper[i],root_upper[i]))
        r['coherent_nonlinear_upper_decimal']=str(min(upper[i],root_upper[i]))
        r['root_taylor_certified_upper']=upfloat(root_upper[i])
        r['certificate_gap']=r['coherent_nonlinear_certified_upper']-r['coherent_nonlinear_feasible_lower']
    return records,{'method':'Finite dyadic full cover with outward Decimal interval Taylor bounds; no nodes omitted. Optimizer points certify lower bounds only.',
        'decimal_precision':42,'cover_depth':depth,'cover_boxes':len(nodes),'arithmetic_scope':'Input binary64 arrays L,A,u interpreted as exact dyadic rationals. Decimal directed arithmetic and correctly rounded ln with one adjacent-value outward expansion. No enclosure of the empirical/physical validity or of preprocessing relative to exact astronomy.',
        'adaptive_search':False,'stopping':'Fixed predeclared cover depth; residual support gaps retained, no exact-optimum claim.'}


class SourceImageError(ValueError):
    """Typed refusal at the conditional source-image boundary."""
    def __init__(self, code, detail):
        self.code = code
        super().__init__(f"{code}: {detail}")


def _array(value, shape, name):
    raw = np.asarray(value)
    if raw.dtype.kind not in 'fiu' or raw.shape != shape:
        raise SourceImageError('UNSUPPORTED_SHAPE', f'{name} requires real {shape}')
    a = np.asarray(raw, dtype=np.float64)
    if not np.isfinite(a).all():
        raise SourceImageError('NONFINITE_INPUT', name)
    # Immutable owned bytes: later caller mutation cannot invalidate the bound.
    return np.frombuffer(a.tobytes(), dtype=np.float64).reshape(shape)


@dataclass(frozen=True)
class SharedRealization:
    xi: tuple[float, ...]
    delta_theta: tuple[float, ...]
    feature_vector: tuple[float, ...]


@dataclass(frozen=True)
class BoxSourceImage:
    """Validated (525 rows, four shared parameters, five features) box only.

    xi is dimensionless in [-1,1]^4; delta_theta = halfwidth * xi.
    G maps delta_theta (dimensionless, km/s, km/s, km/s) to km/s.
    This class has no anchor/gauge or probability interface.
    """
    L: object
    z: object
    v0: object
    G: object
    halfwidth: object
    row_ids: tuple[str, ...]
    expected_row_ids: tuple[str, ...]
    parameter_units: tuple[str, ...] = ('dimensionless', 'km/s', 'km/s', 'km/s')
    velocity_frame: str = 'GALACTIC_CARTESIAN'
    feature_frame: str = 'ICRS_STF_FROBENIUS'
    domain: str = 'BOX4'

    def __post_init__(self):
        if self.domain != 'BOX4':
            raise SourceImageError('UNSUPPORTED_DOMAIN', 'only BOX4 is implemented')
        if tuple(self.parameter_units) != ('dimensionless', 'km/s', 'km/s', 'km/s'):
            raise SourceImageError('UNIT_MISMATCH', 'calibration parameter units')
        if self.velocity_frame != 'GALACTIC_CARTESIAN' or self.feature_frame != 'ICRS_STF_FROBENIUS':
            raise SourceImageError('FRAME_MISMATCH', 'explicit coordinated conversion required')
        rows = tuple(self.row_ids)
        if (len(rows) != 525 or len(set(rows)) != 525 or
                not all(isinstance(x, str) and x for x in rows) or rows != tuple(self.expected_row_ids)):
            raise SourceImageError('ROW_ORDER_MISMATCH', '525 unique ordered release row IDs required')
        object.__setattr__(self, 'row_ids', rows)
        object.__setattr__(self, 'expected_row_ids', rows)
        object.__setattr__(self, 'parameter_units', tuple(self.parameter_units))
        for name, shape in [('L',(5,525)),('z',(525,)),('v0',(525,)),('G',(525,4)),('halfwidth',(4,))]:
            object.__setattr__(self, name, _array(getattr(self,name),shape,name))
        if np.any(self.halfwidth < 0):
            raise SourceImageError('INVALID_DOMAIN', 'halfwidth must be nonnegative')
        d = C_KMS*self.z-self.v0
        if not np.isfinite(d).all() or np.any(d <= 0):
            raise SourceImageError('LOG_DOMAIN_ERROR', 'd=c*z-v0 must be positive finite')
        A = self.G*self.halfwidth/d[:,None]
        if not np.isfinite(A).all():
            raise SourceImageError('NONFINITE_INPUT', 'normalized response A')
        # Check stored-binary64 supports outwards, including touching boundaries.
        for i in range(525):
            rho = sumi(point(abs(x)) for x in A[i])[1]
            radius = sumi(mul(point(abs(g)),point(w)) for g,w in zip(self.G[i],self.halfwidth))
            if rho >= 1 or sub(point(d[i]),radius)[0] <= 0:
                raise SourceImageError('LOG_DOMAIN_ERROR', f'box touches/exceeds boundary at row {i}')
            if add(point(C_KMS),sub(point(self.v0[i]),radius))[0] <= 0:
                raise SourceImageError('REDSHIFT_DOMAIN_ERROR', f'nonpositive prefactor at row {i}')
        object.__setattr__(self,'d',_array(d,(525,),'d'))
        object.__setattr__(self,'A',_array(A,(525,4),'A'))

    def realization(self, xi):
        x = _array(xi,(4,),'shared xi')
        if np.any(np.abs(x)>1):
            raise SourceImageError('OUTSIDE_LATENT_DOMAIN', 'xi must be in [-1,1]^4')
        return SharedRealization(tuple(x),tuple(self.halfwidth*x),tuple(phi(self.L,self.A,x)))

    def velocity(self, xi):
        state = self.realization(xi)
        return self.v0 + self.G @ np.asarray(state.delta_theta)

    def support(self, directions, labels, *, cover_depth=6):
        if type(cover_depth) is not int or not 0 <= cover_depth <= 10:
            raise SourceImageError('INVALID_COVER_DEPTH','integer 0..10 required')
        labels=tuple(labels)
        if not 1 <= len(labels) <= 14 or len(set(labels)) != len(labels) or not all(isinstance(x,str) and x for x in labels):
            raise SourceImageError('INVALID_DIRECTIONS','1..14 unique direction labels required')
        u = _array(directions,(len(labels),5),'directions')
        if np.any(np.linalg.norm(u,axis=1)==0):
            raise SourceImageError('INVALID_DIRECTIONS','nonzero directions required')
        records,certificate = support_records(self.L,self.A,u,labels,cover_depth)
        for row in records:
            state=self.realization(row['feasible_witness_xi'])
            row['feasible_feature_vector']=list(state.feature_vector)
            row['feasible_delta_theta']=list(state.delta_theta)
            row['realization_scope']='ONE_XI_ALL_ROWS_AND_FEATURES; direction queries are separate'
            if not row['coherent_nonlinear_feasible_lower'] <= row['coherent_nonlinear_certified_upper']:
                raise SourceImageError('INVALID_BRACKET','lower exceeds upper')
        return records,certificate
