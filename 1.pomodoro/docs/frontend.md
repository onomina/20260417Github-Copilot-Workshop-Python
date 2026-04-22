# フロントエンド構成

このドキュメントは、PomodoroタイマーWebアプリのフロントエンド実装について記載します。

## 主なUI要素
- ポモドーロ時間選択 (`id="pomodoro"`)
- 休憩時間選択 (`id="break"`)
- テーマ選択 (`id="theme"`)
- サウンド設定 (`id="start-sound"`, `id="end-sound"`, `id="tick-sound"`)
- タイマー表示 (`id="timer"`)
- フェーズ表示 (`id="phase"`)
- 操作ボタン (`id="start"`, `id="pause"`, `id="reset"`)

## JavaScriptロジック
- タイマーの開始・一時停止・リセット
- フェーズ切替（作業/休憩）
- 残り時間の計算・表示
- テーマ切替（light/dark/focus）
- サウンド再生（開始音・終了音・tick音）
- 各種設定の反映

## 備考
- すべてのJSはHTML内にインラインで記述
- 外部JS/CSSファイルは存在しません
