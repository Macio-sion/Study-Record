"""版本管理业务代码：版本存储（内存兜底 + PostgreSQL）+ 应用建议 + 版本对比

持久化策略（项目统一约定）：
- 后端核心持久化数据（简历版本）落 PostgreSQL
- 前端任务请求与结果反馈走 Redis 队列（属 API/任务层，本仓库当前未落地该层）
"""

import copy
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional

from config.setting import get_settings

settings = get_settings()

# 字段路径解析：experience[0].description -> ["experience", 0, "description"]
_PATH_RE = re.compile(r"([^\[\].]+)|\[(\d+)\]")


def _parse_path(path: str) -> list:
    parts = []
    for key, idx in _PATH_RE.findall(path):
        if key:
            parts.append(key)
        if idx:
            parts.append(int(idx))
    return parts


def _descend(node, part):
    if isinstance(node, list) and isinstance(part, int):
        return node[part] if 0 <= part < len(node) else None
    if isinstance(node, dict) and isinstance(part, str):
        return node.get(part)
    return None


def get_field_value(fields: dict, path: str):
    """按叶子字段路径取值（适配 {value, confidence} 结构）"""
    node = fields
    for part in _parse_path(path):
        node = _descend(node, part)
        if node is None:
            return None
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


def set_field_value(fields: dict, path: str, value) -> bool:
    """按叶子字段路径写入新值（适配 {value, confidence} 结构）"""
    parts = _parse_path(path)
    if not parts:
        return False
    node = fields
    for part in parts[:-1]:
        node = _descend(node, part)
        if node is None:
            return False
    last = parts[-1]
    if isinstance(node, list) and isinstance(last, int):
        if 0 <= last < len(node) and isinstance(node[last], dict):
            node[last]["value"] = value
            return True
    if isinstance(node, dict) and isinstance(last, str):
        target = node.get(last)
        if isinstance(target, dict) and "value" in target:
            target["value"] = value
            return True
        node[last] = value
        return True
    return False


def _walk_fields(node, prefix: str = ""):
    """递归遍历字段，yield (path, node)，node 含 value/confidence"""
    if isinstance(node, dict):
        if "value" in node and "confidence" in node:
            yield prefix, node
        else:
            for key, val in node.items():
                path = f"{prefix}.{key}" if prefix else key
                yield from _walk_fields(val, path)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _walk_fields(item, f"{prefix}[{i}]")


def diff_fields(before: dict, after: dict) -> List[dict]:
    """对比两个版本字段快照，返回 [{field, before, after, highlight}]"""
    diffs = []
    for path, node in _walk_fields(after):
        after_value = node.get("value")
        before_value = get_field_value(before, path)
        if after_value == before_value:
            continue
        if after_value is None and before_value is None:
            continue
        diffs.append({
            "field": path,
            "before": before_value if before_value is not None else "",
            "after": after_value if after_value is not None else "",
            "highlight": {"added": [], "removed": []},
        })
    return diffs


def _version_num(version: str) -> int:
    m = re.search(r"\d+", str(version))
    return int(m.group()) if m else 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class VersionStore(ABC):
    """简历版本存储接口（get/latest/save/list），可切换内存 / PostgreSQL 实现"""

    @abstractmethod
    def get(self, resume_id: str, version: str) -> Optional[dict]:
        """读取指定版本记录，不存在返回 None"""

    @abstractmethod
    def latest(self, resume_id: str) -> Optional[dict]:
        """读取最新版本记录，不存在返回 None"""

    @abstractmethod
    def save(self, resume_id: str, version: str, fields: dict, note: str = "") -> dict:
        """写入（或覆盖）一个版本快照，返回记录"""

    @abstractmethod
    def list(self, resume_id: str) -> List[dict]:
        """按版本顺序返回该简历的全部版本记录"""


class InMemoryVersionStore(VersionStore):
    """内存存储：进程内 dict，用于开发/测试兜底"""

    def __init__(self) -> None:
        self._store: dict = {}

    def get(self, resume_id: str, version: str) -> Optional[dict]:
        return self._store.get(resume_id, {}).get(version)

    def latest(self, resume_id: str) -> Optional[dict]:
        versions = self._store.get(resume_id, {})
        if not versions:
            return None
        return versions[max(versions, key=_version_num)]

    def save(self, resume_id: str, version: str, fields: dict, note: str = "") -> dict:
        record = {
            "version": version,
            "fields": copy.deepcopy(fields),
            "note": note,
            "created_at": _now(),
        }
        self._store.setdefault(resume_id, {})[version] = record
        return record

    def list(self, resume_id: str) -> List[dict]:
        versions = self._store.get(resume_id, {})
        return [versions[v] for v in sorted(versions, key=_version_num)]


