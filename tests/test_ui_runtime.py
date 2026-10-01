from streamlit.testing.v1 import AppTest


def test_app_renders_without_runtime_exceptions():
    app = AppTest.from_file("app.py")
    app.run(timeout=30)
    assert len(app.exception) == 0, [str(exc.value) for exc in app.exception]
