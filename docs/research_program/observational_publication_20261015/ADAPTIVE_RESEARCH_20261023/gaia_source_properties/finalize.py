"""Finalize the external review candidate without repository-space assumptions."""
import datetime as dt
import hashlib
import json
from pathlib import Path

B=Path(__file__).resolve().parent
def write(name,value):(B/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def load(name):return json.loads((B/name).read_text())
receipt=load('RAW_RECEIPT.json');first=load('raw/FIRST_PASS_RAW_RECEIPT.json')
receipt['acquisition_elapsed_seconds']=first['elapsed_seconds']
receipt['offline_validation']['preserved_acquisition_elapsed_seconds']=first['elapsed_seconds']
receipt['execution_commands']=[
 {'command':'PYTHONDONTWRITEBYTECODE=1 python -B acquire.py','exit_code':0,'stdout':'acquisition.stdout','stderr':'acquisition.stderr','network_queries':2},
 {'command':'PYTHONDONTWRITEBYTECODE=1 python -B acquire.py --offline-validate','exit_code':0,'stdout':'offline_validation.stdout','stderr':'offline_validation.stderr','network_queries':0},
 {'command':'PYTHONDONTWRITEBYTECODE=1 python -B test_parser.py','exit_code':0,'stdout':'parser_tests.stdout','stderr':'parser_tests.stderr','network_queries':0},
 {'command':'PYTHONDONTWRITEBYTECODE=1 python -B validate_consumer.py','exit_code':0,'stdout':'consumer_validation.stdout','stderr':'consumer_validation.stderr','network_queries':0}]
receipt['first_failure_evidence']='raw/PARSER_FIRST_FAILURE.json'
receipt['provider_documentation_verification']={'Gaia_datamodel_page':'Web tool fetch timeout; frozen source contract and actual returned FIELD metadata used',
 'VOTable_REC_1_4':'https://www.ivoa.net/documents/VOTable/20191021/REC-VOTable-1.4-20191021.html',
 'verified':'2026-10-23; empty TABLEDATA TD is no data/null; whitespace preserved for char'}
receipt['storage']={'repository_available_bytes_at_preflight':0,'substantial_writes':'external only','external_reserve_bytes':2147483648,'deletions':[]}
write('RAW_RECEIPT.json',receipt)
summary=load('products/AVAILABILITY.json')
summary['future_primary_design']={'host1_2':0,'host3':3149,'status':'ZERO_EXPOSURE_SUPPORT',
 'meaning':'Frozen Host1-2 versus3 interaction cannot be evaluated on these released retained-source tags; no substitute regrouping or outcome access.'}
write('products/AVAILABILITY.json',summary)
report='''# Exact-ID Gaia DR3 source-property intake

Owner: htt. Scope: retained-source metadata acquisition only. Claim tier: C0. Transfer source: none. Status: execution validated, independent review pending. No scientific admission is made here.

The frozen exact-ID LEFT OUTER JOIN returned all 4,756 retained IDs, each exactly once and each matched to the same integer DR3 QSO source ID. The independent count query returned n_left=4756 and n_matched=4756. Both anonymous TAP requests succeeded HTTP 200 on the first attempt; no retry, successful-query replay, authentication, full-catalogue request, or PM/covariance/outcome-array access occurred. Only source_id.npy was opened from the identity-checked retained NPZ. Raw responses, upload, requests, HTTP receipts, original parser masks/values and normalized products remain external.

Host flags are 3:3149, 6:669, 5:43, wire-null:895; flags1/2/4 have zero rows. The frozen Host1-2 versus3 interaction has ZERO_EXPOSURE_SUPPORT and cannot be evaluated on this metadata. Every original stratum remains; no regrouping was performed. host_galaxy_detected is False:4713 and True:43; n_transits is literal zero for all4756. These raw categories are preserved without inventing flag-to-boolean implications. DSC labels are quasar:2069 and unclassified:2687; variability is AGN:3216 and wire-null:1540. Missing metadata does not imply nonvariability. Source-selection integers and raw crosstabs are retained; the mask1 provenance bit is never a filter. Scores have no new threshold, propensity or calibrated-probability interpretation; AGN membership is not probability. DSC uses astrometry and is not independent physical validation. Versioned table/pipeline ambiguity, shared processing/selection and unknown cross-source covariance remain limitations.

The responses use VOTable1.4. Full XML and every QUERY_STATUS were checked; OVERFLOW and ERROR are rejected. Astropy7.2.0 represents empty char TD as unmasked empty strings and trims whitespace-only char cells. Normalized values therefore use exact XML text for character fields and the VOTable1.4 empty-TD null convention. Original masks/values remain in property_wire_masks.json; raw XML remains authoritative. Database null versus hypothetical literal empty string cannot be recovered from the wire; no database-null assertion is made. The initial parser falsifier is retained in raw/PARSER_FIRST_FAILURE.json. The correction used offline raw responses only.

Validation: a separate stdlib XML/struct consumer checked all47,560 actual cells,4756 exact IDs, per-field present/null/no-row identities, integer/boolean/numeric types, raw hashes, count agreement, and original parser evidence. Targeted falsifiers reject trailing OVERFLOW and truncated XML and preserve an integer above2^53, wire-null, significant whitespace, False, zero and score endpoints. All final checks passed. Commands and exit codes are in RAW_RECEIPT.json. No native solver, ODE, posterior, causal centroid law or physical MES anchor was introduced. Original17/42, alternate18/42, historical48, one-use/ultra allocations and R9 UNKNOWN remain unchanged.

Sources: frozen input contract00508df7ec44ab6680ab8291868acaa203247aba18aaabfe2eaf029fc6ddad60 and actual Gaia returned FIELD metadata; [IVOA VOTable1.4 Recommendation](https://www.ivoa.net/documents/VOTable/20191021/REC-VOTable-1.4-20191021.html), verified2026-10-23. The Gaia datamodel web fetch timed out, so no new upstream semantic claim was inferred from it.

Complete candidate inventory is MANIFEST.json. RETURN.json is an envelope excluded from that inventory to avoid a candidate-hash cycle. Row-level data and raw VOTables are external inputs; repository publication, if storage is recovered, should use compact summary/code/receipt metadata. No repository copy or Git mutation was performed.
'''
(B/'REPORT.md').write_text(report)
files={}
for p in sorted(B.rglob('*')):
 if p.is_file() and p.name not in ['MANIFEST.json','RETURN.json']:
  data=p.read_bytes();files[str(p.relative_to(B))]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
manifest={'schema':'htt.gaia_source_property_intake_manifest/1','task_id':receipt['task_id'],'packet_id':receipt['packet_id'],
 'input_identity':receipt['input_identity'],'agent_id':receipt['agent_id'],'source_head':'d93605e66adfececa89b90681124b232a5f90220',
 'owner':'htt','scope':'exact retained-ID Gaia DR3 metadata intake','claim_tier':'C0','transfer_source':'none',
 'status':'EXECUTION_VALIDATED_PENDING_INDEPENDENT_REVIEW','independent_review':False,
 'sky_support_status':'retained exact source IDs; no new sky filter','null_mock_status':'not applicable to metadata acquisition',
 'source_id_input_sha256':'41b6ddcb13131b49b97efd6107816af4518fa9e23725cf3b4272c2f3a70acb8f',
 'canonical_source_id_sha256':'a5df0e9ec295b127beaa1309618b62540564d7e5f70abdc1ab27c9ac8747a614',
 'files':files,'inventory_excludes':['MANIFEST.json','RETURN.json'],
 'caveats':summary['caveats']+['Future Host1-2 versus3 ZERO_EXPOSURE_SUPPORT; independent review required; no scientific admission.']}
write('MANIFEST.json',manifest)
candidate='sha256:'+hashlib.sha256((B/'MANIFEST.json').read_bytes()).hexdigest()
result={'task_id':receipt['task_id'],'packet_id':receipt['packet_id'],'input_identity':receipt['input_identity'],
 'agent_id':receipt['agent_id'],'status':'SUCCESS_PENDING_INDEPENDENT_REVIEW','candidate_identity':candidate,
 'raw_receipt':str(B/'RAW_RECEIPT.json'),'manifest':str(B/'MANIFEST.json'),'report':str(B/'REPORT.md'),
 'validation_evidence':[str(B/p) for p in ['VALIDATION.json','CONSUMER_VALIDATION.json','PARSER_TESTS.json']],
 'qualified_products':[{'product':'gaia_source_properties','status':'PROPOSED_FOR_INDEPENDENT_REVIEW','candidate_identity':candidate,'admitted':False}],
 'requested_route':{'model':'gpt-5.6-terra','effort':'medium'},'transport_selected':{'model':'gpt-6.1-sol','effort':'medium'},
 'transport_status':'TRANSPORT_MODEL_UNAVAILABLE','observed_runtime':'UNKNOWN','git_mutations':False,
 'outcomes':{'rows':4756,'matched':4756,'no_qso_row':0,'host1_2':0,'host3':3149,'downstream_primary_design':'ZERO_EXPOSURE_SUPPORT'},
 'residual_holds':['Independent review required before product qualification','Repository packaging unavailable at zero root free space; complete external candidate ready'],
 'next_executable_checkpoint':'Fresh independent read-only review against this manifest identity',
 'preservation':receipt['preservation']}
write('RETURN.json',result)
print(json.dumps(result))