class PostgresVersionStore(VersionStore):
    """PostgreSQL 存储：resume_versions 表（核心持久化数据）"""

    def __init__(self, dsn: str = None) -> None:
        self.conn = self._connect(dsn)
        self._ensure_table()

    def _connect(self, dsn: str):
        dsn = dsn or (
            f"host={settings.postgres_host} port={settings.postgres_port} "
            f"dbname={settings.postgres_db} user={settings.postgres_user} "
            f"password={settings.postgres_password}"
        )
        try:
            import psycopg2
            return psycopg2.connect(dsn)
        except ImportError:
            import psycopg
            return psycopg.connect(dsn)

    def _ensure_table(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS resume_versions (
                    resume_id  VARCHAR(64) NOT NULL,
                    version    VARCHAR(16) NOT NULL,
                    fields     TEXT NOT NULL,
                    note       TEXT DEFAULT '',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (resume_id, version)
                )
                """
            )
        self.conn.commit()

    def ping(self) -> bool:
        with self.conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True

    def get(self, resume_id: str, version: str) -> Optional[dict]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT version, fields, note, created_at FROM resume_versions "
                "WHERE resume_id=%s AND version=%s",
                (resume_id, version),
            )
            row = cur.fetchone()
        return _row_to_record(row) if row else None

    def latest(self, resume_id: str) -> Optional[dict]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT version, fields, note, created_at FROM resume_versions "
                "WHERE resume_id=%s ORDER BY created_at DESC, version DESC LIMIT 1",
                (resume_id,),
            )
            row = cur.fetchone()
        return _row_to_record(row) if row else None

    def save(self, resume_id: str, version: str, fields: dict, note: str = "") -> dict:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO resume_versions (resume_id, version, fields, note, created_at) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (resume_id, version) DO UPDATE SET "
                "fields=EXCLUDED.fields, note=EXCLUDED.note, created_at=EXCLUDED.created_at",
                (resume_id, version, json.dumps(fields, ensure_ascii=False), note, _now()),
            )
        self.conn.commit()
        return {"version": version, "fields": copy.deepcopy(fields), "note": note, "created_at": _now()}

    def list(self, resume_id: str) -> List[dict]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT version, fields, note, created_at FROM resume_versions "
                "WHERE resume_id=%s ORDER BY created_at ASC, version ASC",
                (resume_id,),
            )
            rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]


def _row_to_record(row) -> dict:
    version, fields, note, created_at = row
    return {
        "version": version,
        "fields": json.loads(fields) if isinstance(fields, str) else fields,
        "note": note,
        "created_at": str(created_at) if created_at else None,
    }


def create_version_store() -> VersionStore:
    """优先 PostgreSQL，连接失败回退内存存储"""
    try:
        store = PostgresVersionStore()
        store.ping()
        return store
    except Exception:
        return InMemoryVersionStore()


# 模块级默认存储（共享运行时）
version_store = create_version_store()


def next_version(current: str) -> str:
    """版本号递增：v1 -> v2"""
    return f"v{_version_num(current) + 1}"


def _ensure_initial(store: VersionStore, resume_id: str, fields: dict) -> dict:
    """确保存在起始版本 v1，返回最新版本记录"""
    record = store.latest(resume_id)
    if record:
        return record
    store.save(resume_id, "v1", fields, note="initial")
    return store.get(resume_id, "v1")


def apply_suggestions(
    store: VersionStore,
    resume_id: str,
    current_fields: dict,
    suggestions: List[dict],
    suggestion_ids: List[str] = None,
    accept_all: bool = False,
) -> dict:
    """一键应用：筛选建议 → 写入字段 → 生成新版本，返回 { version, resume_id, updated_fields, diffs }"""
    base = _ensure_initial(store, resume_id, current_fields)

    if accept_all:
        to_apply = suggestions
    else:
        ids = set(suggestion_ids or [])
        to_apply = [s for s in suggestions if s.get("id") in ids]

    if not to_apply:
        return {"version": base["version"], "resume_id": resume_id, "updated_fields": [], "diffs": []}

    new_fields = copy.deepcopy(base["fields"])
    updated = []
    for s in to_apply:
        location = s.get("location") or (s.get("target") or {}).get("field")
        if location and set_field_value(new_fields, location, s.get("after")):
            updated.append(location)

    version = next_version(base["version"])
    store.save(resume_id, version, new_fields, note="apply suggestions")
    return {
        "version": version,
        "resume_id": resume_id,
        "updated_fields": updated,
        "diffs": diff_fields(base["fields"], new_fields),
    }


def diff_versions(store: VersionStore, resume_id: str, version: str, base_version: str = None) -> List[dict]:
    """版本对比：缺省对比上一版本"""
    target = store.get(resume_id, version)
    if target is None:
        return []

    if base_version is None:
        num = _version_num(version)
        base_version = f"v{num - 1}" if num > 1 else None

    base = store.get(resume_id, base_version) if base_version else None
    before = base["fields"] if base else {}
    return diff_fields(before, target["fields"])


def load_resume_fields(store: VersionStore, resume_id: str, version: str = None) -> Optional[dict]:
    """读取指定（或最新）版本的简历字段，供下游复用"""
    record = store.get(resume_id, version) if version else store.latest(resume_id)
    return record["fields"] if record else None
