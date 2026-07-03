"""Tests for the pure knee-detection policy."""

import pytest

from auto_fio import detect_knee


def test_returns_smallest_saturating_block():
    # Throughput plateaus starting at 4 MiB.
    samples = [
        (1 << 19, 100.0),
        (1 << 20, 200.0),
        (1 << 21, 380.0),
        (1 << 22, 400.0),
        (1 << 23, 402.0),
        (1 << 24, 401.0),
    ]
    # peak = 402, target = 0.95 * 402 = 381.9 → smallest qualifying is 4 MiB.
    assert detect_knee(samples, threshold=0.95) == (1 << 22)


def test_order_independent():
    samples = [(1 << 24, 401.0), (1 << 19, 100.0), (1 << 22, 400.0)]
    assert detect_knee(samples, threshold=0.95) == (1 << 22)


def test_threshold_one_requires_peak():
    samples = [(1 << 20, 100.0), (1 << 21, 200.0), (1 << 22, 200.0)]
    assert detect_knee(samples, threshold=1.0) == (1 << 21)


def test_single_sample():
    assert detect_knee([(1 << 20, 50.0)]) == (1 << 20)


def test_zero_throughput_returns_smallest():
    assert detect_knee([(1 << 22, 0.0), (1 << 20, 0.0)]) == (1 << 20)


def test_empty_raises():
    with pytest.raises(ValueError, match="non-empty"):
        detect_knee([])


@pytest.mark.parametrize("bad", [0.0, -0.1, 1.5])
def test_bad_threshold(bad):
    with pytest.raises(ValueError, match="threshold"):
        detect_knee([(1 << 20, 1.0)], threshold=bad)
