# 14 · Observer frame (FB-8)

Observer-frame layering sits on top of the FB-7 cosmological-frame
likelihood and stays type-distinct from the cosmological tilt surface.
The rendered PNGs in this topic document the four operational pieces of
that layer:

- `01_kernel_heatmap_1p23e-3.png`:
  aligned aberration kernel `K_{ell ell'}` at the Sun-dipole speed
  `beta_obs = 1.23e-3`, including the small off-diagonal leakage around
  the identity.
- `02_Cl_ratio_before_after.png`:
  diagonal-spectrum adapter response
  `C_ell^{obs} / C_ell^{frame}` on a synthetic TT/EE/TE/BB ladder.
- `03_alm_mixing_demo.png`:
  a single synthetic `a_{ell m}` map before and after the observer
  mixing kernel.
- `04_discriminator_coverage.png`:
  the FB-8.5 empirical-PIT coverage histograms under both `H_obs` and
  `H_cosmo`, with the KS-uniformity gate annotated on-panel.

Generator:
[`scripts/make_physics_gallery.py`](../../../scripts/make_physics_gallery.py)
Topic key: `14_observer_frame`.
