# auto-fio — Automated Flexible I/O tester

**Profile your storage device and get the optimal I/O block size — automatically.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Why

Block-sequential data pipelines (like [CFM64](https://github.com/anthony-celeres/cfm64))
need one hardware-dependent number: the **smallest block size that saturates
your device's sequential-read throughput**. Picking it by hand means running an
`fio` sweep and eyeballing the knee of the curve. `auto-fio` automates exactly
that — sweep, measure, detect the knee, return the number.

## Install

**Prerequisite: install `fio`.** `auto-fio` drives the [`fio`](https://fio.readthedocs.io/)
benchmark for its gold-standard measurements (it uses `--direct=1` to bypass the
OS page cache). Install it first so it's on your `PATH`:

```bash
# macOS
brew install fio
# Debian/Ubuntu
sudo apt install fio
# Fedora/RHEL
sudo dnf install fio
```

Then install `auto-fio`:

```bash
pip install auto-fio
```

> Without `fio`, `auto-fio` falls back to a portable, zero-dependency `python`
> backend so a result is always available — but its numbers can be optimistic
> where the OS caches the file. Install `fio` for publication-grade accuracy.
> See [Backends](#backends).
>
> If `fio` is missing, `auto-fio` **tells you at runtime** (on stderr) with the
> exact install command for your OS, then continues on the `python` backend —
> it never installs anything or touches your system for you. `--json` stdout
> stays clean. Silence the notice with `--backend python`.

## Use it — command line

```bash
auto-fio /path/on/the/device
```

```
auto-fio · backend=fio · threshold=95%

    512 KiB    1180.4 MB/s
      1 MiB    1910.2 MB/s
      2 MiB    2740.9 MB/s
      4 MiB    3120.5 MB/s
      7 MiB    3305.1 MB/s  <-- optimal
     16 MiB    3319.8 MB/s
     32 MiB    3322.0 MB/s

Optimal block size: 7340032 bytes (7.0 MiB) — reaches 95% of the 3322 MB/s peak.
```

Machine-readable output for scripts/CI: `auto-fio /data --json`.

## Use it — Python

```python
import auto_fio

# Just the number (bytes):
block_size = auto_fio.optimal_block_size("/data")

# Full sweep + metadata:
result = auto_fio.profile("/data", threshold=0.95)
print(result.optimal_block_size, result.peak_throughput_mbps, result.backend)
```

## Backends

| Backend | When | Accuracy |
|---|---|---|
| `fio` | `fio` is on `PATH` | **Gold standard** — uses `--direct=1` to bypass the OS page cache |
| `python` | fio unavailable (default fallback) | Portable, zero-dependency; cache eviction is best-effort (`F_NOCACHE`/`posix_fadvise`), so numbers can be optimistic where the OS caches the file |

Force one with `--backend fio` / `--backend python`, or `backend=...` in Python.
For publication-grade measurements, install `fio` and use the `fio` backend; the
`python` backend exists so a result is always available and to cross-check fio.

## How it decides — the "knee"

`auto-fio` measures throughput at each block size, finds the peak, and returns
the **smallest** block size that reaches `threshold` (default 95%) of that peak.
Smaller is better once saturated: it means fewer bytes buffered per read for the
same bandwidth. This decision rule lives in a pure, unit-tested function
(`auto_fio.detect_knee`) so it can be validated independently of any benchmark.

## Companion to CFM64

```python
import auto_fio
from cfm64 import CFM64Loader, TextBlockDataset

bs = auto_fio.optimal_block_size("/data/train")
dataset = TextBlockDataset("/data/train.csv", block_size_bytes=bs)
loader = CFM64Loader(dataset, batch_size=64, seed=42)
```

Run `auto-fio` **once per machine**, commit the number, and your pipeline is
tuned to that hardware — no manual `fio` step.

## License

MIT — see [LICENSE](LICENSE).
