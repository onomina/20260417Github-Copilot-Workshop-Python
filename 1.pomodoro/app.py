from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - streamlit未導入環境向け
    st = None

XP_PER_COMPLETION = 100
XP_PER_LEVEL = 300


def calculate_level(xp: int) -> int:
    return (xp // XP_PER_LEVEL) + 1


def normalize_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def calculate_streak_days(history: list[dict[str, Any]], today: date | None = None) -> int:
    today = today or date.today()
    completed_dates = {
        normalize_date(item["date"])
        for item in history
        if item.get("completed")
    }

    streak = 0
    cursor = today
    while cursor in completed_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def calculate_achievements(history: list[dict[str, Any]], today: date | None = None) -> list[str]:
    today = today or date.today()
    completed_dates = sorted(
        {
            normalize_date(item["date"])
            for item in history
            if item.get("completed")
        }
    )
    completed_count = sum(1 for item in history if item.get("completed"))

    achievements: list[str] = []
    if completed_count >= 1:
        achievements.append("初回完了")

    longest = 0
    current = 0
    previous: date | None = None
    for current_day in completed_dates:
        if previous and current_day == previous + timedelta(days=1):
            current += 1
        else:
            current = 1
        longest = max(longest, current)
        previous = current_day
    if longest >= 3:
        achievements.append("3日連続")

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    completed_this_week = sum(
        1
        for item in history
        if item.get("completed")
        and week_start <= normalize_date(item["date"]) <= week_end
    )
    if completed_this_week >= 10:
        achievements.append("今週10回完了")
    return achievements


def summarize_period_stats(history: list[dict[str, Any]], days: int, today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    start = today - timedelta(days=days - 1)
    period_records = [
        item
        for item in history
        if start <= normalize_date(item["date"]) <= today
    ]
    completed_records = [item for item in period_records if item.get("completed")]

    total = len(period_records)
    completed = len(completed_records)
    completion_rate = (completed / total * 100) if total else 0.0
    average_focus = (
        sum(int(item.get("focus_minutes", 0)) for item in completed_records) / completed
        if completed
        else 0.0
    )

    by_day: dict[str, dict[str, int]] = {
        (start + timedelta(days=offset)).isoformat(): {"completed": 0, "focus_minutes": 0}
        for offset in range(days)
    }

    for item in period_records:
        key = normalize_date(item["date"]).isoformat()
        by_day[key]["focus_minutes"] += int(item.get("focus_minutes", 0))
        if item.get("completed"):
            by_day[key]["completed"] += 1

    return {
        "completion_rate": completion_rate,
        "average_focus_minutes": average_focus,
        "completed_count": completed,
        "total_count": total,
        "daily_labels": list(by_day.keys()),
        "daily_completed": [value["completed"] for value in by_day.values()],
        "daily_focus_minutes": [value["focus_minutes"] for value in by_day.values()],
    }


def compute_progress(history: list[dict[str, Any]], today: date | None = None) -> dict[str, Any]:
    completed_records = [item for item in history if item.get("completed")]
    xp = len(completed_records) * XP_PER_COMPLETION
    return {
        "xp": xp,
        "level": calculate_level(xp),
        "achievements": calculate_achievements(history, today=today),
        "streak_days": calculate_streak_days(history, today=today),
        "weekly_stats": summarize_period_stats(history, days=7, today=today),
        "monthly_stats": summarize_period_stats(history, days=30, today=today),
    }


def run_app() -> None:
    if st is None:
        raise RuntimeError("streamlit がインストールされていないため、UIを起動できません。")

    st.set_page_config(page_title="Pomodoro Gamification", page_icon="🍅", layout="wide")
    st.title("🍅 Pomodoro Timer + ゲーミフィケーション")
    st.caption("完了ごとにXPを獲得し、レベル・実績・ストリーク・統計グラフで進捗を可視化します。")

    if "history" not in st.session_state:
        st.session_state.history = []

    with st.form("completion_form"):
        completed_date = st.date_input("完了日", value=date.today())
        focus_minutes = st.number_input("集中時間（分）", min_value=1, max_value=180, value=25, step=1)
        submitted = st.form_submit_button("ポモドーロ完了を記録")
        if submitted:
            st.session_state.history.append(
                {
                    "date": completed_date.isoformat(),
                    "focus_minutes": int(focus_minutes),
                    "completed": True,
                }
            )
            st.success("完了を記録しました。XPが加算されます。")

    progress = compute_progress(st.session_state.history)
    col1, col2, col3 = st.columns(3)
    col1.metric("総XP", progress["xp"])
    col2.metric("レベル", progress["level"])
    col3.metric("連続日数（ストリーク）", f'{progress["streak_days"]} 日')

    st.subheader("🏅 実績バッジ")
    if progress["achievements"]:
        for badge in progress["achievements"]:
            st.success(f"達成: {badge}")
    else:
        st.info("まだ実績はありません。まずは1回完了してみましょう。")

    weekly = progress["weekly_stats"]
    monthly = progress["monthly_stats"]
    tab_week, tab_month = st.tabs(["週間統計", "月間統計"])
    with tab_week:
        st.metric("完了率", f'{weekly["completion_rate"]:.1f}%')
        st.metric("平均集中時間", f'{weekly["average_focus_minutes"]:.1f} 分')
        st.line_chart(
            {
                "完了回数": weekly["daily_completed"],
                "集中時間": weekly["daily_focus_minutes"],
            }
        )
        st.dataframe(
            {
                "日付": weekly["daily_labels"],
                "完了回数": weekly["daily_completed"],
                "集中時間": weekly["daily_focus_minutes"],
            },
            use_container_width=True,
        )
    with tab_month:
        st.metric("完了率", f'{monthly["completion_rate"]:.1f}%')
        st.metric("平均集中時間", f'{monthly["average_focus_minutes"]:.1f} 分')
        st.bar_chart(
            {
                "完了回数": monthly["daily_completed"],
                "集中時間": monthly["daily_focus_minutes"],
            }
        )
        st.dataframe(
            {
                "日付": monthly["daily_labels"],
                "完了回数": monthly["daily_completed"],
                "集中時間": monthly["daily_focus_minutes"],
            },
            use_container_width=True,
        )


if __name__ == "__main__":
    run_app()
