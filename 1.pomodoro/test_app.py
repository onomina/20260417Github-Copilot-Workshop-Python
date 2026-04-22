import importlib.util
import pathlib
from datetime import date, timedelta
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
    def test_start_resets_when_remaining_seconds_is_zero(self) -> None:
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
                pass

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


class GamificationTest(unittest.TestCase):
    def test_calculate_level(self) -> None:
        self.assertEqual(app.calculate_level(0), 1)
        self.assertEqual(app.calculate_level(299), 1)
        self.assertEqual(app.calculate_level(300), 2)

    def test_streak_and_achievements_and_xp(self) -> None:
        today = date(2026, 4, 22)
        history = [
            {"date": (today - timedelta(days=2)).isoformat(), "focus_minutes": 25, "completed": True},
            {"date": (today - timedelta(days=1)).isoformat(), "focus_minutes": 30, "completed": True},
            {"date": today.isoformat(), "focus_minutes": 20, "completed": True},
        ]
        progress = app.compute_progress(history, today=today)
        self.assertEqual(progress["xp"], 3 * app.XP_PER_COMPLETION)
        self.assertEqual(progress["streak_days"], 3)
        self.assertIn("初回完了", progress["achievements"])
        self.assertIn("3日連続", progress["achievements"])

    def test_weekly_ten_completions_badge(self) -> None:
        today = date(2026, 4, 22)
        week_start = today - timedelta(days=today.weekday())
        history = []
        for index in range(10):
            history.append(
                {
                    "date": (week_start + timedelta(days=index % 5)).isoformat(),
                    "focus_minutes": 25,
                    "completed": True,
                }
            )
        progress = app.compute_progress(history, today=today)
        self.assertIn("今週10回完了", progress["achievements"])

    def test_summarize_period_stats(self) -> None:
        today = date(2026, 4, 22)
        history = [
            {"date": (today - timedelta(days=1)).isoformat(), "focus_minutes": 20, "completed": True},
            {"date": today.isoformat(), "focus_minutes": 30, "completed": False},
            {"date": today.isoformat(), "focus_minutes": 25, "completed": True},
        ]
        stats = app.summarize_period_stats(history, days=7, today=today)
        self.assertEqual(stats["total_count"], 3)
        self.assertEqual(stats["completed_count"], 2)
        self.assertAlmostEqual(stats["completion_rate"], 66.6666, places=2)
        self.assertAlmostEqual(stats["average_focus_minutes"], 22.5)
        self.assertEqual(len(stats["daily_labels"]), 7)

    def test_streak_requires_consecutive_days(self) -> None:
        today = date(2026, 4, 22)
        history = [
            {"date": (today - timedelta(days=3)).isoformat(), "focus_minutes": 25, "completed": True},
            {"date": (today - timedelta(days=1)).isoformat(), "focus_minutes": 25, "completed": True},
            {"date": today.isoformat(), "focus_minutes": 25, "completed": True},
        ]
        self.assertEqual(app.calculate_streak_days(history, today=today), 2)


if __name__ == "__main__":
    unittest.main()
