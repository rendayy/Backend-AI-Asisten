import time
from datetime import datetime
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../models/users.db")

def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn

class TaskService:

    def create_task(self, task, user_id: int):
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO tasks
                (user_id, title, description, due_date, created_at, is_completed, is_notified)
                VALUES (?, ?, ?, ?, ?, 0, 0)
                """,
                (
                    user_id,
                    task.title,
                    task.description,
                    int(task.due_date.timestamp()),
                    int(time.time())
                )
            )
            conn.commit()
            return {
                "message": "Task created",
                "task_id": cur.lastrowid
            }
        finally:
            conn.close()

    def check_overdue_tasks(self):
        now = int(time.time())
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM tasks
                WHERE is_completed = 0
                  AND is_notified = 0
                  AND due_date <= ?
                """,
                (now,)
            )
            rows = cur.fetchall()

            # 🔥 tandai sudah dikirim
            for r in rows:
                cur.execute(
                    "UPDATE tasks SET is_notified = 1 WHERE id = ?",
                    (r["id"],)
                )

            conn.commit()
            return rows
        finally:
            conn.close()
    