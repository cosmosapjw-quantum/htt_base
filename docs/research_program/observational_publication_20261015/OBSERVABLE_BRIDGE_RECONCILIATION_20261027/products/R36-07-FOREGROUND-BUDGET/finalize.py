"""Assemble R36-07 actual numeric candidate after both consumer phases finish."""
from pathlib import Path
import csv
import hashlib
import json
import platform
import sys
import time

import numpy as np

PRODUCT=Path(__file__).resolve().parent
EXT=Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_budget_actual')
PACKET=Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/NEXT_006.json')
ACK=Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/ACK_006_GO.json')
CONTRACT=Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_contract_preparation/IMPLEMENTATION_CONTRACT.json')

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def save(path,obj):path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n')

g=json.loads((EXT/'GEOMETRY.json').read_text())
n=json.loads((EXT/'NOISE.json').read_text())
f=json.loads((EXT/'FIRAS_FEASIBILITY.json').read_text())
branches=json.loads((EXT/'BRANCH_SENSITIVITY.json').read_text())
packet=json.loads(PACKET.read_text());ack=json.loads(ACK.read_text())
if packet['packet_id']!=ack['packet_id'] or ack['agent_id']!='/root/rc_7f1ac3df12ebbc36':
 raise RuntimeError('ACTUAL_PACKET_ACK_BINDING')
if ack['go']!='preparation; science waits Astra frozen07contract':
 raise RuntimeError('ACK_GO_TEXT_DRIFT')
if digest(CONTRACT)!='ca09bcbcba470c7712a34c69c793703181b99836f4cb51febdd7471435121089':
 raise RuntimeError('CONTRACT_DRIFT')

with (PRODUCT/'ACTUAL_TABLE.csv').open('w',newline='') as out:
 writer=csv.writer(out)
 writer.writerow(('rho_multiple_of_algebraic_minimum','rho_microK_CMB',
                  'conditional_center_radius_microK_CMB','physical_radius_calibrated'))
 for row in g['conditional_curves']:
  writer.writerow((row['rho_multiple_algebraic_minimum'],row['rho_K_CMB']*1e6,
                   row['s_ball_radius_K_CMB']*1e6,'NO'))
with (PRODUCT/'NOISE_TABLE.csv').open('w',newline='') as out:
 writer=csv.writer(out)
 writer.writerow(('coordinate','center_sigma_worst_microK_CMB',
                  '30_microK_CMB','44_microK_CMB','70_microK_CMB','100_microK_CMB',
                  '143_microK_CMB','217_microK_CMB','353_microK_CMB'))
 for i,label in enumerate(g['coordinate_order']):
  writer.writerow((label,n['center_24_sigma_worst_coordinate_K_CMB'][i]*1e6,
                   *(n['per_band_sigma_worst_coordinate_K_CMB'][str(b)][i]*1e6
                     for b in (30,44,70,100,143,217,353))))

