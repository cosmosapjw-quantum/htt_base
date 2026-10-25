"""Structural and arithmetic closeout checks; no native-map rerun."""
import hashlib,json,pathlib
import numpy as np
import healpy as hp
from compute import decode,sha,BANDS,CAP_RSS,CAP_S
P=pathlib.Path(__file__).resolve().parent
with np.load(P/'FULL_CARRIER_AND_CONTRASTS.npz') as z:
    c=z['carrier_canonical_96'];d=z['pair_contrasts_canonical_6x24'];pairs=z['pair_bands_GHz'];q=z['Q_computational']
    assert c.shape==(4,24) and d.shape==(6,24) and pairs.shape==(6,2)
    assert np.isfinite(c).all() and np.isfinite(d).all() and np.isfinite(q).all()
    for k,(a,b) in enumerate(pairs):
        i=BANDS.index(a);j=BANDS.index(b)
        assert np.array_equal(d[k],c[i]-c[j])
    assert np.allclose(q,np.sqrt(np.sum((c/1e-5)**2,axis=1)),rtol=1e-14,atol=0)
    for prefix,values in [('E2_stf',c),('E3_stf',c),('B2_stf',c),('B3_stf',c)]:
        block={'E2_stf':0,'E3_stf':1,'B2_stf':2,'B3_stf':3}[prefix]
        assert np.array_equal(z[prefix],np.stack([decode(x)[block] for x in values]))
    for prefix,values in [('pair_E2_stf',d),('pair_E3_stf',d),('pair_B2_stf',d),('pair_B3_stf',d)]:
        block={'pair_E2_stf':0,'pair_E3_stf':1,'pair_B2_stf':2,'pair_B3_stf':3}[prefix]
        assert np.array_equal(z[prefix],np.stack([decode(x)[block] for x in values]))
with np.load(P/'COMMON_SUPPORT_S4.npz') as z:
    selected=z['selected_mask_ring64'];s4=z['s4_mask_ring64']
    nested=hp.nest2ring(64,np.arange(49152))
    expected=selected[nested].copy()
    for band in BANDS:expected &= z[f'valid_{band}_nest64']
    actual=s4[nested]
    assert np.array_equal(expected,actual)
    assert int(selected.sum())==30021 and int(s4.sum())==30021
    assert np.array_equal(z['retained_ring64'],np.flatnonzero(s4))
    assert np.array_equal(z['removed_ring64'],np.flatnonzero(selected & ~s4))
qual=json.loads((P/'PRODUCT_QUALIFICATION_DECISIONS.json').read_text())
assert [x['band_GHz'] for x in qual['decisions']]==list(BANDS)
assert qual['all_four']=='QUALIFIED_FOR_STAGED4'
assert qual['common_support_s4_sha256']==sha(P/'COMMON_SUPPORT_S4.npz')
for x in qual['decisions']:
    assert x['qualification']=='QUALIFIED_FOR_STAGED4'
    assert pathlib.Path(x['path']).stat().st_size==x['size_bytes']
    assert x['unit_normalized']=='K_CMB'
r=json.loads((P/'RESULT.json').read_text());raw=json.loads((P/'RAW_RECEIPT.json').read_text())
assert r['support_count']==30021 and r['Pi']=='NOT_CALIBRATED' and r['physical_F']=='NOT_EVALUABLE'
assert raw['stage_status']=='CANDIDATE_COMPLETE_REVIEW_REQUIRED'
assert len(raw['first_failures'])==2
for b in BANDS:
    item=raw['product_accounting'][str(b)]
    assert 0<item['charged_seconds']<CAP_S
    assert 0<item['peak_rss_bytes']<CAP_RSS
    assert r['controls'][str(b)]['independent_max_abs_K_CMB']<1e-12
assert (P/'figure.png').stat().st_size>1000
print(json.dumps({'status':'PASS','support_count':int(s4.sum()),'carrier_shape':list(c.shape),'contrasts_shape':list(d.shape),'product_caps':'PASS','first_failures_retained':len(raw['first_failures'])},sort_keys=True))
