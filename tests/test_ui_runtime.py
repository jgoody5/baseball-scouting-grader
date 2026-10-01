import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class StreamlitUiRuntimeTests(unittest.TestCase):
    def _assert_no_exceptions(self, app):
        self.assertEqual(
            len(app.exception),
            0,
            [str(exc.value) for exc in app.exception],
        )

    def test_pitcher_page_renders_without_runtime_exceptions(self):
        app = AppTest.from_file(str(APP_PATH))
        app.run(timeout=30)
        self._assert_no_exceptions(app)

    def test_position_player_page_renders_without_runtime_exceptions(self):
        app = AppTest.from_file(str(APP_PATH))
        app.run(timeout=30)
        self._assert_no_exceptions(app)
        self.assertGreaterEqual(len(app.radio), 1)
        app.radio[0].set_value("Position Player")
        app.run(timeout=30)
        self._assert_no_exceptions(app)


if __name__ == "__main__":
    unittest.main()
