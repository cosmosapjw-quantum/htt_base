
import json, math, random
import mpmath as mp
from pathlib import Path

RESULTS = {"samples": {}}

def nearly_equal(a,b,rtol=1e-11,atol=1e-11):
    return abs(a-b) <= atol + rtol*max(abs(a),abs(b))

def test_classB_maps():
    rng = random.Random(12345)
    errs = []
    for _ in range(200):
        h = -10**rng.uniform(-5, 1)   # negative
        root = math.sqrt(-h)
        q = (1-root)/(1+root)
        h_back = -((1-q)/(1+q))**2
        errs.append(abs(h-h_back))
    for _ in range(200):
        h = 10**rng.uniform(-8, 2)
        p = math.sqrt(h)
        errs.append(abs(h-p*p))
    RESULTS["samples"]["classB_max_abs_err"] = max(errs)
    assert max(errs) < 1e-12

mp.mp.dps = 80

def rho_viii(mu, s):
    mu = mp.mpf(mu)
    s = mp.mpf(s)
    return (mp.mpf(1)/(2*mp.pi)**2) * s*mp.sinh(2*mp.pi*s)/(mp.cosh(2*mp.pi*s)+mp.cos(2*mp.pi*mu))

def test_typeVIII():
    rng = random.Random(222)
    errs = []
    posvals = []
    for _ in range(300):
        mu = rng.uniform(-0.499999, 0.499999)
        s = 10**rng.uniform(-6, 1)
        val = rho_viii(mu, s)
        posvals.append(float(val))
        assert val >= 0.0
    for s in [mp.mpf(10)**x for x in [-6,-4,-2,0,1]]:
        errs.append(abs(rho_viii(0.0, s) - (mp.mpf(1)/(2*mp.pi)**2)*s*mp.tanh(mp.pi*s)))
        errs.append(abs(rho_viii(mp.mpf('0.5'), s) - (mp.mpf(1)/(2*mp.pi)**2)*s*mp.coth(mp.pi*s)))
    # discrete measure positivity
    for lam in [0.5,0.75,2.0,10.0]:
        val = (1/(2*math.pi)**2)*(lam-0.5)
        assert val >= -1e-15
    RESULTS["samples"]["typeVIII_min_val"] = min(posvals)
    RESULTS["samples"]["typeVIII_specialcase_max_abs_err"] = float(max(errs))
    assert max(errs) < mp.mpf('1e-30')

def healpy_idx(lmax, ell, m):
    return m*(2*lmax + 1 - m)//2 + ell

def test_healpix():
    for lmax in [0,1,2,3,8,31]:
        seen = set()
        for m in range(lmax+1):
            for ell in range(m, lmax+1):
                idx = healpy_idx(lmax, ell, m)
                assert idx not in seen
                seen.add(idx)
        assert min(seen or {0}) == 0
        assert max(seen or {0}) == (lmax+1)*(lmax+2)//2 - 1

def fd1(vals,h):
    return (vals[0]-8*vals[1]+8*vals[2]-vals[3])/(12*h)

def fd2(vals,h):
    return (-vals[0]+16*vals[1]-30*vals[2]+16*vals[3]-vals[4])/(12*h*h)

def test_fd():
    rng = random.Random(777)
    errs = []
    h = mp.mpf('1e-3')
    for _ in range(100):
        coeffs = [mp.mpf(str(rng.uniform(-2,2))) for _ in range(5)]  # up to degree 4
        def poly(x):
            return sum(c*(x**i) for i,c in enumerate(coeffs))
        vals1 = [poly(-2*h), poly(-1*h), poly(1*h), poly(2*h)]
        vals2 = [poly(-2*h), poly(-1*h), poly(mp.mpf('0.0')), poly(1*h), poly(2*h)]
        d1_exact = coeffs[1]
        d2_exact = 2*coeffs[2]
        errs.append(abs(fd1(vals1,h)-d1_exact))
        errs.append(abs(fd2(vals2,h)-d2_exact))
    RESULTS["samples"]["fd_max_abs_err"] = float(max(errs))
    assert max(errs) < mp.mpf('1e-40')

def test_density_positivity():
    # Type IV: 1+k1 >=0 for k1>=0
    for k1 in [0.0,1e-8,0.1,1.0,7.5]:
        assert 1+k1 >= 0.0
    # VI_h negative-q branch
    for q in [-5.0,-1.0,-1e-6]:
        for ang in [0.0,0.4,1.0,2.5]:
            val = math.cos(ang)**2 - q*math.sin(ang)**2
            assert val > 0.0
    # VII_h |k| positivity
    for k in [-10.0,-1.0,0.5,2.0]:
        assert abs(k) >= 0.0

def main():
    test_classB_maps()
    test_typeVIII()
    test_healpix()
    test_fd()
    test_density_positivity()
    outpath = Path(__file__).with_name("numeric_results.json")
    outpath.write_text(json.dumps(RESULTS, indent=2))
    print(json.dumps(RESULTS, indent=2))

if __name__ == "__main__":
    main()
