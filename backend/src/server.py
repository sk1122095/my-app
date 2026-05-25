import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


PORT = int(os.environ.get("PORT", "3000"))
DB_PATH = os.environ.get("SQLITE_PATH", "/data/portal.db")


def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with connect_db() as connection:
        connection.executescript(
            """
            create table if not exists announcements (
              id integer primary key autoincrement,
              title text not null,
              body text not null,
              category text not null,
              published_at text not null
            );

            create table if not exists employees (
              id integer primary key autoincrement,
              name text not null,
              department text not null,
              role text not null,
              email text not null unique
            );

            create table if not exists support_tickets (
              id integer primary key autoincrement,
              title text not null,
              owner text not null,
              status text not null,
              priority text not null
            );
            """
        )

        announcement_count = connection.execute("select count(*) from announcements").fetchone()[0]
        if announcement_count == 0:
            connection.executemany(
                """
                insert into announcements (title, body, category, published_at)
                values (?, ?, ?, ?)
                """,
                [
                    (
                        "四半期全社会のお知らせ",
                        "来週金曜日 15:00 からオンラインで全社会を開催します。各部門の取り組みと次期ロードマップを共有します。",
                        "全社",
                        "2026-05-10T09:00:00+09:00",
                    ),
                    (
                        "VPN メンテナンス",
                        "今週土曜日 22:00 から 30 分程度、VPN のメンテナンスを実施します。作業中は社外からの接続が不安定になる場合があります。",
                        "IT",
                        "2026-05-09T10:30:00+09:00",
                    ),
                    (
                        "新しい勤怠ルール",
                        "リモート勤務時の休憩登録ルールを更新しました。詳細は人事ポータルのガイドを確認してください。",
                        "人事",
                        "2026-05-08T13:00:00+09:00",
                    ),
                ],
            )

        employee_count = connection.execute("select count(*) from employees").fetchone()[0]
        if employee_count == 0:
            connection.executemany(
                """
                insert into employees (name, department, role, email)
                values (?, ?, ?, ?)
                """,
                [
                    ("佐藤 葵", "Corporate IT", "System Administrator", "aoi.sato@example.local"),
                    ("田中 蓮", "Sales", "Account Executive", "ren.tanaka@example.local"),
                    ("鈴木 美咲", "Human Resources", "HR Specialist", "misaki.suzuki@example.local"),
                    ("高橋 悠真", "Engineering", "Backend Engineer", "yuma.takahashi@example.local"),
                ],
            )

        ticket_count = connection.execute("select count(*) from support_tickets").fetchone()[0]
        if ticket_count == 0:
            connection.executemany(
                """
                insert into support_tickets (title, owner, status, priority)
                values (?, ?, ?, ?)
                """,
                [
                    ("共有フォルダにアクセスできない", "佐藤 葵", "対応中", "高"),
                    ("新入社員 PC セットアップ", "佐藤 葵", "未対応", "中"),
                    ("会議室ディスプレイ不調", "高橋 悠真", "完了", "低"),
                ],
            )


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


class ApiHandler(BaseHTTPRequestHandler):
    def send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_json(204, {})

    def do_GET(self):
        path = urlparse(self.path).path

        try:
            with connect_db() as connection:
                if path == "/api/health":
                    connection.execute("select 1")
                    self.send_json(200, {"status": "ok", "database": "sqlite connected"})
                elif path == "/api/announcements":
                    rows = connection.execute(
                        "select id, title, body, category, published_at from announcements order by published_at desc"
                    ).fetchall()
                    self.send_json(200, rows_to_dicts(rows))
                elif path == "/api/employees":
                    rows = connection.execute(
                        "select id, name, department, role, email from employees order by id"
                    ).fetchall()
                    self.send_json(200, rows_to_dicts(rows))
                elif path == "/api/tickets":
                    rows = connection.execute(
                        "select id, title, owner, status, priority from support_tickets order by id desc"
                    ).fetchall()
                    self.send_json(200, rows_to_dicts(rows))
                else:
                    self.send_json(404, {"message": "Not found"})
        except Exception as error:
            print(error)
            self.send_json(500, {"message": "Internal server error"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/api/tickets":
            self.send_json(404, {"message": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"message": "Invalid JSON body"})
            return

        title = payload.get("title", "")
        owner = payload.get("owner", "")
        priority = payload.get("priority", "")

        title = title.strip() if isinstance(title, str) else ""
        owner = owner.strip() if isinstance(owner, str) else ""
        priority = priority.strip() if isinstance(priority, str) else ""

        if not title or not owner or priority not in ["高", "中", "低"]:
            self.send_json(
                400,
                {"message": "title, owner, priority are required. priority must be 高, 中, or 低."},
            )
            return

        try:
            with connect_db() as connection:
                cursor = connection.execute(
                    """
                    insert into support_tickets (title, owner, status, priority)
                    values (?, ?, ?, ?)
                    """,
                    (title, owner, "未対応", priority),
                )
                row = connection.execute(
                    "select id, title, owner, status, priority from support_tickets where id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
                self.send_json(201, dict(row))
        except Exception as error:
            print(error)
            self.send_json(500, {"message": "Internal server error"})

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))


if __name__ == "__main__":
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), ApiHandler)
    print(f"Backend API listening on port {PORT} with SQLite database {DB_PATH}")
    server.serve_forever()
