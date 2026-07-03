"""Tests for profiling orchestration and the pure-Python backend.

Uses tiny test files so the suite stays fast and runs on every OS in CI.
"""

import pytest

import auto_fio
from auto_fio.backends import select_backend
from auto_fio.profiler import _human


def test_python_backend_profiles(tmp_path):
    res = auto_fio.profile(
        str(tmp_path),
        block_sizes=[1 << 16, 1 << 18, 1 << 20],
        file_size=4 << 20,  # 4 MiB
        backend="python",
        threshold=0.9,
    )
    assert res.backend == "python"
    assert len(res.samples) == 3
    assert res.optimal_block_size in {1 << 16, 1 << 18, 1 << 20}
    assert res.peak_throughput_mbps > 0


def test_optimal_block_size_returns_positive_int(tmp_path):
    bs = auto_fio.optimal_block_size(
        str(tmp_path),
        block_sizes=[1 << 16, 1 << 18],
        file_size=2 << 20,
        backend="python",
    )
    assert isinstance(bs, int) and bs > 0


def test_block_sizes_larger_than_file_are_skipped(tmp_path):
    res = auto_fio.profile(
        str(tmp_path),
        block_sizes=[1 << 16, 1 << 30],  # second exceeds the 1 MiB test file
        file_size=1 << 20,
        backend="python",
    )
    assert [s.block_size for s in res.samples] == [1 << 16]


def test_all_block_sizes_too_large_raises(tmp_path):
    with pytest.raises(RuntimeError, match="no measurements"):
        auto_fio.profile(
            str(tmp_path),
            block_sizes=[1 << 30],
            file_size=1 << 20,
            backend="python",
        )


def test_no_temp_file_left_behind(tmp_path):
    auto_fio.profile(
        str(tmp_path), block_sizes=[1 << 16], file_size=1 << 20, backend="python"
    )
    leftovers = [p for p in tmp_path.iterdir() if p.name.startswith(".autofio_")]
    assert leftovers == []


def test_select_backend():
    from auto_fio.backends import Backend

    assert select_backend("python").name == "python"
    # "auto" falls back to the python backend when fio is absent; regardless,
    # it always returns a Backend instance.
    assert isinstance(select_backend("auto"), Backend)


def test_unknown_backend_raises():
    with pytest.raises(ValueError, match="unknown backend"):
        select_backend("magic")


def test_fio_backend_requires_binary(monkeypatch):
    import auto_fio.backends as backends

    monkeypatch.setattr(backends.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="not on PATH"):
        select_backend("fio")


@pytest.mark.parametrize(
    "n, expected",
    [(512, "512 B"), (1 << 20, "1.0 MiB"), (7 << 20, "7.0 MiB")],
)
def test_human_readable(n, expected):
    assert _human(n) == expected
