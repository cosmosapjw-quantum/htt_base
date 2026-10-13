"""OBS-02 single grouped CF4 sample; table3 contributes method presence only."""
from dataclasses import dataclass
from pathlib import Path
import gzip
import hashlib
import re
import numpy as np

METHODS = ('CAL', 'SNIA', 'FP', 'TF', 'SBFO', 'SBFI', 'SNII')
T4 = {'1PGC': (1,7), 'DMzp': (9,14), 'e_DMzp': (16,20), 'Vh': (28,32),
      'RAdeg': (84,91), 'DEdeg': (93,100)}
T3 = {'1PGC': (1,7), 'o_DMcal': (89,90), 'o_DMsnIa': (99,99),
      'o_DMfp': (114,116), 'o_DMtf': (131,132), 'o_DMsbfo': (147,149),
      'o_DMsbfi': (164,164), 'DMsnII': (179,184)}

@dataclass(frozen=True)
class GroupedObservations:
    group_id: np.ndarray
    modulus: np.ndarray
    modulus_error: np.ndarray
    vh_km_s: np.ndarray
    direction: np.ndarray
    method_presence: np.ndarray
    provenance: dict

    def __post_init__(self):
        n = len(self.group_id)
        if not n or len(np.unique(self.group_id)) != n:
            raise ValueError('empty or duplicate group IDs')
        for a in (self.modulus, self.modulus_error, self.vh_km_s):
            if np.shape(a) != (n,) or not np.isfinite(a).all():
                raise ValueError('invalid grouped numeric data')
        if np.shape(self.direction) != (n,3) or not np.isfinite(self.direction).all():
            raise ValueError('invalid direction')
        if not np.allclose(np.linalg.norm(self.direction,axis=1),1):
            raise ValueError('direction must have unit norm')
        if np.shape(self.method_presence) != (n,len(METHODS)) or np.asarray(self.method_presence).dtype != bool:
            raise ValueError('method metadata shape')
        if np.any(self.modulus_error <= 0) or np.any(self.vh_km_s/299792.458 <= -1):
            raise ValueError('invalid modulus uncertainty or redshift domain')

def _read(path, columns, *, optional_trailing=False):
    opener = gzip.open if str(path).endswith('.gz') else open
    rows = {}
    with opener(path, 'rt', encoding='ascii') as stream:
        for line in stream:
            if not line.strip():
                continue
            if len(line.rstrip('\r\n')) < max(b for a,b in columns.values()):
                if not optional_trailing or len(line.rstrip('\r\n')) < 7:
                    raise ValueError('short fixed-width record')
                line=line.rstrip('\r\n').ljust(max(b for a,b in columns.values()))
            values = {k: line[a-1:b].strip() for k,(a,b) in columns.items()}
            group = int(values['1PGC'])
            if group in rows:
                raise ValueError('duplicate group ID')
            rows[group] = values
    return rows

def load_grouped_observations(table3, table4, readme):
    """Validate local byte schema and join unique groups without another likelihood."""
    text = Path(readme).read_text()
    for table, columns in [('table3.dat',T3), ('table4.dat',T4)]:
        section = text.split('Byte-by-byte Description of file: '+table,1)[1].split('Note (',1)[0]
        for label,(a,b) in columns.items():
            position = rf'{a}\s*-\s*{b}' if a != b else str(a)
            if not re.search(rf'^\s*{position}\s+\S+\s+\S+\s+{re.escape(label)}\b', section,re.M):
                raise ValueError('ReadMe schema mismatch: '+table+'.'+label)
    rows3, rows4 = _read(table3,T3,optional_trailing=True), _read(table4,T4)
    if set(rows3) != set(rows4):
        raise ValueError('table3/table4 group identity mismatch')
    ids = np.array(sorted(rows4),dtype=np.int64)
    def val(label):
        return np.array([float(rows4[i][label]) for i in ids])
    ra, dec = val('RAdeg'), val('DEdeg')
    if not np.isfinite(ra).all() or not np.isfinite(dec).all() or np.any((ra<0)|(ra>=360)|(dec<-90)|(dec>90)):
        raise ValueError('invalid J2000 angular range')
    ra,dec=np.deg2rad(ra),np.deg2rad(dec)
    n=np.column_stack((np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)))
    presence=[]
    for i in ids:
        p=[]
        for label in list(T3)[1:]:
            raw=rows3[i][label]
            value=float(raw) if raw else 0.
            if not np.isfinite(value) or value<0:
                raise ValueError('invalid method presence metadata')
            p.append(value>0)
        presence.append(p)
    hashes={str(Path(p)):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (table3,table4,readme)}
    return GroupedObservations(ids,val('DMzp'),val('e_DMzp'),val('Vh'),n,np.array(presence,dtype=bool),
        {'source_sha256':hashes,'release':'CDS J/ApJ/944/94','frame':'heliocentric Vh; J2000 equatorial',
         'table4_columns':list(T4),'table3_columns':list(T3),'table3_role':'method PRESENCE only; no second likelihood'})
