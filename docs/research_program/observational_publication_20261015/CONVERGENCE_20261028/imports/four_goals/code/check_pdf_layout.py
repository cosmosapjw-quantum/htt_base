"""Mechanical PDF layout check; visual inspection is recorded separately."""
from pathlib import Path
import json
import fitz

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'output/HTT_FOUR_GOALS_FIBRE_20261028.pdf'
doc = fitz.open(path)
records = []
for index, page in enumerate(doc):
    out = []
    for block in page.get_text('blocks'):
        if block[6] != 0:
            continue
        box = fitz.Rect(block[:4])
        if not page.rect.contains(box):
            out.append({'box': list(box), 'sample': block[4][:100]})
    records.append({'page': index + 1, 'chars': len(page.get_text()),
                    'images': len(page.get_images()), 'outside_page': out})
text = ''.join(page.get_text() for page in doc)
result = {'pages': len(doc), 'summary': records,
          'current_sign_result_present': '98.086' in text,
          'obsolete_sign_result_absent': '98.004' not in text,
          'visual_inspection': {'pages': [1, 8, 15, 19, 21, 26, 31, 36],
              'repair': 'Split the long source-result path paragraph on page 21.',
              'note': 'All six scientific figures and the repaired page were visually inspected.'}}
(ROOT / 'output/PDF_QA.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'pages': len(doc), 'outside_page_blocks': sum(len(r['outside_page']) for r in records),
                  'current_sign_result_present': result['current_sign_result_present'],
                  'obsolete_sign_result_absent': result['obsolete_sign_result_absent']}))
assert result['current_sign_result_present'] and result['obsolete_sign_result_absent']
assert not any(r['outside_page'] for r in records)
