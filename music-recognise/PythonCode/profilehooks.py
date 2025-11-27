"""Minimal stub of the `profilehooks` package used by the project.

This provides a no-op `profile` decorator so the project can run without
installing the external `profilehooks` package. It intentionally keeps
behavior minimal and safe for runtime.
"""
from functools import wraps
import typing

def profile(func: typing.Callable = None, **kwargs):
    """No-op decorator compatible with `from profilehooks import profile`.

    Usage:
        @profile
        def f(...):
            ...

    or

        @profile(verbose=True)
        def f(...):
            ...
    """
    if func is None:
        def decorator(f):
            @wraps(f)
            def wrapper(*a, **k):
                return f(*a, **k)
            return wrapper
        return decorator

    @wraps(func)
    def wrapper(*a, **k):
        return func(*a, **k)

    return wrapper
