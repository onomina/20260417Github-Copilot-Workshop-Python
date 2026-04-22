import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("app.py")
SPEC = importlib.util.spec_from_file_location("pomodoro_app", MODULE_PATH)
app = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(app)


class PomodoroVisualFeedbackTest(unittest.TestCase):
    def test_clamp_limits_range(self) -> None:
        self.assertEqual(app.clamp(-1, 0, 1), 0)
        self.assertEqual(app.clamp(2, 0, 1), 1)
        self.assertEqual(app.clamp(0.5, 0, 1), 0.5)

    def test_progress_color_stages(self) -> None:
        self.assertEqual(app.progress_to_color(0.0), "#4287f5")
        self.assertEqual(app.progress_to_color(0.5), "#f5cd42")
        self.assertEqual(app.progress_to_color(1.0), "#f54242")

    def test_progress_color_clamps_input(self) -> None:
        self.assertEqual(app.progress_to_color(-2.0), "#4287f5")
        self.assertEqual(app.progress_to_color(3.0), "#f54242")


if __name__ == "__main__":
    unittest.main()
