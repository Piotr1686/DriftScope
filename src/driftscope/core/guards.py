"""Runtime guards: timeout decorator + RAM limit assertion."""
from __future__ import annotations

import functools
import os
import sys
import threading
from typing import Any, Callable, TypeVar

import psutil

F = TypeVar("F", bound=Callable[..., Any])


def assert_memory_below(gb: float) -> None:
    """Raises MemoryError jeśli bieżący proces przekracza gb GB RSS."""
    used_gb = psutil.Process(os.getpid()).memory_info().rss / (1024 ** 3)
    if used_gb > gb:
        raise MemoryError(f"RAM {used_gb:.2f} GB przekracza limit {gb:.1f} GB")


def with_timeout(seconds: int) -> Callable[[F], F]:
    """Dekorator: przerywa funkcję po `seconds` sekundach.

    Windows: threading.Timer (best-effort — nie przerywa C-extensions w trakcie).
    Unix: SIGALRM (hard interrupt).
    """
    def decorator(func: F) -> F:
        if sys.platform == "win32":
            @functools.wraps(func)
            def _win_wrapper(*args: Any, **kwargs: Any) -> Any:
                result: list[Any] = [None]
                exc: list[BaseException | None] = [None]

                def _target() -> None:
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        exc[0] = e

                t = threading.Thread(target=_target, daemon=True)
                t.start()
                t.join(timeout=seconds)
                if t.is_alive():
                    raise TimeoutError(
                        f"{func.__name__}: przekroczono limit {seconds}s"
                    )
                if exc[0] is not None:
                    raise exc[0]
                return result[0]

            return _win_wrapper  # type: ignore[return-value]

        else:
            import signal

            @functools.wraps(func)
            def _unix_wrapper(*args: Any, **kwargs: Any) -> Any:
                def _handler(signum: int, frame: Any) -> None:
                    raise TimeoutError(
                        f"{func.__name__}: przekroczono limit {seconds}s"
                    )

                old = signal.signal(signal.SIGALRM, _handler)  # type: ignore[attr-defined]
                signal.alarm(seconds)  # type: ignore[attr-defined]
                try:
                    return func(*args, **kwargs)
                finally:
                    signal.alarm(0)  # type: ignore[attr-defined]
                    signal.signal(signal.SIGALRM, old)  # type: ignore[attr-defined]

            return _unix_wrapper  # type: ignore[return-value]

    return decorator  # type: ignore[return-value]
