"""Finalize the staged candidate inventory after numeric work; no native rerun."""
import hashlib,json,os,pathlib,subprocess,sys,time
import numpy as np
from astropy.io import fits
P=pathlib.Path(__file__).resolve().parent
BANDS=(30,44,70,100)
PACKET='58a4f9a76a227a91229b71a44a02044ca3d8978a1e12b2996e6fd19f734c5d9a'
INPUT_SHA='ff5db155e8266b4a913ceb48e69b60d6a6356928940305cd2d28d82fc3f690e5'
SHARED_EARLIER_OBSERVED=16.9671  # five exec wall outputs: 3.2767+3.5268+1.0475+2.9156+6.2005 s
start=time.monotonic()

def write(path,obj):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n');os.replace(tmp,path)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

qual=json.loads((P/'PRODUCT_QUALIFICATION_DECISIONS.json').read_text())
for d in qual['decisions']:
    with fits.open(d['path'],memmap=True,lazy_load_hdus=True) as hdul:
        h=hdul[1].header
        observed=h.get('FILENAME')
    if observed is None:
        d['filename_header_status']='ABSENT'
        d['filename_identity_evidence']='exact bound filesystem basename, source URL, local file SHA256/size, receipt/header metadata SHA256, release and frequency header'
    else:
        d['filename_header_status']='PRESENT_MATCH' if observed.strip()==pathlib.Path(d['path']).name else 'PRESENT_MISMATCH'
        assert d['filename_header_status']=='PRESENT_MATCH'
        d['filename_header_value']=observed.strip()
write(P/'PRODUCT_QUALIFICATION_DECISIONS.json',qual)
with np.load(P/'FULL_CARRIER_AND_CONTRASTS.npz') as z:
    Q=z['Q_computational'];pairs=z['pair_bands_GHz'];diff=z['pair_contrasts_canonical_6x24']
    norms=np.linalg.norm(diff,axis=1)
