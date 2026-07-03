"""auto-fio — Automated Flexible I/O tester.

Profiles a storage device's sequential-read throughput across a range of block
sizes and recommends the **smallest block size that saturates throughput** —
the same "knee of the curve" you would pick by hand from an ``fio`` sweep.

Two backends:

* ``fio``   — wraps the Flexible I/O tester (``--direct=1``) when it is on
  ``PATH``. This is the gold standard: it bypasses the OS page cache.
* ``python`` — a portable pure-Python sequential-read benchmark used when
  ``fio`` is unavailable (best-effort cache eviction; see backend docs).

Companion to **CFM64**: feed the reported value straight into a dataset::

    import auto_fio
    bs = auto_fio.optimal_block_size("/data")          # bytes
    ds = TextBlockDataset("train.csv", block_size_bytes=bs)

Or from the shell::

    $ auto-fio /data
    Optimal block size: 7340032 bytes (7.0 MiB) ...
"""

from .knee import detect_knee
from .profiler import BlockSample, ProfileResult, optimal_block_size, profile

__version__ = "0.1.0"

__all__ = [
    "profile",
    "optimal_block_size",
    "detect_knee",
    "ProfileResult",
    "BlockSample",
]
