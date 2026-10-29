"""
全局异常处理
定义业务异常类 + FastAPI全局异常处理器注册
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.response import fail, ErrorCode


# ---------- 业务异常 ----------

class BusinessException(Exception):
    """业务异常基类"""

    def __init__(self, code: int = 400, message: str = "业务异常"):
        self.code = code
        self.message = message
        super().__init__(message)


class UnauthorizedException(BusinessException):
    """未认证异常 (401)"""

    def __init__(self, message: str = "未登录或Token已过期"):
        super().__init__(code=ErrorCode.UNAUTHORIZED, message=message)


class ForbiddenException(BusinessException):
    """无权限异常 (403)"""

    def __init__(self, message: str = "无操作权限"):
        super().__init__(code=ErrorCode.FORBIDDEN, message=message)


class NotFoundException(BusinessException):
    """资源不存在异常 (404)"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=ErrorCode.NOT_FOUND, message=message)


class ConflictException(BusinessException):
    """资源冲突异常 (409)"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(code=ErrorCode.CONFLICT, message=message)


# ---------- 全局异常处理器注册 ----------

def register_exception_handlers(app):
    """注册所有全局异常处理器"""

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        return JSONResponse(
            status_code=exc.code,
            content=fail(code=exc.code, message=exc.message).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(code=exc.status_code, message=str(exc.detail)).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            errors.append(f"{field}: {err['msg']}")
        message = "; ".join(errors) if errors else "请求参数校验失败"
        return JSONResponse(
            status_code=422,
            content=fail(code=422, message=message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=fail(code=500, message="服务器内部错误").model_dump(),
        )
