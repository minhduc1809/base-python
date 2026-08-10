from contextvars import ContextVar
from typing import Optional

# ContextVars to store thread-safe async request context
partition_code_ctx: ContextVar[Optional[str]] = ContextVar("partition_code_ctx", default=None)
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id_ctx", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id_ctx", default=None)


def get_current_partition_code() -> Optional[str]:
    return partition_code_ctx.get()


def set_current_partition_code(code: Optional[str]) -> None:
    partition_code_ctx.set(code)


def get_current_request_id() -> Optional[str]:
    return request_id_ctx.get()


def set_current_request_id(req_id: Optional[str]) -> None:
    request_id_ctx.set(req_id)


def get_current_user_id() -> Optional[str]:
    return user_id_ctx.get()


def set_current_user_id(user_id: Optional[str]) -> None:
    user_id_ctx.set(user_id)
