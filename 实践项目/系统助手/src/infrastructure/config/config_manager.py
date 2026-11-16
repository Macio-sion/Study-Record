"""配置管理器。

基于 YAML 的配置读写，支持：
- 嵌套 key 点号访问（如 ``llm.ollama.model``）
- 默认值回退（default_config.yaml）
- reset_to_default 恢复默认
- 属性式访问（config.llm.ollama.model）
"""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# 目录推导：config -> infrastructure -> src -> 项目根目录
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "default_config.yaml"
_SRC_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = _SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"


class ConfigSection:
    """配置子节点，支持属性式访问与字典式访问。"""

    def __init__(self, data: Dict[str, Any]) -> None:
        object.__setattr__(self, "_data", data)

    def __getattr__(self, name: str) -> Any:
        data = object.__getattribute__(self, "_data")
        if name in data:
            value = data[name]
            return ConfigSection(value) if isinstance(value, dict) else value
        raise AttributeError(f"配置项不存在: {name}")

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        return self._data

    def __repr__(self) -> str:  # pragma: no cover - 仅调试用
        return f"ConfigSection({self._data!r})"


class ConfigManager:
    """配置管理器。"""

    def __init__(self, config_path: Optional[Path] = None, data_dir: Optional[Path] = None) -> None:
        self.data_dir: Path = Path(data_dir) if data_dir else DATA_DIR
        self.config_path: Path = Path(config_path) if config_path else (self.data_dir / "config.yaml")
        self._defaults: Dict[str, Any] = self._load_yaml(_DEFAULT_CONFIG_PATH)
        self._data: Dict[str, Any] = deepcopy(self._defaults)

    # ------------------------------------------------------------------
    # 文件读写
    # ------------------------------------------------------------------
    @staticmethod
    def _load_yaml(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f) or {}
        return content if isinstance(content, dict) else {}

    def load(self) -> "ConfigManager":
        """加载用户配置（config.yaml），合并到默认值之上。"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.config_path.exists():
            user_config = self._load_yaml(self.config_path)
            self._data = self._deep_merge(self._defaults, user_config)
        return self

    def save(self) -> None:
        """保存当前配置到 config.yaml。"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._data, f, allow_unicode=True, sort_keys=False)

    def reset_to_default(self) -> None:
        """恢复所有配置到默认值。"""
        self._data = deepcopy(self._defaults)
        self.save()

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        result = deepcopy(base)
        for key, value in (override or {}).items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result

    # ------------------------------------------------------------------
    # 点号访问
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """按点号路径读取配置，如 ``get("llm.ollama.model")``。"""
        node: Any = self._data
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set(self, key: str, value: Any) -> None:
        """按点号路径写入配置（内存中，需调用 save 持久化）。"""
        parts = key.split(".")
        node = self._data
        for part in parts[:-1]:
            child = node.get(part)
            if not isinstance(child, dict):
                child = {}
                node[part] = child
            node = child
        node[parts[-1]] = value

    # ------------------------------------------------------------------
    # 属性式访问（config.llm / config.tools 等）
    # ------------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        # 避免递归调用期间 self._data 尚未初始化
        data = self.__dict__.get("_data")
        if data is not None and name in data:
            value = data[name]
            return ConfigSection(value) if isinstance(value, dict) else value
        raise AttributeError(f"配置项不存在: {name}")

    def as_dict(self) -> Dict[str, Any]:
        return deepcopy(self._data)

    def __repr__(self) -> str:  # pragma: no cover - 仅调试用
        return f"ConfigManager(config_path={self.config_path})"


__all__ = ["ConfigManager", "ConfigSection", "PROJECT_ROOT", "DATA_DIR"]