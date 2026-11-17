"""Independent SymPy algebra checks; no four-axis CAS admission is implied."""
import argparse
import json
from pathlib import Path
import sympy as s


def run(output):
    z, c, h0, a = s.symbols('z c h0 a', positive=True)
    h, chi, eta, r, focus = [s.Function(k)(z) for k in ('h', 'chi', 'eta', 'r', 'focus')]
    b = h*chi/c
    hd = h*s.exp(eta)/(1-b*s.diff(eta, z))
    substitute = {s.diff(chi, z): c/h}
    q = -1+(1+z)*s.diff(h,z)/h+(1+z)*(s.diff(eta,z)+
        ((1+b*s.diff(h,z)/h)*s.diff(eta,z)+b*s.diff(eta,z,2))/(1-b*s.diff(eta,z)))
    differences = {
        'eta_H': (c/s.diff(chi*s.exp(-eta),z)).subs(substitute)-hd,
        'eta_q': (-1+(1+z)*s.diff(s.log(hd),z)).subs(substitute)-q,
        'calibration': hd.xreplace({eta:eta+a})-s.exp(a)*hd,
    }
    rm = c/(2*h0)*((1+z)-1/(1+z))
    hm = 2*h0*(1+z)**2/((1+z)**2+1)
    differences['Milne_H'] = c/s.diff(rm,z)-hm
    differences['Milne_q'] = -1+(1+z)*s.diff(s.log(hm),z)-(1-(1+z)**2)/(1+(1+z)**2)
    da = r/(1+z)
    lhs = (1+z)*(s.diff(da,z,2)+(2/(1+z)+s.diff(h,z)/h)*s.diff(da,z)+c*c*focus*da/((1+z)**4*h*h))
    rhs = s.diff(r,z,2)+s.diff(h,z)/h*s.diff(r,z)+(c*c*focus/((1+z)**4*h*h)-s.diff(h,z)/((1+z)*h))*r
    differences['Sachs_R'] = lhs-rhs
    points = list(map(s.Rational, ('1/40','1/25','3/50','2/25')))
    p3 = s.interpolate([(v,1/v) for v in points],z)
    differences['cubic_null'] = 1/z-p3-s.prod(z-v for v in points)/(z*s.prod(points))
    # A squared physical rate turns the optical closure into a linear ODE.
    yy = s.Function('Y')(z)
    optical = s.expand(rhs*h*h).subs(h*s.diff(h,z),s.diff(yy,z)/2).subs(h*h,yy)
    yode = (s.diff(r,z)-r/(1+z))*s.diff(yy,z)/2+s.diff(r,z,2)*yy+c*c*focus*r/(1+z)**4
    differences['physical_H_squared_ODE'] = optical-yode
    result = {name:str(s.simplify(value)) for name,value in differences.items()}
    if any(value!='0' for value in result.values()):
        raise AssertionError(result)
    out = dict(sympy=s.__version__,differences=result,status='ALL_DIFFERENCES_ZERO',
               scope='symbolic algebra only; no physical-closure, source-covariance or four-axis CAS admission')
    Path(output).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    run(args.output)
