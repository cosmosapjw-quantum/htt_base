# Act Dr4 Archive Windowed Fixed Yp2 Sensitivity

Owner: HTT. Diagnostic-only; scientific admission not evaluated.

Source: [release documentation](https://github.com/ACTCollaboration/pyactlike/blob/master/pyactlike/like.py). Exact methods, arrays and limitations: `result.json`; source/code/runtime receipt: `execution_receipt.json`.

- Deep then wide TT40/TE45/EE45; exact archived windows and full covariance
- Source procedure: Dl->Cl, 150x150 window blocks, TT bins5:45, TE/EE first45
- Theory truncated above ell5000 exactly as archived standalone default, not a missing-input fill
- yp2 grid fixed at 0.95,0.97,1,1.03; no optimization or posterior
- Foregrounds already marginalized by release; official full-likelihood runtime parity not established
- Do not substitute plotting-only coadded Dl errors for this covariance
- No calibrated quadratic p-value or independent combination with Planck
