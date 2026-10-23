# R24 functional depth images · repaired candidate

The first candidate is archived under `first_candidate_03222b7d/`. Its
functional map used the raw bin intercepts and omitted the shared slope.
The repaired map composes the source M24→Y18 reported-bin transform with
bin and contrast selection. It changes the functional means by up to
8.02452 µas/year and covariance entries
by up to 10.2636 (µas/year)²;
35 of 72 norm Pi cells and
18 of 18 E·B Pi cells change.
The raw intercepts remain explicit alongside Y18 and full24.

The reviewed `tensor_scenario` source is transformed as one full24 joint object. Its original
24-coordinate mean/covariance and all 4096 retained sample rows are carried in `RESULT.json`
and `IMAGES.npz`. The 36-coordinate functional image includes E1 polar and B1 axial
three-vectors for each of three reported-redshift bins, both adjacent contrasts, and
the deep–shallow contrast. The full 36×36 covariance preserves common slope/nuisance
and cross-bin blocks. `Y18` and anchored `Z18=(Y0,Y1−Y0,Y2−Y1)` include full
covariance and the same sample rows; neither substitutes for full24.

For the shared full24 `C_ρ` radii [0, 1, 2, 4, 8], every coordinate support
is exact. Each norm interval is a certified conservative outer bound from the
spectral norm and triangle inequality. Positive norm lower bounds number
[12, 12, 10, 4, 1] across the twelve vectors; zero is
contained in [0, 0, 2, 8, 11] intervals. No interval is
presented as a sharp nonlinear image.

The retained law yields strict empirical norm exceedance at thresholds
[0, 1, 2, 5, 10, 20] µas/year and signed
E·B exceedance at [-25, 0, 25]
(µas/year)². There are 25 nontrivial
norm cells and 17 nontrivial
pseudoscalar cells. Ties are excluded. The finite frequency is specific to
these 4096 conditional Gaussian replicate rows; physical Pi remains [0,1]
with unknown mass 1. The 10 µas/year ball and per-image references are
computational conventions. A physical MES anchor is unavailable.

Zeroing cross-depth covariance changes the six contrast spectral scales:
full/zero-cross ratios are [0.195986, 0.22805, 0.21611, 0.253114, 0.280563, 0.326478]. This is a
counterfactual diagnostic, not a valid substitute covariance. The largest
absolute cancellation discrepancy between the direct contrast formula and
the full linear image is 2.33e-15
(µas/year)², against rtol=atol=1e−10. The Y→Z transform has rank 18;
delta-only rank is 12 and loses common mode. M24→Y18 has rank 18 and loses
six full24 directions, so the original carrier remains available.

`NORM_IMAGES.png` uses point markers and known ρ=1 outer bars. The second
figure shows discrete empirical Pi cells and covariance scale ratios. Neither
joins samples or bounds with a chord through a clipping or nonlinear kink.
Both figures concern reported-bin coordinates. True depth, calibrated survey
coverage, physical law, physical source response, tilt identification, R9 and
original 17/42 or 18/42 acceptance remain unavailable or unchanged.

Production: `0` in 0.352s;
plot: `0` in 1.302s;
tests: `0` in 4.017s (7 passed).
Independent review and scientific admission remain pending.
