"""Synthetic checks only; no human or wearable performance evidence."""
from copy import deepcopy
import unittest
from validate_meal import validate_meal, validate_chronology

def meal():
    return dict(participant_id='synthetic', meal_id='example', sensor_id='example', role='calibration',
        started_at='2026-09-08T12:00:00-05:00', finished_at='2026-09-08T12:20:00-05:00',
        calibration_response_ends_at='2026-09-08T15:00:00-05:00',
        components=[dict(served_g=150, leftover_g=50, reference_basis_g=100,
                        carbs_g=20, protein_g=10, fat_g=5,
                        weighed_state='cooked', reference_state='cooked',
                        reference_source='Synthetic arithmetic example, not food advice', uniform_composition=True)])

class Checks(unittest.TestCase):
    def test_leftovers_and_reference_basis(self):
        self.assertEqual(validate_meal(meal())['recorded_macros'], dict(carbs_g=20, protein_g=10, fat_g=5))
    def test_missing_fat_is_not_zero(self):
        r=meal();r['components'][0]['fat_g']=None
        with self.assertRaises(ValueError):validate_meal(r)
    def test_mass_inconsistent_reference(self):
        r=meal();r['components'][0].update(reference_basis_g=4,carbs_g=41,protein_g=30,fat_g=12)
        with self.assertRaises(ValueError):validate_meal(r)
    def test_mixed_leftovers(self):
        r=meal();r['components'][0]['uniform_composition']=False
        with self.assertRaises(ValueError):validate_meal(r)
    def test_raw_cooked_mismatch(self):
        r=meal();r['components'][0]['reference_state']='raw'
        with self.assertRaises(ValueError):validate_meal(r)
    def test_timezone_required(self):
        r=meal();r['started_at']='2026-09-08T12:00:00'
        with self.assertRaises(ValueError):validate_meal(r)
    def test_future_calibration_rejected(self):
        c=meal();q=deepcopy(c);q.update(meal_id='query',role='evaluation',started_at='2026-09-08T14:00:00-05:00')
        with self.assertRaises(ValueError):validate_chronology([c,q])
    def test_valid_chronology(self):
        c=meal();q=deepcopy(c);q.update(meal_id='query',role='evaluation',started_at='2026-09-08T16:00:00-05:00',finished_at='2026-09-08T16:20:00-05:00')
        validate_chronology([c,q])

if __name__=='__main__':unittest.main()
