from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

POMODORO_OPTIONS = [15, 25, 35, 45]
BREAK_OPTIONS = [5, 10, 15]
THEMES = {
    "light": {"label": "ライト", "bg": "#f6f7fb", "card": "#ffffff", "text": "#1e2330", "accent": "#4f46e5"},
    "dark": {"label": "ダーク", "bg": "#121826", "card": "#1f2937", "text": "#f9fafb", "accent": "#60a5fa"},
    "focus": {"label": "フォーカス", "bg": "#031b11", "card": "#0b2a1e", "text": "#dcfce7", "accent": "#34d399"},
}


def build_html() -> str:
    html = """<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Pomodoro Timer</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --card: #ffffff;
      --text: #1e2330;
      --accent: #4f46e5;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
      min-height: 100vh;
      display: grid;
      place-items: center;
      transition: background .2s ease, color .2s ease;
    }}
    main {{
      width: min(90vw, 560px);
      background: var(--card);
      border-radius: 16px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, .1);
      padding: 24px;
    }}
    h1 {{ margin: 0 0 16px; font-size: 1.6rem; }}
    .settings {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .sounds {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin: 12px 0 20px;
    }}
    .timer {{
      text-align: center;
      font-size: clamp(2rem, 8vw, 4rem);
      letter-spacing: .08em;
      margin: 8px 0;
    }}
    .phase {{ text-align: center; margin-bottom: 12px; font-weight: 600; }}
    .actions {{ display: flex; justify-content: center; gap: 12px; }}
    button {{
      border: none;
      background: var(--accent);
      color: white;
      padding: 10px 16px;
      border-radius: 10px;
      cursor: pointer;
      font-weight: 600;
    }}
    button.secondary {{ background: #6b7280; }}
    label {{ display: grid; gap: 6px; font-size: .92rem; }}
    select {{ padding: 8px; border-radius: 8px; border: 1px solid #d1d5db; }}
  </style>
</head>
<body>
  <main>
    <h1>Pomodoro Timer</h1>
    <section class=\"settings\">
      <label>
        ポモドーロ時間
        <select id=\"pomodoro\"></select>
      </label>
      <label>
        休憩時間
        <select id=\"break\"></select>
      </label>
      <label>
        テーマ
        <select id=\"theme\"></select>
      </label>
    </section>
    <section class=\"sounds\">
      <label><input type=\"checkbox\" id=\"start-sound\" checked> 開始音</label>
      <label><input type=\"checkbox\" id=\"end-sound\" checked> 終了音</label>
      <label><input type=\"checkbox\" id=\"tick-sound\"> tick音</label>
    </section>
    <div class=\"phase\" id=\"phase\">作業時間</div>
    <div class=\"timer\" id=\"timer\">25:00</div>
    <div class=\"actions\">
      <button id=\"start\">開始</button>
      <button id=\"pause\" class=\"secondary\">一時停止</button>
      <button id=\"reset\" class=\"secondary\">リセット</button>
    </div>
  </main>
  <script>
    const pomodoroOptions = __POMODORO_OPTIONS__;
    const breakOptions = __BREAK_OPTIONS__;
    const themes = __THEMES__;

    const el = {
      pomodoro: document.getElementById('pomodoro'),
      break: document.getElementById('break'),
      theme: document.getElementById('theme'),
      startSound: document.getElementById('start-sound'),
      endSound: document.getElementById('end-sound'),
      tickSound: document.getElementById('tick-sound'),
      phase: document.getElementById('phase'),
      timer: document.getElementById('timer'),
      start: document.getElementById('start'),
      pause: document.getElementById('pause'),
      reset: document.getElementById('reset'),
    };

    const state = {
      running: false,
      phase: 'work',
      remaining: 25 * 60,
      intervalId: null,
    };

    function fillOptions(select, options) {
      options.forEach((value) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = `${value}分`;
        select.appendChild(option);
      });
    }

    function fillThemeOptions() {
      Object.entries(themes).forEach(([key, theme]) => {
        const option = document.createElement('option');
        option.value = key;
        option.textContent = theme.label;
        el.theme.appendChild(option);
      });
    }

    function applyTheme() {
      const theme = themes[el.theme.value] || themes['light'];
      document.documentElement.style.setProperty('--bg', theme.bg);
      document.documentElement.style.setProperty('--card', theme.card);
      document.documentElement.style.setProperty('--text', theme.text);
      document.documentElement.style.setProperty('--accent', theme.accent);
    }

    function formatTime(totalSeconds) {
      const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
      const seconds = String(totalSeconds % 60).padStart(2, '0');
      return `${minutes}:${seconds}`;
    }

    function currentWorkSeconds() {
      return Number(el.pomodoro.value) * 60;
    }

    function currentBreakSeconds() {
      return Number(el.break.value) * 60;
    }

    function playTone(enabled, frequency, duration = 0.08) {
      if (!enabled) return;
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      oscillator.frequency.value = frequency;
      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      oscillator.start();
      gainNode.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);
      oscillator.stop(audioCtx.currentTime + duration);
      oscillator.onended = () => audioCtx.close();
    }

    function updateTimer() {
      el.timer.textContent = formatTime(state.remaining);
    }

    function setPhase(phase) {
      state.phase = phase;
      el.phase.textContent = phase === 'work' ? '作業時間' : '休憩時間';
      state.remaining = phase === 'work' ? currentWorkSeconds() : currentBreakSeconds();
      updateTimer();
    }

    function tick() {
      if (!state.running) return;
      state.remaining -= 1;
      if (state.remaining > 0) {
        playTone(el.tickSound.checked, 1046, 0.03);
        updateTimer();
        return;
      }

      playTone(el.endSound.checked, 523, 0.12);
      if (state.phase === 'work') {
        setPhase('break');
      } else {
        setPhase('work');
      }
      playTone(el.startSound.checked, 784, 0.12);
    }

    function startTimer() {
      if (state.running) return;
      state.running = true;
      playTone(el.startSound.checked, 880, 0.12);
      state.intervalId = window.setInterval(tick, 1000);
    }

    function pauseTimer() {
      if (!state.running) return;
      state.running = false;
      window.clearInterval(state.intervalId);
      state.intervalId = null;
    }

    function resetTimer() {
      pauseTimer();
      setPhase('work');
    }

    fillOptions(el.pomodoro, pomodoroOptions);
    fillOptions(el.break, breakOptions);
    fillThemeOptions();

    el.pomodoro.value = '25';
    el.break.value = '5';
    el.theme.value = 'light';
    applyTheme();
    resetTimer();

    el.theme.addEventListener('change', applyTheme);
    el.start.addEventListener('click', startTimer);
    el.pause.addEventListener('click', pauseTimer);
    el.reset.addEventListener('click', resetTimer);
    el.pomodoro.addEventListener('change', () => {
      if (!state.running && state.phase === 'work') {
        state.remaining = currentWorkSeconds();
        updateTimer();
      }
    });
    el.break.addEventListener('change', () => {
      if (!state.running && state.phase === 'break') {
        state.remaining = currentBreakSeconds();
        updateTimer();
      }
    });
  </script>
</body>
</html>
"""
    return (
        html.replace("__POMODORO_OPTIONS__", json.dumps(POMODORO_OPTIONS))
        .replace("__BREAK_OPTIONS__", json.dumps(BREAK_OPTIONS))
        .replace("__THEMES__", json.dumps(THEMES, ensure_ascii=False))
    )


class PomodoroHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            body = build_html().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/healthz":
            body = b"ok"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pomodoro timer web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with ThreadingHTTPServer((args.host, args.port), PomodoroHandler) as server:
        print(f"Pomodoro app running: http://{args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
