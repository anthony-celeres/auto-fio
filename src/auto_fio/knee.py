"""Saturation-knee detection — the core policy of auto-fio.

Pure, side-effect-free, and cheaply unit-tested: given (block_size, throughput)
measurements, return the smallest block size that reaches a target fraction of
peak throughput. This is deliberately isolated from all I/O so the decision
rule can be validated independently of any benchmark backend.
"""

from __future__ import annotations

from collections.abc import Sequence


def detect_knee(
    samples: Sequence[tuple[int, float]],
    threshold: float = 0.95,
) -> int:
    """Return the smallest block size that saturates throughput.

    Parameters
    ----------
    samples:
        ``(block_size_bytes, throughput_mbps)`` pairs, in any order.
    threshold:
        Fraction of peak throughput that counts as "saturated" (default 0.95).
        The knee is the smallest block size whose throughput is at least
        ``threshold * peak``.

    Returns
    -------
    int
        The recommended block size in bytes.
    """
    if not samples:
        raise ValueError("samples must be non-empty")
    if not 0.0 < threshold <= 1.0:
        raise ValueError(f"threshold must be in (0, 1] (got {threshold})")

    peak = max(t for _, t in samples)
    if peak <= 0.0:
        # No meaningful throughput measured — fall back to the smallest size.
        return min(bs for bs, _ in samples)

    target = threshold * peak
    saturating = sorted(bs for bs, t in samples if t >= target)
    return saturating[0]