result={
 'schema':'R36-07-actual-foreground-budget-candidate-v1',
 'task_id':'R36-07-FOREGROUND-BUDGET',
 'packet_id':packet['packet_id'],'input_identity':packet['input_identity'],
 'actual_ack_path':str(ACK),'actual_agent':'/root/rc_7f1ac3df12ebbc36',
 'requested_runtime':'gpt-6-sol/high','observed_runtime':'UNKNOWN',
 'checkout_head_at_start':'7a751cc2419f32e98446642b35ca50fa767ebe93',
 'checkout_state_at_start':'DIRTY_EXISTING_PRIMARY_CHECKOUT; unrelated edits preserved',
 'scientific_contract_path':str(CONTRACT),'scientific_contract_sha256':digest(CONTRACT),
 'predecessor_exploratory_candidate':{'identity':'793f49450e26bf0a14da9cd98b6d7b266caa5969436941932fcb266e53ca80a0',
   'preserved_preimages':str(EXT/'preimage_793f49450e26bf0a'),
   'reason':'Exploratory C-vector/covariance numerical equality gate removed; exact observed difference remains unresolved.'},
 'owner':'obsstat','scope':'Actual PR3 S7 finite complex coefficient and marginal-noise diagnostic under conditional R32 common spatial response',
 'claim_tier':'C0','transfer_source':'none',
 'status':'HOLD_MISSING_PHYSICAL_FOREGROUND_UPPER_RADIUS',
 'acceptance_met':False,'qualified_outputs':[], 'independent_review':'PENDING',
 'signature':'(-,+,+,+)','c_m_per_s':299792458,
 'frame':'Galactic COSMO, P=Q+iU, no U flip; exact S7 NSIDE64 selected parent cells',
 'units':{'map_and_coefficients':'K_CMB','display':'microK_CMB','map_covariance':'K_CMB^2',
          'FIRAS':'MJy/sr, absolute sky spectra, not componentwise source upper',
          'future_intensity_to_K_CMB':'1 MJy/sr=1e-20 W m^-2 Hz^-1 sr^-1; divide frequency-specific intensity by dB_nu(T=2.7255 K)/dT using c=299792458 m/s, h=6.62607015e-34 J s, k_B=1.380649e-23 J/K; no RJ substitution. No conversion applied without a certified source functional.'},
 'source_bindings':{
  'R31_numeric':{'path':str(PRODUCT.parents[2]/'PUBLICATION_ACCELERATION_20261025/evidence/R31/report/data/RESULT.json'),
                 'sha256':'b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f'},
  'R32_repair_05':{'sha256':'3517d2f6178a830248b9e32ad57b88c4c7345d6ee39d5bb8cbf9bfb54ea1a86a',
                   'branch':'A_BT_1e-07'},
  'FULL7_CARRIER_sha256':'cda1a0c714221e6c69f975baa3b94ad2c0457975b901393891ac86870a42811d',
  'S7_sha256':'caab42ed1a0d4507b998ce34ad433e8ef9e69e7d1e4b6856f7213599b5465014',
  'SMICA_derived_comparator_sha256':'42a46b0af55bee19b9ce92d51327222509b5e95ac6e32fbd3da5b3f516c71c05',
  'native_map_noise_sources':{b:{'path':row['source_path'],'sha256_from_frozen_manifest':row['source_sha256_from_frozen_manifest'],
                                 'bytes_from_frozen_manifest':row['bytes_from_frozen_manifest']}
                              for b,row in n['receipts'].items()},
  'FIRAS_files':f['source_files']},
 'actual_geometry':{
  'ell':g['ell'],'J0_K_CMB_squared':g['J0_K_CMB_squared'],
  'rho_min_algebraic_K_CMB':g['rho_min_algebraic_K_CMB'],
  'center_24_K_CMB':g['center_24_K_CMB'],
  'center_B_norm_K_CMB':g['center_B_norm_K_CMB'],
  'SMICA_B_descriptive_scale_K_CMB':g['SMICA_B_comparator_K_CMB'],
  'compensators':g['compensators'],'conditional_curves':g['conditional_curves'],
  'six_branch_convention_sensitivity':branches,
  'interpretation':'Every actual coefficient matrix admits a growing free-class CMB/foreground compensator. Algebraic rho_min is a lower representation budget, not a physical upper radius. SMICA is a derived same-sky comparator and its B residual is a different fitted statistic.'},
 'noise_support':{
  'law':n['model'],
  'full_operator':'Retained native-pixel spin-2 sum to E2/E3/B2/B3, all 24 real coordinates; QQ+2QU+UU per selected pixel',
  'scalar_formula':'sigma_worst(v)=sum over native band/pixels sqrt(l_bp(v)^T Sigma_QU,bp l_bp(v)); sharp for a prespecified scalar over PSD completions',
  'callable_support_oracle':'compute.scalar_support_oracle(directions_7x24) reconstructs arbitrary prespecified scalar support from original seven native FITS blocks and exact spin weights; it rereads data on demand',
  'center_24_sigma_worst_coordinate_K_CMB':n['center_24_sigma_worst_coordinate_K_CMB'],
  'center_24_simultaneous_Euclidean_Chebyshev_radii_K_CMB':n['center_24_simultaneous_Euclidean_Chebyshev_radii_K_CMB'],
  'actual_Y_168_simultaneous_Euclidean_Chebyshev_radii_K_CMB':n['actual_Y_168_simultaneous_Euclidean_Chebyshev_radii_K_CMB'],
  'cross_coordinate_covariance_bound':n['cross_coordinate_covariance_bound'],
  'limits':'Released native-pixel marginals only; unknown cross-pixel/channel correlations range over PSD completions. Mean-zero and marginals are conditional. Calibration, leakage and bias are excluded. Post-selected scalar directions require simultaneous bound.'},
 'positive_source_feasibility':{
  'FIRAS_rows':f['rows'],'valid_frequency_count':f['valid_frequency_count_from_NUM_FREQ'],
  'frequency_GHz_first_last':f['frequency_GHz_first_last'],
  'valid43_negative_measured_entries':f['valid43_negative_sample_count'],
  'padding_not_data':f['trailing_zero_columns_are_padding'],
  'S7_centres_gt3p5deg_nearest_source':f['S7_ring_centres_more_than_3p5_deg_from_nearest_FIRAS_centre'],
  'max_nearest_source_angle_deg':f['nearest_FIRAS_centre_angle_deg_quantiles'][-1],
  'C_vector_diagonal_relative_max':f['C_vector_diagonal_relative_max'],
  'C_vector_covariance_relation':f['C_vector_vs_released_covariance_status'],
  'interpretation':'Measured source centres and representative Moon beam do not certify a nonnegative lower response over every S7 target atom; negative observed spectral entries require an uncertainty model. No physical hole follows from nearest-centre diagnostic.'},
 'complex_moment_law':{
  'P':'Q+iU with complex signed LOS weights dnu, |dnu|<=dmu_I only under independently justified positive emitter intensity model',
  'cancelled_reference_counterexample':'Two components P=+1 and P=-1 have M0=0, TV=2 and nonzero spectral signal if responses differ; each has |P|<=I=1.',
  'Taylor_remainder':'For support ||delta_theta||<=d and TV<=A_TV: ||K r3||<=A_TV*d^3/6*sup_D ||K D^3 s||op; factorial-normalized second moments. No numeric epsilon3 without justified D and TV.',
  'moment_metric':'D=diag(R32 common reference scales), rho=||D U||_F in K_CMB for actual physical reference-temperature moments; not a measured contamination radius.',
  'unrestricted_class':'Unbounded actual-Y CMB-equivalent shifts follow from F c=a. This is a coefficient-class obstruction, not proof that arbitrary coefficients are positive emissivity distributions.'},
 'missing_inputs':[
  {'issue_class':'ABSOLUTE_INTENSITY_DOMINATION','needed':'A calibrated full-sky absolute source integral upper set or nonnegative FIRAS aggregate lower response dominating the exact native target kernel across sky/spectral atoms, including stripe/gain/calibration/model-selection and beam uncertainty.'},
  {'issue_class':'PHYSICAL_LOS_DOMAIN','needed':'Independently justified compact synch/dust line-of-sight spectral support or bounded out-of-domain mass and neglected polarized components; sky-map prior scatter/hard lookup bounds do not suffice.'},
  {'issue_class':'NATIVE_RESPONSE_OR_CONSERVATIVE_NORM','needed':'Native component-dependent response domination or a qualified common-response bridge for translating source amplitude into the R32 K_CMB moment ball and matched B residual.'}],
 'claim_ceiling':'CONDITIONAL_FINITE_GEOMETRY_PLUS_MARGINAL_NOISE_SUPPORT_AND_SOURCE_OBSTRUCTION; NO_PHYSICAL_FOREGROUND_BUDGET; ORIGINAL42_UNCHANGED',
 'generating_commands':[
  'python compute.py geometry','python compute.py noise','python firas_feasibility.py',
  'python plot.py','python -m pytest test_compute.py -q','python finalize.py'],
 'artifacts':{'actual_geometry_npz':str(EXT/'ACTUAL_GEOMETRY.npz'),
              'noise_support_json':str(EXT/'NOISE.json'),
              'firas_feasibility_json':str(EXT/'FIRAS_FEASIBILITY.json'),
              'branch_sensitivity_json':str(EXT/'BRANCH_SENSITIVITY.json'),
              'conditional_plot_png':str(EXT/'conditional_geometry.png'),
              'conditional_plot_pdf':str(EXT/'conditional_geometry.pdf'),
              'actual_table':str(PRODUCT/'ACTUAL_TABLE.csv'),
              'branch_sensitivity_table':str(PRODUCT/'BRANCH_SENSITIVITY.csv'),
              'noise_table':str(PRODUCT/'NOISE_TABLE.csv'),
              'firas_valid43_table':str(EXT/'FIRAS_VALID43_TABLE.csv')},
 'next_executable_checkpoint':'Controller records this precise HOLD and requests next independent READY task; future physical repair must bind positive source/domain/operator inputs, not repeat this same failed calibration experiment.'}
