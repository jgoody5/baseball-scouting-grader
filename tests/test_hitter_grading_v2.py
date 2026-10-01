import unittest

from hitter_grading import (
    grade_game_power_from_projected_hr,
    grade_hit_from_projected_avg,
    grade_raw_power,
    grade_raw_power_from_ev90,
    grade_raw_power_from_max_ev,
    grade_run_from_60,
    grade_run_from_home_to_first,
    resolve_reference_grade,
)


class HitterGradingTests(unittest.TestCase):
    def test_hit_reference(self):
        self.assertEqual(grade_hit_from_projected_avg(.260), 50)
        self.assertEqual(grade_hit_from_projected_avg(.280), 60)
        self.assertEqual(grade_hit_from_projected_avg(.320), 80)

    def test_raw_power_ev90(self):
        self.assertEqual(grade_raw_power_from_ev90(104.0), 50)
        self.assertEqual(grade_raw_power_from_ev90(105.0), 55)
        self.assertEqual(grade_raw_power_from_ev90(110.0), 80)

    def test_raw_power_max_ev_fallback(self):
        self.assertEqual(grade_raw_power_from_max_ev(110.0), 50)
        self.assertEqual(grade_raw_power_from_max_ev(113.0), 60)
        self.assertEqual(grade_raw_power(None, 113.0), (60, "Max EV fallback"))
        self.assertEqual(grade_raw_power(106.0, 113.0), (60, "EV90"))

    def test_game_power_reference(self):
        self.assertEqual(grade_game_power_from_projected_hr(10), 40)
        self.assertEqual(grade_game_power_from_projected_hr(20), 50)
        self.assertEqual(grade_game_power_from_projected_hr(30), 60)
        self.assertEqual(grade_game_power_from_projected_hr(40), 80)

    def test_run_60(self):
        self.assertEqual(grade_run_from_60(6.90), 50)
        self.assertEqual(grade_run_from_60(6.80), 55)
        self.assertEqual(grade_run_from_60(6.50), 70)
        self.assertEqual(grade_run_from_60(7.20), 40)

    def test_home_to_first_handedness(self):
        self.assertEqual(grade_run_from_home_to_first(4.30, "R"), 50)
        self.assertEqual(grade_run_from_home_to_first(4.20, "L"), 50)
        self.assertEqual(grade_run_from_home_to_first(4.20, "R"), 60)
        self.assertIsNone(grade_run_from_home_to_first(4.20, "S"))

    def test_manual_override(self):
        self.assertEqual(resolve_reference_grade(50, "Auto"), 50)
        self.assertEqual(resolve_reference_grade(50, 60), 60)
        self.assertEqual(resolve_reference_grade(None, 55), 55)


if __name__ == "__main__":
    unittest.main()
