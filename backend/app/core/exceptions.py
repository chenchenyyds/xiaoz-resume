"""业务异常 + 统一响应"""

from typing import Any, Optional


# 业务错误码
class BizCode:
    OK = 0
    PARAM_ERROR = 40001
    AUTH_FAILED = 40101
    TOKEN_EXPIRED = 40102
    TOKEN_INVALID = 40103
    NO_PERMISSION = 40301
    NOT_FOUND = 40401
    CONFLICT = 40901
    INSUFFICIENT_POINTS = 41001
    RATE_LIMIT = 42901
    PAY_ERROR = 50001
    SMS_ERROR = 50002
    LLM_ERROR = 50003
    OSS_ERROR = 50004
    SERVER_ERROR = 50000


class BizException(Exception):
    """业务异常,被全局 handler 转成 JSON"""

    def __init__(
        self, code: int, message: str, data: Any = None, http_status: int = 200
    ):
        self.code = code
        self.message = message
        self.data = data
        self.http_status = http_status  # 业务码 HTTP 一般 200,特殊情况可改
        super().__init__(message)


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": BizCode.OK, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