save(PRODUCT/'RESULT.json',result)

report=f'''# R36-07 actual complex foreground response — conditional result

The seven released PR3 polarization maps supply actual S7 E2/E3/B2/B3
coefficients, and their native QQ/QU/UU columns supply per-pixel marginal
noise blocks. The R31/R32 nine-column operator has row rank seven. On the
actual 7×24 coefficient matrix, the corrected A_BT_1e-07 geometry gives
ell={g['ell']:.12g}, J0={g['J0_K_CMB_squared']:.12g} K_CMB², and the **algebraic
minimum** rho={g['rho_min_algebraic_K_CMB']*1e6:.9g} microK_CMB. This minimum
is not a measured upper bound on physical foreground contamination.

The actual-data compensators in RESULT.json shift a B-centered CMB-equivalent
24-vector by 1, 10, and 100 microK_CMB while reproducing the seven observed
coefficient vectors to about 1.4e-16 K_CMB Frobenius error. This proves an
obstruction within the retained free signed-moment coefficient class. It does
not prove that each compensator is a positive-emissivity line-of-sight sky.
The conditional response curve and all six bandpass-convention rows are in
ACTUAL_TABLE.csv and BRANCH_SENSITIVITY.csv; the plot is
`{EXT/'conditional_geometry.png'}`. The saved derived-SMICA B residual is
{g['SMICA_B_comparator_K_CMB']*1e6:.9g} microK_CMB after a different E-only
anchor fit. Its same-sky derivation and different statistic forbid treating it
as an independent frequency or direct radius threshold.

For each prespecified real spin direction v, the released marginal covariance
blocks imply the sharp worst-case scalar standard deviation
`sum_(band,pixel) sqrt(l_bp(v)^T Sigma_bp l_bp(v))` over all positive
semidefinite cross-pixel and cross-channel completions. The native-pixel
operator includes the actual mask, Q/U, spin-2 harmonics and QU covariance.
The center's 24-coordinate simultaneous covariance-only Euclidean radii are
{', '.join(f'{alpha}: {value*1e6:.6g}' for alpha,value in n['center_24_simultaneous_Euclidean_Chebyshev_radii_K_CMB'].items())}
microK_CMB for the listed alpha_N values. They use only a
mean-zero marginal model and Markov; unspecified calibration, leakage and
bias remain outside this noise bound. A direction chosen after seeing Y
requires the simultaneous bound, not a scalar Chebyshev interval.

An optically thin positive-intensity physical model could bound complex
polarization variation via |dnu|<=dmu_I. It must include all relevant
emitters and a supported spectral/sky domain. Two opposite polarization
phases can give M0=0, total variation 2, and nonzero spectral moments.
For declared domain radius d and variation A_TV, the explicit third-order
remainder is `||K r3|| <= A_TV d^3/6 sup_D ||K D^3 s||_op` in the stated
dimensionless beta_s, beta_d, t coordinates. Neither d nor A_TV has a
source-supported upper value here, so no numerical remainder was invented.

The [FIRAS Pass4 LOWF release](https://lambda.gsfc.nasa.gov/product/cobe/firas_dss_get.html)
was consumed with its [C vector](https://lambda.gsfc.nasa.gov/product/cobe/firas_cvect_get.html),
[frequency covariance](https://lambda.gsfc.nasa.gov/product/cobe/firas_cm_get.html),
and [model-error product](https://lambda.gsfc.nasa.gov/product/cobe/firas_moderr_get.html).
It has {f['rows']} rows and {f['valid_frequency_count_from_NUM_FREQ']} valid
frequency bins; the remaining {f['trailing_zero_columns_are_padding']} stored
zero columns are padding. The valid measured table contains
{f['valid43_negative_sample_count']} negative entries, which cannot be
zero-filled or read as negative physical source intensity. The original S7
has {f['S7_ring_centres_more_than_3p5_deg_from_nearest_FIRAS_centre']}
pixel centres more than 3.5 degrees from the nearest FIRAS row centre,
maximum {f['nearest_FIRAS_centre_angle_deg_quantiles'][-1]:.6g} degrees.
This is a centre-distance diagnostic; the scan-elongated beam lower response
has not been certified, so it is not a physical uncovered-sky finding.
The separately released C-vector squared and covariance diagonal differ by
up to {f['C_vector_diagonal_relative_max']:.6g} relative; the exact source-format
relationship is unresolved and no equality tolerance admits it as a bound.

The finite physical radius remains HOLD on three precise inputs: a
source-calibrated absolute intensity upper set or positive response dual
covering every target atom; independently justified line-of-sight parameter
support and neglected-component bounds; and native component-dependent
response domination or a qualified common-response bridge. The R31 free
class and original 42-node acceptances retain their prior status. This
diagnostic has owner obsstat, tier C0, transfer source none, Galactic COSMO
Q+iU convention, signature (-,+,+,+), and c=299792458 m/s.
'''
(PRODUCT/'REPORT.md').write_text(report)

