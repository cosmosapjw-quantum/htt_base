# K03: executable observer-acceleration subchannel and its falsifiers

Owner: `obsstat` for the response and source features; `htt` for the declared compressed likelihood. Baseline `76595070beb97e52dce9f2d7a0ff1dbf3c289e98`. Scope: exploratory C0, `CONDITIONAL`; no native transfer, cosmic detection significance, K05 or publication promotion. Requested author Sol/high; observed model `UNKNOWN`. Independent review is pending the parent review. The project physics/math, scientific-code-validation, claim-firewall and provenance-ledger skills were read and applied. No checkout, native/ODE solver, raw catalogue refit, or radio rerun was created.

**A physical nonradial observer-acceleration response and correlated, executable working likelihood now exist.** This is new downstream capability relative to the old catalogue VSH fits. It does not complete original K03: observer coordinate acceleration is not the cosmic congruence acceleration `A_a`, and the chosen published covariance has an unresolved inter-frame table discrepancy. Both failures are calculated, not replaced by a generic request for more data.

## Source qualification and comparison with prior work

The numerical source is Gaia Collaboration, Klioner et al., A&A 649 A9 (2021), [DOI 10.1051/0004-6361/202039734](https://doi.org/10.1051/0004-6361/202039734), Table2. A&A full text, its separate table and PDF text were fetched through Exa after direct HTTP403. For independent parsing, the arXiv PDF was downloaded, its actual header identified as `2012.02036v1`, and Table2 on PDF page14 rendered and inspected. Labels and numbers agree with the published table. Section pointers in the registry follow this local v1 PDF: Sect2 response and first-order accuracy, Sect3.4 rotation conventions, Sect4.1 source selection, Sect5 method, Sect6 analysis, Sect7 conclusions, AppendixA amplitude bias. The published A&A HTML uses different section numbering. This checks transcription; it is not an independent astrometric observation.

The paper uses 1,215,942 five-parameter Gaia-CRF3 QSO-like sources. It jointly fits E and B VSH through `lmax=3`, clips sources robustly at kappa3 (approximately3800 rejected), includes each source's two-component correlations, and reports bootstrap uncertainties. These increase uncertainties of a fit already scaled by unit-weight error1.048 by factors1.05–1.08. Source selection uses external QSO/AGN matches, astrometric quality and near-zero-motion/parallax filtering. It is not a random sample of all QSOs. The paper tests multipole truncation, clipping, magnitude, colour, CTI, contamination and ephemerides; it explicitly does not model inter-source correlations.

The legacy D05 report was fetched at the exact baseline (Git blob `9c8893652382bf29fe18401b8aed184e6c1f9561`). It already analyzed all1,614,173 Gaia sources, l1+l2 observable VSH, frame projection,12 angular deletes and713radio sources. Its E1 mean `(-.63924,-4.31228,-2.61280)` differs from the published five-parameter lmax3/clipped mean below. Sample, model and clipping differ. Both use overlapping Gaia astrometry. Their difference has no independent-sample significance, and their likelihoods must not be multiplied. No large catalogue data was fetched again.

Freshness check matters. [Brown, Bastian and Klioner (2025), arXiv2503.03389v1](https://arxiv.org/html/2503.03389v1) explicitly explain BCRS-origin/ICRS-axis conventions. [Nguyen and Murray, arXiv2605.30367v3,9October2026](https://arxiv.org/html/2605.30367v3) compare a source-noise fit with a model marginalizing stochastic l4–10 power. Their unmasked Quaia acceleration is `(1.01,-4.94,-2.13)` with marginal lower errors `(.72,.55,.58)` and upper errors `(.72,.54,.58)` μas/yr; amplitude5.55 with lower/upper errors.53/.54. Their correlated-power model broadens intervals substantially, especially under sky cuts. These are model/posterior summaries from overlapping Gaia data, not a supplied covariance replacement. No 3×3 matrix was manufactured from these marginal intervals. A current-v3 web read is essential: Exa's unversioned abstract fetch returned stale v1 values. The v3 amplitude-versus-redshift discussion also flags a marginal trend; do not repeat v1's blanket no-redshift-trend description as a proven physical null. No reusable posterior/code link was found in the inspected paper.

## Derived physical response and covariance

Use ICRS Cartesian axes, RA `alpha`, declination `delta`, observer-to-source unit vector `n`, tangents `e_alpha`, `e_delta`, and catalogue `mu_alpha*=dot(alpha) cos(delta)`. The catalogue origin is the solar-system barycentre; its axes align with ICRS. The source's `a_obs=dv_obs/dt` is a coordinate/kinematic acceleration relative to remote extragalactic sources. It is not the proper four-acceleration `u^b nabla_b u_a` of a cosmic-fluid congruence. Gravitational orbital acceleration may be nonzero while proper acceleration vanishes. Metric signature does not enter this leading astrometric Euclidean projection; the project convention remains(-,+,+,+).

At fixed distant-source direction, first-order aberration is `delta n=P_n v_obs/c`, where `P_n=I-nn^T`. Its time derivative yields

\[
\boldsymbol\mu(\boldsymbol n)=P_{\boldsymbol n}\boldsymbol g,
\quad \boldsymbol g=\boldsymbol a_{\rm obs}/c,
\qquad
D(\alpha,\delta)=\begin{pmatrix}
-\sin\alpha&\cos\alpha&0\\
-\sin\delta\cos\alpha&-\sin\delta\sin\alpha&\cos\delta
\end{pmatrix}.
\]

Thus `mu_tangent=D g`. On the unit sphere, `P_n g=grad_S(g.n)`, so its divergence is `-2 g.n` and its surface curl is zero: an electric dipole, not a cosmic-curl measurement. Response vanishes at apex/antapex and has maximum magnitude |g| at90degrees. In the paper's normalized VSH convention `s10=sqrt(8pi/3) gz`, `Re(s11)=-sqrt(4pi/3) gx`, `Im(s11)=sqrt(4pi/3) gy`. Two nonparallel sightlines suffice for algebraic rank3. A finite selected-sky likelihood still inherits source/model systematics; full-sphere E/B orthogonality is not assumed for the footprint.

The compressed source input is

\[
\widehat g=(-0.07,-4.30,-2.64)\ {\rm \mu as/yr},\quad
C_g=\begin{pmatrix}
0.1681&0.0001435&-0.0138744\\
0.0001435&0.1225&-0.00315\\
-0.0138744&-0.00315&0.1296
\end{pmatrix}({\rm \mu as/yr})^2.
\]

Define a *working* Gaussian `log L=-.5[(g-g_hat)^T C^-1(g-g_hat)+logdet C+3log(2pi)]`. It approximates a published bootstrap summary; it is not a reconstructed catalogue likelihood or full-systematics sampling law. `prediction` returns `D g_hat` and `D C D^T`; `cross_prediction_covariance` supplies `D(n) C D(n')^T`. The latter is covariance of the fitted mean field due to uncertain parameters, not the unknown spatial covariance of the actual catalogue measurement errors.

Using c299792458m/s and a Julian year,1μas/yr corresponds to4.6056571e-11m/s². The reconstructed amplitude is5.046236μas/yr, or2.3241234e-10m/s²; this is the published result represented in Cartesian form, not a new acceleration detection. The covariance is positive definite with eigenvalues(.120563,.127034,.172603), condition1.432. Its nominal Gaussian joint95% ellipsoid uses q=7.8147279 and principal semiaxes(.970652,.996361,1.161399)μas/yr. These are not calibrated total-error confidence bounds.

For a deterministic additive E1 bias bounded in Euclidean angular-rate norm, the minimum bias needed to make zero enter that nominal95% region is4.0723006μas/yr. The code solves the convex KKT equations and checks the boundary and gradient. This is a useful sensitivity threshold, not an observational upper bound on systematics. Without an admitted bias bound the threshold does not restore a cosmic detection.

## A source-table falsifier that stays failed

The chosen equatorial covariance transforms mathematically as `R C R^T`, and its field/likelihood are rotation invariant. However, the resulting Galactic correlations are `(.0112089,-.0265794,-.0682466)` for XY,XZ,YZ, whereas Table2 prints `(.036,-.014,-.079)`. Do not replace either source block or average them.

We checked the usual printed-precision explanation. Let each equatorial sigma lie within its printed value±.005 and each correlation within±.0005. For each parameter box, interval products enclose the six covariance entries; a linear interval transform encloses Galactic CXY,CXX,CYY; the positive-denominator ratio encloses rhoXY. Branching the input box twice gives a global numerical upper enclosure of rhoXY≤.0353435732, below the separately printed Galactic lower endpoint.0355. Calculations use ordinary float64 with conservative1e-12 arithmetic padding, not a formal directed-rounding proof. The observed margin is about1.56e-4, many orders above roundoff. `published_frame_covariance_audit()` returns `FAIL_PRINTED_FRAME_COVARIANCE_PARITY`; passing implementation tests verify this failure is retained. A corner scan alone was insufficient as a proof and was replaced by the interval enclosure.

This is an unresolved source precision/estimator discrepancy under a stated rounding model. Separate bootstrap procedures, an unreported precision convention, or an erratum could explain it; we do not infer which or allege the astrometric result is false. It prevents claiming that both printed frame covariance blocks are one fully verified joint summary. The ICRS matrix can still be consumed as an explicitly chosen source-conditional working law, with this limitation visible.

## Constructive null-space result and original K03 decision

Even granting the working covariance, let `g_obs=k+b`, with k an intended cosmic-acceleration contribution in the same angular pattern and b an unrestricted local Galactic/source/frame E1 contribution. The compressed response is `[I3 I3]`, rank3 for6parameters, with exact null directions `(delta,-delta)`. For every k, choosing `b=g_hat-k` yields profile quadratic zero. The code evaluates this at zero, moderate and million-unit candidate k; residual roundoff remains below2e-19. The cosmic identified set is all R³. This is a derived limitation of the stated additive model, not a claim that a fully specified physical model can never constrain cosmic acceleration.

| Target | What this subchannel supplies | Remaining physical input |
|---|---|---|
| Observer a_obs | Nonradial electric-dipole response; correlated working likelihood; nominal ellipsoid and bias threshold | Full systematic covariance/justified bound and source-table clarification for stronger statistical use |
| Cosmic A_a | No admitted mapping or finite identified set | Congruence/frame history map and independently restricted local/source E1 nuisance |
| Cosmic omega | No inference from E1; B1 remains frame-spin degenerate in legacy analysis | Qualified physical curl/NNR/frame transfer |
| beta/tilt | A constant aberrational displacement is not determined from quasar proper-motion drift | Time/depth-dependent source/observer optical response; constant beta derivative alone is insufficient |
| kSZ/polarization | None supplied | Their source-matched physical responses and uncertainties |

The original objective is “Secure nonradial physical observables and matching covariance for omega/A/beta”; output is “physical kSZ/polarization/proper-motion channel response”; acceptance is “Independent source qualification and nonradial response demonstrated”. The observer proper-motion response portion is now derived and executable with a real published vector/covariance. The original omega/A/beta objective is not met merely by relabeling observer a_obs as A_a. The unresolved printed covariance parity is a second, independent source qualification limitation. Recommendation: retain original K03 pending, record this bounded subchannel advance, and do not add to completed-node counts or promote K05. This decision uses the original estimands; it does not invent a blanket requirement for unrelated sectors to share one covariance.

## Validation and handoff

Run `python acceleration_channel.py` to generate `RESULT.json`, and `python -m unittest discover -s . -p 'test_*.py' -v` inside this directory.9tests pass: source covariance/units, direct aberration derivative, apex/sign/rank, electric divergence/curl, rotation of field/covariance/likelihood, cross-sky covariance PSD, printed-precision audit, convex sensitivity threshold and exact additive degeneracy. Initial validation exposed an over-tight1e-15 numerical apex tolerance (observed1.60e-15; repaired to3e-15) and the genuine printed-frame covariance parity failure (retained, not relaxed). Runtime/commands/initial errors are in `VALIDATION.json`.

Primary scientific kill switches: no automatic cosmic interpretation of observer a_obs; no independent likelihood multiplication across legacyGaia/Quaia/radio overlaps; no diagonal replacement for newer marginal intervals; no promotion of bootstrap covariance to full spatial/systematic covariance. Authored deliverables are this report, script, tests, `RESULT.json`, `source_registry.json`, `VALIDATION.json`. The `raw/` PDF,text and screenshot are read-only source evidence and excluded from publication. Parent independent review should decide admission; author tests alone do not establish independent review.
