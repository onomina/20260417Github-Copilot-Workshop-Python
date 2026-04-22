import math
import random
import time
from typing import cast
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


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def lerp_color(start: RGBColor, end: RGBColor, t: float) -> RGBColor:
    ratio = clamp(t, 0.0, 1.0)
    return cast(RGBColor, tuple(int(s + (e - s) * ratio) for s, e in zip(start, end)))


def progress_to_color(elapsed_ratio: float) -> str:
    ratio = clamp(elapsed_ratio, 0.0, 1.0)
    if ratio < 0.5:
        rgb = lerp_color(BLUE, YELLOW, ratio * 2)
    else:
        rgb = lerp_color(YELLOW, RED, (ratio - 0.5) * 2)
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


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
        self.canvas.delete("ring")
        self.canvas.delete("effect")

        center_x, center_y = 170, 170
        ring_radius = 96
        ring_width = 20
        total_seconds = max(1.0, float(self.total_seconds))
        elapsed_ratio = 1 - (self.remaining_seconds / total_seconds)
        progress_extent = 360 * (self.remaining_seconds / total_seconds)

        self.canvas.create_oval(
            center_x - ring_radius - 10,
            center_y - ring_radius - 10,
            center_x + ring_radius + 10,
            center_y + ring_radius + 10,
            fill="#eef0fb",
            outline="",
            tags="effect",
        )

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
                        center_x - r,
                        center_y - r,
                        center_x + r,
                        center_y + r,
                        outline=ripple_color,
                        width=2,
                        tags="effect",
                    )
            self.ripples = [r for r in self.ripples if r["radius"] < r["max_radius"]]

            current_color = progress_to_color(elapsed_ratio)
            for p in self.particles:
                p["radius"] += p["speed"]
                p["angle"] += p["drift"]
                px = center_x + math.cos(p["angle"]) * p["radius"]
                py = center_y + math.sin(p["angle"]) * p["radius"]
                self.canvas.create_oval(
                    px - p["size"],
                    py - p["size"],
                    px + p["size"],
                    py + p["size"],
                    fill=current_color,
                    outline="",
                    tags="effect",
                )
            self.particles = [p for p in self.particles if p["radius"] < PARTICLE_MAX_RADIUS]

        self.canvas.create_oval(
            center_x - ring_radius,
            center_y - ring_radius,
            center_x + ring_radius,
            center_y + ring_radius,
            outline="#dcdfea",
            width=ring_width,
            tags="ring",
        )

        self.canvas.create_arc(
            center_x - ring_radius,
            center_y - ring_radius,
            center_x + ring_radius,
            center_y + ring_radius,
            start=90,
            extent=-progress_extent,
            style=tk.ARC,
            outline=progress_to_color(elapsed_ratio),
            width=ring_width,
            tags="ring",
        )

        self.canvas.itemconfigure(self.time_text, text=self.format_time(self.remaining_seconds))

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    if tk is None:
        raise SystemExit(TKINTER_UNAVAILABLE_MESSAGE)
    PomodoroApp().run()
