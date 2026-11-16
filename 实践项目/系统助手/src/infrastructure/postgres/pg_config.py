"""PostgreSQL 连接配置管理。

从 ``data/postgres/postgres_config.json`` 读取数据库连接信息，提供统一的
SQLAlchemy 连接 URI（psycopg 方言）以及 ``vector`` 扩展初始化能力，供
PGVector 向量库与记忆持久化模块复用。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from loguru import logger

# 项目根目录：postgres -> infrastructure -> src -> 项目根
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "data" / "postgres" / "postgres_config.json"


class PostgresConfig:
    """PostgreSQL 连接配置。"""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
        self._data: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    def load(self) -> "PostgresConfig":
        """从配置文件加载连接信息。"""
        self._data = self._read_json(self.config_path)
        return self

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        """读取 JSON 配置，缺失或非法时返回空字典。"""
        if not path.exists():
            logger.warning(f"Postgres 配置文件不存在: {path}")
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(f"读取 Postgres 配置失败: {exc}")
            return {}
        return data if isinstance(data, dict) else {}

    # ------------------------------------------------------------------
    @property
    def host(self) -> str:
        """数据库主机。"""
        return str(self._data.get("host", "127.0.0.1"))

    @property
    def port(self) -> int:
        """数据库端口。"""
        return int(self._data.get("port", 5432))

    @property
    def user(self) -> str:
        """数据库用户名。"""
        return str(self._data.get("user", "postgres"))

    @property
    def password(self) -> str:
        """数据库密码。"""
        return str(self._data.get("password", ""))

    @property
    def database(self) -> str:
        """默认数据库名。"""
        return str(self._data.get("database", "dbvector"))

    # ------------------------------------------------------------------
    def build_uri(self) -> str:
        """构建 SQLAlchemy 连接串（psycopg 方言）。

        形如 ``postgresql+psycopg://user:password@host:port/database``。
        """
        return (
            f"postgresql+psycopg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    # ------------------------------------------------------------------
    def ensure_vector_extension(self) -> bool:
        """确保 ``vector`` 扩展已加载，返回是否成功。

        使用 psycopg 直接连接执行 ``CREATE EXTENSION IF NOT EXISTS vector``，
        不依赖 SQLAlchemy，避免方言差异。
        """
        import psycopg

        try:
            with psycopg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.database,
                connect_timeout=5,
            ) as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
            logger.info("Postgres vector 扩展已就绪")
            return True
        except Exception as exc:  # noqa: BLE001 - 由调用方决定如何处理
            logger.warning(f"初始化 vector 扩展失败: {exc}")
            return False


__all__ = ["PostgresConfig"]
