# R66 stage 8 constructive addendum — unit-free directional reference

Scope: derive a usable conditional likelihood for the signed DQ-quotient direction when a genuine temperature MC bank has one unknown common positive unit factor. The rejected all-zero 005a intensity field supplies no temperature ensemble. No file acquisition, native execution, additional child, fit or review is performed here. Requested result: a finite-N construction, not an absolute-amplitude calibration or a current anomaly claim.

## 1. Statistical experiment and the information retained

Let s_obs=U^T q_obs in R^p, p=4, in observed μK, and let z_i=U^T q_i be the corresponding simulation vectors in their common but unbound numeric unit. Assume

    s_obs ~ N_p(0,Sigma),
    z_i ~ iid N_p(0,kappa^2 Sigma),      kappa>0,

with observation independent of the MC bank and the same declared downstream response/quotient. Define u_obs=s_obs/||s_obs|| on the **directed** unit sphere S^(p-1). Multiplication by kappa leaves u unchanged, so the simulation vectors can calibrate its distribution without binding the μK conversion. The fixed Euclidean metric must be the same orthonormal STF/quotient metric for observed and simulated vectors. A nonsingular change of coordinate metric changes what is meant by direction.

Unknown overall scale is the only calibration freedom removed here. Different per-mode transfer, additive offsets, different foreground/noise mixtures, non-Gaussianity, a wrong quotient, or observed/simulation nonexchangeability are not absorbed by kappa. Pixel reading, the monopole/dipole fit and subsequent operations must be homogeneous: O(kappa t)=kappa O(t), with masks/weights fixed independently of map values. A separately supplied additive correction must scale consistently or be retained as a nuisance. No inference from the raw numerical magnitude alone establishes these conditions or the unit.

## 2. Finite-N predictive derivation

For an asserted known-zero population mean, form

    S0=(1/N) sum_i z_i z_i^T.

Under the zero-mean Gaussian model and the same covariance Jeffreys prior as the main note, pi(Sigma_MC) proportional to |Sigma_MC|^(-(p+1)/2), the predictive vector in MC units has

    nu=N-p+1,
    Omega=N S0/nu,
    z_new | bank ~ t_nu(0,Omega).

This posterior/predictive is proper when N>p-1 and the scatter has full rank. Thus N=8,p=4 gives nu=5, and N=20 gives nu=17. Angular existence does not require a finite second moment of the predictive vector.

Put a=u^T Omega^-1 u. Polar coordinates z=r u, r>0 give the directional density with respect to ordinary sphere surface area:

    f_U(u|bank) = integral_0^infinity r^(p-1) t_nu(r u;0,Omega) dr.

The radial integral is

    integral_0^infinity r^(p-1)(1+a r^2/nu)^(-(nu+p)/2) dr
      = (1/2)(nu/a)^(p/2) B(p/2,nu/2).

Combining constants and cancelling Omega's scalar factor yields the angular central Gaussian (ACG) density

    f_U(u|S0)= Gamma(p/2)/(2 pi^(p/2))
               |S0|^(-1/2) (u^T S0^-1 u)^(-p/2),
    ||u||=1.

For p=4 this is

    f_U(u|S0)= [1/(2 pi^2)] |S0|^(-1/2)
                              (u^T S0^-1 u)^(-2).

Multiplying S0 by any positive scalar leaves the density unchanged. In particular the unknown kappa cancels exactly. For stable implementation, use a Cholesky solve for u^T S0^-1 u and a log determinant; equivalently use the determinant-normalized shape M=S0/|S0|^(1/p). The vector must be nonzero; the direction of a zero vector is undefined. Singular scatter does not permit the displayed inverse/density.

The cancellation of nu does **not** mean finite-N shape uncertainty has disappeared. S0 is random and poorly determined for a very small bank; the formula is the exact posterior predictive angular density under the stated Gaussian likelihood and improper invariant covariance prior. It is not a prior-free assertion that the true directional density equals ACG(S0), and it is not an exact frequentist p-value for a chosen angular statistic. Shape-prior sensitivity can matter materially with N=8–20. Posterior draws of Sigma_MC from inverse-Wishart(N S0,N) would expose shape uncertainty if later needed; no such calculation is executed here.

The same ACG form is obtained from any zero-centered elliptical vector distribution with scatter proportional to S0 and an integrable radial density. That fact supports the radial elimination, but it does not establish that this particular public MC family has the required shape or source law.

## 3. Sign, dipole removal and the nonzero-mean failure

