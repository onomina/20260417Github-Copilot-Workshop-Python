// 通知・アラート用
let notificationEnabled = true;
let audio = null;

function playSound() {
    if (!audio) {
        audio = new Audio('https://freesound.org/data/previews/337/337049_3232294-lq.mp3'); // フリーのベル音
    }
    audio.currentTime = 0;
    audio.play();
}

function showNotification(title, body) {
    if (!notificationEnabled) return;
    if (window.Notification && Notification.permission === 'granted') {
        new Notification(title, { body });
    }
}

// タイマー設定
const WORK_DURATION = 1 * 60; // 作業25分
const SHORT_BREAK = 5 * 60;    // 短い休憩5分
const LONG_BREAK = 15 * 60;    // 長い休憩15分
const LONG_BREAK_INTERVAL = 4; // 4回ごとに長い休憩

let timerInterval = null;
let timeLeft = WORK_DURATION;
let isRunning = false;
let sessionType = 'work'; // 'work', 'shortBreak', 'longBreak'
let pomodoroCount = 0;


function updateTimerDisplay() {
    const minutes = String(Math.floor(timeLeft / 60)).padStart(2, '0');
    const seconds = String(timeLeft % 60).padStart(2, '0');
    document.getElementById('timer').textContent = `${minutes}:${seconds}`;
    // セッション種別の表示
    let label = '';
    if (sessionType === 'work') label = '作業中';
    else if (sessionType === 'shortBreak') label = '5分休憩';
    else if (sessionType === 'longBreak') label = '15分休憩';
    document.getElementById('timer-label').textContent = label;
    // ポモドーロ回数の表示更新
    if (document.getElementById('pomodoro-count')) {
        document.getElementById('pomodoro-count').textContent = pomodoroCount;
    }
}


function startTimer() {
    if (isRunning) return;
    isRunning = true;
    timerInterval = setInterval(() => {
        if (timeLeft > 0) {
            timeLeft--;
            updateTimerDisplay();
        } else {
            clearInterval(timerInterval);
            isRunning = false;
            handleSessionEnd();
        }
    }, 1000);
}

function handleSessionEnd() {
    // 通知・アラート
    playSound();
    let notifyTitle = '';
    let notifyBody = '';
    if (sessionType === 'work') {
        notifyTitle = '作業セッション終了';
        notifyBody = 'お疲れさまです！休憩しましょう。';
    } else if (sessionType === 'shortBreak') {
        notifyTitle = '5分休憩終了';
        notifyBody = '次の作業を始めましょう。';
    } else {
        notifyTitle = '15分休憩終了';
        notifyBody = '次の作業を始めましょう。';
    }
    showNotification(notifyTitle, notifyBody);

    if (sessionType === 'work') {
        pomodoroCount++;
        // 4回ごとに長い休憩
        if (pomodoroCount % LONG_BREAK_INTERVAL === 0) {
            sessionType = 'longBreak';
            timeLeft = LONG_BREAK;
            updateTimerDisplay();
            // 長い休憩は自動開始しない
            return;
        } else {
            sessionType = 'shortBreak';
            timeLeft = SHORT_BREAK;
        }
    } else {
        sessionType = 'work';
        timeLeft = WORK_DURATION;
    }
    updateTimerDisplay();
    // 長い休憩以外は自動開始
    startTimer();
}


function resetTimer() {
    clearInterval(timerInterval);
    isRunning = false;
    // 現在のセッション種別に応じて初期化
    if (sessionType === 'work') {
        timeLeft = WORK_DURATION;
    } else if (sessionType === 'shortBreak') {
        timeLeft = SHORT_BREAK;
    } else {
        timeLeft = LONG_BREAK;
    }
    updateTimerDisplay();
}


document.addEventListener('DOMContentLoaded', () => {
    updateTimerDisplay();
    document.getElementById('start-btn').addEventListener('click', startTimer);
    document.getElementById('reset-btn').addEventListener('click', resetTimer);
    // 通知許可リクエスト
    if (window.Notification && Notification.permission !== 'granted') {
        Notification.requestPermission();
    }
});
