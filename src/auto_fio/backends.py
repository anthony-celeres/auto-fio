"""Measurement backends: gold-standard ``fio`` and a portable pure-Python one."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence

Measurement = tuple[int, float]  # (block_size_bytes, throughput_mbps)

# macOS fcntl command to disable the unified buffer cache for a descriptor.
_F_NOCACHE = 48


class Backend:
    """Backend interface: measure sequential-read throughput per block size."""

    name = "base"

    def available(self) -> bool:
        return True

    def measure(
        self, path: str, block_sizes: Sequence[int], file_size: int
    ) -> list[Measurement]:
        raise NotImplementedError


class PythonBackend(Backend):
    """Portable pure-Python sequential-read benchmark.

    Writes a temporary test file on the target filesystem, then reads it back
    at each block size. Cache eviction is *best effort* (``F_NOCACHE`` on macOS,
    ``posix_fadvise(DONTNEED)`` on Linux, none on Windows), so absolute numbers
    can be optimistic where the OS caches the file. Prefer the ``fio`` backend
    (``--direct=1``) when accuracy matters; this backend exists so a result is
    always available and to validate ``fio`` against a second method.
    """

    name = "python"

    def measure(self, path, block_sizes, file_size):
        testfile = _make_test_file(path, file_size)
        try:
            out: list[Measurement] = []
            for bs in block_sizes:
                if bs > file_size:
                    continue
                nbytes, elapsed = _timed_sequential_read(testfile, bs)
                mbps = (nbytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0
                out.append((bs, mbps))
            return out
        finally:
            try:
                os.remove(testfile)
            except OSError:
                pass


class FioBackend(Backend):
    """Wraps the ``fio`` binary with direct I/O (bypasses the page cache)."""

    name = "fio"

    def available(self) -> bool:
        return shutil.which("fio") is not None

    def measure(self, path, block_sizes, file_size):
        out: list[Measurement] = []
        for bs in block_sizes:
            if bs > file_size:
                continue
            out.append((bs, _run_fio(path, bs, file_size)))
        return out


def select_backend(name: str = "auto") -> Backend:
    """Resolve a backend by name (``auto`` prefers fio, falls back to python)."""
    if name == "auto":
        fio = FioBackend()
        return fio if fio.available() else PythonBackend()
    if name == "fio":
        fio = FioBackend()
        if not fio.available():
            raise RuntimeError("fio backend requested but 'fio' is not on PATH")
        return fio
    if name == "python":
        return PythonBackend()
    raise ValueError(f"unknown backend {name!r} (use 'auto', 'fio', or 'python')")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _target_dir(path: str) -> str:
    if os.path.isdir(path):
        return path
    return os.path.dirname(os.path.abspath(path)) or "."


def _make_test_file(path: str, size: int) -> str:
    """Create a temp file of *size* bytes on the same filesystem as *path*."""
    fd, name = tempfile.mkstemp(prefix=".autofio_", dir=_target_dir(path))
    try:
        chunk = b"\0" * (1024 * 1024)
        written = 0
        with os.fdopen(fd, "wb") as f:
            while written < size:
                n = min(len(chunk), size - written)
                f.write(chunk[:n])
                written += n
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        try:
            os.remove(name)
        except OSError:
            pass
        raise
    return name


def _advise_no_cache(fd: int) -> None:
    """Best-effort request to not serve reads from the OS page cache."""
    try:
        if sys.platform == "darwin":
            import fcntl

            fcntl.fcntl(fd, _F_NOCACHE, 1)
        elif sys.platform.startswith("linux") and hasattr(os, "posix_fadvise"):
            size = os.fstat(fd).st_size
            os.posix_fadvise(fd, 0, size, os.POSIX_FADV_DONTNEED)
    except (OSError, ValueError, ImportError):
        pass


def _timed_sequential_read(name: str, bs: int) -> tuple[int, float]:
    """Read *name* sequentially in *bs*-byte chunks; return (bytes, seconds)."""
    fd = os.open(name, os.O_RDONLY)
    try:
        _advise_no_cache(fd)
        total = 0
        start = time.perf_counter()
        while True:
            block = os.read(fd, bs)
            if not block:
                break
            total += len(block)
        elapsed = time.perf_counter() - start
    finally:
        os.close(fd)
    return total, elapsed


def _run_fio(path: str, bs: int, file_size: int) -> float:
    """Run a single fio sequential-read job and return throughput in MB/s."""
    with tempfile.TemporaryDirectory(dir=_target_dir(path)) as tmp:
        cmd = [
            "fio",
            "--name=seqread",
            "--rw=read",
            f"--bs={bs}",
            f"--size={file_size}",
            "--direct=1",
            "--iodepth=1",
            f"--directory={tmp}",
            "--output-format=json",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
        # fio reports bandwidth in KiB/s.
        bw_kib = data["jobs"][0]["read"]["bw"]
        return bw_kib / 1024.0
