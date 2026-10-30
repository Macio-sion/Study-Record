"""数据仓库：users / resumes / job_records / feedback / task_logs 的增删改查。

所有函数均为同步实现（psycopg2）。在 async 任务 handler 中调用时，请用
``await asyncio.to_thread(...)`` 避免阻塞事件循环；FastAPI 同步路由则直接调用。
"""

from __future__ import annotations

import json
from typing import Any

import psycopg2.extras

from db.connection import get_conn

Json = psycopg2.extras.Json


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

def create_user(user_id: str, account: str, password_hash: str, nickname: str = "") -> dict:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (id, account, password_hash, nickname) "
                "VALUES (%s, %s, %s, %s)",
                (user_id, account, password_hash, nickname),
            )
    return get_user(user_id)


def get_user(user_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()


def get_user_by_account(account: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE account = %s", (account,))
            return cur.fetchone()


def update_user(user_id: str, **fields) -> dict | None:
    if not fields:
        return get_user(user_id)
    allowed = {"nickname", "avatar", "phone", "email", "job_intention"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_user(user_id)
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [user_id]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE users SET {set_clause}, updated_at = NOW() WHERE id = %s",
                values,
            )
    return get_user(user_id)


def update_password(user_id: str, password_hash: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
                (password_hash, user_id),
            )


def _public_user(row: dict | None) -> dict | None:
    if not row:
        return None
    return {
        "id": row["id"],
        "account": row["account"],
        "nickname": row["nickname"],
        "avatar": row["avatar"],
        "phone": row["phone"],
        "email": row["email"],
        "job_intention": row["job_intention"],
        "created_at": str(row["created_at"]) if row.get("created_at") else None,
    }


# ---------------------------------------------------------------------------
# resumes
# ---------------------------------------------------------------------------

def create_resume(
    resume_id: str,
    user_id: str,
    fields: dict,
    pending: list,
    name: str = "",
    source_type: str = "",
    ocr_used: bool = False,
    file_hash: str = "",
) -> dict:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO resumes (id, user_id, name, source_type, ocr_used, file_hash, "
                "fields, pending) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    resume_id,
                    user_id,
                    name,
                    source_type,
                    ocr_used,
                    file_hash,
                    Json(fields),
                    Json(pending),
                ),
            )
    return get_resume(resume_id)


def get_resume(resume_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM resumes WHERE id = %s", (resume_id,))
            return cur.fetchone()


def get_resume_for_user(resume_id: str, user_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM resumes WHERE id = %s AND user_id = %s",
                (resume_id, user_id),
            )
            return cur.fetchone()


def list_resumes(user_id: str, page: int = 1, page_size: int = 10) -> dict:
    offset = (page - 1) * page_size
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT COUNT(*) AS total FROM resumes WHERE user_id = %s", (user_id,)
            )
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT id, user_id, name, source_type, ocr_used, created_at, updated_at "
                "FROM resumes WHERE user_id = %s ORDER BY updated_at DESC LIMIT %s OFFSET %s",
                (user_id, page_size, offset),
            )
            rows = cur.fetchall()
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [{**r, "created_at": str(r["created_at"]), "updated_at": str(r["updated_at"])} for r in rows],
    }


def update_resume_fields(resume_id: str, fields: dict, pending: list | None = None) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if pending is not None:
                cur.execute(
                    "UPDATE resumes SET fields = %s, pending = %s, updated_at = NOW() WHERE id = %s",
                    (Json(fields), Json(pending), resume_id),
                )
            else:
                cur.execute(
                    "UPDATE resumes SET fields = %s, updated_at = NOW() WHERE id = %s",
                    (Json(fields), resume_id),
                )
    return get_resume(resume_id)


