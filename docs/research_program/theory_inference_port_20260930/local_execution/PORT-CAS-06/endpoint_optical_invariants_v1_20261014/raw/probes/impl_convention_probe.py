"""Numerical convention cross-check (not a proof): implementation vs Lean formulas."""
import sys, json, math
import numpy as np
sys.path.insert(0, "/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/src")
from common.relativistic_kinematics import endpoint_boost, inverse_temperature_boost, lorentz_boost, four_velocity
rng = np.random.default_rng(20261014); worst = {}
def upd(k, v): worst[k] = max(worst.get(k, 0.0), float(abs(v)))
for _ in range(2000):
    b = rng.normal(size=3); b *= rng.uniform(0, 0.95) / np.linalg.norm(b)
    n = rng.normal(size=3); n /= np.linalg.norm(n)
    z, da, dl = rng.uniform(0, 5), rng.uniform(0.1, 10), rng.uniform(0.1, 10)
    zp, dap, dlp, d = endpoint_boost(z, da, dl, n, b)
    g = 1/math.sqrt(1 - b@b); h = g*g/(g+1); D = g*(1 + b@n)
    upd("doppler", d - D)
    k = np.r_[1.0, -n]                       # photon E=1, sourceward n
    kp = lorentz_boost(-b) @ k               # Binv k
    upd("energy_ratio", kp[0] - D)
    nprime = -kp[1:]/kp[0]
    ab = (n + g*b + h*(b@n)*b)/D             # Lean `aberr`
    upd("aberr", np.max(np.abs(nprime - ab)))
    upd("aberr_unit", nprime@nprime - 1)
    upd("reciprocal", D*g*(1 - b@nprime) - 1)
    upd("product", (1+zp)*dap - (1+z)*da)
    upd("dL", dlp - dl/D)
    T0 = rng.uniform(1, 3); a = g/T0; c = -g*b/T0
    Trest, beta = inverse_temperature_boost(a, c)
    upd("rest_T", Trest - T0); upd("beta", np.max(np.abs(beta - b)))
    upd("affine", 1/(D*T0) - (a + c@nprime))
print(json.dumps(worst, indent=1))
