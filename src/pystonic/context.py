import contextvars
from typing import Any, Dict

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


def set_trace(value: str):
    setvars(trace=value)
