"""Postgres 记忆 Provider 单元测试。"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

import agent.postgres_memory as pm_module
from agent.postgres_memory import PostgresMemoryProvider


class _FakePgConfig:
    host = "127.0.0.1"
    port = 5432
    user = "postgres"
    password = "root"
    database = "dbvector"

    def load(self):
        return self


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows or []


class _Conn:
    def __init__(self, history_rows=None):
        self.queries = []
        self._history_rows = history_rows

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        return _Rows(self._history_rows)

    def commit(self):
        return None


def _mock_pg(monkeypatch, history_rows=None):
    conn = _Conn(history_rows)
    monkeypatch.setattr("psycopg.connect", lambda **kwargs: conn)
    monkeypatch.setattr(pm_module, "PostgresConfig", _FakePgConfig)
    return conn


def test_add_message_persists(monkeypatch):
    """add_message 执行 INSERT。"""
    conn = _mock_pg(monkeypatch)
    mem = PostgresMemoryProvider(session_id="s1")
    mem.add_message("user", "你好")
    assert any("INSERT INTO chat_memory" in q[0] for q in conn.queries)


def test_add_message_normalizes_role(monkeypatch):
    """human 角色归一化为 user。"""
    conn = _mock_pg(monkeypatch)
    mem = PostgresMemoryProvider(session_id="s1")
    mem.add_message("human", "你好")
    insert = [q for q in conn.queries if "INSERT INTO chat_memory" in q[0]][0]
    assert insert[1][1] == "user"


def test_add_message_skips_empty(monkeypatch):
    """空内容不写入。"""
    conn = _mock_pg(monkeypatch)
    mem = PostgresMemoryProvider(session_id="s1")
    mem.add_message("user", "")
    assert not any("INSERT INTO chat_memory" in q[0] for q in conn.queries)


def test_get_history_order(monkeypatch):
    """get_history 返回正序的 HumanMessage / AIMessage。"""
    _mock_pg(monkeypatch, history_rows=[("assistant", "回答"), ("user", "你好")])
    mem = PostgresMemoryProvider(session_id="s1", k=10)
    history = mem.get_history()
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert history[0].content == "你好"
    assert isinstance(history[1], AIMessage)
    assert history[1].content == "回答"


def test_clear(monkeypatch):
    """clear 执行 DELETE。"""
    conn = _mock_pg(monkeypatch)
    mem = PostgresMemoryProvider(session_id="s1")
    mem.clear()
    assert any("DELETE FROM chat_memory" in q[0] for q in conn.queries)


def test_save_and_load(monkeypatch):
    """save 为空操作，load 切换会话 ID。"""
    _mock_pg(monkeypatch)
    mem = PostgresMemoryProvider(session_id="s1")
    assert mem.save() is None
    mem.load("s2")
    assert mem.session_id == "s2"
