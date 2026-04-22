import math
import random
import time
try:
    import tkinter as tk
except ModuleNotFoundError:
    tk = None


FOCUS_SECONDS = 25 * 60
UPDATE_INTERVAL_MS = 50
MAX_PARTICLES = 48
PARTICLE_MAX_RADIUS = 180.0
RIPPLE_BASE_SHADE = 180
RIPPLE_SHADE_OFFSET = 40
RIPPLE_MIN_SHADE = 70
RIPPLE_INITIAL_RADIUS = 38.0
RIPPLE_SPEED = 1.2
RIPPLE_MAX_RADIUS = 162.0
RIPPLE_RADIUS_STEP_MULTIPLIER = 2.0
RIPPLE_SPAWN_INTERVAL_SECONDS = 0.6
PARTICLE_RADIUS_MIN = 104.0
PARTICLE_RADIUS_MAX = 118.0
PARTICLE_SPEED_MIN = 0.8
PARTICLE_SPEED_MAX = 1.8
PARTICLE_SIZE_MIN = 2.0
PARTICLE_SIZE_MAX = 4.5
PARTICLE_DRIFT_MIN = -0.03
PARTICLE_DRIFT_MAX = 0.03
TKINTER_UNAVAILABLE_MESSAGE = "tkinter が利用できない環境です。GUI を実行できません。"