raw=json.loads((P/'RAW_RECEIPT.json').read_text())
result=json.loads((P/'RESULT.json').read_text())
lines=['# R25 staged four-frequency native pseudo-tensors','',
'Four delivered Galactic COSMO maps were qualified individually and projected at their native NSIDE on the same validity-only S4 support. The original selected support contains 30,021 RING64 cells; S4 also contains 30,021. One 100 GHz BAD_DATA pixel lies outside those selected cells. No Q/U map was downgraded, smoothed or deconvolved.','',
'The complete result contains all 96 E2/E3/B2/B3 canonical coordinates, four sets of full STF tensors and six oriented 24-coordinate contrasts with their full STF tensors. The independent native Wigner-d quadrature agrees with healpy in every coordinate within the declared 1e-12 K absolute and 1e-9 relative tolerance. The 24-basis NSIDE16 synthetic fixture, parity, permutation, sentinel, mask, linearity, reduction and STF sign checks passed.','',
'| Band (GHz) | Computational Q |','|---:|---:|']
for b,q in zip(BANDS,Q):lines.append(f'| {b} | {q:.12g} |')
lines+=['','| Oriented pair (GHz) | Full 24-coordinate contrast Euclidean norm (K_CMB) |','|---:|---:|']
for (a,b),v in zip(pairs,norms):lines.append(f'| {a}-{b} | {v:.12g} |')
lines+=['','The figure displays the canonical coordinates and the pair norms; the NPZ preserves every coordinate and tensor. Q uses the declared 1e-5 K ell-2 and ell-3 computational gauges. F_frequency_empirical is the four-point count with mass 1/4 at each band. It has no physical or sampling-law interpretation.','',
'Delivered beams, mapmaking, pixelization, mask-induced E/B and higher-mode leakage and instrumental/systematic differences remain in the pseudo-modes. Physical MES/F are NOT_EVALUABLE; Pi is NOT_CALIBRATED; G_F is NOT_APPLICABLE because frequency is not depth. The result does not reject a foreground model, establish significance, invert a full-sky response, or promote the original all-seven acquisition. Independent review and scientific admission remain pending.','',
'The first failed import-path synthetic probe and two native-run plumbing failures are retained in TEST_RECEIPT.json and RAW_RECEIPT.json, with cumulative product charges.']
(P/'REPORT.md').write_text('\n'.join(lines)+'\n')
env=os.environ.copy();env.update({'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
proc=subprocess.run([sys.executable,'-B',str(P/'validate_candidate.py')],cwd=P,env=env,capture_output=True,text=True)
validation={'schema':'htt.staged4_validation_receipt/1','command':'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -B validate_candidate.py',
            'cwd':str(P),'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,
            'source_script_sha256':sha(P/'validate_candidate.py')}
write(P/'VALIDATION_RECEIPT.json',validation)
if proc.returncode:raise RuntimeError('FINAL_VALIDATION_FAILED')
shared_total=SHARED_EARLIER_OBSERVED+(time.monotonic()-start)
for b in BANDS:
    rec=raw['product_accounting'][str(b)]
    rec['charged_seconds']+=shared_total/4
    if rec['charged_seconds']>=900 or rec['peak_rss_bytes']>=4294967296:raise RuntimeError(f'FINAL_PRODUCT_CAP {b}')
raw['shared_control_and_packaging_wall_seconds']=shared_total
raw['shared_charge_allocation']='equal fourth to each of four products'
raw['stage_status']='CANDIDATE_COMPLETE_REVIEW_REQUIRED'
raw['finalized_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
write(P/'RAW_RECEIPT.json',raw)
result['product_accounting']=raw['product_accounting']
write(P/'RESULT.json',result)
# The two prior provisional outputs are replaced after all byte-bearing inputs settle.
files={x.name:sha(x) for x in sorted(P.iterdir()) if x.is_file() and x.name not in ('MANIFEST.json','RETURN.json')}
manifest={'schema':'htt.staged4_manifest/1','task_id':'R25-PR3-STAGED4-TENSOR-CONTRAST','packet_id':PACKET,
          'input_identity':'sha256:'+INPUT_SHA,'source_head':'d93605e66adfececa89b90681124b232a5f90220',
          'files_sha256':files,'input_products_sha256':{str(d['band_GHz']):d['sha256'] for d in qual['decisions']},
          'base_support_sha256':'7a462ba827ebe3ef5768552565f323ad2e1a679425be5d077fe8f46b9f0fdec6',
          'decoder_sha256':'ecccebc39c4814546552b9fbc6b6ed798cc644fec1f6616a26003fda17932216',
          'support_sha256':sha(P/'COMMON_SUPPORT_S4.npz'),'validation_evidence':{'test_receipt_sha256':sha(P/'TEST_RECEIPT.json'),
          'validation_receipt_sha256':sha(P/'VALIDATION_RECEIPT.json'),'native_controls':result['controls'],
          'per_product_accounting':raw['product_accounting'],'first_failures_retained':len(raw['first_failures'])},
          'claim_tier':'descriptive delivered-map pseudo-tensor','independent_review':'REQUIRED','scientific_admission':'HOLD'}
write(P/'MANIFEST.json',manifest)
candidate='sha256:'+sha(P/'MANIFEST.json')
ret={'packet_id':PACKET,'task_id':'R25-PR3-STAGED4-TENSOR-CONTRAST','input_identity':'sha256:'+INPUT_SHA,
     'candidate_identity':candidate,'status':'CANDIDATE_COMPLETE_REVIEW_REQUIRED',
     'proposed_qualified_products':['pr3_frequency_30_44_70_100_native_tensor_staged4'],
     'raw_receipt':str(P/'RAW_RECEIPT.json'),'manifest':str(P/'MANIFEST.json'),
     'validation_evidence':str(P/'VALIDATION_RECEIPT.json'),'independent_review':'REQUIRED','scientific_admission':'HOLD'}
write(P/'RETURN.json',ret)
print(json.dumps(ret,sort_keys=True))
