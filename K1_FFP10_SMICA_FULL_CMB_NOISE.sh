#!/usr/bin/env bash
# K1_FFP10_SMICA_FULL_CMB_NOISE
BASE="http://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID="

# --- CMB MC: 00000-00999, EXCLUDING 00970 (not present in archive) ---
for i in $(seq -w 0 999); do
  [ "$i" = "0970" ] && continue   # seq -w uses 4 digits; see note below
  f="dx12_v3_smica_cmb_mc_$(printf '%05d' $((10#$i)))_raw.fits"
  wget -O "$f" "${BASE}${f}"
done

# --- NOISE MC: 00000-00299 (complete) ---
for i in $(seq 0 299); do
  f="dx12_v3_smica_noise_mc_$(printf '%05d' "$i")_raw.fits"
  wget -O "$f" "${BASE}${f}"
done