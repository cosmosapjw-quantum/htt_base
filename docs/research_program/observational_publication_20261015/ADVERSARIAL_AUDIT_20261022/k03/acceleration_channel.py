"""Source-qualified compressed Gaia observer-acceleration channel.

No raw-catalogue refit and no identification of cosmic congruence A_a.
The Gaussian is a declared approximation to published bootstrap summaries.
"""
from pathlib import Path
import json
import heapq
import platform
import sys
import numpy as np
import scipy
from scipy.optimize import brentq
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parent
YEAR_S = 365.25 * 86400
C_LIGHT = 299792458.0
UAS_RAD = np.pi / (180.0 * 3600.0 * 1e6)
UAS_YR_TO_M_S2 = C_LIGHT * UAS_RAD / YEAR_S
# Standard ICRS -> Galactic Cartesian rotation (arXiv v1 Sect3.4 conventions).
ICRS_TO_GAL = np.array([
    [-0.0548755604162154, -0.8734370902348850, -0.4838350155487132],
    [0.4941094278755837, -0.4448296299600112, 0.7469822444972189],
    [-0.8676661490190047, -0.1980763734312015, 0.4559837761750669]])


def load_summary():
    source = json.loads((ROOT / "source_registry.json").read_text())["primary"]
    mean = np.array(source["table2_mean"], dtype=float)
    sigma = np.array(source["table2_sigma"], dtype=float)
    xy, xz, yz = source["table2_rho_xy_xz_yz"]
    corr = np.array([[1, xy, xz], [xy, 1, yz], [xz, yz, 1.]])
    return mean, corr * np.outer(sigma, sigma)


def sky_basis(ra, dec):
    """Radians; tangent pair is (mu_alpha*cos(delta), mu_delta)."""
    ca, sa, cd, sd = np.cos(ra), np.sin(ra), np.cos(dec), np.sin(dec)
    return (np.array([cd*ca, cd*sa, sd]),
            np.array([[-sa, ca, 0.], [-sd*ca, -sd*sa, cd]]))


def tangent_response(ra, dec):
    """2x3 response to g=a_obs/c in angular-rate units; Eq4."""
    return sky_basis(ra, dec)[1]


def cartesian_response(n):
    n = np.asarray(n, dtype=float)
    if n.shape != (3,) or not np.isclose(n @ n, 1., atol=1e-12):
        raise ValueError("n must be a unit Cartesian vector")
    return np.eye(3) - np.outer(n, n)


def prediction(ra, dec, mean, covariance):
    d = tangent_response(ra, dec)
    return d @ mean, d @ covariance @ d.T


def cross_prediction_covariance(ra1, dec1, ra2, dec2, covariance):
    """Parameter-estimation covariance of fitted mean field, not spatial noise."""
    return tangent_response(ra1, dec1) @ covariance @ tangent_response(ra2, dec2).T


def quadratic(g, mean, covariance):
    d = np.asarray(g, dtype=float) - mean
    return float(d @ np.linalg.solve(covariance, d))


def gaussian_loglike(g, mean, covariance):
    sign, logdet = np.linalg.slogdet(covariance)
    if sign != 1:
        raise ValueError("Covariance must be positive definite")
    return -.5 * (quadratic(g, mean, covariance) + logdet + 3*np.log(2*np.pi))


def smallest_additive_bias_to_include_zero(mean, covariance, radius2):
    """Minimum ||b|| so 0 is in E(mean-b,C,radius2), by convex KKT.

    b_i(lambda)=lambda*m_i/(eigenvalue_i+lambda) in eigenbasis.
    This is an adversarial sensitivity threshold, not an inferred systematic.
    """
    if quadratic(np.zeros(3), mean, covariance) <= radius2:
        return np.zeros(3)
    values, vectors = np.linalg.eigh(covariance)
    m = vectors.T @ mean
    def constraint(lam):
        return np.sum(m*m*values/(values+lam)**2) - radius2
    hi = float(values.max())
    while constraint(hi) > 0:
        hi *= 2
    lam = brentq(constraint, 0., hi, xtol=1e-14)
    return vectors @ (lam*m/(values+lam))


