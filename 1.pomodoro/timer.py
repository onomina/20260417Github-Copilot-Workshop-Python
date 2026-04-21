# timer.py
# ポモドーロタイマーのロジックをクラスとして実装

class PomodoroTimer:
    def __init__(self, work_duration=25*60, short_break=5*60, long_break=15*60, long_break_interval=4):
        self.work_duration = work_duration
        self.short_break = short_break
        self.long_break = long_break
        self.long_break_interval = long_break_interval
        self.session_type = 'work'  # 'work', 'shortBreak', 'longBreak'
        self.pomodoro_count = 0
        self.time_left = self.work_duration

    def start_session(self):
        if self.session_type == 'work':
            self.time_left = self.work_duration
        elif self.session_type == 'shortBreak':
            self.time_left = self.short_break
        else:
            self.time_left = self.long_break

    def next_session(self):
        if self.session_type == 'work':
            self.pomodoro_count += 1
            if self.pomodoro_count % self.long_break_interval == 0:
                self.session_type = 'longBreak'
                self.time_left = self.long_break
            else:
                self.session_type = 'shortBreak'
                self.time_left = self.short_break
        else:
            self.session_type = 'work'
            self.time_left = self.work_duration

    def reset(self):
        self.pomodoro_count = 0
        self.session_type = 'work'
        self.time_left = self.work_duration

    def get_state(self):
        return {
            'session_type': self.session_type,
            'pomodoro_count': self.pomodoro_count,
            'time_left': self.time_left
        }
