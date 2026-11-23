# Signed transfer references

The three comparisons in `SIGNED_REFERENCE.json` exercise different inputs. They were executed on the R102 native checkout. The command below runs the same comparisons for the current checkout. The script writes the BASS commit to the output and uses temporary paths for upstream solver output.

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH="$PWD/htt"
reference_root=/home/cosmosapjw/workdir/htt_external_physics_20261015/reference_code
.venv/bin/python scripts/r103/signed_reference.py \
  --anilos-root "$reference_root/AniLoS" \
  --aniclass-root "$reference_root/AniCLASS" \
  --output /tmp/htt_r103_signed_reference.json
```

## Thomson block

Take forward positive scattering depth in the cold-electron frame. For conformal time in seconds, $ds=a n_e\sigma_T c\,d\eta$. With no streaming, sources or shear, Eqs. 18–24 of Vicente, Pereira & Pitrou give $ d(\Theta_2,E_2)^t/ds=M(\Theta_2,E_2)^t$, where

```text
M = [[−9, −√6], [−√6, −4]] / 10 .
```

Use the signed BASS linear-polarization convention `−(Q±iU)=Σ(E±iB) {}_{±2}Y`. In the isolated two-component block the change from the source convention is $D=\mathrm{diag}(1,-1)$, after removing its common harmonic phase. The rates are −1 and −3/10. With $M_B=DMD$, the slow-mode projector is $P=(I+M_B)/(7/10)$. The closed solution is $e^{-s}(I-P)+e^{-3s/10}P$. Tests inject ten real modes spanning the temperature and electric quadrupoles and measure the complete outgoing Stokes vector. Both a native harmonic generator and the finite-depth angular coherency propagator are compared with this solution. The multistep SDIRK check uses 4, 8 and 16 steps at $s=1$. There are no collisional magnetic or circular sources in this fixture.

Source: [Vicente et al., §§III.1 and IV](https://arxiv.org/html/2506.07786v2).

## Closed IX with both handednesses

Work in units of the curvature radius $\ell_c$ and use dimensionless conformal distance $u=c\eta/\ell_c$. A round spatial IX geometry has commutator matrix $n^{ij}=\pm2\delta^{ij}/\ell_c$, with vanishing class-B vector and shear. This free-propagation coefficient maps to the upstream branch $K>0,\ \nu\ell_c=\pm3$. For the homogeneous tensor quadrupole $m=+2$, the free-transport part rotates $E,B$ at signed rate $4\nu\ell_c/[2(2+1)]=\pm2$. Both signs are tested. The initial data independently excite each of T, E and B. Optical depth increases at $ds/du=1.7$ until $u=0.43$. Fix the metric, set the photon gravity source to zero, and set the neutrino quadrupole and shear perturbations to zero. Under these assumptions the three-component subspace closes. In the two codes' internal tensor variables the isolated transfer blocks are related by $D=\mathrm{diag}(1,-1,-1)$. Relative signs are checked separately by pure input channels and by the leakage to all other modes.

The external RHS is executed from AniLoS commit `9b7a2611882dcca80a1491bcad2b8f05635faca7`, `src/anilos/hierarchy.py` Git blob `d54fdf7d1c757d249105602b19fe40441813d70e`. The runner verifies the complete source file before evaluating the original NumPy function without its Numba compilation decorator. External time integration uses SciPy DOP853. BASS integrates the same block using 128 SDIRK substeps. This tests independent implementations of the coupled collision and spin transport in a prescribed closed background. Time-dependent Einstein feedback, recombination, neutrino sourcing and radial line-of-sight integration enter the cosmological comparison below or remain open.

Source: [upstream tensor RHS](https://github.com/jgvicente/AniLoS/blob/9b7a2611882dcca80a1491bcad2b8f05635faca7/src/anilos/hierarchy.py#L132), [curved mode identifications](https://arxiv.org/html/1909.13688v2).

## Compiled AniCLASS open tensor solve

The checkout at `be1e43fcb1d7549710ba3ca2baa74bb0216bd228` supplied a prebuilt executable. Its SHA-256 is in the receipt. The script ran identical open VIIh tensor configurations at $\Omega_k=0.01$ and input $k=0.001\,\mathrm{Mpc}^{-1}$ with `multipole_normalization=tam` and `observable`. It stores the resulting complex observed multipoles at every integer $2\leq\ell\leq16$. The measured conversion to observed coefficients is $i^\ell\sqrt{4\pi/(2\ell+1)}$ times the TAM value, with an extra minus sign for magnetic polarization. Omitting that minus sign gave a normalized error of 2.0. Source `transfer.c` uses explicit tensor/vector magnetic-mode branches. The header for the complex q/ν values of this executable contains a literal invalid numeric format directive, so the receipt records the parsed input parameters.

The compiled open-universe runs above exercised AniCLASS only. The BASS comparison recorded here used the prescribed closed IX test-photon block on R102, commit `664845022a9600ad925d6c1332143395aac5ed90`. R103 adds a common-tilt, isotropic-rest-frame initialization and an optional collisionless massless-neutrino hierarchy. Its default uses one interacting radiation species. In the split mode each species carries its own energy-normalized angular stress, and Thomson exchange connects photons and baryons. See the massless-neutrino run receipt for its coupled checks. Matching the open cosmological $a_{\ell m}$ requires a common background, regular tensor metric and species initial data, visibility, helicity, and observation tetrad. The present cosmological output remains an external reference for that comparison.

For curvature the primary paper's Table 1, its examples and the AniLoS implementation give $K=-\Omega_k H_0^2/c^2$. Open VIIh uses $\nu=m/\ell_s+i/\ell_c$, while closed IX uses $\nu=\pm3/\ell_c$. The inequalities printed next to Eq. 42 are reversed relative to that convention. AniLoS replaces an exact zero curvature input with $10^{-6}$. Exact flat-space regression should use an analytic fixture.

Source: [Vicente et al., Fig. 8 and Eq. 46](https://arxiv.org/html/2506.07786v2), [AniLoS parameter mapping](https://github.com/jgvicente/AniLoS/blob/9b7a2611882dcca80a1491bcad2b8f05635faca7/src/anilos/anilos.py#L201).
