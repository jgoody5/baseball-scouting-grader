import math
import unittest

from draft_valuation import apply_override, evaluate, load_valuation_config, valuation_report_text


def hitters(value=50):
    return [{"Tool": name, "Present": value, "Future": value}
            for name in ("Hit", "Raw Power", "Game Power", "Run", "Arm", "Field")]


def pitchers(value=50):
    return [{"Tool": name, "Present": value, "Future": value}
            for name in ("Fastball Velocity", "Fastball Life", "Slider", "Changeup", "Command", "Control")]


class ValuationTests(unittest.TestCase):
    def test_missing_future_does_not_use_present_as_projection(self):
        rows = hitters(); rows[0]["Future"] = "-"
        self.assertFalse(evaluate(rows, "Position Player", "CF")["ready"])

    def test_position_changes_identical_tools(self):
        cf = evaluate(hitters(), "Position Player", "CF", risk="Lower")
        first = evaluate(hitters(), "Position Player", "1B", risk="Lower")
        self.assertGreater(cf["index"], first["index"])
        self.assertGreater(cf["bonus_high"], first["bonus_high"])

    def test_pitcher_role_and_no_double_count(self):
        starter = evaluate(pitchers(), "Pitcher", "Starter")
        reliever = evaluate(pitchers(), "Pitcher", "Reliever")
        self.assertEqual(starter["base_index"], 50)
        self.assertEqual(reliever["base_index"], 50)
        self.assertGreater(starter["index"], reliever["index"])

    def test_duplicate_slider_cannot_create_starter_depth(self):
        rows = [r for r in pitchers() if r["Tool"] != "Changeup"]
        rows.append({"Tool": "Slider", "Present": 60, "Future": 60})
        self.assertFalse(evaluate(rows, "Pitcher", "Starter")["ready"])
        self.assertTrue(evaluate(rows, "Pitcher", "Reliever")["ready"])

    def test_physical_fit_requires_reason(self):
        self.assertFalse(evaluate(hitters(), "Position Player", "CF",
                                 physical_fit="Supports projected role")["ready"])
        v = evaluate(hitters(), "Position Player", "CF", physical_fit="Supports projected role",
                     physical_note="Maintains mobility with strength")
        self.assertEqual(v["trait_adjustment"], 1)

    def test_adjustment_cap_and_unknown_traits(self):
        v = evaluate(hitters(), "Position Player", "SS",
                     {k: "Strength" for k in ("Athleticism", "Makeup / learning", "Role reliability")},
                     physical_fit="Supports projected role", physical_note="Evidence")
        self.assertEqual(v["trait_adjustment"], 3)
        with self.assertRaises(ValueError):
            evaluate(hitters(), "Position Player", "CF", {"Unknown": "Strength"})

    def test_risk_only_widens(self):
        low = evaluate(hitters(55), "Position Player", "3B", risk="Lower")
        high = evaluate(hitters(55), "Position Player", "3B", risk="Higher")
        self.assertEqual(low["index"], high["index"])
        self.assertLessEqual(high["bonus_low"], low["bonus_low"])
        self.assertGreaterEqual(high["bonus_high"], low["bonus_high"])

    def test_projection_gap_is_not_upside_bonus(self):
        rows = hitters(60)
        for row in rows: row["Present"] = 40
        result = evaluate(rows, "Position Player", "3B", risk="Lower")
        self.assertEqual(result["range_width"], 4)
        self.assertEqual(result["index"], 60)

    def test_nonfinite_and_invalid_grade_rejected(self):
        for value in (float("nan"), float("inf"), 81, 49):
            rows = hitters(); rows[0]["Future"] = value
            with self.assertRaises(ValueError): evaluate(rows, "Position Player", "CF")

    def test_override_preserves_model_and_validates(self):
        model = evaluate(hitters(), "Position Player", "CF")
        v = apply_override(model, 7, 12, 300000, 450000, "My board value")
        self.assertEqual(v["model_suggestion"], model)
        self.assertEqual(v["basis"], "Scout override")
        self.assertIn("$300,000", valuation_report_text(v))
        for args in [(8, 4, 1, 2, "x"), (1, 2, 4, 1, "x"), (1, 2, 1, 2, "")]:
            with self.assertRaises(ValueError): apply_override(model, *args)

    def test_weights_and_all_grade_boundaries(self):
        c = load_valuation_config()
        for group in ("hitter_weights", "pitcher_weights"):
            for weights in c[group].values(): self.assertAlmostEqual(sum(weights.values()), 1)
        for position in c["hitter_weights"]:
            previous = -1
            for g in range(20, 81, 5):
                v = evaluate(hitters(g), "Position Player", position)
                self.assertTrue(v["ready"])
                self.assertLessEqual(v["bonus_low"], v["bonus_high"])
                self.assertGreaterEqual(v["bonus_high"], previous)
                previous = v["bonus_high"]

    def test_dh_does_not_require_defensive_tools(self):
        self.assertTrue(evaluate(hitters()[:3], "Position Player", "DH")["ready"])


if __name__ == "__main__":
    unittest.main()
