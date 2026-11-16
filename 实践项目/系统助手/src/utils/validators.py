"""输入校验模块。

基于 Pydantic 模型对用户输入进行校验，覆盖：
- 终端命令校验
- 文件路径校验
- 环境变量名校验
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# 环境变量名合法字符（Windows 下允许字母、数字、下划线；实践中也允许部分特殊字符）
_ENV_VAR_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# 命令中危险字符（用于校验，真正的黑名单/链式检测在 system/terminal_executor.py）
_UNSAFE_CHARS = {"\x00", "\n", "\r"}


class CommandValidation(BaseModel):
    """终端命令校验模型。"""

    command: str = Field(..., min_length=1, max_length=2000)

    @field_validator("command")
    @classmethod
    def _command_must_be_clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("命令不能为空")
        if any(ch in v for ch in _UNSAFE_CHARS):
            raise ValueError("命令包含非法控制字符")
        return v


class PathValidation(BaseModel):
    """文件路径校验模型。"""

    path: str = Field(..., min_length=1, max_length=4096)

    @field_validator("path")
    @classmethod
    def _path_must_be_valid(cls, v: str) -> str:
        v = v.strip().strip('"')
        if not v:
            raise ValueError("路径不能为空")
        if any(ch in v for ch in _UNSAFE_CHARS):
            raise ValueError("路径包含非法控制字符")
        return v


class EnvVarNameValidation(BaseModel):
    """环境变量名校验模型。"""

    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def _name_must_be_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("变量名不能为空")
        if not _ENV_VAR_NAME_RE.match(v):
            raise ValueError(f"非法环境变量名: {v}")
        return v


def validate_command(command: str) -> str:
    """校验并返回清洗后的命令，非法时抛出异常。"""
    return CommandValidation(command=command).command


def validate_path(path: str) -> str:
    """校验并返回清洗后的路径，非法时抛出异常。"""
    return PathValidation(path=path).path


def validate_env_var_name(name: str) -> str:
    """校验并返回清洗后的环境变量名，非法时抛出异常。"""
    return EnvVarNameValidation(name=name).name


__all__ = [
    "CommandValidation",
    "PathValidation",
    "EnvVarNameValidation",
    "validate_command",
    "validate_path",
    "validate_env_var_name",
]