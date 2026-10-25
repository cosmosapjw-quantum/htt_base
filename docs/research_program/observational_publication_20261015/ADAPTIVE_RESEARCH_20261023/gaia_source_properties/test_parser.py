import importlib.util
import json
from pathlib import Path

B=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('intake',B/'acquire.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
raw=(B/'raw/property_attempt1.vot').read_bytes();tests=[]
for name,data in [('TRAILING_OVERFLOW',raw.replace(b'</RESOURCE>',b'<INFO name="QUERY_STATUS" value="OVERFLOW"/></RESOURCE>')),('TRUNCATED_XML',raw[:-20])]:
    try:m.read_votable(data,name)
    except Exception as e:tests.append({'case':name,'status':'PASS_REJECTED','exception':type(e).__name__})
    else:raise AssertionError(name+' incorrectly accepted')
t,_=m.read_votable((B/'raw/null_parser_fixture.vot').read_bytes(),'null_parser_fixture')
assert m.scalar(t.array,'sid',0)==9007199254740993
assert m.scalar(t.array,'label',0) is None
assert m.scalar(t.array,'label',1)==' '
assert m.scalar(t.array,'flag',0) is False
assert m.scalar(t.array,'score',0)==0.0 and m.scalar(t.array,'score',1)==1.0
tests.append({'case':'NULL_WHITESPACE_FALSE_SCORE_ENDPOINTS_EXACT_INT64','status':'PASS'})
(B/'PARSER_TESTS.json').write_text(json.dumps({'status':'PASS','tests':tests,'network_requests':0},indent=2)+'\n')
print(json.dumps(tests))
