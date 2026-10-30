from typing import TypedDict, Optional


class ErrorMessage(TypedDict, total=False):
    """
    统一的错误信息格式，包含错误码、错误模块、错误消息、错误节点等信息
    """
    code: str                    # 错误码，如 PARSE_FORMAT_ERROR
    module: str                  # 错误模块
    message: str                 # 错误消息
    place: Optional[str]         # 错误节点
