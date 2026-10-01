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


class HitterPdfSmokeTests(unittest.TestCase):
    def test_position_player_pdf_builds(self):
        from hitter_report_export import build_hitter_report_pdf

        pdf = build_hitter_report_pdf(
            profile={
                "name": "Test Player",
                "position": "CF",
                "bats": "L",
                "throws": "R",
                "school": "Florida",
                "height": "6'1\"",
                "weight": 195,
                "draft_class": "2027",
            },
            impact="Everyday-center-field profile with on-base and defensive value.",
            grades=[
                {"Tool": "Hit", "Present": 50, "Future": 55, "Reference": "Projected MLB AVG: .260"},
                {"Tool": "Raw Power", "Present": 60, "Future": 65, "Reference": "EV90: 106.0 mph"},
                {"Tool": "Game Power", "Present": 50, "Future": 55, "Reference": "Projected MLB HR: 20"},
                {"Tool": "Run", "Present": 55, "Future": 55, "Reference": "60-Yard: 6.80s"},
                {"Tool": "Arm", "Present": 60, "Future": 60, "Reference": "Throw velo: 91.0 mph"},
                {"Tool": "Field", "Present": 65, "Future": 70, "Reference": "-"},
            ],
            summary="Athletic up-the-middle defender with contact ability and room for game power growth.",
            observations={
                "date": "2026-10-01",
                "games_seen": 2,
                "positions_seen": "CF",
                "swing": "Compact path with bat speed.",
                "approach": "Controls the zone.",
                "adjustments": "Shortens with two strikes.",
                "defense": "Reads and routes play above average.",
                "baserunning": "Aggressive with solid instincts.",
                "makeup": "Competitive on-field presence.",
                "arm_notes": "Above-average carry with accuracy.",
            },
            overall={"floor": 45, "most_likely": 50, "ceiling": 60},
        )
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1000)