def published_frame_covariance_audit():
    """Interval enclosure falsifier for the separately printed Table2 frames.

    Assumption: rounding to nearest .01 in sigma and .001 in rho. Propagate
    enclosing intervals for all six independent covariance entries, transform
    them linearly, and enclose rho_XY. Subdivide the original parameter box.
    Each box bound includes every interior point; unlike a corner scan it is
    a global enclosure. A conservative 1e-12 pad dominates floating error.
    """
    r = ICRS_TO_GAL
    center = np.array([.41,.35,.36,.001,-.094,-.025])
    radius = np.array([.005]*3+[.0005]*3)
    coeffs = []
    pairs = [(0,1),(0,2),(1,2)]
    for k,l in [(0,1),(0,0),(1,1)]:
        coeffs.append([r[k,i]*r[l,i] for i in range(3)] +
                      [r[k,i]*r[l,j]+r[k,j]*r[l,i] for i,j in pairs])
    coeffs = np.array(coeffs)
    def upper_bound(lo,hi):
        lower, upper = list(lo[:3]**2), list(hi[:3]**2)
        for h,(i,j) in enumerate(pairs):
            products = [x*y*z for x in [lo[i],hi[i]]
                        for y in [lo[j],hi[j]] for z in [lo[3+h],hi[3+h]]]
            lower.append(min(products)); upper.append(max(products))
        lower,upper = np.array(lower),np.array(upper)
        transformed_lo = (np.maximum(coeffs,0)*lower+np.minimum(coeffs,0)*upper).sum(axis=1)-1e-12
        transformed_hi = (np.maximum(coeffs,0)*upper+np.minimum(coeffs,0)*lower).sum(axis=1)+1e-12
        if np.any(transformed_lo[1:] <= 0):
            raise ValueError("Interval denominator not positive")
        return float(transformed_hi[0]/np.sqrt(np.prod(transformed_lo[1:]))+1e-12)
    lo,hi = center-radius,center+radius
    queue = [(-upper_bound(lo,hi),0,lo,hi)]
    serial = 0
    target_lower = .036-.0005
    boxes_split = 0
    for _ in range(10000):
        neg,_,lo,hi = heapq.heappop(queue)
        if -neg < target_lower:
            return {"status":"FAIL_PRINTED_FRAME_COVARIANCE_PARITY",
                    "assumption":"Rounding-to-nearest sigma .01, correlations .001; same underlying covariance and standard rotation",
                    "global_upper_rho_XY":-neg,"published_lower_rho_XY":target_lower,
                    "boxes_split":boxes_split,"remaining_boxes":len(queue)+1,
                    "arithmetic_padding":1e-12,
                    "interpretation":"Printed frame summaries cannot be one identically transformed covariance under the stated rounding model; estimator/precision explanation unresolved. Chosen ICRS covariance remains a declared working summary."}
        j = int(np.argmax((hi-lo)/radius)); midpoint=(lo[j]+hi[j])/2
        for side in range(2):
            nl,nh = lo.copy(),hi.copy()
            if side == 0: nh[j]=midpoint
            else: nl[j]=midpoint
            serial += 1
            heapq.heappush(queue,(-upper_bound(nl,nh),serial,nl,nh))
        boxes_split += 1
    raise RuntimeError("Frame covariance interval audit did not resolve")