The domain is the directed sphere, with total area 2 pi^(p/2)/Gamma(p/2); do not silently identify u with -u. The zero-mean model nevertheless predicts f(u)=f(-u), so this particular reference cannot distinguish the two signs. Save the signed observed vector and direction for physical interpretation and other qualified models.

A large physical or simulated dipole is harmless to this construction only if the common estimator removes its actual pixelized response. Exact E Z=0 applies to the columns actually used, including averaging/pixelization where required. It does not certify removal of an arbitrary native-pixel dipole by a different pixel-center approximation. A surviving deterministic dipole/monopole leakage can generate a nonzero quadrupole mean. The declared rank-one DQ quotient removes only its own response span.

A nonzero finite sample mean is expected even when the population mean is zero; it is not by itself evidence for a residual bias. But a genuinely nonzero population mean invalidates the centered ACG shortcut. For example, z=mu+epsilon with small isotropic epsilon has directions concentrated near +mu. The uncentered second moment is then approximately mu mu^T, whose ACG density allocates symmetric mass near both +mu and -mu. It replaces a directional bias by a spurious axial covariance shape.

Do not repair this by subtracting the MC sample mean while leaving the observation unchanged. If a common unknown nonzero mean is the explicitly chosen model, a scale-invariant alternative still exists: with sample mean m, centered S, a flat mean prior and the same covariance prior, use

    nu=N-p,
    Omega=(1+1/N)(N-1)S/(N-p),
    f_U(u|bank)=integral_0^infinity r^(p-1)
                            t_nu(r u;m,Omega) dr.

This one-dimensional radial integral is generally not ACG. It remains invariant under m->kappa m and Omega->kappa^2 Omega by changing the radial integration variable. It requires N>p and a shared mean/shape source model. It is a different declared statistical model, not permission to refit away whichever direction looks inconvenient. If the mean mismatch is due to different observed/simulated processing, neither version restores exchangeability.

## 4. What can defensibly be reported

The constructive public-data output is the full signed observed stress proxy plus a **unit-free conditional directional predictive density**, its MC shape, N, quotient/processing response and source qualifications. One can compare it with a uniform-direction reference through the density ratio

    f_U(u)/(1/area)=|S0|^(-1/2)(u^T S0^-1 u)^(-p/2).

This ratio is a likelihood density ratio, not a tail probability. A lower density in the estimated directional reference is not an absolute C2/stress anomaly. Direction-only inference deliberately discards amplitude: it cannot calibrate the observed stress norm, C2, an absolute deterministic mean-stress likelihood, physical-volume confidence occupancy, or the earlier radial F-statistic while MC units remain unbound. The observed deterministic μK-to-stress conversion can remain valid under its own physical assumptions; what is absent is its absolute MC calibration.

For a frozen score and genuinely independent calibration directions, an exchangeability rank reference is also unit-free: p_rank=(1+# calibration scores at least as extreme as the new score)/(m+1), with ties handled conservatively. This is a finite-sample frequentist option for a future fixed-rule experiment, distinct from the predictive density. With only 8–20 files, an honest train/calibration split has coarse tail resolution: four held-out directions give minimum 0.2, ten give minimum 1/11. No small-tail discovery is available from that resolution. Choosing this construction after inspecting the observed controls also requires retaining its exploratory status for the current sky.

If the physically adopted ideal isotropic Gaussian sky has quotient covariance sigma^2 I4, its direction is exactly uniform and this likelihood is constant. It supplies no preferred-direction discrimination by itself. Apparent anisotropy of S0 from a tiny bank is not evidence for a physical preferred axis. A nonuniform directional reference is useful only insofar as a qualified finite operator/source model produces that shape, or a separately specified directional physical alternative supplies a meaningful comparison.

An alternative unit-calibrated ideal Gaussian-sky experiment may use a declared spectrum in μK^2 and the actual downstream operator to construct Sigma_ideal=O C_sky O^T. This permits absolute conditional calculations, but its title and conclusions must say **ideal isotropic Gaussian injection reference**. It does not become a Commander end-to-end calibration or inherit the unknown public-bank noise, foreground, beam or dipole response. Keep this alternative separate from the public-data angular likelihood; neither repairs the other's missing source assumptions.

Status: the radial integration, scale invariance, finite-N prior/degree conditions and nonzero-mean counterexample are DERIVED. Public temperature units, Gaussianity, common shape/mean and observed/simulated exchangeability remain source obligations. The zero 005a intensity products remain rejected; no formula recovers temperature information from them.
