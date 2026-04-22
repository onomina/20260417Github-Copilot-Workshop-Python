import importlib.util
import pathlib
import unittest


module_path = pathlib.Path(__file__).with_name("app.py")
spec = importlib.util.spec_from_file_location("pomodoro_app", module_path)
if spec is None or spec.loader is None:
    raise RuntimeError("テスト対象モジュールをロードできません。")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class ProgressColorTest(unittest.TestCase):
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

    def test_lerp_color_interpolation_and_bounds(self) -> None:
        self.assertEqual(app.lerp_color((0, 0, 0), (255, 255, 255), 0.0), (0, 0, 0))
        self.assertEqual(app.lerp_color((0, 0, 0), (255, 255, 255), 1.0), (255, 255, 255))
        self.assertEqual(app.lerp_color((10, 20, 30), (110, 120, 130), 0.5), (60, 70, 80))
        self.assertEqual(app.lerp_color((0, 0, 0), (255, 255, 255), -1.0), (0, 0, 0))
        self.assertEqual(app.lerp_color((0, 0, 0), (255, 255, 255), 2.0), (255, 255, 255))


if __name__ == "__main__":
    unittest.main()
