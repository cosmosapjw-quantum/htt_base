import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.r105 import program


class TestR105Overlay(unittest.TestCase):
    def test_real_ledger(self):
        r=program.build()
        self.assertEqual((r['counts']['nodes'],r['counts']['edges']),(60,129))
        self.assertEqual(r['counts']['canonical_open'],42)
        self.assertEqual(r['counts']['r105_new_scientific_acceptances'],0)
        self.assertEqual(len(r['seven_research_axes']),7)
        self.assertEqual(len(r['seven_cross_routes']),7)
        self.assertEqual(r['next_id'],'SQ-CF4')
        rows={n['id']:n for n in r['nodes']}
        self.assertEqual(rows['H02']['R104_evidence_files'],['CF4_2MRS_FIELD.json'])
        self.assertIn('SQ-CF4',rows['H02']['hard_dependencies'])
        self.assertEqual(rows['SQ-NATIVE']['R104_report_state'],'blocked_external')
        self.assertEqual(rows['PHY-05']['R105_direct_evidence'][0]['section'],'PHY-05')
        self.assertTrue(all(n['canonical_acceptance'] and n['local_action'] for n in rows.values()))

    def test_invalid_link_or_changed_evidence_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=root/'r.json'
            path.write_text(json.dumps({'actual':1}))
            source={'r.json':{'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'kind':'data','nodes':{'N':'actual'}}}
            self.assertEqual(program.verified_evidence(root,Path('.'),source,{'N':{}}),source)
            source['r.json']['nodes']['N']='absent'
            with self.assertRaises(ValueError):
                program.verified_evidence(root,Path('.'),source,{'N':{}})
            path.write_text('{}')
            with self.assertRaises(ValueError):
                program.verified_evidence(root,Path('.'),source,{'N':{}})
            md=root/'comparison.md'
            md.write_text('# Common-window estimands\n')
            text={'comparison.md':{'sha256':hashlib.sha256(md.read_bytes()).hexdigest(),
                                   'format':'markdown','kind':'literature_comparison','nodes':{'H05':None}}}
            self.assertEqual(program.verified_evidence(root,Path('.'),text,{'H05':{}}),text)
            md.write_text('edited after review')
            with self.assertRaises(ValueError):
                program.verified_evidence(root,Path('.'),text,{'H05':{}})