small_sources=[PRODUCT/x for x in ('compute.py','firas_feasibility.py','plot.py','test_compute.py','finalize.py',
                                   'branch_sensitivity.py','ACTUAL_TABLE.csv','NOISE_TABLE.csv',
                                   'BRANCH_SENSITIVITY.csv','RESULT.json','REPORT.md')]
raw_artifacts=[EXT/x for x in ('GEOMETRY.json','ACTUAL_GEOMETRY.npz','NOISE.json','FIRAS_FEASIBILITY.json',
                              'BRANCH_SENSITIVITY.json',
                              'FIRAS_COVERAGE_DIAGNOSTIC.npz','FIRAS_VALID43_TABLE.csv',
                              'conditional_geometry.png','conditional_geometry.pdf',
                              'FIRST_FAILURE_geometry.json','FIRST_FAILURE_firas.json',
                              'RUN_geometry.json','RUN_noise.json')]
manifest=[{'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)} for p in small_sources+raw_artifacts]
candidate_identity=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
receipt={
 'packet_id':packet['packet_id'],'task_id':packet['task_id'],'input_identity':packet['input_identity'],
 'actual_ack_path':str(ACK),'actual_ack_sha256':digest(ACK),
 'agent_id':'/root/rc_7f1ac3df12ebbc36','requested_runtime':'gpt-6-sol/high','observed_runtime':'UNKNOWN',
 'candidate_identity':candidate_identity,'source_manifest':manifest,
 'predecessor_exploratory_candidate_identity':'793f49450e26bf0a14da9cd98b6d7b266caa5969436941932fcb266e53ca80a0',
 'predecessor_preimage_path':str(EXT/'preimage_793f49450e26bf0a'),
 'checkout_head_at_start':'7a751cc2419f32e98446642b35ca50fa767ebe93',
 'producer_runs':{phase:json.loads((EXT/f'RUN_{phase}.json').read_text()) for phase in ('geometry','noise')},
 'validation_evidence':['5 focused pytest falsifiers pass','actual R31/R32 F, ell and center reuse checked',
                         'all seven native QQ/QU/UU on selected original S7 pixels consumed',
                         'FIRAS LOWF/C/cov/model source identities and NUM_FREQ checked',
                         'first geometry label and C-vector rounding failures preserved'],
 'qualified_products':[],'acceptance_met':False,'review':'PENDING',
 'source_publication':'NOT_REQUESTED_BY_THIS_WORKER',
 'python':platform.python_version(),'numpy':np.__version__,
 'finalized_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
save(EXT/'RAW_RECEIPT.json',receipt)
print(json.dumps({'candidate_identity':candidate_identity,'receipt':str(EXT/'RAW_RECEIPT.json'),
                  'result':str(PRODUCT/'RESULT.json'),'files':len(manifest)}))