RGBColor = tuple[int, int, int]
BLUE: RGBColor = (66, 135, 245)
YELLOW: RGBColor = (245, 205, 66)
RED: RGBColor = (245, 66, 66)
POMODORO_OPTIONS = [15, 25, 35, 45]
BREAK_OPTIONS = [5, 10, 15]
THEMES = {
    "light": {"label": "ライト", "bg": "#f6f7fb", "card": "#ffffff", "text": "#1e2330", "accent": "#4f46e5"},
    "dark": {"label": "ダーク", "bg": "#121826", "card": "#1f2937", "text": "#f9fafb", "accent": "#60a5fa"},
    "focus": {"label": "フォーカス", "bg": "#031b11", "card": "#0b2a1e", "text": "#dcfce7", "accent": "#34d399"},
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def lerp_color(start: RGBColor, end: RGBColor, t: float) -> RGBColor:
    ratio = clamp(t, 0.0, 1.0)
    return (
        int(start[0] + (end[0] - start[0]) * ratio),
        int(start[1] + (end[1] - start[1]) * ratio),
        int(start[2] + (end[2] - start[2]) * ratio),
    )


def progress_to_color(elapsed_ratio: float) -> str:
    ratio = clamp(elapsed_ratio, 0.0, 1.0)
    if ratio < 0.5:
        rgb = lerp_color(BLUE, YELLOW, ratio * 2)
    else:
        rgb = lerp_color(YELLOW, RED, (ratio - 0.5) * 2)
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def build_html() -> str:
    """互換テスト向けに必要なコントロールIDを含む最小HTMLを返す。"""
    pomodoro_options = "".join(f'<option value="{minutes}">{minutes}分</option>' for minutes in POMODORO_OPTIONS)
    break_options = "".join(f'<option value="{minutes}">{minutes}分</option>' for minutes in BREAK_OPTIONS)
    theme_options = "".join(
        f'<option value="{theme_key}">{theme_value["label"]}</option>' for theme_key, theme_value in THEMES.items()
    )
    return f"""
<!doctype html>
<html lang="ja">
<head><meta charset="utf-8"><title>Pomodoro Timer</title></head>
<body>
  <select id="pomodoro">{pomodoro_options}</select>
  <select id="break">{break_options}</select>
  <select id="theme">{theme_options}</select>
  <input id="start-sound" type="checkbox" checked>
  <input id="end-sound" type="checkbox" checked>
  <input id="tick-sound" type="checkbox">
</body>
</html>
""".strip()


class PomodoroApp:
    def __init__(self) -> None:
        if tk is None:
            raise RuntimeError(TKINTER_UNAVAILABLE_MESSAGE)
        self.root = tk.Tk()
        self.root.title("ポモドーロタイマー")
        self.root.configure(bg="#f4f4fb")
        self.root.resizable(False, False)

        self.running = False
        self.total_seconds = FOCUS_SECONDS
        self.remaining_seconds = float(self.total_seconds)
        self.started_at = 0.0
        self.last_tick_remaining = float(self.total_seconds)
        self.ripples: list[dict[str, float]] = []
        self.particles: list[dict[str, float]] = []
        self.last_ripple_at = 0.0
        self.center_x = 170
        self.center_y = 170
        self.ring_radius = 96
        self.ring_width = 20

        self.status_label = tk.Label(
            self.root,
            text="作業中",
            font=("Yu Gothic UI", 16, "bold"),
            fg="#555",
            bg="#f4f4fb",
        )
        self.status_label.pack(pady=(16, 8))

        self.canvas = tk.Canvas(self.root, width=340, height=340, bg="#f4f4fb", highlightthickness=0)
        self.canvas.pack()

        self.background_oval = self.canvas.create_oval(
            self.center_x - self.ring_radius - 10,
            self.center_y - self.ring_radius - 10,
            self.center_x + self.ring_radius + 10,
            self.center_y + self.ring_radius + 10,
            fill="#eef0fb",
            outline="",
        )
        self.base_ring = self.canvas.create_oval(
            self.center_x - self.ring_radius,
            self.center_y - self.ring_radius,
            self.center_x + self.ring_radius,
            self.center_y + self.ring_radius,
            outline="#dcdfea",
            width=self.ring_width,
        )
        self.progress_ring = self.canvas.create_arc(
            self.center_x - self.ring_radius,
            self.center_y - self.ring_radius,
            self.center_x + self.ring_radius,
            self.center_y + self.ring_radius,
            start=90,
            extent=-360,
            style=tk.ARC,
            outline=progress_to_color(0.0),
            width=self.ring_width,
        )
        self.time_text = self.canvas.create_text(
            170, 170, text="25:00", fill="#2f2f38", font=("Yu Gothic UI", 36, "bold")
        )

        controls = tk.Frame(self.root, bg="#f4f4fb")
        controls.pack(pady=(8, 18))

        self.start_button = tk.Button(
            controls,
            text="開始",
            command=self.start,
            font=("Yu Gothic UI", 14, "bold"),
            width=10,
            bg="#5865f2",
            fg="white",
            bd=0,
            activebackground="#4f5ad9",
            activeforeground="white",
        )
        self.start_button.grid(row=0, column=0, padx=8)

        self.reset_button = tk.Button(
            controls,
            text="リセット",
            command=self.reset,
            font=("Yu Gothic UI", 14, "bold"),
            width=10,
            bg="#f4f4fb",
            fg="#5865f2",
            bd=2,
            activebackground="#e9e9f5",
            activeforeground="#5865f2",
        )
        self.reset_button.grid(row=0, column=1, padx=8)

        self.draw()

    def format_time(self, seconds: float) -> str:
        safe_seconds = max(0, int(math.ceil(seconds)))
        minute, second = divmod(safe_seconds, 60)
        return f"{minute:02d}:{second:02d}"

    def start(self) -> None:
        if self.running:
            return
        if self.remaining_seconds <= 0:
            self.remaining_seconds = float(self.total_seconds)
            self.ripples.clear()
            self.particles.clear()
            self.draw()
        self.running = True
        self.start_button.configure(text="進行中")
        self.started_at = time.perf_counter()
        self.last_tick_remaining = self.remaining_seconds
        self.last_ripple_at = self.started_at
        self.root.after(UPDATE_INTERVAL_MS, self.tick)

    def reset(self) -> None:
        self.running = False
        self.remaining_seconds = float(self.total_seconds)
        self.ripples.clear()
        self.particles.clear()
        self.start_button.configure(text="開始")
        self.draw()

    def tick(self) -> None:
        if not self.running:
            return

        now = time.perf_counter()
        elapsed = now - self.started_at
        self.remaining_seconds = max(0.0, self.last_tick_remaining - elapsed)

        if now - self.last_ripple_at >= RIPPLE_SPAWN_INTERVAL_SECONDS:
            self.ripples.append(
                {"radius": RIPPLE_INITIAL_RADIUS, "speed": RIPPLE_SPEED, "max_radius": RIPPLE_MAX_RADIUS}
            )
            self.last_ripple_at = now

        self.particles.append(
            {
                "angle": random.uniform(0, 2 * math.pi),
                "radius": random.uniform(PARTICLE_RADIUS_MIN, PARTICLE_RADIUS_MAX),
                "speed": random.uniform(PARTICLE_SPEED_MIN, PARTICLE_SPEED_MAX),
                "size": random.uniform(PARTICLE_SIZE_MIN, PARTICLE_SIZE_MAX),
                "drift": random.uniform(PARTICLE_DRIFT_MIN, PARTICLE_DRIFT_MAX),
            }
        )
        if len(self.particles) > MAX_PARTICLES:
            self.particles = self.particles[-MAX_PARTICLES:]

        if self.remaining_seconds <= 0:
            self.running = False
            self.start_button.configure(text="開始")

        self.draw()
        if self.running:
            self.root.after(UPDATE_INTERVAL_MS, self.tick)

    def draw(self) -> None:
        self.canvas.delete("effect_dynamic")

        total_seconds = max(1.0, float(self.total_seconds))
        elapsed_ratio = 1 - (self.remaining_seconds / total_seconds)
        progress_extent = 360 * (self.remaining_seconds / total_seconds)

        if self.running:
            for ripple in self.ripples:
                ripple["radius"] += ripple["speed"] * RIPPLE_RADIUS_STEP_MULTIPLIER
                r = ripple["radius"]
                if r < ripple["max_radius"]:
                    shade = int(
                        clamp(
                            RIPPLE_BASE_SHADE - (r - RIPPLE_SHADE_OFFSET),
                            RIPPLE_MIN_SHADE,
                            RIPPLE_BASE_SHADE,
                        )
                    )
                    ripple_color = f"#{shade:02x}{shade:02x}ff"
                    self.canvas.create_oval(
                        self.center_x - r,
                        self.center_y - r,
                        self.center_x + r,
                        self.center_y + r,
                        outline=ripple_color,
                        width=2,
                        tags="effect_dynamic",
                    )
            self.ripples = [r for r in self.ripples if r["radius"] < r["max_radius"]]

            current_color = progress_to_color(elapsed_ratio)
            for p in self.particles:
                p["radius"] += p["speed"]
                p["angle"] += p["drift"]
                px = self.center_x + math.cos(p["angle"]) * p["radius"]
                py = self.center_y + math.sin(p["angle"]) * p["radius"]
                self.canvas.create_oval(
                    px - p["size"],
                    py - p["size"],
                    px + p["size"],
                    py + p["size"],
                    fill=current_color,
                    outline="",
                    tags="effect_dynamic",
                )
            self.particles = [p for p in self.particles if p["radius"] < PARTICLE_MAX_RADIUS]

        self.canvas.itemconfigure(
            self.progress_ring,
            extent=-progress_extent,
            outline=progress_to_color(elapsed_ratio),
        )

        self.canvas.itemconfigure(self.time_text, text=self.format_time(self.remaining_seconds))

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    if tk is None:
        raise SystemExit(TKINTER_UNAVAILABLE_MESSAGE)
    PomodoroApp().run()
