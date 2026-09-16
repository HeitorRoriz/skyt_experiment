"""Refuse writes into historical artifact trees."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]

PROTECTED_RELATIVE = (
    Path("outputs") / "gate0",
    Path("outputs") / "humaneval_plus" / "pilot",
)


class ProtectedOutputError(ValueError):
    """Raised when --out-dir is a frozen historical tree."""


def default_protected() -> list[Path]:
    return [REPO_ROOT / relative for relative in PROTECTED_RELATIVE]


def is_protected(out_dir: Path, frozen: Sequence[Path] | None = None) -> bool:
    target = out_dir.expanduser().resolve()
    roots = frozen if frozen is not None else default_protected()
    for root in roots:
        frozen_root = Path(root).expanduser().resolve()
        if target == frozen_root or frozen_root in target.parents:
            return True
    return False


def assert_writable(
    out_dir: Path,
    *,
    frozen: Iterable[Path] | None = None,
) -> None:
    roots = list(frozen) if frozen is not None else default_protected()
    if is_protected(out_dir, roots):
        names = ", ".join(str(path) for path in roots)
        raise ProtectedOutputError(
            f"Refusing to write into a frozen historical tree: {out_dir}. "
            f"Protected: {names}. Pick a new --out-dir "
            "(for example outputs/benchmark/)."
        )
