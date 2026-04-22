# データモデル仕様

このアプリはサーバサイドで永続的なデータモデルを持ちません。

## 定数
- `POMODORO_OPTIONS`: [15, 25, 35, 45]
- `BREAK_OPTIONS`: [5, 10, 15]
- `THEMES`: `light`, `dark`, `focus` (各テーマの色・ラベル情報)

## クライアント状態
- `state`オブジェクト (JS):
    - `running`: タイマー稼働中か
    - `phase`: 'work' または 'break'
    - `remaining`: 残り秒数
    - `intervalId`: setIntervalのID

## 備考
- サーバ側でユーザデータや履歴は保持しません。
- すべての状態はクライアント側で管理されます。
