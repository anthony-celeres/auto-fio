"""Profiling orchestration: sweep block sizes, then pick the knee."""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence

from .backends import select_backend
from .knee import detect_knee

# Default sweep: 512 KiB … 64 MiB, doubling.
_DEFAULT_SWEEP: tuple[int, ...] = tuple(1 << e for e in range(19, 27))
# Default test-file size for the pure-Python backend.
_DEFAULT_FILE_SIZE: int = 1 << 30  # 1 GiB


def _human(n: int) -> str:
    """Render a byte count as a compact binary-unit string."""
    step = 1024.0
    value = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < step or unit == "TiB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= step
    return f"{n} B"


@dataclasses.dataclass(frozen=True)
class BlockSample:
    """A single measurement: throughput at one block size."""

    block_size: int
    throughput_mbps: float


@dataclasses.dataclass(frozen=True)
class ProfileResult:
    """The full result of a profiling run."""

    samples: tuple[BlockSample, ...]
    optimal_block_size: int
    peak_throughput_mbps: float
    backend: str
    threshold: float

    def summary(self) -> str:
        """Human-readable report of the sweep and the chosen block size."""
        lines = [
            f"auto-fio · backend={self.backend} · threshold={self.threshold:.0%}",
            "",
        ]
        for s in self.samples:
            marker = "  <-- optimal" if s.block_size == self.optimal_block_size else ""
            lines.append(
                f"  {_human(s.block_size):>10}  {s.throughput_mbps:8.1f} MB/s{marker}"
            )
        lines += [
            "",
            f"Optimal block size: {self.optimal_block_size} bytes "
            f"({_human(self.optimal_block_size)}) — reaches {self.threshold:.0%} "
            f"of the {self.peak_throughput_mbps:.0f} MB/s peak.",
        ]
        return "\n".join(lines)


def profile(
    path: str = ".",
    *,
    block_sizes: Sequence[int] | None = None,
    file_size: int = _DEFAULT_FILE_SIZE,
    backend: str = "auto",
    threshold: float = 0.95,
) -> ProfileResult:
    """Profile *path*'s storage and recommend a block size.

    Parameters
    ----------
    path:
        A directory (or file whose directory) on the device to profile.
    block_sizes:
        Block sizes to sweep, in bytes (default: 512 KiB … 64 MiB).
    file_size:
        Size of the temporary test file for the pure-Python backend.
    backend:
        ``"auto"`` (fio if available, else python), ``"fio"``, or ``"python"``.
    threshold:
        Fraction of peak throughput treated as saturated (see :func:`detect_knee`).
    """
    sizes = tuple(sorted(set(block_sizes or _DEFAULT_SWEEP)))
    be = select_backend(backend)
    raw = be.measure(path, sizes, file_size)
    if not raw:
        raise RuntimeError(
            "no measurements produced (all block sizes exceeded the test-file size?)"
        )
    samples = tuple(BlockSample(bs, mbps) for bs, mbps in raw)
    optimal = detect_knee([(s.block_size, s.throughput_mbps) for s in samples], threshold)
    peak = max(s.throughput_mbps for s in samples)
    return ProfileResult(samples, optimal, peak, be.name, threshold)


def optimal_block_size(path: str = ".", **kwargs) -> int:
    """Convenience wrapper returning just the recommended block size in bytes."""
    return profile(path, **kwargs).optimal_block_size