def delete_resume(resume_id: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM resumes WHERE id = %s", (resume_id,))
            cur.execute("DELETE FROM resume_versions WHERE resume_id = %s", (resume_id,))


def _resume_to_dict(row: dict | None) -> dict | None:
    if not row:
        return None
    return {
        "resume_id": row["id"],
        "name": row["name"],
        "source": {
            "type": row["source_type"],
            "ocr_used": row["ocr_used"],
            "file_type": row["source_type"],
        },
        "fields": row["fields"] or {},
        "pending": row["pending"] or [],
        "file_valid": True,
        "created_at": str(row["created_at"]) if row.get("created_at") else None,
    }


# ---------------------------------------------------------------------------
# job_records
# ---------------------------------------------------------------------------

JOB_STATUSES = ("待投递", "已投递", "面试中", "已录用", "已拒绝")


def create_job(user_id: str, company: str, position: str, status: str = "待投递",
               date: str | None = None, note: str = "") -> dict:
    import uuid

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO job_records (id, user_id, company, position, status, date, note) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (job_id, user_id, company, position, status, date, note),
            )
    return get_job(job_id)


def get_job(job_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM job_records WHERE id = %s", (job_id,))
            return cur.fetchone()


def list_jobs(user_id: str, status: str | None = None, page: int = 1, page_size: int = 10) -> dict:
    offset = (page - 1) * page_size
    where = "user_id = %s"
    params: list[Any] = [user_id]
    if status:
        where += " AND status = %s"
        params.append(status)
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM job_records WHERE {where}", params)
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM job_records WHERE {where} ORDER BY created_at DESC "
                f"LIMIT %s OFFSET %s",
                params + [page_size, offset],
            )
            rows = cur.fetchall()
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [_serialize_job(r) for r in rows],
    }


def update_job(job_id: str, **fields) -> dict | None:
    allowed = {"company", "position", "status", "date", "note"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if updates:
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [job_id]
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE job_records SET {set_clause}, updated_at = NOW() WHERE id = %s",
                    values,
                )
    return get_job(job_id)


def delete_job(job_id: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM job_records WHERE id = %s", (job_id,))


def job_board(user_id: str) -> dict:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT status, COUNT(*) AS cnt FROM job_records WHERE user_id = %s "
                "GROUP BY status",
                (user_id,),
            )
            rows = cur.fetchall()
    board = {s: 0 for s in JOB_STATUSES}
    for r in rows:
        if r["status"] in board:
            board[r["status"]] = r["cnt"]
    return board


def _serialize_job(r: dict) -> dict:
    return {
        "id": r["id"],
        "company": r["company"],
        "position": r["position"],
        "status": r["status"],
        "date": str(r["date"]) if r.get("date") else None,
        "note": r["note"],
        "created_at": str(r["created_at"]) if r.get("created_at") else None,
        "updated_at": str(r["updated_at"]) if r.get("updated_at") else None,
    }


# ---------------------------------------------------------------------------
# feedback
# ---------------------------------------------------------------------------

def create_feedback(user_id: str, content: str, screenshot: str = "") -> dict:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedback (user_id, content, screenshot) VALUES (%s, %s, %s) RETURNING id",
                (user_id, content, screenshot),
            )
            feedback_id = cur.fetchone()[0]
    return {"id": feedback_id, "user_id": user_id, "content": content, "screenshot": screenshot}


# ---------------------------------------------------------------------------
# task_logs（使用统计）
# ---------------------------------------------------------------------------

def log_task(task_id: str, user_id: str, task_type: str, resume_id: str | None = None,
             status: str = "queued") -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO task_logs (task_id, user_id, task_type, resume_id, status) "
                "VALUES (%s, %s, %s, %s, %s)",
                (task_id, user_id, task_type, resume_id, status),
            )


def update_task_status(task_id: str, status: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE task_logs SET status = %s WHERE task_id = %s", (status, task_id))


def usage_stats(user_id: str) -> dict:
    """统计解析/优化/问答次数。"""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT task_type, COUNT(*) AS cnt FROM task_logs WHERE user_id = %s "
                "GROUP BY task_type",
                (user_id,),
            )
            rows = cur.fetchall()
    stats = {"parse_count": 0, "edit_count": 0, "qa_count": 0}
    for r in rows:
        t = r["task_type"]
        if t == "parse":
            stats["parse_count"] = r["cnt"]
        elif t.startswith("edit"):
            stats["edit_count"] += r["cnt"]
        elif t in ("coaching", "mock_interview"):
            stats["qa_count"] += r["cnt"]
    return stats
