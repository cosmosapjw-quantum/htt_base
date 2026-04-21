# 99. References
## primary sources / implementation lookup priority / why each source matters

---

## 0. lookup order

When a design card marks an item as `LOOKUP_REQUIRED`, consult sources in this order:

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

## 3. lookup-required examples

- unavailable analytic backend details for intrinsic families
- special-function normalization not written in family cards
- backend-specific collocation constants
- harmonic library storage order if it differs from package recommendation

---

## 4. citation discipline

Any formula, branch convention, or backend-specific normalization imported from outside this pack must be:
1. cited in the implementation patch note,
2. copied into a local authority note if it becomes load-bearing,
3. never left as an implicit memory-based convention.
