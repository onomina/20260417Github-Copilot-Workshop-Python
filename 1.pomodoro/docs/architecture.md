# アーキテクチャ概要

このドキュメントは、PomodoroタイマーWebアプリの最新アーキテクチャを記載します。

## 構成
- Python (標準ライブラリ) のみで構築
- サーバ: `app.py` (HTTPServer + HTML生成)
- クライアント: 単一HTML + 組み込みJavaScript

## レイヤー
1. **サーバ**: 静的HTMLを返すのみ。APIやDBはなし。
2. **クライアント**: タイマーUI・ロジック・テーマ切替・音再生など全てJSで実装

## 依存関係
- 外部ライブラリ・DBなし
- すべてのロジックは`app.py`内に集約

## テスト
- `tests/test_pomodoro_app.py`で主要な定数・HTML生成・UI要素の存在を検証
