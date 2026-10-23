"""Independent wire-to-consumer comparison, with no network or source NPZ access."""
import collections
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as E

B=Path(__file__).resolve().parent

def load(name):return json.loads((B/name).read_text())

def run():
    report=load('products/property_table.json'); summary=load('products/AVAILABILITY.json')
    tree=E.parse(B/'raw/property_attempt1.vot').getroot()
    table=next(x for x in tree.iter() if x.tag.split('}')[-1]=='TABLE')
    fields=[x.attrib for x in table if x.tag.split('}')[-1]=='FIELD']
    wire=[x for x in table.iter() if x.tag.split('}')[-1]=='TR']
    ids=[int(s) for s in (B/'inputs/source_ids.txt').read_text().splitlines()]
    assert len(wire)==len(report['rows'])==len(ids)==4756
    checked=0; availability={f['name']:collections.Counter() for f in fields[2:]}
    char_empty=0
    for sid, tr, row in zip(ids,wire,report['rows']):
        assert len(tr)==len(fields)
        for f,td in zip(fields,tr):
            name=f['name'];kind=f['datatype'];text=td.text
            if text is None or text=='':value=None
            elif kind in ['long','int','short']:value=int(text)
            elif kind=='boolean':
                assert text.lower() in ['t','f','true','false','1','0']
                value=text.lower() in ['t','true','1']
            elif kind=='float':value=struct.unpack('f',struct.pack('f',float(text)))[0]
            elif kind=='double':value=float(text)
            elif kind=='char':value=text
            else:raise AssertionError(kind)
            assert row[name]==value,(sid,name,row[name],value)
            assert row[name] is None or type(row[name]) is type(value),(sid,name,'type changed')
            checked+=1
            if kind=='char' and value is None:char_empty+=1
            if name in availability:
                state='NO_QSO_ROW' if row['qso_source_id'] is None else ('ROW_NULL' if value is None else 'PRESENT')
                assert row['field_states'][name]==state
                availability[name][state]+=1
        assert row['retained_source_id']==sid and row['qso_source_id']==sid
    for f,c in availability.items():
        assert sum(c.values())==4756
        for k in ['NO_QSO_ROW','ROW_NULL','PRESENT']:assert summary['availability'][f][k]==c[k]
    masks=load('products/property_wire_masks.json')
    assert masks['votable_version']=='1.4'
    assert len(masks['wire_empty_TD_indices']['vari_best_class_name'])==char_empty==1540
    assert masks['astropy_original_mask_indices']['vari_best_class_name']==[]
    assert all(masks['astropy_original_values']['vari_best_class_name'][i]=='' for i in masks['wire_empty_TD_indices']['vari_best_class_name'])
    assert summary['strata']['host_flag']['1']==summary['strata']['host_flag']['2']==0
    assert summary['strata']['variability']=={'AGN':3216,'ROW_NULL':1540}
    raw=load('RAW_RECEIPT.json')
    assert len(raw['requests'])==2 and all(x['attempt']==1 and x['http_status']==200 for x in raw['requests'])
    for request in raw['requests']:
        data=Path(request['raw_path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==request['sha256']
        root=E.fromstring(data)
        assert all(x.attrib.get('value')=='OK' for x in root.iter() if x.tag.split('}')[-1]=='INFO' and x.attrib.get('name')=='QUERY_STATUS')
    return {'status':'PASS','validated_cells':checked,'validated_rows':4756,'source_id_only':True,
        'normalized_empty_char_nulls':char_empty,'preserved_false_and_zero':True,
        'original_parser_masks_and_values_preserved':True,'no_network':True,
        'future_primary_exposed_host1_2_count':0,'downstream_primary_design':'ZERO_EXPOSURE_SUPPORT',
        'claim_admission':False}

if __name__=='__main__':
    result=run()
    (B/'CONSUMER_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
