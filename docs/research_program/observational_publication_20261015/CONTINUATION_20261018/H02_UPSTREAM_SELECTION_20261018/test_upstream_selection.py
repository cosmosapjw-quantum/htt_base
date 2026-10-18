import hashlib
import tempfile
import unittest
from pathlib import Path
import numpy as np
from upstream_selection import schema, parse_rows, band_class, join_status, group_summary, sealed, UPSTREAM, CF4, SOURCE, HERE
import json


class UpstreamTests(unittest.TestCase):
    def test_readme_schema_single_and_range(self):
        text='Byte-by-byte Description of file: x.dat\n 1- 7 I7 --- PGC identifier\n 9 F1.0 mag x value\n'
        self.assertEqual(schema(text,'x.dat'),{'PGC':(0,7,'I'),'x':(8,9,'F')})

    def test_trailing_blanks_missing_distances(self):
        # Real release legitimately omits all trailing distance fields on 11 rows.
        result=parse_rows(b'      2\n',{'PGC':(0,7,'I'),'DM':(8,13,'F')},1,13)
        self.assertIsNone(result[2]['DM'])

    def test_ambiguous_or_malformed_rows_rejected(self):
        fields={'PGC':(0,7,'I')}
        for data,n,width in [(b'      2\n      2\n',2,7),(b'      2\n',2,7),(b'      23\n',1,7),(b'       \n',1,7)]:
            with self.assertRaises(ValueError):
                parse_rows(data,fields,n,width)

    def test_missing_does_not_become_zero(self):
        result=parse_rows(b'      2  0.00\n',{'PGC':(0,7,'I'),'DM':(8,13,'F'),'other':(14,19,'F')},1,19)
        self.assertEqual(result[2]['DM'],0.)
        self.assertIsNone(result[2]['other'])

    def test_optical_presence_does_not_mean_W1_adoption(self):
        row={'DM-r':33.,'DM-i':33.,'DM-z':33.,'DM-W1':34.}
        self.assertEqual(band_class(row),'optical_and_W1')
        row.update({'DM-r':None,'DM-i':None,'DM-z':None})
        self.assertEqual(band_class(row),'W1_only')

    def test_join_missing_group_not_silently_selected(self):
        galaxy={2:{'1PGC':10},3:{'1PGC':11},4:{'1PGC':12}}
        counts=join_status([1,2,3,4],galaxy,{10,11},{10})
        self.assertEqual(set(counts.values()),{1})
        self.assertEqual(sum(counts.values()),4)

    def test_group_count_and_mass_no_repeated_galaxy_weight(self):
        args=([10,11,12],np.array([.02,.04,.06]),np.array([1.,2.,1.]),np.eye(3))
        first=group_summary({10,11},*args)
        repeated=group_summary([10,10,11,11,11],*args)
        self.assertEqual(first,repeated)
        self.assertEqual(first[0]['supporting_groups'],2)
        self.assertAlmostEqual(first[0]['working_inverse_variance_mass_fraction'],1.25/2.25)
        self.assertAlmostEqual(first[0]['effective_support_groups_kish'],1.25**2/1.0625)

    def test_empty_support_is_unavailable_not_zero_direction(self):
        result=group_summary(set(),np.array([10]),np.array([.02]),np.array([1.]),np.array([[1.,0,0]]))
        self.assertEqual(result[0]['kernel_mass_fraction'],0.)
        self.assertIsNone(result[0]['support_weighted_direction_mean'])

    def test_source_byte_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'raw'
            path.write_bytes(b'original')
            expected=hashlib.sha256(b'original').hexdigest()
            self.assertEqual(sealed(path,expected),b'original')
            path.write_bytes(b'changed')
            with self.assertRaises(ValueError): sealed(path,expected)

    def test_actual_release_join_against_independent_fixed_slices(self):
        # Independently use only literal documented PGC/group/modulus slices.
        # This catches the real non-nested sample and absent-distance records.
        data={int(line[:7]) for line in (UPSTREAM/'table1.dat').read_text().splitlines()}
        rows=(UPSTREAM/'table4.dat').read_text().splitlines()
        distances={int(line[:7]) for line in rows}
        measured={int(line[:7]) for line in rows if line[26:31].strip()}
        self.assertEqual((len(data-distances),len(distances-data),len(distances-measured)),(947,2,11))
        group={int(line[:7]):int(line[8:15]) for line in (CF4/'table2.dat').read_text().splitlines()}
        with np.load(SOURCE,allow_pickle=False) as f:
            selected=set(f['group_id'].tolist())
        joined=[p for p in measured if p in group and group[p] in selected]
        self.assertEqual((len(joined),len({group[p] for p in joined})),(7573,6697))
        result=json.loads((HERE/'results/UPSTREAM_SELECTION.json').read_text())
        self.assertEqual(sum(x['has_DMbest_count'] for x in result['quality_cells']),len(data&measured))
        self.assertEqual(result['band_contributors']['has_DMbest']['selected_groups'],6697)


if __name__ == '__main__': unittest.main()
