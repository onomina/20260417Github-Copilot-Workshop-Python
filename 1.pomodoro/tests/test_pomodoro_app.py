import importlib.util
import pathlib
import unittest


APP_PATH = pathlib.Path(__file__).resolve().parent.parent / "app.py"


spec = importlib.util.spec_from_file_location("pomodoro_app", APP_PATH)
app = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(app)


class PomodoroAppTests(unittest.TestCase):
    def test_options_are_customizable(self):
        self.assertEqual(app.POMODORO_OPTIONS, [15, 25, 35, 45])
        self.assertEqual(app.BREAK_OPTIONS, [5, 10, 15])

    def test_theme_modes_exist(self):
        self.assertEqual(set(app.THEMES.keys()), {"light", "dark", "focus"})

    def test_html_contains_required_controls(self):
        html = app.build_html()
        self.assertIn('id="pomodoro"', html)
        self.assertIn('id="break"', html)
        self.assertIn('id="theme"', html)
        self.assertIn('id="start-sound"', html)
        self.assertIn('id="end-sound"', html)
        self.assertIn('id="tick-sound"', html)


if __name__ == "__main__":
    unittest.main()
