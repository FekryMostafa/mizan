"""Audit saved notebook provenance; this does not execute or reproduce its models."""
from collections import Counter
from pathlib import Path
import ast
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PATH = ROOT / 'reference/literature_refresh/mealmeter_code/MealMeter.ipynb'


def main():
    notebook = json.loads(PATH.read_text())
    cells = notebook['cells']
    def source(i):
        return ''.join(cells[i]['source'])
    def filenames(i):
        text = ''.join(''.join(o.get('text', [])) for o in cells[i].get('outputs', []))
        return re.findall(r'(P\d+_D\d+_[^\\\s]+)\.(?:csv|xlsx)', text)
    signal_files, label_files = filenames(4), filenames(7)
    assert len(signal_files) == len(label_files) == 173
    assert len(set(signal_files)) == len(signal_files)
    tree = ast.parse(source(10))
    ranges = tree.body[0].value.elts
    blocks = []
    for r in ranges:
        assert isinstance(r, ast.Call) and r.func.id == 'range'
        start, end = [ast.literal_eval(a) for a in r.args]
        counts = dict(Counter(f.split('_')[0] for f in signal_files[start:end]))
        blocks.append({'start_inclusive': start, 'end_exclusive': end,
                       'participant_counts_from_saved_filenames': counts,
                       'mixed_participants': len(counts) > 1})
    mismatches = [{'row_zero_based': i, 'signal': a, 'label': b}
                  for i, (a, b) in enumerate(zip(signal_files, label_files))
                  if a.replace('_short', '') != b.replace('_label', '')]
    # Feature construction is signal-major: 16 consecutive features per signal.
    # Trace which original signal indices the published reshape assigns to each bar.
    wrong_groups = {str(j): dict(Counter((7*k+j)//16 for k in range(16)))
                    for j in range(7)}
    result = {'notebook_sha256': hashlib.sha256(PATH.read_bytes()).hexdigest(),
              'scope': 'Saved source and outputs, not a rerun on missing raw participant data.',
              'signal_count': len(signal_files), 'label_count': len(label_files),
              'participant_counts': dict(Counter(f.split('_')[0] for f in signal_files)),
              'evaluation_blocks': blocks,
              'mixed_evaluation_blocks': sum(b['mixed_participants'] for b in blocks),
              'filename_pair_mismatches': mismatches,
              'feature_attribution_actual_signal_mixture_per_bar': wrong_groups,
              'cautions': ['Notebook outputs may be stale relative to current cell source.',
                           'Filename discrepancies do not establish the contents of missing labels.',
                           'No clinical accuracy can be recomputed without released raw inputs.']}
    (OUT / 'notebook_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
