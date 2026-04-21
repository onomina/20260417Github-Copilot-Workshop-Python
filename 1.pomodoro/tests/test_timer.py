import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from timer import PomodoroTimer

class TestPomodoroTimer(unittest.TestCase):
    def setUp(self):
        self.timer = PomodoroTimer(work_duration=10, short_break=5, long_break=15, long_break_interval=4)

    def test_initial_state(self):
        state = self.timer.get_state()
        self.assertEqual(state['session_type'], 'work')
        self.assertEqual(state['pomodoro_count'], 0)
        self.assertEqual(state['time_left'], 10)

    def test_next_session_short_break(self):
        self.timer.next_session()
        state = self.timer.get_state()
        self.assertEqual(state['session_type'], 'shortBreak')
        self.assertEqual(state['pomodoro_count'], 1)
        self.assertEqual(state['time_left'], 5)

    def test_next_session_long_break(self):
        for _ in range(3):
            self.timer.next_session()  # 1,2,3回目 shortBreak
            self.timer.next_session()  # work
        self.timer.next_session()  # 4回目 work→longBreak
        state = self.timer.get_state()
        self.assertEqual(state['session_type'], 'longBreak')
        self.assertEqual(state['pomodoro_count'], 4)
        self.assertEqual(state['time_left'], 15)

    def test_reset(self):
        self.timer.next_session()
        self.timer.reset()
        state = self.timer.get_state()
        self.assertEqual(state['session_type'], 'work')
        self.assertEqual(state['pomodoro_count'], 0)
        self.assertEqual(state['time_left'], 10)

if __name__ == '__main__':
    unittest.main()
