import contextvars
import functools
import uuid
from typing import Any, Callable, Dict

_context_vars: Dict[str, contextvars.ContextVar] = {}


def setvars(**kwargs):
    global _context_vars

    for key, value in kwargs.items():
        if key not in _context_vars:
            context_var = contextvars.ContextVar(key)
            context_var.set(value)
            _context_vars[key] = context_var
        _context_vars[key].set(value)


def getvar(key: str, default=None) -> Any:
    global _context_vars

    if key not in _context_vars:
        return None
    return _context_vars[key].get(default)


def set_trace(value: str | None = None):
    setvars(trace=value or f"trace-{uuid.uuid4()}")


def account() -> str:
    return getvar("account", "")


def set_account(account: str):
    setvars(account=account)


def with_trace_id(func: Callable):

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        set_trace()
        return func(*args, **kwargs)

    return _wrapper


# CTX = contextvars.ContextVar[dict] = contextvars.ContextVar("CTX", default={})
