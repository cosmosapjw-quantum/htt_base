# 06A. Output Schema and Metadata Note
## harmonic ordering / archive objects / map schema / boost-split metadata

---

## 0. purpose

이 문서는 observables appendix를 implementation agent가 바로 사용할 수 있도록
archive schema와 metadata key를 고정한다.

---

## 1. mandatory archive layout

Every opened output gate must produce:

1. `solver_summary.json`
2. `alm_det.npz`
3. `alm_stoch.npz`
4. `alm_boost.npz`
5. optional `maps_tqu.fits` or equivalent once map gate opens

---

## 2. `solver_summary.json` minimum keys

```json
{
  "family": "...",
  "branch": "...",
  "backend": "...",
  "ic_mode": "...",
  "lmax_dev": 0,
  "lmax_prod": 0,
  "ordering": "...",
  "boost_applied": false,
  "global_tilt_present": false,
  "residual_summary": {...},
  "gate_status": {...}
}
```

---

## 3. harmonic archive contract

Each `alm_*.npz` file must store:

- `lmax`
- `ordering`
- `alm_T`
- `alm_E`
- `alm_B`
- `metadata_json`

### recommended \((\ell,m)\) order
\[
(0,0),(1,-1),(1,0),(1,1),\ldots
\]
unless a chosen harmonic library imposes a documented alternate order.

---

## 4. map-domain schema once map gate opens

The optional map file must store, at minimum:

- `T_map`
- `Q_map`
- `U_map`
- `nside_or_resolution`
- `pixel_ordering`
- `mask_if_any`
- `beam_if_any`
- `boost_applied`
- `global_tilt_present`
- `det_stoch_boost_split_available`

If a FITS-like container is used, the metadata must repeat these fields.

---

## 5. mandatory split semantics

### `alm_det`
must contain only deterministic forward-model contribution

### `alm_stoch`
must contain only stochastic perturbation contribution

### `alm_boost`
must contain only output-stage observer-boost contribution

If boost is not applied, `alm_boost` still exists with explicit zero arrays and metadata `boost_applied=false`.

---

## 6. output-only boost metadata rule

The metadata must contain both:

- `global_tilt_present`
- `boost_applied`

This prevents output consumers from conflating the two.

---

## 7. archive validity checks

Before writing an archive, the implementation must check:

- harmonic ordering recorded
- boost flags consistent
- split files all present
- residual summary finite
- family/branch/backend labels present

---

## 8. one-line summary

이 문서는  
**observables appendix를 실제 저장/전달 규약으로 닫는 schema note** 다.
