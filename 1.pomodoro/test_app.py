from datetime import date, timedelta
import unittest

from app import (
    XP_PER_COMPLETION,
    calculate_level,
    calculate_streak_days,
    compute_progress,
    summarize_period_stats,
)


class TestPomodoroGamification(unittest.TestCase):
    def test_calculate_level(self) -> None:
        self.assertEqual(calculate_level(0), 1)
        self.assertEqual(calculate_level(299), 1)
        self.assertEqual(calculate_level(300), 2)

    def test_streak_and_achievements_and_xp(self) -> None:
        today = date(2026, 4, 22)
        history = [
            {"date": (today - timedelta(days=2)).isoformat(), "focus_minutes": 25, "completed": True},
            {"date": (today - timedelta(days=1)).isoformat(), "focus_minutes": 30, "completed": True},
            {"date": today.isoformat(), "focus_minutes": 20, "completed": True},
        ]
        progress = compute_progress(history, today=today)
        self.assertEqual(progress["xp"], 3 * XP_PER_COMPLETION)
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
        progress = compute_progress(history, today=today)
        self.assertIn("今週10回完了", progress["achievements"])

    def test_summarize_period_stats(self) -> None:
        today = date(2026, 4, 22)
        history = [
            {"date": (today - timedelta(days=1)).isoformat(), "focus_minutes": 20, "completed": True},
            {"date": today.isoformat(), "focus_minutes": 30, "completed": False},
            {"date": today.isoformat(), "focus_minutes": 25, "completed": True},
        ]
        stats = summarize_period_stats(history, days=7, today=today)
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
        self.assertEqual(calculate_streak_days(history, today=today), 2)


if __name__ == "__main__":
    unittest.main()
