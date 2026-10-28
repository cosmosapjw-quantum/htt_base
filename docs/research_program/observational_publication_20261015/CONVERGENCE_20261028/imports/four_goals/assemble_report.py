from pathlib import Path
import re

W=Path(__file__).resolve().parent
head=r'''---
title: "From sky morphology to physical confidence images"
subtitle: "Four constructive research routes with radiation, optical and fibre responses"
author: "HTT internal theory study"
date: "28 October 2026"
geometry: margin=22mm
fontsize: 10pt
colorlinks: true
---

# The recovered research programme

The original target is physical: infer specified kinematics and geometry from observed angular and depth structure. The five coordinates $(x,F,Q,\Pi,G_F)$ can retain their roles while their domain expands to signed STF/PSTF tensors, calibrated polarization states and their detector-accessible images. A matrix-valued matter response does not replace the spacetime metric or the observer congruence. It identifies additional physical information only through a specified source, transport and measurement map.

This report develops four concrete routes: low-multipole morphology and radiation-to-kinematics; beyond-FLRW kinematic measurement; anisotropy-family classification including supplied Bianchi geometries; and directional Hubble/optical-distance consistency. Each route includes a mathematical construction, a finite executed control, reuse of the latest pushed work and a precise next observable contract. The separate fibre-count experiment tests what actual analyzer channels preserve. The joint-error section connects the new MF02 reduction bounds to physical confidence regions.

The active branch was freshly checked at `7f3f49a6b6d9`, unchanged from the preceding foundation pass. Current R36 results include the positive radiation shear operator, exact nonlinear temperature-to-stress tests, optical source Jacobians and joint octupole budget, common E2 PM-history response, and finite geometry images. They are reused at their qualified conditional scope. The two new source documents are the 152-page MF02 unified fibre note and the 14-page optical manuscript. Full source identities, code and numerical receipts accompany the report. No push, live-controller change, native solver, ODE evolution or raw-catalogue refit was performed.

## What this pass establishes

| Original objective | Constructive result in this pass | Physical use |
|:--|:--|:--|
| Low-$\ell$ morphology and dipole/radiation response | A common 23-component linear carrier preserves Thomson gain and the whole shear operator; 20 suffice without circular polarization. A polarized collision omission gives an explicit shear-bias bound. | Identify the intensity and polarization moments required for a conditional MES inverse. |
| Beyond-FLRW kinematic quantities | A finite detector-rank formula and a calibrated radial/transverse inverse, with frame-spin and source kernels retained. | Construct joint regions for the identifiable shear, expansion, vorticity-relative-to-frame and internal-response components. |
| Anisotropy and Bianchi-family comparison | A Gauss bridge to spatial Ricci, orbit-aware compatible-family sets, finite separation certificates and an exact fixed-quadrupole chirality sign radius. | Compare supplied physical families without forcing a geometric label from one morphology scalar. |
| Direction/redshift-dependent Hubble factor | An opacity/finite-distance local Hubble interval, calibrated matrix-distance bounds, and opacity-qualified CBL/curvature regions. | Separate optical-response uncertainty from the geometric quantity being tested. |

The most useful new connection is a complete error path. MF02 supplies a conditional state-reduction bound. The source and detector map turn it into a *joint* observable error body. The kinematic response turns that body into a parameter bias bound. A common statistical event then gives physical confidence images and family compatibility. The supporting linear algebra and robust-inference tools are established; the scientific content lies in the supplied physical response and the quantities it permits us to constrain.

## Four distinctions carried through every route

| Axis | What is held distinct |
|:--|:--|
| Symmetry and redundancy | Passive coordinate/triad/fibre changes; active model orientation; actual photon polarization rotation; unknown calibration. |
| Invariants | Scalar powers, trace, spectra and chirality relative to their stated transformation group and physical question. |
| Observables | Detector counts, Stokes channels, radial distance response and transverse proper motion, with selection and covariance. |
| Physical quantities | The chosen congruence's kinematics, radiation stress, internal drift/transport, spatial curvature and family parameters. |

Throughout, the physical velocity has $u^au_a=-c^2$. A unit velocity is written $\bar u=u/c$ when translating the optical manuscript. A density-normalized internal drift is a matter response, not another classical congruence. In particular, opposite helicity currents can coexist with unchanged total stress. Isotropy under proper rotations also does not require parity symmetry: a circular-polarization imbalance alone is not a geometric FLRW violation.

For comparison across fibres, transform state, detector effect and channel together. A geometric photon screen connection preserves helicity; it does not supply an arbitrary SU(2) analyzer rotation. Actual polarization conversion must be a specified interaction or instrument operation. These distinctions determine the ranks in the count experiment below.

'''

def read_lane(name):
    s=(W/'lanes'/name).read_text()
    # Each lane is independently readable. Remove only its dated workflow paragraph
    # in the integrated exposition; all science and detailed evidence remain.
    lines=s.splitlines()
    lines=[line for line in lines if not line.startswith('28 October 2026.')]
    s='\n'.join(lines)
    return s.strip()+'\n'

