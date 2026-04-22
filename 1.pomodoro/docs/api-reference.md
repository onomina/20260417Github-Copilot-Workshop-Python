# APIリファレンス

このドキュメントは、PomodoroタイマーWebアプリのAPI仕様を記載します。

## エンドポイント一覧

### 1. ルート (GET /, /index.html)
- HTMLのPomodoroタイマーアプリ本体を返します。
- ステータス: 200 OK
- Content-Type: text/html; charset=utf-8

### 2. ヘルスチェック (GET /healthz)
- サービスの稼働確認用。
- レスポンス: `ok`
- ステータス: 200 OK
- Content-Type: text/plain; charset=utf-8

### 3. その他
- 上記以外のパスは404 Not Foundを返します。

---

## 備考
- REST APIとしてのデータ送受信はありません。
- すべてのUI・ロジックはHTML/JSでクライアントサイドに実装されています。
