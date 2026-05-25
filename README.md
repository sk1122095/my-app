# Mock Company Portal

インフラ学習用の、Docker Compose で動く模擬社内ポータルです。

SQLite 版では `frontend` と `backend` の 2 コンテナ構成です。frontend は Nginx で静的ファイルを配信し、`/api/*` を backend にリバースプロキシします。backend は Python 標準ライブラリで作った REST API で、SQLite の DB ファイルからデータを読み書きします。

## 起動手順

```bash
docker compose up --build
```

バックグラウンドで起動する場合:

```bash
docker compose up -d --build
```

停止する場合:

```bash
docker compose down
```

SQLite の保存データも削除して初期状態に戻す場合:

```bash
docker compose down -v
docker compose up --build
```

## ディレクトリ構成

```text
.
├── docker-compose.yml
├── README.md
├── backend
│   ├── Dockerfile
│   └── src
│       └── server.py
└── frontend
    ├── Dockerfile
    ├── nginx.conf
    └── src
        ├── app.js
        ├── index.html
        └── styles.css
```

## コンテナ構成

| サービス | 役割 | 公開ポート |
| --- | --- | --- |
| `frontend` | 社内ポータル画面、API へのリバースプロキシ | `8080` |
| `backend` | REST API と SQLite DB 操作 | `3000` |

SQLite の DB ファイルは backend コンテナ内の `/data/portal.db` に作成されます。この `/data` は Docker volume `my-app_sqlite_data` に保存されるため、`docker compose down` だけではデータは消えません。

## 動作確認方法

ブラウザで frontend を開きます。

```text
http://localhost:8080
```

API の疎通確認:

```bash
curl http://localhost:8080/api/health
```

期待されるレスポンス:

```json
{
  "status": "ok",
  "database": "sqlite connected"
}
```

backend に直接アクセスする場合:

```bash
curl http://localhost:3000/api/announcements
curl http://localhost:3000/api/employees
curl http://localhost:3000/api/tickets
```

チケットを追加する場合:

```bash
curl -X POST http://localhost:8080/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"title":"プリンターに接続できない","owner":"佐藤 葵","priority":"中"}'
```

画面からは `http://localhost:8080` の IT サポート欄にあるフォームで追加できます。追加したチケットは SQLite に保存され、一覧に反映されます。

## SQLite の確認方法

backend コンテナの中で SQLite の DB ファイルを確認できます。

```bash
docker compose exec backend python -c "import sqlite3; c=sqlite3.connect('/data/portal.db'); print(c.execute('select id, title, owner, status, priority from support_tickets order by id desc').fetchall())"
```

テーブル一覧を確認する場合:

```bash
docker compose exec backend python -c "import sqlite3; c=sqlite3.connect('/data/portal.db'); print(c.execute(\"select name from sqlite_master where type='table'\").fetchall())"
```

Git練習用の追記です
