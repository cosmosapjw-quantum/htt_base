#!/usr/bin/env python3
"""Assemble the authored teaching chapters; no science computation or network access.

The small replacements below finish the reading guide after Appendix E was
written. They do not edit the chapter sources or the accepted Report A R3.
The output directory must be empty. Build and inspection remain separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

PARTS = (
    '01_FOUNDATIONS_AND_THE_SKY.md',
    '02_ORBITS_PHYSICAL_STATE_AND_MES.md',
    '03_INFERENCE_RANDOMISATION_AND_OBSERVER_RESPONSE.md',
    '04_MASKS_NUISANCE_AND_NUMERICAL_ERROR.md',
    '05_APPENDICES_CERTIFICATES_AND_FIBRES.md',
    '06_RADIATION_MODEL_AND_MES_DERIVATION.md',
)


def identity(raw: bytes) -> dict[str, object]:
    return {
        'bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(),
        'git_blob': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
    }


def replace_one(text: str, old: str, new: str, name: str, edits: list[str]) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f'{name}: expected one source passage, found {count}')
    edits.append(name)
    return text.replace(old, new, 1)


def replace_paragraph(text: str, start: str, new: str, name: str,
                      edits: list[str]) -> str:
    pattern = re.compile(r'^' + re.escape(start) + r'[^\n]*(?:\n(?!\n)[^\n]*)*', re.M)
    text, count = pattern.subn(lambda _: new, text)
    if count != 1:
        raise ValueError(f'{name}: expected one paragraph, found {count}')
    edits.append(name)
    return text


def assemble(chapters: dict[str, str]) -> tuple[str, list[str]]:
    edits: list[str] = []
    first = chapters[PARTS[0]]
    first = replace_paragraph(
        first, 'One boundary needs stating at the outset.',
        'The mathematical development is self-contained relative to the stated physical model. '
        'In particular, Appendix E derives the kinematical bounds used in Section 6 from an '
        'explicit first-order collisionless-radiation system and precisely defined derivative '
        'envelopes. These are sufficient physical premises, not observations extracted from one '
        'sky. The general nonlinear almost-isotropy theorem is not asserted here. Historical '
        'nonaxial numerical results remain labelled calculations, while the axial continuum '
        'rank result has its defining finite arithmetic and exact certificate in Appendix B.',
        'reading-guide-after-radiation-derivation', edits)

    second = chapters[PARTS[1]]
    start = second.index('To state exactly what is supplied,')
    end = second.index('**Physical input M', start)
    replacement = r'''To specify the derivative premises, let \(\tau_{A_\ell}\) denote a fractional-temperature STF multipole; \(A_\ell\) is a list of \(\ell\) spatial indices. Let \(\epsilon_\ell\) bound its full tensor norm. A star denotes a derivative along the observer, and a prime a projected spatial derivative, with each derivative normalised by the expansion rate. The exact normed operators used for the mixed and second derivative envelopes are stated in Eqs. (E.9)–(E.10). In particular, the double-prime quadrupole envelope bounds the displayed antisymmetric differentiated divergence, not an unspecified second-derivative norm with an omitted contraction factor. Propagation-direction and outward-sky multipoles have the same norms. Appendix E derives a sufficient first-order radiation model for the bounds below; this is a specific, explicit branch of the broader physical programme.

'''
    second = second[:start] + replacement + second[end:]
    edits.append('define-exact-MES-derivative-operators')
    second = replace_one(
        second,
        '**Physical input M — retained MES derivative estimates.** On the stated branch, the following norm bounds are supplied by the radiation–geometry analysis:',
        '**Model M — a sufficient first-order radiation branch.** Appendix E derives the following norm bounds from the stated moment equations and derivative envelopes. Weak envelope assumptions give non-strict inequalities. Where the displays use a strict sign, a corresponding strict envelope or slack is an additional premise:',
        'connect-MES-bounds-to-internal-proof', edits)
    second = replace_one(
        second,
        'We do not relabel their full Einstein–Liouville derivation as a theorem proved here.',
        'The local derivation and the distinction between weak and strict bounds are supplied in Appendix E. No nonlinear converse or inference of the derivative premises from a local sky is used.',
        'replace-obsolete-import-only-description', edits)

    fourth = chapters[PARTS[3]]
    fourth = replace_paragraph(
        fourth, 'The general mathematical statements of this exposition',
        'The mathematical statements have their hypotheses and proofs within this report. '
        'For the kinematical bounds, Appendix E supplies an explicit sufficient first-order '
        'radiation model, moment equations and derivative-envelope calculation. Its premises '
        'remain physical assumptions; a full nonlinear almost-isotropy or converse theorem is '
        'not claimed. Historical numerical results remain calculations with stated domains. '
        'These distinctions make the conclusions usable without confusing an assumed physical '
        'model, an exact deduction and a finite numerical observation.',
        'conclusions-after-radiation-derivation', edits)

    fifth = chapters[PARTS[4]]
    fifth = replace_paragraph(
        fifth, 'A theorem in the text is a conditional mathematical statement',
        'A theorem in the text is a conditional mathematical statement with an internal proof. '
        'Model M states an explicit first-order radiation system and derivative controls; '
        'Appendix E derives the resulting kinematical estimates. The finite-direction rank '
        'ladder and finite-pixel outcomes remain reported calculations, not universal theorems. '
        'The exact axial certificate includes its defining arithmetic and its tabulated values. '
        'The contraction-fibre appendix is a finite-dimensional derivation, not an empirical '
        'velocity analysis.',
        'notation-status-after-radiation-derivation', edits)
    fifth = replace_paragraph(
        fifth, "The older report's complete proof of the global almost-isotropy result",
        'The internal derivation is sufficient for the conditional model used in this account. '
        'References acknowledge the physical and mathematical lineage; none is needed to '
        'supply a missing step in a claimed finite-dimensional theorem. More general nonlinear '
        'spacetime statements, error bounds for neglected perturbative orders and the validity '
        'of the maintained physical assumptions are distinct questions, not conclusions '
        'deduced from the observable tensors.',
        'remove-obsolete-external-proof-dependency', edits)
    fifth = replace_one(fifth, '\n# References\n', '\n', 'move-references-after-appendix-E', edits)

    parts = [first, second, chapters[PARTS[2]], fourth, fifth, chapters[PARTS[5]]]
    text = '\n\n'.join(p.rstrip() for p in parts) + '\n\n# References\n'
    controls = [(i, ord(c)) for i, c in enumerate(text) if ord(c) < 32 and c not in '\t\r\n']
    if controls:
        raise ValueError(f'Unexpected source control characters: {controls[:10]}')
    return text, edits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chapters', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--bibliography', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source_dir = args.chapters.resolve()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError(f'Refusing nonempty output directory: {out}')
    raw_parts = {name: (source_dir / name).read_bytes() for name in PARTS}
    chapters = {name: raw.decode('utf-8') for name, raw in raw_parts.items()}
    text, edits = assemble(chapters)
    bibliography = args.bibliography.resolve().read_bytes()
    if identity(bibliography)['git_blob'] != '331c557c0f6a7de84fdd97123d8bdb8fae0e0a53':
        raise ValueError('Bibliography is not the retained twenty-entry source')
    sections = re.findall(r'^## (\d+)\. ', text, re.M)
    appendices = re.findall(r'^# Appendix ([A-Z])\.', text, re.M)
    if sections != [str(n) for n in range(1, 14)]:
        raise ValueError(f'Unexpected main section sequence: {sections}')
    if appendices != list('ABCDE'):
        raise ValueError(f'Unexpected appendix sequence: {appendices}')
    if text.count('\n# References\n') != 1:
        raise ValueError('References heading must occur exactly once')
    out.mkdir(parents=True, exist_ok=True)
    manuscript = text.encode('utf-8')
    (out / 'FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.md').write_bytes(manuscript)
    (out / 'references.bib').write_bytes(bibliography)
    record = {
        'operation': 'deterministic authored-text assembly, not mathematical verification',
        'input_chapters': {name: identity(raw) for name, raw in raw_parts.items()},
        'editorial_replacements': edits,
        'main_sections': sections,
        'appendices': appendices,
        'output_manuscript': identity(manuscript),
        'bibliography': identity(bibliography),
        'original_R3_modified': False,
        'proof_or_rendering_pass_claimed': False,
    }
    (out / 'ASSEMBLY_RECORD.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