sections=[
 ('GOAL1_MORPHOLOGY.md','goal1_thomson_carrier','Positive input skies, the shear-operator difference, and detector-accessible response ranks.'),
 ('GOAL2_KINEMATICS.md','goal2_kinematic_design','Finite instrument ranks and the matrix-log variation check.'),
 ('GOAL3_CLASSIFICATION.md',None,None),
 ('GOAL4_HUBBLE_CBL.md',None,None),
 ('FIBRE_INFO.md',None,None),
 ('JOINT_REMAINDER.md','joint_remainder','A supplied physical response-error bound propagated into simultaneous parameter coverage; synthetic fixed-law controls.')]

tail=r'''
# A concrete continuation for the original four goals

The next work should use the already retained observational carriers and the smallest additional response inputs. The matrix generalization need not become a prerequisite for every existing scalar/optical result.

1. **Radiation:** apply the exact intensity adapter to a common T/Q/U carrier, retaining intensity degrees 0,2,4 and the integrated linear-polarization source. Compute a joint shear-support curve against a declared derivative/collision budget. Include circular data only for a circular-polarization target. This directly compares the full and unpolarized conditional physical inverse.
2. **Kinematics:** reuse the R36 optical Jacobians, shared octupole budget and PM-history E2 response. Fit the matched source response with its calibration nullspace. Use a source-qualified radial/transverse pair before interpreting a recovered matrix gradient as geometric vorticity. Add the two supplied bridge paragraphs to the optical discussion only within that physical scope.
3. **Classification:** select already supplied physical response families, including their histories and orientation domains. Map one confidence event to compatible family images, retain an out-of-family diagnostic, and plot separation against the physical error budget. CMB Bianchi classification additionally needs full, qualified T/E/B family templates; the current finite Ricci experiment supplies a geometry-response result, not that missing transfer.
4. **Hubble/curvature:** begin with the existing released SN/optical response and independently qualified expansion measurements. Use a bounded opacity function and test a common first-derivative curvature constant across windows. Polarimetric channel shape can constrain dichroism, while an independent calibration or physical bound supplies the grey direction. This produces an identified region even when a unique corrected distance is unavailable.

These units admit an informative scientific result before every nuisance is identified: an interval, a response-sensitive upper bound, a common nullspace, a family compatibility set, or a quantified approximation error. Their completion does not redefine the original 42-node acceptance. The accompanying research-unit JSON records the inputs and concrete checks without changing the existing controller.

# Reproducibility and source interpretation

All new computations are finite linear algebra, exact rational angular moments, quadrature, analytic matrix jets or fixed-law Monte Carlo. Actual Wolfram checks verified the STF and optical identities and the noncommuting CBL formulas; unsuccessful syntax/context calls and local missing-package repairs are retained with their replacements. A separate native reviewer used an independent exact angular-moment implementation and independent rank/matrix checks. Numerical precision checks support the stated finite constructions, while the displayed proofs supply their domains.

The attached MF02 Eq. (1.6.8), checked on the rendered page, already uses the positive multiplicative form $f_0(E)[I+\varepsilon(n\cdot e)\sigma_3]$. The additive form in the pasted proposal/text extraction should not be attributed to a defect in the PDF. Likewise the attachment itself already distinguishes grey loss, channel shape and the limits of observational tomography. Several corrections in this report therefore repair the proposed application shortcuts, while preserving the source's actual qualifications.

The separate research-decision memo compares candidate contributions with polarized radiative transfer, optimal compression, process tomography, opacity-aware CBL work and robust inference. This report states the physical constructions and their evidence. Full-source texts of third-party papers are not redistributed; primary URLs and read scope are recorded. The user's two attachments and the small source-bound R36 geometry fixture are retained in the reproduction bundle.
'''

parts=[head]
for name,fig,caption in sections:
    parts.append('\n\n'+read_lane(name)+'\n')
    if fig:parts.append(f'\n![{caption}](../figures/{fig}.png){{width=100%}}\n')
parts.append(tail)
s=''.join(parts)
s=s.replace(r'\dim_\mathbb R',r'\dim_{\mathbb R}')
s=s.replace('- New code: `code/goal3_classification.py`; machine-readable results: `lanes/GOAL3_CLASSIFICATION.json`; plot: `figures/goal3_classification.png` and vector PDF. Final executed command: `OPENBLAS_NUM_THREADS=1 python code/goal3_classification.py`, exit 0.', '- Computation: `code/goal3_classification.py` (exit 0).\n- Numerical receipt: `lanes/GOAL3_CLASSIFICATION.json`.\n- Figure: `figures/goal3_classification.png` and vector PDF.\n\nThe bundle README gives the complete reproduction commands.')
# Normalize display delimiters and eliminate paragraph breaks inside math blocks.
s=re.sub(r'\\\[(.*?)\\\]',lambda m:'$$\n'+re.sub(r'\n\s*\n','\n',m.group(1).strip())+'\n$$',s,flags=re.S)
# Long identities remain byte-exact in source manifests, with short display in PDF.
s=re.sub(r'(?<![0-9a-f])([0-9a-f]{40})(?![0-9a-f])',lambda m:m.group(1)[:12],s)
(W/'output/FOUR_GOALS_REPORT.md').write_text(s)
print('Words:',len(s.split()))
