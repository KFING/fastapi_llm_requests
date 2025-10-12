from typing import Any


def fmt_err(err: Exception | str | None, tb: Any = None) -> str:
    if isinstance(err, Exception):
        tb = f"\n\n{tb}" if tb else ""
        return f"{type(err).__name__}: {err}{tb}".strip()
    if err is None:
        return ""
    return err.strip()
