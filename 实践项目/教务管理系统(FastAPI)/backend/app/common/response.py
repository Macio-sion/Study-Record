"""
统一响应封装
所有API返回格式: { code: int, message: str, data: any }
"""
from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class R(BaseModel, Generic[T]):
    """统一响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

    class Config:
        json_schema_extra = {
            "example": {"code": 200, "message": "success", "data": None}
        }


class PageData(BaseModel, Generic[T]):
    """分页数据模型"""
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


class PageR(BaseModel, Generic[T]):
    """分页响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[PageData[T]] = None


def _to_dict(obj):
    """将 Pydantic model 或 model 列表转为纯 dict"""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, list) and obj and isinstance(obj[0], BaseModel):
        return [o.model_dump() for o in obj]
    return obj


# ---------- 快捷构建函数 ----------

def success(data: Any = None, message: str = "success") -> R:
    """成功响应"""
    return R(code=200, message=message, data=_to_dict(data))


def success_page(
    items: list,
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "success",
) -> PageR:
    """分页成功响应"""
    items = _to_dict(items)
    return PageR(
        code=200,
        message=message,
        data=PageData(items=items or [], total=total, page=page, page_size=page_size),
    )


def fail(code: int = 400, message: str = "fail", data: Any = None) -> R:
    """失败响应"""
    return R(code=code, message=message, data=data)


# ---------- 常用错误码 ----------

class ErrorCode:
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_ERROR = 500
