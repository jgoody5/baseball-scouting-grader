import unittest

from streamlit.testing.v1 import AppTest


class StreamlitUiRuntimeTests(unittest.TestCase):
    def test_app_renders_without_runtime_exceptions(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=30)
        self.assertEqual(
            len(app.exception),
            0,
            [str(exc.value) for exc in app.exception],
        )


if __name__ == "__main__":
    unittest.main()
