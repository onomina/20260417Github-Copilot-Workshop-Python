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


class StartBehaviorTest(unittest.TestCase):
    def test_start_resets_remaining_seconds_after_finish(self) -> None:
        class _DummyButton:
            def __init__(self) -> None:
                self.last_text = ""

            def configure(self, **kwargs: str) -> None:
                self.last_text = kwargs.get("text", "")

        class _DummyRoot:
            def __init__(self) -> None:
                self.after_calls: list[tuple[int, object]] = []

            def after(self, delay: int, callback: object) -> None:
                self.after_calls.append((delay, callback))

        class _DummyApp:
            def __init__(self) -> None:
                self.running = False
                self.total_seconds = 1500
                self.remaining_seconds = 0.0
                self.ripples = [{"radius": 1.0}]
                self.particles = [{"radius": 1.0}]
                self.start_button = _DummyButton()
                self.root = _DummyRoot()
                self.started_at = 0.0
                self.last_tick_remaining = 0.0
                self.last_ripple_at = 0.0
                self.draw_called = 0

            def draw(self) -> None:
                self.draw_called += 1

            def tick(self) -> None:
                return

        dummy = _DummyApp()
        app.PomodoroApp.start(dummy)

        self.assertTrue(dummy.running)
        self.assertEqual(dummy.remaining_seconds, float(dummy.total_seconds))
        self.assertEqual(dummy.ripples, [])
        self.assertEqual(dummy.particles, [])
        self.assertEqual(dummy.draw_called, 1)
        self.assertEqual(dummy.last_tick_remaining, float(dummy.total_seconds))
        self.assertEqual(dummy.start_button.last_text, "進行中")
        self.assertEqual(len(dummy.root.after_calls), 1)
        self.assertEqual(dummy.root.after_calls[0][0], app.UPDATE_INTERVAL_MS)


if __name__ == "__main__":
    unittest.main()
