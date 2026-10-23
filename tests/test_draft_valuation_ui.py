import unittest
from io import BytesIO
from pathlib import Path

from streamlit.testing.v1 import AppTest
from draft_valuation import evaluate, apply_override
from report_export import build_report_pdf
from hitter_report_export import build_hitter_report_pdf

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class ValuationUiTests(unittest.TestCase):
    def test_hitter_value_and_invalid_override(self):
        app = AppTest.from_file(APP)
        state = {"player_type_selector": "Position Player", "hv_enabled": True, "hv_target": "CF"}
        for tool in ("hit", "raw", "game", "run", "arm", "field"):
            state[tool + "_future"] = 50
        for k, v in state.items(): app.session_state[k] = v
        app.run(timeout=30)
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(len([m for m in app.metric if m.label.startswith("Suggested")]), 2)
        app.checkbox(key="hv_override").check().run()
        self.assertTrue(any("reason" in e.value for e in app.error))
        app.text_area(key="hv_override_reason").set_value("My board value").run()
        self.assertFalse(app.error)
        self.assertTrue(any("Your value" in e.value for e in app.success))
        app.number_input(key="hv_rlo").set_value(20).run()
        self.assertTrue(any("ordered" in e.value for e in app.error))

    def test_pitcher_value_and_missing_secondary(self):
        app = AppTest.from_file(APP)
        state = {"pv_enabled": True, "pv_target": "Reliever", "future_velo_0": 60,
                 "future_life_0": 55, "future_1": 55, "command_future": 45, "control_future": 50}
        for k, v in state.items(): app.session_state[k] = v
        app.run(timeout=30)
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(len([m for m in app.metric if m.label.startswith("Suggested")]), 2)
        app.selectbox(key="pv_target").set_value("Starter").run()
        self.assertFalse(app.exception)
        self.assertEqual(len([m for m in app.metric if m.label.startswith("Suggested")]), 0)
        self.assertTrue(any("secondary" in e.value for e in app.info))

    def test_manual_valuation_works_without_history_and_exports_exact_value(self):
        app = AppTest.from_file(APP)
        app.session_state['pv_enabled'] = True
        app.run(timeout=30)
        self.assertFalse(app.exception)
        app.checkbox(key='pv_override').check().run()
        app.number_input(key='pv_rlo').set_value(7)
        app.number_input(key='pv_rhi').set_value(12)
        app.number_input(key='pv_blo').set_value(300000)
        app.number_input(key='pv_bhi').set_value(450000)
        app.text_area(key='pv_override_reason').set_value('My board value').run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertTrue(any('$300,000 - $450,000' in e.value for e in app.success))

    def test_pdf_exports_only_round_and_dollar_value(self):
        rows = [{"Tool": k, "Present": 50, "Future": 55}
                for k in ("Hit", "Raw Power", "Game Power", "Run", "Arm", "Field")]
        v = evaluate(rows, "Position Player", "CF")
        v = apply_override(v, 4, 7, 300000, 450000, "Strength & mobility < frame")
        for build in (build_report_pdf, build_hitter_report_pdf):
            pdf = build({"name": "Test Player"}, "Impact", rows, "Summary", {}, valuation=v)
            self.assertTrue(pdf.startswith(b"%PDF"))
            from pypdf import PdfReader
            text=' '.join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
            self.assertIn('$300,000 - $450,000', text)
            self.assertIn('Rounds 4-7 value', text)
            for unwanted in ('Scout override', '2026 USD', 'Historical-profile investment guide', 'Rationale:', 'Strength & mobility'):
                self.assertNotIn(unwanted, text)


if __name__ == "__main__":
    unittest.main()
