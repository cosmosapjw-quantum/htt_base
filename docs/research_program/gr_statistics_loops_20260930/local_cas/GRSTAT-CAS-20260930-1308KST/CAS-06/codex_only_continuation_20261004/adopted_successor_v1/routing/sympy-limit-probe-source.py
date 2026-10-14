import json,sys,sympy as s
y=s.Symbol("y",positive=True)
t=s.Symbol("t",real=True)
a=s.Symbol("a",positive=True)
rows=[]
for name,x,f in [("positive_y_unit",y,y/s.sqrt(1-y*y)),("real_t_unit",t,t/s.sqrt(1-t*t)),("positive_y_positive_coefficient",y,a*y/s.sqrt(1-y*y)),("real_t_positive_coefficient",t,a*t/s.sqrt(1-t*t))]:
 rows.append({"case":name,"expression":str(f),"limit_from_below":str(s.limit(f,x,1,dir="-"))})
print(json.dumps({"python":sys.version,"sympy_version":s.__version__,"sympy_module":s.__file__,"observations":rows,"scientific_admission":"HOLD","probe_is_axis_PASS":False}))