def summarize():
    mean, covariance = load_summary()
    values, axes = np.linalg.eigh(covariance)
    r95 = float(chi2.ppf(.95, 3))
    galmean = ICRS_TO_GAL @ mean
    galcov = ICRS_TO_GAL @ covariance @ ICRS_TO_GAL.T
    galsigma = np.sqrt(np.diag(galcov))
    galcorr = galcov / np.outer(galsigma, galsigma)
    norm = float(np.linalg.norm(mean))
    direction = mean/norm
    bias = smallest_additive_bias_to_include_zero(mean, covariance, r95)
    probes = [(0, 0), (90, 0), (180, 45), (270, -30)]
    predictions = []
    for ra, dec in probes:
        mu, cov = prediction(np.deg2rad(ra), np.deg2rad(dec), mean, covariance)
        predictions.append({"ra_deg":ra, "dec_deg":dec,
                            "mu_uas_yr":mu.tolist(), "mean_field_covariance":cov.tolist()})
    source = json.loads((ROOT / "source_registry.json").read_text())
    legacy = np.array(source["legacy"]["legacy_mean"])
    # For ANY proposed cosmic vector k, choosing galactic/frame/source E1
    # nuisance b=mean-k fits the compressed summary exactly.
    candidates = [np.array([0.,0.,0.]), np.array([10.,-20.,30.]), np.array([-1e6,2e6,-3e6])]
    profile = [{"candidate_cosmic_g":k.tolist(),
                "free_additive_nuisance":(mean-k).tolist(),
                "profile_quadratic":quadratic(k+(mean-k),mean,covariance)} for k in candidates]
    return {
        "owner":"obsstat response; htt compressed working likelihood",
        "scope":"Solar-system observer coordinate acceleration relative to remote QSO-like sources",
        "status":"CONDITIONAL_SOURCE_QUALIFIED_SUBCHANNEL",
        "claim_tier":"C0 exploratory; NO_AUTOMATIC_PHYSICAL_PROMOTION",
        "repository_baseline":source["repository_baseline"],
        "transfer_source":"Published first-order observer aberration law; no Bianchi/native transfer",
        "generating_command":"python acceleration_channel.py",
        "runtime":{"python":sys.version.split()[0],"executable":sys.executable,
                   "numpy":np.__version__,"scipy":scipy.__version__,"platform":platform.platform()},
        "sky_support_status":"Published selected five-parameter Gaia-CRF3 sample, not all-QSO population",
        "null_mock_status":"No calibrated cosmic null; no raw-catalogue replay",
        "covariance_status":"Rounded published bootstrap parameter covariance; Gaussian approximation conditional on source model; unknown inter-source/calibration law not set zero",
        "mean_g_uas_yr":mean.tolist(),"covariance_g_uas2_yr2":covariance.tolist(),
        "covariance_eigenvalues":values.tolist(),"covariance_condition_number":float(values.max()/values.min()),
        "mean_acceleration_m_s2":(mean*UAS_YR_TO_M_S2).tolist(),
        "covariance_acceleration_m2_s4":(covariance*UAS_YR_TO_M_S2**2).tolist(),
        "unit_conversion_m_s2_per_uas_yr":UAS_YR_TO_M_S2,
        "norm_g_uas_yr":norm,"norm_delta_method_sigma":float(np.sqrt(direction@covariance@direction)),
        "norm_acceleration_m_s2":norm*UAS_YR_TO_M_S2,
        "ra_deg":float(np.rad2deg(np.arctan2(mean[1],mean[0]))%360),
        "dec_deg":float(np.rad2deg(np.arcsin(mean[2]/norm))),
        "galactic_mean_g":galmean.tolist(),"galactic_sigma_g":galsigma.tolist(),
        "galactic_correlation_g":galcorr.tolist(),
        "published_frame_covariance_audit":published_frame_covariance_audit(),
        "conditional_95_ellipsoid":{"q_threshold":r95,"principal_semiaxes_uas_yr":np.sqrt(r95*values).tolist(),
                                    "principal_axes_columns_icrs":axes.tolist(),
                                    "interpretation":"Nominal Gaussian joint95 region only; not calibrated total-systematics coverage"},
        "observer_zero_quadratic_working_only":quadratic(np.zeros(3),mean,covariance),
        "prediction_probes":predictions,
        "additive_bias_sensitivity":{"unit":"uas/yr","minimum_euclidean_bias_for_zero_at_nominal95":float(np.linalg.norm(bias)),
                                     "bias_vector_icrs":bias.tolist(),
                                     "boundary_quadratic":quadratic(bias,mean,covariance),
                                     "interpretation":"Conditional threshold under deterministic bounded additive E1 bias; no such bound is supplied by this source"},
        "cosmic_acceleration_falsifier":{"design":"[I3 I3] for cosmic plus unrestricted local/source E1",
                                          "rank":3,"parameter_count":6,"null_dimension":3,
                                          "profiles":profile,
                                          "identified_set":"all R^3 for cosmic g when additive nuisance unrestricted"},
        "legacy_difference_uas_yr":(mean-legacy).tolist(),
        "legacy_comparison":"Dependent analyses with different lmax/sample/clipping; no difference significance or combination",
        "original_K03":{"recommendation":"REMAINS_PENDING; observer acceleration subchannel complete subject independent review",
                         "reason":"No admitted map from a_obs=dv_obs/dt to congruence A_a, omega or beta; original target sectors are not identified by this compressed observer datum"},
        "K05_promotion":False,
        "caveats":["Chosen ICRS working covariance; printed-frame covariance discrepancy unresolved under stated rounding model",
                   "Cross-sky fitted-mean covariance is not measured astrometric spatial-noise covariance",
                   "No likelihood product with legacy Gaia or overlapping radio713",
                   "No kSZ or polarization response supplied", "No cosmic p-value or detection significance"]
    }


if __name__ == "__main__":
    result = summarize()
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({key:result[key] for key in ["norm_g_uas_yr","norm_acceleration_m_s2","additive_bias_sensitivity","cosmic_acceleration_falsifier"]},indent=2))
