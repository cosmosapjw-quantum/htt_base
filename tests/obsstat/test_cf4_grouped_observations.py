import numpy as np
import pytest
from obsstat.catalogs.cf4_grouped_observations import GroupedObservations,_read

def test_parser_rejects_duplicate_and_short(tmp_path):
    p=tmp_path/'t.dat';p.write_text('1  3\n1  4\n')
    with pytest.raises(ValueError,match='duplicate'):_read(p,{'1PGC':(1,1),'foo':(4,4)})
    p.write_text('1\n')
    with pytest.raises(ValueError,match='short'):_read(p,{'1PGC':(1,1),'foo':(4,4)})

def test_group_domain_nonfinite_and_negative_redshift():
    args=[np.array([1]),np.array([30.]),np.array([.5]),np.array([-300.]),np.array([[1.,0,0]]),np.zeros((1,7),bool),{}]
    assert GroupedObservations(*args).vh_km_s[0]<0
    for j,value in [(1,np.nan),(2,0),(3,np.inf)]:
        bad=args.copy();bad[j]=np.array([value])
        with pytest.raises(ValueError):GroupedObservations(*bad)

def test_join_method_presence_and_modulus_source(tmp_path):
    from obsstat.catalogs.cf4_grouped_observations import load_grouped_observations,T3,T4
    # A tiny deterministic fixed-width fixture using the existing release schema.
    def row(columns,values):
        chars=[' ']*max(b for a,b in columns.values())
        for label,value in values.items():
            a,b=columns[label];chars[a-1:b]=str(value).rjust(b-a+1)
        return ''.join(chars).rstrip()+'\n'
    p3,p4=tmp_path/'table3',tmp_path/'table4'
    p3.write_text(row(T3,{'1PGC':2,'o_DMfp':1})+row(T3,{'1PGC':1,'o_DMcal':2}))
    p4.write_text(row(T4,{'1PGC':1,'DMzp':31,'e_DMzp':.5,'Vh':-100,'RAdeg':0,'DEdeg':0})+
        row(T4,{'1PGC':2,'DMzp':33,'e_DMzp':.3,'Vh':1000,'RAdeg':90,'DEdeg':0}))
    # Frozen CDS J/ApJ/944/94 schema excerpt; independent of ignored raw files.
    readme=tmp_path/'ReadMe'
    readme.write_text("""Byte-by-byte Description of file: table3.dat
  1-7 I7 --- 1PGC Group identity
 89-90 I2 --- o_DMcal Calibrator presence count
 99 I1 --- o_DMsnIa SNIa presence count
 114-116 I3 --- o_DMfp FP presence count
 131-132 I2 --- o_DMtf TF presence count
 147-149 I3 --- o_DMsbfo Optical SBF presence count
 164 I1 --- o_DMsbfi Infrared SBF presence count
 179-184 F6.3 mag DMsnII SNII presence indicator
Note (1): frozen schema excerpt
Byte-by-byte Description of file: table4.dat
 1-7 I7 --- 1PGC Group identity
 9-14 F6.3 mag DMzp Group modulus
 16-20 F5.3 mag e_DMzp Modulus uncertainty
 28-32 I5 km/s Vh Heliocentric group velocity
 84-91 F8.4 deg RAdeg J2000
 93-100 F8.4 deg DEdeg J2000
Note (5): frozen schema excerpt
""")
    cat=load_grouped_observations(p3,p4,readme)
    np.testing.assert_array_equal(cat.group_id,[1,2])
    np.testing.assert_array_equal(cat.modulus,[31,33])
    assert cat.method_presence[0,0] and cat.method_presence[1,2]
    assert cat.method_presence.sum()==2
    p3.write_text(row(T3,{'1PGC':3,'o_DMfp':1}))
    with pytest.raises(ValueError,match='identity mismatch'):load_grouped_observations(p3,p4,readme)
