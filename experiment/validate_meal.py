"""Validate weighed meal references. Does not predict intake from a sensor."""
import argparse
from datetime import datetime
import json
import math
from pathlib import Path

MACROS = ('carbs_g', 'protein_g', 'fat_g')

def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f'{name} must be a finite nonnegative number, not a missing value.')
    return float(value)

def instant(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.utcoffset() is None:
        raise ValueError('Timestamps must include timezone offsets.')
    return t

def validate_meal(record):
    for name in ('participant_id', 'meal_id', 'sensor_id'):
        if not isinstance(record.get(name), str) or not record[name].strip():
            raise ValueError(f'{name} is required.')
    if record.get('role') not in ('calibration', 'evaluation'):
        raise ValueError('role must be calibration or evaluation.')
    start, end = instant(record['started_at']), instant(record['finished_at'])
    if end < start:
        raise ValueError('Meal finish precedes start.')
    components = record.get('components')
    if not isinstance(components, list) or not components:
        raise ValueError('Record at least one individually weighed component.')
    total = {m: 0. for m in MACROS}
    details = []
    for index, c in enumerate(components):
        served, leftover = number(c.get('served_g'), 'served_g'), number(c.get('leftover_g'), 'leftover_g')
        if leftover > served:
            raise ValueError('Leftovers cannot exceed served mass.')
        basis = number(c.get('reference_basis_g'), 'reference_basis_g')
        if basis == 0:
            raise ValueError('Nutrition reference basis must be positive grams.')
        if not c.get('weighed_state') or c.get('weighed_state') != c.get('reference_state'):
            raise ValueError('Weighed and reference states must match, e.g. cooked versus raw.')
        if not isinstance(c.get('reference_source'), str) or not c['reference_source'].strip():
            raise ValueError('A traceable nutrition reference is required.')
        nutrients = {m: number(c.get(m), m) for m in MACROS}
        if sum(nutrients.values()) > basis * 1.1:
            raise ValueError('Reference macro mass exceeds its stated food mass; check serving units.')
        if c.get('uniform_composition') is not True:
            raise ValueError('Split mixed components before using leftover mass to scale nutrients.')
        multiplier = (served-leftover)/basis
        computed = {m: nutrients[m]*multiplier for m in MACROS}
        for m in MACROS:
            total[m] += computed[m]
        details.append(dict(component=index, consumed_g=served-leftover, **computed))
    return dict(meal_id=record['meal_id'], participant_id=record['participant_id'], role=record['role'],
                recorded_macros=total, components=details,
                reference_truth_certified=False,
                note='Calculated from supplied references; label uncertainty and sensor performance are not validated.')

def validate_chronology(records):
    identifiers = [(r['participant_id'], r['meal_id']) for r in records]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate meal identifiers.')
    for pid in {r['participant_id'] for r in records}:
        personal = [r for r in records if r['participant_id'] == pid]
        cal = [r for r in personal if r['role'] == 'calibration']
        query = [r for r in personal if r['role'] == 'evaluation']
        if query and not cal:
            raise ValueError('Evaluation requires earlier calibration records.')
        if query:
            ends = [instant(r['calibration_response_ends_at']) for r in cal]
            if any(t < instant(r['finished_at']) for t, r in zip(ends, cal)):
                raise ValueError('Calibration response ends before its meal finishes.')
            if max(ends) >= min(instant(r['started_at']) for r in query):
                raise ValueError('Calibration response windows must finish before evaluation begins.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='JSON array of meal records')
    args = parser.parse_args()
    records = json.loads(args.input.read_text())
    results = [validate_meal(r) for r in records]
    validate_chronology(records)
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
