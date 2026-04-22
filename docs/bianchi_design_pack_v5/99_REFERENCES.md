# 99. References
## primary sources / implementation lookup priority / why each source matters

---

## 0. lookup order

This v5 bundle has no active unresolved backend placeholders. If a future patch introduces one, consult sources in this order:

1. package authority docs
2. primary formalism reference
3. backend-specific or numerical-method reference
4. only then secondary literature

---

## 1. 1+3 orthonormal frame and Bianchi dynamics

### Uggla, van Elst, Wainwright, Ellis
- topic: orthonormal frame approach and dynamical systems in cosmology
- why it matters: background 1+3 / frame-based Bianchi setup

### Challinor and collaborators
- topic: covariant radiative transport, PSTF multipoles, polarization
- why it matters: exact electron-frame scattering, multipoles, basis transport

### Pereira / Pitrou / collaborators
- topic: isotropic-limit Bianchi subsets, curved-space mode structure
- why it matters: family-aware backends, isotropic-limit seed logic

---

## 2. numerical and source-history references

### SUNDIALS ARKODE docs
- topic: additive Runge–Kutta IMEX infrastructure
- why it matters: hierarchy stiff/nonstiff split

### HYREC-2
- topic: recombination history adapter
- why it matters: isotropic-history recombination baseline

---

## 3. formerly unresolved items now frozen

These items are now frozen in `03B_FROZEN_BACKEND_CONSTANTS_AND_LOOKUP_RESOLUTION.md` and the verification pack:

- intrinsic-family backend constants for II/III/IV/VI_0/VI_h/VII_h
- Type VIII principal/discrete-series label and Plancherel measure conventions
- discrete weighted \(L^2\) seed normalization
- package-wide collocation defaults
- HYREC-like recombination adapter I/O contract
- HEALPix/healpy harmonic packing rule

---

## 4. citation discipline

Any formula, branch convention, or backend-specific normalization imported from outside this pack must be:
1. cited in the implementation patch note,
2. copied into a local authority note if it becomes load-bearing,
3. never left as an implicit memory-based convention.


## 5. concrete primary-source anchors used by v5 frozen constants

### van Elst & Uggla (1996)
- title: *General Relativistic 1+3 Orthonormal Frame Approach Revisited*
- why it matters: 1+3 orthonormal-frame equations, frame derivatives, constraint language
- identifier: arXiv:gr-qc/9603026

### Ellis & van Elst (1998 lectures)
- title: *Cosmological Models (Cargèse lectures)*
- why it matters: canonical Bianchi classification, class-A/B structure constants, parameter \(h=a^2/(n_2 n_3)\)
- identifier: arXiv:gr-qc/9812046

### Challinor (1999)
- title: *The Covariant Perturbative Approach to Cosmic Microwave Background Anisotropies*
- why it matters: exact polarized radiative transport and electron-frame Thomson scattering
- identifier: arXiv:astro-ph/9903283

### Avetisyan & Verch (2013)
- title: *Explicit harmonic and spectral analysis in Bianchi I–VII type cosmologies*
- why it matters: solvable-family dual spaces, cross-sections, Plancherel measures, scalar spectral ODE
- identifiers: DOI 10.1088/0264-9381/30/15/155006, arXiv:1212.6180

### Pereira & Pitrou (2019)
- title: *Bianchi spacetimes as supercurvature modes around isotropic cosmologies*
- why it matters: isotropic-limit subset and supercurvature/open-branch interpretation
- identifier: DOI 10.1103/PhysRevD.100.123534, arXiv:1909.13688

### Iliesiu, Pufu, Verlinde, Wang (2019)
- title: *An exact quantization of Jackiw–Teitelboim gravity*
- why it matters: explicit \(\widetilde{SL}(2,\mathbb R)\) principal/discrete-series Plancherel densities used for Type VIII authority freeze
- identifier: DOI 10.1007/JHEP11(2019)091

### Kitaev (2018 notes)
- title: *Notes on \(\widetilde{SL}(2,\mathbb R)\) representations*
- why it matters: representation labels and Fourier/Plancherel language for the universal cover
- identifier: arXiv:1711.08169

### HYREC-2
- title: *HYREC-2: a highly accurate sub-millisecond recombination code*
- why it matters: isotropic-history recombination adapter
- identifiers: arXiv:2007.14114, official repository `nanoomlee/HYREC-2`

### SUNDIALS ARKODE documentation
- why it matters: additive Runge–Kutta IMEX solver split \(M(t)\dot y=f^E+f^I\)
- identifier: ARKODE official docs

### HEALPix FITS specification and healpy Alm.getidx
- why it matters: map metadata, m-major \(a_{\ell m}\) packing, interoperability
- identifiers: HEALPix FITS spec PDF, healpy `Alm.getidx` docs
