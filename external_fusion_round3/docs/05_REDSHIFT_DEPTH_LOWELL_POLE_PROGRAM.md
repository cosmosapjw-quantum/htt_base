# Redshift/Depth-Resolved CMB Low-ell Pole Programme

## 1. Four distinct objects

The symbol `pole(z)` is forbidden without a type tag.  The programme uses:

1. `ShellSourcePole[ell,z_bin]`: the pole of a registered line-of-sight source contribution in a redshift shell.
2. `CumulativeObserverPole[ell,z_max]`: the pole after accumulating source shells to depth `z_max`, with the local observer endpoint carried separately.
3. `RemoteDipolePole[z_bin]`: the CMB dipole seen at remote electron locations, reconstructed through kSZ tomography.
4. `RemoteQuadrupolePole[z_bin]`: the remote CMB quadrupole, reconstructed through pSZ statistics.

These objects cannot be added or compared without a registered bridge and their full cross-covariance.

## 2. Scientific discrimination target

A local boost is an observer-end boundary transformation.  A coherent global source is present in remote fields and in source-shell transfer.  Local structure is strongest at shallow depth and follows the density/velocity field.  The decisive programme therefore combines:

\[
\mathcal O = \{p_\ell^{\rm local},\ p_\ell^{\rm shell}(z),\ v_{\rm eff}(z),\ q_{\rm eff}(z),\delta_g(z)\}
\]

rather than comparing one present-day dipole amplitude with one bulk-flow number.

Registered summary families include

\[
A_\ell(z_i,z_j)=|\hat p_\ell(z_i)\cdot\hat p_\ell(z_j)|,
\]

cumulative pole drift, remote/local mean-axis separation, cross-ell alignment, power-tensor eigen-gap, and the nuisance-projected response singular spectrum.  Oriented dipoles use a signed dot product; unoriented quadrupole/octupole axes use an absolute dot product.

## 3. Track-I simulation stack

### Stage I-A — dependency-free reference

Use `src/htt_ext/lowell` and `src/htt_ext/remote` to validate rotation, reality, source-superposition, coverage and abstention gates.  This stage is never a cosmological transfer result.

### Stage I-B — FLRW line-of-sight shell transfer

- CAMB: baseline CMB spectra, source windows and CMB/source cross-correlations.
- CLASS: independent perturbation and transfer output.
- nanoCMB or another readable line-of-sight implementation: source-term audit and shell-sum oracle.
- healpy/S2FFT: correlated shell alm generation and rotations.

Redshift bins are frozen before data use.  SW, Doppler, early ISW, late ISW and observer endpoint are stored separately.  Two shell refinements must reproduce the total low-ell transfer and stable identified pole regions.

### Stage I-C — LSS, foreground and survey windows

- GLASS: correlated lightcone density/lensing/tracer shells.
- PySM3 or selected PanEx products: Galactic foreground complexity.
- NaMaster/pspy: masked-sky spectra and covariance baselines.
- S2WAV/S2FFT: directional and differentiable morphology.
- optional WebSky/PM subsets: non-Gaussian and velocity-field reality checks.

### Stage I-D — remote fields

Implement the remote dipole/quadrupole kernels and mock quadratic estimators following the kSZ/pSZ literature.  Optical-depth bias, galaxy-electron response, foregrounds and estimator mean field remain explicit nuisances.

## 4. Actual-data comparison ladder

1. **Local present-observer pole:** official Planck PR3 SMICA/Commander/NILC/SEVEM maps and common masks.  Map products are one sky and are treated as a nuisance family, not independent replications.
2. **Remote dipole summary:** Planck + unWISE velocity-reconstruction constraints and, where public products permit, an independent reimplementation.  The ACT+DESI velocity-reconstruction measurements provide a higher-S/N external comparison but have different tracer/window/foreground assumptions.
3. **Remote quadrupole summary:** the Planck/ACT + unWISE/CIB pSZ bispectrum constraints are incorporated as a low-S/N identified region, not a zero field.
4. **LSS shell comparison:** GLASS/COFFE and public galaxy maps/catalo gs predict the local-structure contribution and redshift dependence.

Evidence tiers are `PAPER_SUMMARY`, `PUBLIC_BANDPOWER_OR_MAP`, and `FULL_RECONSTRUCTION_CODE`.  A lower tier cannot masquerade as a higher tier.

## 5. Local-boost/global-tilt hypotheses

- `H_LOCAL`: known observer boost plus FLRW primordial/LSS fields.
- `H_LSS`: local density/velocity field and survey selection without global coherent source.
- `H_GLOBAL_PHENO`: adversarial coherent source family used only in Track I.
- `H_GLOBAL_NATIVE`: native Bianchi/multi-fluid transfer, Track II only.
- `H_MIX`: superposition of local, LSS, systematics and global components.
- `H_UNKNOWN`: contamination outside the model list; must yield inadequacy/abstention.

`H_GLOBAL_PHENO` is not a substitute for `H_GLOBAL_NATIVE`.  Its role is to design and stress-test the statistical machinery before the solver arrives.

## 6. Track-II native upgrade

The native solver must output shell-resolved T/E/B transfer, remote observer dipole/quadrupole fields, frame/tetrad metadata and error estimates.  Paired boosted/unboosted runs establish the local endpoint response.  Only then can a Bianchi family/mode redshift-pole atlas and geometry-level response quotient be constructed.

## 7. Strict success criteria

- Rotation covariance error below 1e-9 for the reference pole implementation.
- Physical shell totals agree across CAMB/CLASS/readable oracle within preregistered tolerance.
- Pole region coverage reaches the registered 95% target with a 99% binomial lower bound at least 0.93.
- Confusable or superposed sources trigger abstention rather than forced global labels.
- Mask/foreground/map-product variation is contained in the reported region.
- Remote-field amplitude claims expose optical-depth bias; low-S/N bins do not receive point poles.
- Actual-data statistics, bins and source family are frozen before unblinding.
- Track-I outputs never emit Bianchi family or geometry claims.
