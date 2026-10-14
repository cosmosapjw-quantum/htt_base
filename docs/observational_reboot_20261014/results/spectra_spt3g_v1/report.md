# Spt3G Source Ordered Cmb Only Window And Beam Control

Owner: HTT. Diagnostic-only; scientific admission not evaluated.

Source: [release documentation](https://lambda.gsfc.nasa.gov/product/spt/). Exact methods, arrays and limitations: `result.json`; source/code/runtime receipt: `execution_receipt.json`.

- Fixed Planck2018 CAMB reference; foregrounds zero, calibration unity, SSL/aberration disabled
- CMB-only residuals include omitted foregrounds; not an adequacy test of the cosmological model
- Actual dataset cuts exclude placeholder TT bins; window columns follow declared spectrum order
- Fractional beam covariance multiplies outer(theory,theory)
- No covariance flooring; nonpositive-definite matrices return typed HOLD
- Official eigenmode conditioning/nuisance likelihood parity not established
- No fitted nuisance posterior or calibrated quadratic p-value
