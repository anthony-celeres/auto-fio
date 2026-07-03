"""OS-aware guidance for installing the optional ``fio`` binary.

Pure and side-effect-free (like :mod:`auto_fio.knee`): given a platform string
and which backend was requested vs. actually used, decide *whether* to nudge the
user toward installing ``fio`` and *what* command to suggest. Isolated from all
I/O so the exact wording and platform selection can be unit-tested without a
shell, an OS probe, or a real benchmark run.
"""

from __future__ import annotations

import sys

# Per-platform command to install fio, matched by ``sys.platform`` prefix.
_INSTALL_COMMANDS: dict[str, str] = {
    "darwin": "brew install fio",
    "linux": "sudo apt install fio     # or: sudo dnf install fio",
    "win32": "choco install fio        # or: https://github.com/axboe/fio/releases",
}
# Shown when the platform isn't one we have a package command for.
_FALLBACK_HINT = "install fio — see https://fio.readthedocs.io"


def fio_install_command(platform: str = sys.platform) -> str:
    """Return the recommended shell command to install ``fio`` on *platform*."""
    for prefix, cmd in _INSTALL_COMMANDS.items():
        if platform.startswith(prefix):
            return cmd
    return _FALLBACK_HINT


def fio_missing_warning(
    requested_backend: str,
    effective_backend: str,
    platform: str = sys.platform,
) -> str | None:
    """Suggest installing ``fio`` when we silently fell back to ``python``.

    Returns a multi-line message (for stderr) only when the fallback was a
    *surprise*: the user asked for ``auto`` and got ``python`` because ``fio``
    was not on ``PATH``. Returns ``None`` when ``fio`` was used, or when the user
    explicitly chose ``--backend python`` (so nagging would be noise). The
    message names the exact install command for *platform*.
    """
    if effective_backend != "python" or requested_backend != "auto":
        return None
    cmd = fio_install_command(platform)
    return (
        "fio not found on PATH — using the pure-Python fallback backend, whose\n"
        "numbers can be optimistic because it cannot bypass the OS page cache.\n"
        "For publication-grade accuracy, install fio and re-run:\n"
        f"    {cmd}\n"
        "Silence this notice with: --backend python"
    )
